# Contributing & Maintenance Guide

How to change this codebase without eroding its structure. Read
[ARCHITECTURE.md](ARCHITECTURE.md) first.

## Golden rules

1. **The domain imports no framework.** Nothing under `tasks/domain/` may import
   Django, the ORM, DRF, or any of `application/`, `infrastructure/`, `interface/`.
   If you need one of those, the code belongs in a different layer.
2. **Business rules live in the domain.** A rule ("you can't complete a draft",
   "completing sets `completed_at`") goes in the aggregate or the state machine —
   never in a view, serializer, or repository.
3. **Services orchestrate; they don't decide.** `TaskApplicationService` methods
   should read: load → call domain behavior → commit (persist + append events in
   one unit of work) → dispatch post-commit. No `if` statements encoding business
   logic.
4. **Every state change emits an event.** If you add a mutator to `Task`, it must
   record a domain event, and you must wire that event type into the container's
   `_ALL_EVENT_TYPES`.
5. **The application depends on ports, not adapters.** Depend on
   `TaskRepository`/`EventPublisher`, not `DjangoTaskRepository`/`InMemoryEventBus`.
6. **Transports are thin.** Views validate input, build a DTO, call the service,
   render via a presenter. That's all.

## Coding standards

- Python 3.11+, `from __future__ import annotations` at the top of modules.
- Type-hint public functions and methods. Prefer immutable DTOs
  (`@dataclass(frozen=True, slots=True)`).
- Keep the domain deterministic: isolate `uuid4()`/`now()` in small helpers at the
  edges, as `TaskId.new` and the `_utcnow` helpers already do.
- Match the surrounding style; comments explain *why*, not *what*.

## Commit conventions

- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`.
- Describe what changed and why when it isn't obvious. Prefer small, logical
  commits over one large one. No AI/tool branding in messages.

## Testing expectations

Put each test at the cheapest layer that can prove the behavior
([ADR-0012](adr/0012-testing-strategy.md)):

| Testing… | Write it in | Needs a DB? |
|----------|-------------|-------------|
| A rule, invariant, or state transition | `tests/test_domain.py` | No |
| Use-case orchestration / event publishing | `tests/test_application.py` (fake repo) | No |
| HTTP status, serialization, persistence, event store | `tests/test_api.py` | Yes (`@pytest.mark.django_db`) |

Run `pytest` before every commit. Add or update tests with every behavior change.
If you touch the schema, run `python manage.py makemigrations tasks` and commit the
migration.

## Worked example: add a due date

A full example of a change that reaches every layer. Follow the order; it mirrors
the dependency direction (inside-out).

### 1. Domain (`tasks/domain/`)

- `entities.py`: add `due_date: datetime | None = None` to `Task`; accept it in
  the `create` factory; add a `reschedule(due_date)` mutator that validates
  (e.g. not in the past, if that's a rule), calls `_touch()`, and records a new
  `TaskRescheduled` event.
- `events.py`: add the `TaskRescheduled` event with a serializable payload
  (store the date as an ISO string).
- Add domain unit tests in `tests/test_domain.py` (no DB needed).

### 2. Application (`tasks/application/`)

- `dto.py`: add a `RescheduleTaskCommand` (and a `due_date` field on
  `CreateTaskCommand` if creation should accept it).
- `services.py`: add `reschedule_task(command)` — load, call
  `task.reschedule(...)`, then `events = self._commit(task, persist=self._repository.save)`
  and `self._dispatch(events)` (the existing helpers run the unit of work). No
  business logic here.

### 3. Infrastructure (`tasks/infrastructure/`)

- `models.py`: add `due_date = models.DateTimeField(null=True, blank=True)` to
  `TaskRecord`.
- `mappers.py`: map `due_date` in **both** directions (`record_to_entity` and
  `apply_entity_to_record`).
- `container.py`: add `TaskRescheduled` to `_ALL_EVENT_TYPES` so the logging and
  audit subscribers pick it up.
- Run `python manage.py makemigrations tasks`.

### 4. Interface (`tasks/interface/`)

- `serializers.py`: add a `RescheduleSerializer` (and a `due_date` field on
  `CreateTaskSerializer` if applicable).
- `api_views.py`: add a `@action` (e.g. `POST /api/tasks/{id}/reschedule/`) that
  validates, builds the command, calls the service, returns `present_task(task)`.
- `urls.py`: bind the new action.
- `presenters.py`: add `"due_date"` to `present_task`.
- Templates: surface it where useful.

### 5. Tests & docs

- Add an end-to-end test in `tests/test_api.py` (create → reschedule → assert the
  field and a `TaskRescheduled` row in the event store).
- If the change embodies a non-obvious decision, add or update an
  [ADR](adr/README.md).

### What this example teaches

A domain-reaching change touches **all four layers** and the container. That
breadth is the deliberate cost of the architecture
([ADR-0002](adr/0002-layered-hexagonal-architecture.md)). A change that only
affects output (like the `word_count` example in
[ONBOARDING.md](ONBOARDING.md#7-your-first-change-guided)) touches only one file.
The architecture rewards changes that respect the boundaries and punishes ones
that don't — that's the point.

## Adding or changing an event subscriber

Cross-cutting reactions (metrics, notifications) are subscribers, not inline code:

1. Write a callable handler in `application/handlers.py` accepting a `DomainEvent`.
2. Subscribe it in `infrastructure/container.py` for the event types it cares
   about, ideally behind a feature flag.
3. Remember failures are isolated (logged and swallowed) — do not rely on a
   subscriber to enforce a hard invariant. Hard invariants belong in the domain.

## The audit trail is transactional

Every use case runs inside a **unit of work**: the state write and the event-store
append commit atomically ([ADR-0013](adr/0013-transactional-unit-of-work-event-store.md)).
When you add a use case, keep the mutation inside `self._uow.atomic()` (follow the
existing `_commit` helper in `services.py`) so this guarantee holds. Durable audit
persistence goes through the `EventStore` (in-transaction), **not** the event bus —
the bus is for post-commit side-effects only, and its failures are swallowed.
