# Architecture Reference

This is the authoritative description of how the system is structured and why.
For the *reasoning and trade-offs* behind each decision, follow the linked ADRs.
For **C4 diagrams** (context / container / component) and a request-flow diagram,
see [architecture-diagrams.md](architecture-diagrams.md).

## Contents

- [The dependency rule](#the-dependency-rule)
- [The four layers](#the-four-layers)
- [Request lifecycle](#request-lifecycle)
- [The task lifecycle state machine](#the-task-lifecycle-state-machine)
- [Domain events and the event bus](#domain-events-and-the-event-bus)
- [File-by-file map](#file-by-file-map)
- [Data model](#data-model)
- [Configuration and feature flags](#configuration-and-feature-flags)

## The dependency rule

Source code dependencies point **inward only**:

```
interface  ──▶ application ──▶ domain ◀── infrastructure
                                  ▲              │
                                  └──────────────┘
                          (infrastructure implements
                           ports defined for the domain
                           and consumed by application)
```

- **`domain/`** depends on nothing but the Python standard library.
- **`application/`** depends on `domain/` and on abstract **ports** — never on a
  concrete adapter.
- **`infrastructure/`** and **`interface/`** are the outer ring; they may depend
  inward. Only these two layers may import Django.

Why this rule exists and what it costs:
[ADR-0002](adr/0002-layered-hexagonal-architecture.md),
[ADR-0003](adr/0003-value-objects.md).

## The four layers

### `tasks/domain/` — the pure core

Business concepts with zero framework or persistence knowledge.

- `value_objects.py` — `Priority` (`IntEnum`, ordered), `TaskStatus` (`Enum`),
  `TaskId` (UUID-backed identity). → [ADR-0003](adr/0003-value-objects.md)
- `entities.py` — the `Task` **aggregate root**. Owns invariants; every mutator
  also records a domain event. → [ADR-0004](adr/0004-rich-aggregate-and-state-machine.md)
- `events.py` — immutable event types (`TaskCreated`, `TaskStatusChanged`, …).
- `state_machine.py` — the single source of truth for allowed status transitions.
- `exceptions.py` — transport-agnostic domain errors.

### `tasks/application/` — use-case orchestration

- `ports.py` — the `TaskRepository`, `UnitOfWork`, `EventStore`, and
  `EventPublisher` **protocols** the application depends on. →
  [ADR-0008](adr/0008-ports-repositories-mappers.md),
  [ADR-0013](adr/0013-transactional-unit-of-work-event-store.md)
- `dto.py` — immutable **commands** (writes) and **queries** (reads). →
  [ADR-0007](adr/0007-application-service-cqrs.md)
- `services.py` — `TaskApplicationService`: one thin method per use case; wraps
  each mutation in a unit of work.
- `event_bus.py` — synchronous in-memory pub/sub for **post-commit** side-effects. →
  [ADR-0005](adr/0005-event-bus.md)
- `handlers.py` — post-commit subscribers: structured logging. →
  [ADR-0006](adr/0006-event-log-and-transactional-gap.md)

### `tasks/infrastructure/` — concrete adapters (the only layer that imports Django)

- `models.py` — ORM records `TaskRecord`, `DomainEventRecord`. Distinct from the
  domain entities. → [ADR-0011](adr/0011-infrastructure-sqlite-config.md)
- `mappers.py` — record ⇄ entity conversion.
- `repositories.py` — `DjangoTaskRepository` implements the persistence port.
- `unit_of_work.py` — `DjangoUnitOfWork` (transaction boundary via
  `transaction.atomic`). → [ADR-0013](adr/0013-transactional-unit-of-work-event-store.md)
- `event_store.py` — `DjangoEventStore` (transactional audit persistence). →
  [ADR-0013](adr/0013-transactional-unit-of-work-event-store.md)
- `container.py` — the **composition root**; wires the object graph once. →
  [ADR-0009](adr/0009-di-container.md)

### `tasks/interface/` — transport adapters

- `serializers.py` — DRF **input** validation only.
- `presenters.py` — render a `Task` entity → serializable dict (the **output**).
- `api_views.py` — DRF `ViewSet` (REST).
- `web_views.py` — server-rendered pages + form actions (Post/Redirect/Get).
- `exceptions.py` — maps domain errors → HTTP status codes.
- `health.py` — liveness/readiness probe with a real DB round-trip.
- `urls.py` — explicit route wiring.

All interface decisions: [ADR-0010](adr/0010-interface-adapters.md).

## Request lifecycle

Both the REST API and the web UI are thin adapters over the **same** application
service. A mutating request flows:

```
1. interface     Validate input (serializer or form), build a Command DTO.
2. application   service.<use_case>(command):
                   a. repository.get(id)            → load the aggregate
                   b. aggregate.<behavior>(...)     → domain enforces rules,
                                                       mutates state, records events
                   c. with unit_of_work.atomic():   ┐ ONE transaction:
                        repository.add/save(agg)     │   state
                        events = agg.pull_events()   │
                        event_store.append(events)   ┘   history
                   d. event_publisher.publish_all(events)  → POST-commit only
3. infrastructure In-transaction: DjangoEventStore writes the audit rows.
                   Post-commit: LoggingEventHandler logs (side-effects only).
4. interface     Presenter renders the result → JSON (API) or redirect (web).
```

State (step c, repository) and history (step c, event store) commit **atomically**
in one unit of work — if either write fails, the whole use case rolls back and
nothing is persisted. The event bus (step d) runs only after commit, so its
failure-isolating behavior can no longer corrupt persisted state
([ADR-0013](adr/0013-transactional-unit-of-work-event-store.md)).

A read request skips steps b–e: the service runs a **query**, the repository
returns entities, the presenter renders them.

Errors: the domain raises transport-agnostic exceptions (e.g.
`IllegalStateTransitionError`); `interface/exceptions.py` maps them to HTTP status
codes (404 / 409 / 400). The domain never imports `rest_framework`.

## The task lifecycle state machine

Defined once in `domain/state_machine.py`. Illegal transitions are rejected by the
domain and surface as HTTP `409 Conflict`.

```
        ┌───────────────── archive (from any non-terminal state) ──────────────┐
        ▼                                                                       │
   ┌─────────┐   start    ┌────────┐   complete   ┌───────────┐                 │
   │  DRAFT  │──────────▶ │ ACTIVE │────────────▶ │ COMPLETED │                 │
   └─────────┘            └────────┘ ◀──────────── └───────────┘                 │
        │                   │   ▲       reopen                                   │
        │                   ▼   │                                                │
        │                 ┌─────────┐                                            │
        │                 │ BLOCKED │── unblock (→ ACTIVE) ──┐                   │
        │                 └─────────┘                        │                   │
        └──────────────────────────────────────────────▶ ARCHIVED (terminal) ◀──┘
```

| From | Allowed targets |
|------|-----------------|
| `DRAFT` | `ACTIVE`, `ARCHIVED` |
| `ACTIVE` | `BLOCKED`, `COMPLETED`, `ARCHIVED` |
| `BLOCKED` | `ACTIVE`, `ARCHIVED` |
| `COMPLETED` | `ACTIVE` (reopen), `ARCHIVED` |
| `ARCHIVED` | — (terminal) |

Invariant maintained alongside status: entering `COMPLETED` sets `completed_at`;
leaving it clears `completed_at`. → [ADR-0004](adr/0004-rich-aggregate-and-state-machine.md)

## Domain events and the event bus

The aggregate accumulates events in `_pending_events` as it mutates. It does **not**
publish them — publishing is an application concern. Inside the unit of work the
service drains them (`pull_events()`), persists them via the **`EventStore`**
(transactional, durable), and — after commit — hands them to the `EventPublisher`
for side-effects.

Two distinct paths, deliberately separated:

- **`EventStore` (in-transaction, durable):** `DjangoEventStore` writes
  `DomainEventRecord` rows inside the same `atomic()` block as the state change.
  This is the audit trail; it commits or rolls back with the state.
- **`EventPublisher` / `InMemoryEventBus` (post-commit, side-effects):** synchronous,
  per-type subscription, failure-isolating (a raising handler is logged and
  swallowed). Safe to swallow, because it runs only *after* the transaction commits.
  Carries `LoggingEventHandler` (if `EVENT_LOGGING`).

Wired in the container per feature flag (`EVENT_SOURCING` gates the store append;
`EVENT_LOGGING` gates the logging subscriber). →
[ADR-0005](adr/0005-event-bus.md),
[ADR-0006](adr/0006-event-log-and-transactional-gap.md),
[ADR-0013](adr/0013-transactional-unit-of-work-event-store.md)

## File-by-file map

```
config/                     Django project (settings, urls, wsgi/asgi)
  settings.py               Env-driven config, FEATURE_FLAGS, logging
  urls.py                   Root routes: admin, /healthz, include(tasks)

tasks/
  apps.py                   AppConfig.ready(): registers models, builds container
  admin.py                  Admin for TaskRecord + read-only event store

  domain/                   Pure core (no Django)
    value_objects.py        Priority, TaskStatus, TaskId
    entities.py             Task aggregate root
    events.py               Domain event types
    state_machine.py        Allowed transitions
    exceptions.py           DomainError hierarchy

  application/              Use cases (depends on domain + ports)
    ports.py                TaskRepository, UnitOfWork, EventStore, EventPublisher
    dto.py                  Command + Query DTOs
    services.py             TaskApplicationService (mutations run in a unit of work)
    event_bus.py            InMemoryEventBus (post-commit side-effects)
    handlers.py             LoggingEventHandler

  infrastructure/           Adapters (imports Django)
    models.py               TaskRecord, DomainEventRecord
    mappers.py              record <-> entity
    repositories.py         DjangoTaskRepository
    unit_of_work.py         DjangoUnitOfWork (transaction.atomic)
    event_store.py          DjangoEventStore (transactional audit append)
    container.py            DI composition root

  interface/                Transports
    serializers.py          Input validation (DRF)
    presenters.py           Entity -> dict (output)
    api_views.py            TaskViewSet (REST)
    web_views.py            Server-rendered pages/actions
    exceptions.py           Domain error -> HTTP status
    health.py               /healthz
    urls.py                 Route wiring

  management/commands/
    seed_tasks.py           Seeds via the application service (not the ORM)

  templates/tasks/          base, task_list, task_detail
  static/tasks/app.css      Hand-rolled, theme-aware CSS

tests/
  test_domain.py            Pure domain unit tests (no DB)
  test_application.py       Service tests against a fake repository
  test_api.py               Full-stack API/web tests
```

## Data model

Two tables, both defined in `infrastructure/models.py`:

- **`tasks_task`** (`TaskRecord`) — UUID primary key; `title`, `description`,
  `priority` (int), `status` (string), timestamps, nullable `completed_at`.
  Indexed on `status`, `priority`, `-created_at` to match the query paths.
- **`tasks_domain_event`** (`DomainEventRecord`) — append-only log; `aggregate_id`,
  `event_name`, `occurred_at`, JSON `payload`, `recorded_at`. Written by the audit
  handler; surfaced read-only in the admin.

ORM records are intentionally **not** the domain entities; the repository maps
between them. → [ADR-0008](adr/0008-ports-repositories-mappers.md)

## Configuration and feature flags

All configuration is environment-driven with safe local defaults (see
`.env.example`). Feature flags are read **once** at startup by the container and
resolved into structure (which subscribers are wired, whether the state machine is
enforced).

| Flag | Default | Effect |
|------|---------|--------|
| `FEATURE_EVENT_SOURCING` | `True` | Persist every domain event to the event store |
| `FEATURE_EVENT_LOGGING` | `True` | Emit a structured log line per event |
| `FEATURE_STRICT_STATE_MACHINE` | `True` | Enforce lifecycle transition rules |

→ [ADR-0011](adr/0011-infrastructure-sqlite-config.md)
