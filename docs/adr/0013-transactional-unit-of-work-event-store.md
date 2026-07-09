# ADR-0013: Persist state and events atomically via a Unit of Work and Event Store

- **Status:** Accepted
- **Date:** 2026-07-09
- **Deciders:** Initial author
- **Supersedes:** the transactional-gap portion of [ADR-0006](0006-event-log-and-transactional-gap.md)

## Context

[ADR-0006](0006-event-log-and-transactional-gap.md) shipped the domain-event audit
log with a known, documented defect: the aggregate was persisted first, then events
were published to a fire-and-forget bus whose `AuditTrailEventHandler` wrote the
audit row in a **separate**, non-transactional DB write. Because the bus swallows
handler exceptions, a failed audit write was only logged — so a crash or error
between the two writes could leave task state and its recorded history divergent.
An independent review confirmed this as the top defect, and we chose to fix it.

The constraint: the fix must not make the application layer import Django (the
dependency rule of [ADR-0002](0002-layered-hexagonal-architecture.md)).

## Decision

We introduce two new ports and their Django adapters, and split persistence from
post-commit side-effects:

- **`UnitOfWork` port** (`application/ports.py`) — `atomic()` returns a context
  manager defining a transactional boundary. Django adapter `DjangoUnitOfWork`
  wraps `django.db.transaction.atomic`.
- **`EventStore` port** — `append(events)` durably persists events. Django adapter
  `DjangoEventStore` bulk-inserts `DomainEventRecord` rows.

`TaskApplicationService` now performs every mutation inside one unit of work:

```
with uow.atomic():
    repository.add/save(task)      # state
    events = task.pull_events()
    event_store.append(events)     # history — same transaction
dispatch(events)                   # post-commit: logging / side-effects only
```

The event bus is demoted to **post-commit side-effects** (logging today,
notifications later); it no longer carries audit persistence. Its exception
isolation is now appropriate, because a failed subscriber runs *after* the state is
safely committed and cannot corrupt it.

## Consequences

### Positive
- **State and audit history commit or roll back together.** A failed event write
  aborts the whole use case; nothing is persisted. Verified by
  `test_event_store_failure_rolls_back_state` (injects an append failure and asserts
  no task or event rows survive) and reproduced across create/edit/transition.
- The application stays framework-free — it depends on the `UnitOfWork`/`EventStore`
  ports, not Django.
- Failure surfaces (HTTP 500 / raised error) instead of being silently swallowed.
- Bus semantics are now honest: swallowing is fine for post-commit side-effects.

### Negative
- More moving parts: two new ports and two adapters, and the service takes two more
  collaborators. Proportionate to the guarantee gained.
- This is transactional (single-datastore) durability, **not** the full transactional
  outbox. For at-least-once delivery to an *external* bus, an outbox relay would
  still be the next step — but there is no external bus here, so it is unnecessary.

### Neutral
- The `FEATURE_EVENT_SOURCING` flag now gates `event_store.append`; `EVENT_LOGGING`
  gates the logging subscriber. Behavior is unchanged when both are on (the default).

## Alternatives considered

- **`transaction.atomic()` directly in the service** — simplest, but imports Django
  into the application layer, violating [ADR-0002](0002-layered-hexagonal-architecture.md).
  Rejected in favor of the `UnitOfWork` port.
- **`ATOMIC_REQUESTS = True`** — one settings line, but request-scoped (misses the
  seed command and direct service calls), coarser than use-case scope, and leaves the
  audit write inside the swallowing bus. Rejected.
- **Full transactional outbox now** — the strongest pattern, but its value is
  at-least-once delivery to an *external* consumer, which this app does not have.
  Deferred; noted as the path if an external bus is ever added.

## Related

- [ADR-0006](0006-event-log-and-transactional-gap.md) (superseded on the
  transactional point), [ADR-0009](0009-di-container.md),
  [TECH_DEBT.md](../TECH_DEBT.md)
