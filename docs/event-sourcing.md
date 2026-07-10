# Event sourcing (a demonstration)

The app stores each task's **current state** and treats events as an audit log.
**Event sourcing** flips that: the *events* are the source of truth, and current
state is *derived* by replaying them. This page demonstrates it — faithfully but
*alongside* the state table, so the running app is unaffected ([ADR-0016](adr/0016-event-sourcing.md)).

## The idea

Instead of storing "this task is COMPLETED", you store the sequence *TaskCreated →
TaskStatusChanged(active) → TaskStatusChanged(completed)* and **fold** it to get the
current state — like re-summing a bank ledger instead of storing a balance.

```python
task = EventSourcedTaskRepository().get(task_id)   # loaded by replaying its events
```

`Task.rebuild(events)` reconstructs the aggregate; `Task._apply(event)` is a
validation-free state-setter (replaying *trusted* history skips validation — that
already happened when the event was first produced).

## The lesson that jumps out: audit events ≠ source-of-truth events

Our events were designed as an **audit log** (thin) and turned out **too thin to
reconstruct state**: `TaskCreated` had no `description`, and `TaskDetailsEdited`
recorded only *which* fields changed, not their new values. Event sourcing needs
**fat** events. So we enriched them — which is exactly what motivates **versioning**.

## Versioning & upcasting

Events live forever, but their shape changes. Each stored event has a `version`; an
`upcast` hook transforms old payloads to the current schema on replay:

```python
# v1 TaskCreated (audit era) had no description; upcast defaults it.
upcast("TaskCreated", 1, {"title": "x", ...})  # -> {..., "description": ""}
```

## Snapshots & time-travel

- **Snapshots** (`take_snapshot`) fold history into `TaskSnapshot` so future reads
  replay only the events *after* the snapshot — keeping replay cheap.
- **Time-travel** (`reconstitute_at`) replays up to a past event: "what did this
  task look like right after it was activated?"

```python
past = repo.reconstitute_at(task_id, activated_event_id)  # status == ACTIVE
```

## Honest ROI

For a to-do app this is **🎭 pure over-engineering** — no real need for time-travel
or an immutable ledger of truth, and you pay with harder reads. It's kept as a
*demonstration alongside* the state table; the app still reads from the state row.

Two honest limits ([TECH_DEBT.md](TECH_DEBT.md)):

- **Two representations.** True event sourcing drops the state table — but then all
  queries need **projections**, i.e. it forces **CQRS (#21)**.
- **The payoff is elsewhere.** Where replay genuinely shines here is **undo/redo
  (#32)**, which it makes nearly free.

See also: [verified three ways](verified-three-ways.md) and the
[architecture reference](ARCHITECTURE.md).
