# ADR-0017: A CQRS read-model projection (status counts)

- **Status:** Accepted
- **Date:** 2026-07-10
- **Deciders:** Initial author

## Context

We already had "CQRS-lite" — separate command and query DTOs
([ADR-0007](0007-application-service-cqrs.md)) — but both sides read the same
table (`TaskRecord`). Full **CQRS** separates the *write model* from one or more
*read models* (projections): denormalized, query-shaped tables maintained by
consuming events. It is also the answer to the question event sourcing
([ADR-0016](0016-event-sourcing.md)) left open: *how do you query an event stream?*
You project it into a read model.

## Decision

Add **one** read model as a demonstration (Option B): `TaskStatistics` — a
denormalized "count of tasks per status" table, which turns a `GROUP BY` over the
write model into an O(1) read.

- **`StatisticsProjector`** — a post-commit event subscriber (wired in the
  container) that maintains the counts incrementally: `TaskCreated` → draft +1;
  `TaskStatusChanged(from, to)` → from −1, to +1; `TaskDeleted(status)` → status −1.
- **`TaskStatisticsQuery`** — the query side; reads the projection, never the write
  model.
- **`rebuild_projections`** — a command that rebuilds the read model from scratch by
  replaying the whole event log (heals any drift).
- The app keeps reading from `TaskRecord`; the projection is demonstrated (tests +
  command), not swapped in as the default.

To make the projection *correct*, hard deletes — which previously emitted no event —
now emit **`TaskDeleted`** (`Task.mark_deleted`). This also retroactively improves
event sourcing: deletions are now auditable and replayable, and
`EventSourcedTaskRepository.get` reports a deleted task as not-found (while
time-travel to before the deletion still works).

## Consequences

### Positive
- A real, query-optimized read model, kept in sync incrementally and **rebuildable
  from events** — verified to match a `GROUP BY` over the write model, including
  after deletes.
- Closes the ES → CQRS story from [ADR-0016](0016-event-sourcing.md).
- Deletions are now first-class events (auditability + replay improvement).

### Negative / caveats
- **Three representations of task data now exist** (write table, event stream, read
  projection) — for a to-do list. Peak over-engineering; the "you almost never need
  this" note is loudest here. Recorded in [TECH_DEBT.md](../TECH_DEBT.md).
- **Eventual consistency:** the projector runs *post-commit*, so there is a brief
  window where the read model lags the write (and, since the bus isolates
  subscriber failures, a failed projection is only logged). `rebuild_projections`
  heals it. Production CQRS often makes this async by design.
- The projection is a demonstration; the web dashboard still computes counts from
  the write model (wiring it to the read model is a trivial follow-on).

## Alternatives considered

- **Option A — full CQRS:** all reads move to projections; `TaskRecord` becomes
  write-only. Large, invasive, app-wide eventual consistency. Rejected as overkill.
- **Option C — skip:** the most defensible "skip" of any Phase-4 item, since we
  kept the state table and already have a fine read model. Chosen to build only to
  complete the ES → CQRS showcase.

## Related

- [ADR-0007](0007-application-service-cqrs.md) (CQRS-lite),
  [ADR-0016](0016-event-sourcing.md) (event sourcing),
  [TECH_DEBT.md](../TECH_DEBT.md); issue #32 (undo/redo).
