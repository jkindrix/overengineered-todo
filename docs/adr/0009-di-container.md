# ADR-0009: Wire the object graph in a DI container / composition root

- **Status:** Accepted
- **Date:** 2026-07-08
- **Deciders:** Initial author

## Context

The object graph — event bus, its subscribers, repository, application service — must
be constructed and connected somewhere, exactly once, honoring feature flags. We
must decide where wiring lives and how instances are shared.

## Decision

A single **`Container`** (the composition root) constructs the graph and wires
event-bus subscribers according to `settings.FEATURE_FLAGS`, read **once** at
startup. It is exposed as a process-wide singleton via `get_container()` using
double-checked locking for thread safety; `reset_container()` lets tests rebuild
with fresh state. The container is built in `apps.ready()`.

## Consequences

### Positive
- All wiring is in one greppable place; no service-locator calls buried in business
  code. Collaborators are injected, not fetched from globals.
- Feature flags are resolved into *structure* (which subscribers exist, whether the
  state machine is enforced) rather than re-checked per request.
- Subscriptions are established exactly once — no doubled log lines or audit rows.

### Negative
- A module-level singleton is a controlled global; it complicates parallel test
  isolation (hence `reset_container`, see [TECH_DEBT.md](../TECH_DEBT.md) #4).
- Hand-rolled DI has no scoping/lifetime management a full framework would provide.

### Neutral
- The container legitimately holds process-wide state (the bus and subscriptions),
  so a singleton is a defensible fit here.

## Alternatives considered

- **A DI framework (`dependency-injector`, `punq`)** — offers scopes and lifetimes;
  rejected as more machinery than a to-do app can justify. ~30 lines by hand suffice.
- **Global singletons constructed at import time** — rejected; import-time side
  effects are brittle and hard to reset in tests. `ready()` + lazy first-use is
  safer.
- **Per-request construction** — rejected; would re-subscribe handlers repeatedly
  and defeat the "wire once" goal.

## Related

- [ADR-0005](0005-event-bus.md),
  [ADR-0002](0002-layered-hexagonal-architecture.md)
