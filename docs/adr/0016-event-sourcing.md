# ADR-0016: Demonstrate event sourcing (replay, snapshots, versioning)

- **Status:** Accepted
- **Date:** 2026-07-10
- **Deciders:** Initial author

## Context

The app is state-oriented: `tasks_task` holds current state (the source of truth)
and the event log is a secondary audit trail. **Event sourcing inverts this** —
events become the source of truth and current state is *derived* by replaying them.

We wanted to demonstrate event sourcing faithfully without a risky rewrite. Doing
it "for real" (dropping the state table) would force projections/CQRS for all
queries (#21) and rewrite the read path — high effort, high blast radius.

A design snag surfaced immediately, and it is itself the central lesson: **our
events were designed as an audit log (thin), not a source of truth (fat).**
`TaskCreated` lacked `description`, and `TaskDetailsEdited` recorded only *which*
fields changed, not their new values — so replay could not reconstruct them.

## Decision

Implement event sourcing **alongside** the state table (Option B):

- **Fat events.** Enrich `TaskCreated` (add `description`) and `TaskDetailsEdited`
  (carry the new `title`/`description`) so events are sufficient to reconstruct
  state. This is a schema change, motivating versioning (below).
- **Replay engine.** `Task.rebuild(events)` folds an event stream into a Task via a
  validation-free `Task._apply` (replaying trusted history skips validation).
- **Event-sourced repository.** `EventSourcedTaskRepository.get` loads a Task purely
  by replaying its events; `reconstitute_at` gives time-travel (state as of a past
  event); `take_snapshot` folds history into a `TaskSnapshot` so future reads replay
  only events after the snapshot.
- **Versioning + upcasting.** A `version` column on events + `CURRENT_EVENT_VERSION`
  + an `upcast` hook that transforms old payloads to the current schema (v1
  `TaskCreated` → v2 by defaulting `description`).
- The app **keeps using the state-based `DjangoTaskRepository`** for all reads and
  queries; the event-sourced path is proven in tests + available for demos.

## Consequences

### Positive
- State is provably **fully derivable from events** (test: rebuilt == stored,
  including an edited description), with **time-travel** and **snapshots** working,
  and a **real upcaster** (not just scaffolding).
- The running app is unaffected — existing behavior and tests stay green.
- Sets up #32 (undo/redo), which becomes nearly free with replay.

### Negative / caveats
- **Two representations now exist** (state table + event stream). True event
  sourcing would drop the state table — but then queries need projections, i.e.
  it **forces CQRS (#21)**. Documented in [TECH_DEBT.md](../TECH_DEBT.md).
- **Reconstruction is ≈, not exact, on timestamps:** rebuilt `created_at`/
  `updated_at`/`completed_at` come from event `occurred_at`, which differs by
  microseconds from the state row's `_touch()` timestamps. Business state matches
  exactly; timestamps are event-derived by design.
- `_apply` (replay) and the command methods both set state; kept safe because
  `_apply` is a dumb, validation-free setter while validation lives only in the
  command path.

## Alternatives considered

- **Option A — full event sourcing** (drop the state table; projections for all
  reads). Faithful but a large rewrite that drags in CQRS. Rejected as too invasive.
- **Option C — defer, do it with #21 (CQRS) + #32 (undo/redo)**. Honest about the
  coupling; rejected only because event sourcing *can* demonstrate standalone
  (replay, time-travel) unlike the outbox (#20).

## Related

- [ADR-0006](0006-event-log-and-transactional-gap.md),
  [ADR-0013](0013-transactional-unit-of-work-event-store.md),
  [ADR-0014](0014-tamper-evident-audit-log.md), [TECH_DEBT.md](../TECH_DEBT.md);
  issues #21 (CQRS), #32 (undo/redo).
