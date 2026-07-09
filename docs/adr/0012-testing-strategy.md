# ADR-0012: Test in three tiers matching the layers

- **Status:** Accepted
- **Date:** 2026-07-08
- **Deciders:** Initial author

## Context

The layered architecture creates natural test seams. We must decide how to
distribute tests so that each behavior is verified at an appropriate cost, and so
the fast feedback the architecture enables is actually realized.

## Decision

Tests are organized in **three tiers that mirror the architecture**, each placed at
the cheapest layer that can prove the behavior:

1. **Domain unit tests** (`tests/test_domain.py`) — rules, invariants, and state
   transitions on pure entities. **No database.**
2. **Application-service tests** (`tests/test_application.py`) — use-case
   orchestration and event publishing against an **in-memory `FakeRepository`** that
   satisfies the port. **No database.**
3. **Full-stack tests** (`tests/test_api.py`) — HTTP status codes, serialization,
   persistence, and the event store, through the real DB
   (`@pytest.mark.django_db`).

## Consequences

### Positive
- The bulk of behavior is verified in microseconds without a database.
- The `FakeRepository` is the concrete payoff of the ports abstraction
  ([ADR-0008](0008-ports-repositories-mappers.md)): the service is tested with zero
  infrastructure.
- Failures localize by tier, pointing at the layer at fault.
- Tests double as executable documentation of each layer's contract.

### Negative
- Three test styles to learn and maintain.
- The layering that enables fast tests is itself overkill for the trivial rules
  being guarded — the pyramid is lovely but guards a to-do list.

### Neutral
- Tier placement is a guideline in [CONTRIBUTING.md](../CONTRIBUTING.md); most new
  tests will be tier 1 or tier 3.

## Alternatives considered

- **Only full-stack tests** — simplest to reason about but slow and coarse; a rule
  bug and an HTTP bug look the same. Rejected.
- **Mocking the ORM instead of a fake repository** — rejected; brittle and couples
  tests to ORM call shapes. A protocol-shaped fake is cleaner and faster.

## Related

- [ADR-0002](0002-layered-hexagonal-architecture.md),
  [ADR-0008](0008-ports-repositories-mappers.md),
  [CONTRIBUTING.md](../CONTRIBUTING.md)
