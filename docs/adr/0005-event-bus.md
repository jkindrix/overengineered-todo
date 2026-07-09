# ADR-0005: Dispatch domain events via a synchronous, in-memory bus

- **Status:** Accepted
- **Date:** 2026-07-08
- **Deciders:** Initial author

## Context

Aggregates emit domain events ([ADR-0004](0004-rich-aggregate-and-state-machine.md)).
Cross-cutting reactions — structured logging and audit persistence — must run in
response, without embedding that code in the use cases. We need a dispatch
mechanism and must choose its delivery semantics.

## Decision

We use a hand-written **`InMemoryEventBus`** with:

- **Per-type subscription** — handlers register for a concrete event class.
- **Synchronous, in-process dispatch** — handlers run inline when an event is
  published.
- **Failure isolation** — a handler that raises is caught, logged, and swallowed,
  so one bad subscriber cannot break the use case or sibling handlers.

Subscribers are wired in the container ([ADR-0009](0009-di-container.md)) per
feature flag.

## Consequences

### Positive
- Use cases stay ignorant of logging/audit; new reactions are added as subscribers
  without touching services.
- Synchronous delivery means the audit log reflects reality immediately (no
  eventual consistency to reason about).
- No external infrastructure (no broker/queue) — fits the zero-dependency goal.

### Negative
- Swallowing handler errors means an **audit-write failure is only logged, not
  surfaced** — a sharp edge that interacts with the transactional gap in
  [ADR-0006](0006-event-log-and-transactional-gap.md).
- Synchronous handlers run in the request path; a slow subscriber slows the
  request.
- We reimplemented a slice of what a signal/queue system already offers.

### Neutral
- The bus is exposed to the application only through the `EventPublisher` port, so
  it could be swapped for an async/queued implementation later.

## Alternatives considered

- **Django signals** — idiomatic and zero-code, but (a) couples the application to
  Django, violating [ADR-0002](0002-layered-hexagonal-architecture.md), and (b)
  fires on ORM lifecycle (`post_save`) — every row write, including migrations and
  admin edits — whereas we want events tied to *domain intentions*
  (`TaskCompleted`), not row saves. Rejected.
- **A real message broker (Celery/Redis/Kafka)** — rejected; enormous
  infrastructure for zero benefit at this scale, and it would make the audit log
  eventually consistent.

## Related

- [ADR-0004](0004-rich-aggregate-and-state-machine.md),
  [ADR-0006](0006-event-log-and-transactional-gap.md),
  [ADR-0009](0009-di-container.md)
