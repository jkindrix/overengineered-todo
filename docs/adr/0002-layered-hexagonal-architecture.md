# ADR-0002: Adopt a layered / hexagonal architecture

- **Status:** Accepted
- **Date:** 2026-07-08
- **Deciders:** Initial author

## Context

We need a structure for a Django app whose stated purpose is to *demonstrate*
enterprise patterns applied faithfully. The central question is where business
rules live relative to the framework. The idiomatic Django answer ("fat models"
with the ORM model as the domain object) tightly couples rules to Django.

## Decision

We use a **four-layer hexagonal (ports-and-adapters) architecture** —
`domain → application → infrastructure/interface` — with dependencies pointing
strictly **inward**. The domain is the center; the framework is an outer detail.
The dependency rule is enforced by convention and by keeping the domain
import-free of Django (see [ADR-0003](0003-value-objects.md)).

## Consequences

### Positive
- Business rules are independent of Django and testable without a database
  (see [ADR-0012](0012-testing-strategy.md)).
- Clear "where does this code go?" answers; changes localize by layer.
- Transports (REST, web) are interchangeable adapters over one service.

### Negative
- Substantial ceremony: mappers, ports, DTOs, a container, and duplicate
  Task shapes (entity vs ORM record) that idiomatic Django would eliminate.
- A domain-reaching change touches all four layers (see the worked example in
  [CONTRIBUTING.md](../CONTRIBUTING.md)).
- The payoff (framework independence) only materializes in large, long-lived,
  logic-heavy systems — which a to-do app is not.

### Neutral
- This is the core of the project's intentional over-engineering. It is
  implemented faithfully so the pattern is real, not cargo-culted.

## Alternatives considered

- **Idiomatic Django MTV / fat models** — the *correct* choice for a real to-do
  app: ~80 lines, instantly familiar, ORM does the work. Rejected here only because
  it wouldn't demonstrate the layered pattern the project exists to show. For any
  genuinely small app, prefer this.
- **Service layer over Django models (no pure domain)** — a lighter middle ground
  (services + ORM models, no separate entities). Rejected because it still couples
  rules to the ORM and wouldn't exercise the ports/mappers seam.

## Related

- [ARCHITECTURE.md](../ARCHITECTURE.md), [TECH_DEBT.md](../TECH_DEBT.md),
  [ADR-0003](0003-value-objects.md)
