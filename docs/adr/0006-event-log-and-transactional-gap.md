# ADR-0006: Persist an append-only domain-event log (and accept a known transactional gap)

- **Status:** Accepted — transactional gap **resolved by [ADR-0013](0013-transactional-unit-of-work-event-store.md)**
- **Date:** 2026-07-08
- **Deciders:** Initial author

> **Update (2026-07-09):** The non-transactional defect described below as
> consequence #1 has been **fixed**. State and events now commit atomically via a
> Unit of Work + Event Store — see [ADR-0013](0013-transactional-unit-of-work-event-store.md).
> The naming caveat (#2) still stands: this remains an audit log, not true event
> sourcing. The original text is retained below for the historical record.

## Context

We want a history of what happened to each task — an audit trail — as a
demonstration of event-driven persistence. We must decide what the log is
authoritative for and how it relates transactionally to state changes.

## Decision

We persist every published domain event to an append-only table
(`DomainEventRecord` / `tasks_domain_event`) via the `AuditTrailEventHandler`, when
`FEATURE_EVENT_SOURCING` is enabled. Payloads are stored as JSON, coerced to
JSON-safe primitives. The store is surfaced read-only in the Django admin.

**The `TaskRecord` row remains the source of truth**; the events are a parallel
history. This is a **domain-event audit log**, not true event sourcing.

## Consequences

### Positive
- A full, queryable-by-aggregate history of state changes exists.
- Decoupled from use cases (it's a subscriber), toggleable by flag.

### Negative — two honest caveats
1. **Not transactional (real defect, High severity).** The state write
   (`repository.save`) and the event write are separate DB writes, not in one
   transaction. A crash between them, or a swallowed audit-write failure
   ([ADR-0005](0005-event-bus.md)), diverges state from history. **Fix:** the
   outbox pattern (write events in the same transaction as state, then relay) or
   wrapping each use case in `transaction.atomic()`. This is the highest-value
   change available. Tracked in [TECH_DEBT.md](../TECH_DEBT.md) #1.
2. **Naming.** Calling this "event sourcing" is aspirational. True event sourcing
   makes events authoritative and rebuilds state by replaying them, with snapshots,
   versioning, and upcasting — none of which exist here. Read it as an audit log.
   Tracked in [TECH_DEBT.md](../TECH_DEBT.md) #2.

### Neutral
- JSON payloads are flexible but not typed/queryable at the DB layer.

## Alternatives considered

- **True event sourcing (events as source of truth, rebuild by replay)** — rejected
  for scope; heavy machinery (snapshots, versioning) for a to-do app.
- **`transaction.atomic()` around the use case now** — deferred, not rejected; it's
  the recommended near-term fix and is documented as such rather than silently
  implemented, to keep the demonstration wiring legible.
- **No history at all** — rejected; the audit trail is a core thing the project
  sets out to show.

## Related

- [ADR-0005](0005-event-bus.md), [TECH_DEBT.md](../TECH_DEBT.md),
  [ADR-0007](0007-application-service-cqrs.md)
