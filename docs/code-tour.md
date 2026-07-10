# Annotated code tour

Follow **one request** — *completing a task via the REST API* — through every
layer. Each stop names the file, shows the essential code, and explains why it's
there. Read it with the files open. For the big picture first, see
[architecture-diagrams.md](architecture-diagrams.md).

> Excerpts are lightly trimmed (type hints and comments removed) for readability —
> open the named file for the exact source.

The request:

```http
POST /api/tasks/{id}/transition/
{ "target_status": "completed" }
```

---

## Stop 1 — the route · `tasks/interface/urls.py`

Actions are bound to URLs explicitly (no router magic), so the whole API surface
is greppable in one file:

```python
task_transition = TaskViewSet.as_view({"post": "transition"})
# ...
path("api/tasks/<uuid:pk>/transition/", task_transition, name="api-task-transition"),
```

## Stop 2 — the transport adapter · `tasks/interface/api_views.py`

The view is thin: validate input, build a **command DTO**, delegate, render. It
holds no business logic.

```python
@action(detail=True, methods=["post"])
def transition(self, request, pk):
    serializer = TransitionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    task = self.service.transition_task(
        TransitionTaskCommand(task_id=pk, target_status=serializer.validated_data["target_status"])
    )
    return Response(present_task(task))
```

Why: the same `TransitionTaskCommand` is used by the web UI and the seed command,
so every transport shares one code path ([ADR-0007](adr/0007-application-service-cqrs.md)).

## Stop 3 — the use case · `tasks/application/services.py`

`TaskApplicationService.transition_task` orchestrates; it does not decide:

```python
def transition_task(self, command):
    task = self._repository.get(TaskId.parse(command.task_id))     # load
    task.transition_to(                                            # act (domain decides)
        TaskStatus.from_value(command.target_status),
        enforce=self._strict_state_machine,
    )
    events = self._commit(task, persist=self._repository.save)     # persist + append (atomic)
    self._dispatch(events)                                         # post-commit side-effects
    return task
```

## Stop 4 — the business rule · `tasks/domain/entities.py`

The `Task` aggregate owns the invariant. It changes state **and** records the
event together — you cannot do one without the other:

```python
def transition_to(self, target, *, enforce=True):
    if target == self.status:
        return
    if enforce and not state_machine.can_transition(self.status, target):
        raise IllegalStateTransitionError(current=self.status.value, requested=target.value)
    previous, self.status = self.status, target
    self._touch()
    if target == TaskStatus.COMPLETED:
        self.completed_at = self.updated_at          # invariant kept in lockstep
    elif previous == TaskStatus.COMPLETED:
        self.completed_at = None
    self._record(ev.TaskStatusChanged(aggregate_id=str(self.id), from_status=previous.value, to_status=target.value))
    if target == TaskStatus.COMPLETED:
        self._record(ev.TaskCompleted(aggregate_id=str(self.id)))
```

## Stop 5 — the rule table · `tasks/domain/state_machine.py`

The lifecycle lives in exactly one place, read by both the entity (to enforce) and
the presenter (to show only valid buttons):

```python
_ALLOWED_TRANSITIONS = {
    TaskStatus.ACTIVE: frozenset({TaskStatus.BLOCKED, TaskStatus.COMPLETED, TaskStatus.ARCHIVED}),
    # ...
}
def can_transition(current, requested):
    return current != requested and requested in _ALLOWED_TRANSITIONS.get(current, frozenset())
```

## Stop 6 — the transaction · `tasks/application/services.py` (`_commit`)

State and history commit together, or not at all — the fix for the old audit gap
([ADR-0013](adr/0013-transactional-unit-of-work-event-store.md)):

```python
def _commit(self, task, *, persist):
    with self._uow.atomic():
        persist(task)                     # state row
        events = task.pull_events()       # drain
        if self._event_sourcing and events:
            self._event_store.append(events)   # audit rows — same transaction
    return events
```

## Stop 7 — persistence & mapping · `tasks/infrastructure/repositories.py`, `mappers.py`

The repository maps the domain entity onto an ORM row — the domain never sees the
ORM:

```python
def save(self, task):
    record = TaskRecord.objects.get(pk=task.id.value)   # raises -> TaskNotFoundError
    apply_entity_to_record(task, record)
    record.save(force_update=True)
```

## Stop 8 — the adapters · `tasks/infrastructure/unit_of_work.py`, `event_store.py`

`DjangoUnitOfWork.atomic()` wraps `transaction.atomic`; `DjangoEventStore.append`
bulk-inserts `DomainEventRecord` rows inside it. Both are tiny — the interesting
part is that they satisfy application-layer *ports*, so the application stays
Django-free.

## Stop 9 — post-commit reactions · `tasks/application/event_bus.py`, `handlers.py`

After the transaction commits, `_dispatch` publishes to the bus. The
`LoggingEventHandler` logs; failures here are isolated and can't corrupt state
(it already committed). Durable audit is *not* here — it's transactional (Stop 6).

## Stop 10 — rendering · `tasks/interface/presenters.py`

`present_task` turns the aggregate into a plain dict (including derived fields like
`allowed_transitions`) for JSON — keeping the domain's value objects out of the
serializer.

## The error path

If you POST `completed` to a `draft` task, Stop 4 raises
`IllegalStateTransitionError`. It bubbles up untouched until
`tasks/interface/exceptions.py` maps it to **HTTP 409** — the only place the domain
meets HTTP. The domain never imports `rest_framework`.

---

## Design journal — why the architecture accreted

A short narrative of *why* each layer exists (the ADRs have the full reasoning):

1. **Start honest.** The whole app is [67 lines](fifty-lines-vs-this.md). Everything
   below is deliberately more than a to-do list needs — the point is to see the cost.
2. **Pull rules out of views** into a rich aggregate so they can't be bypassed or
   duplicated across transports ([ADR-0004](adr/0004-rich-aggregate-and-state-machine.md)).
3. **Free the domain from Django** so rules are testable in microseconds and the
   framework is a detail ([ADR-0002](adr/0002-layered-hexagonal-architecture.md),
   [ADR-0003](adr/0003-value-objects.md)). Enforced by `import-linter`.
4. **Add ports** so persistence and events are swappable seams, testable with fakes
   ([ADR-0008](adr/0008-ports-repositories-mappers.md)).
5. **Record events** for a history, then make that history **transactional** once we
   admitted the first design could diverge ([ADR-0006](adr/0006-event-log-and-transactional-gap.md)
   → [ADR-0013](adr/0013-transactional-unit-of-work-event-store.md)).
6. **Wire it once** in a composition root ([ADR-0009](adr/0009-di-container.md)).
7. **Keep transports thin** and mapped cleanly onto HTTP
   ([ADR-0010](adr/0010-interface-adapters.md)).

Every step is a localized change *because* of the boundaries — that locality is the
payoff the extra code buys. Whether it's worth buying is
[the whole question](fifty-lines-vs-this.md).
