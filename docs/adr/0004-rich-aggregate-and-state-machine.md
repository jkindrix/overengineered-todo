# ADR-0004: Rich aggregate that emits events; centralize the lifecycle in a state machine

- **Status:** Accepted
- **Date:** 2026-07-08
- **Deciders:** Initial author

## Context

Task behavior has invariants (non-empty title; `completed_at` must track the
COMPLETED status) and a lifecycle with legal and illegal transitions. We must
decide where those rules live and how state changes relate to the events that
record them.

## Decision

`Task` is a **behavior-rich aggregate root**. Every mutator (`transition_to`,
`change_priority`, `edit_details`) both changes state *and* appends a domain event
to an internal `_pending_events` list. The application layer drains them via
`pull_events()` after persistence (it does not publish them itself — publication is
an application concern).

The lifecycle is a **single lookup table** in `state_machine.py`
(`{state: frozenset(reachable)}`), consulted by `Task.transition_to` to enforce and
by presenters to show only valid transitions. `transition_to` also maintains the
`completed_at` invariant and emits semantic events (`TaskCompleted`,
`TaskArchived`) for notable destinations.

## Consequences

### Positive
- It is structurally impossible to change state without emitting the matching
  event.
- The lifecycle rule exists in exactly one place; UI, enforcement, and tests all
  read from it and cannot drift.
- Invariants live with the data they constrain, not scattered across views.

### Negative
- `transition_to(target, enforce=...)` threads the `STRICT_STATE_MACHINE` flag into
  a domain signature — a minor purity leak (see [TECH_DEBT.md](../TECH_DEBT.md) #5).
- The drain (`pull_events`) requires the service to remember to flush after saving;
  forgetting means events are silently lost. Encapsulated in the service to
  mitigate.

### Neutral
- `Task` is `@dataclass(eq=False)`: entities are compared by identity, not value —
  correct for an entity, but worth stating.

## Alternatives considered

- **Anemic model + logic in services** — rejected; invariants would drift out of
  the entity and events could be forgotten on some paths.
- **Scattered `if status == ... and target == ...` checks** — rejected; the classic
  way lifecycle bugs breed. The table centralizes the rule.
- **The aggregate publishes its own events** — rejected; that would couple the
  domain to the bus (an application concern), violating [ADR-0002](0002-layered-hexagonal-architecture.md).

## Related

- [ADR-0005](0005-event-bus.md),
  [ADR-0006](0006-event-log-and-transactional-gap.md),
  [ARCHITECTURE.md](../ARCHITECTURE.md#the-task-lifecycle-state-machine)
