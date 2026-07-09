# ADR-0008: Abstract persistence behind ports, with mapper-based repositories

- **Status:** Accepted
- **Date:** 2026-07-08
- **Deciders:** Initial author

## Context

The application must persist and query aggregates without depending on Django (the
dependency rule, [ADR-0002](0002-layered-hexagonal-architecture.md)). We must
choose how the abstraction is expressed and how domain entities relate to ORM rows.

## Decision

The application depends on **ports** defined as `typing.Protocol`s
(`TaskRepository`, `EventPublisher`) in `ports.py`. Concrete adapters
(`DjangoTaskRepository`, `InMemoryEventBus`) live in the outer layers and satisfy
the protocols **structurally** (no inheritance required). ORM records are kept
**distinct** from domain entities; `mappers.py` converts between them in both
directions. Client-supplied `order_by` values pass through a fixed whitelist before
reaching `.order_by()`.

## Consequences

### Positive
- The application is testable against an in-memory fake that simply matches the
  protocol shape ([ADR-0012](0012-testing-strategy.md)), no DB required.
- Schema and domain evolve independently; the ORM is a swappable detail.
- The order whitelist prevents arbitrary-field ordering / ORM-injection surprises
  and defines a stable public sort contract.

### Negative
- Real duplication: two shapes for a `Task` (entity + record) and hand-written
  mapping — exactly the code idiomatic Django would eliminate.
- `Protocol` structural typing gives no compile-time "did I implement everything?"
  check that an ABC's `@abstractmethod` would (mitigated by `@runtime_checkable`
  and tests).
- `save()`/`get()` do an extra fetch to give uniform `TaskNotFoundError` semantics —
  a query traded for clean errors (see [TECH_DEBT.md](../TECH_DEBT.md) #3).

### Neutral
- The mapper is the single, explicit boundary-crossing point in both directions.

## Alternatives considered

- **ABCs instead of Protocols** — more ceremony and forces inheritance on adapters
  and test doubles; rejected in favor of structural typing.
- **Use ORM models directly as the domain (no separate entities/mappers)** — the
  idiomatic Django path; rejected because it recouples the domain to Django and
  removes the ports/mappers seam the project exists to demonstrate.
- **Single `UPDATE ... WHERE id=` with affected-row count (no pre-fetch)** — faster;
  deferred in favor of clearer error semantics at this scale.

## Related

- [ADR-0002](0002-layered-hexagonal-architecture.md),
  [ADR-0007](0007-application-service-cqrs.md),
  [ADR-0011](0011-infrastructure-sqlite-config.md)
