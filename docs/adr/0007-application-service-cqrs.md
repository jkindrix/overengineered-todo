# ADR-0007: Orchestrate use cases in an application service with CQRS-lite DTOs

- **Status:** Accepted
- **Date:** 2026-07-08
- **Deciders:** Initial author

## Context

Something must coordinate each use case: load the aggregate, invoke domain
behavior, persist, and publish events. We must decide where that orchestration
lives and how inputs cross into it from the transports.

## Decision

A single **`TaskApplicationService`** exposes **one thin method per use case**. Each
method is pure orchestration — load, act, then commit (persist + append events in
one unit of work, see [ADR-0013](0013-transactional-unit-of-work-event-store.md))
and dispatch post-commit — with **no business logic**. Inputs are immutable **command** (write) and **query** (read)
dataclasses in `dto.py`, a light CQRS split. The service parses domain enums from
DTO strings internally, so transports never import domain internals.

## Consequences

### Positive
- One unambiguous answer to "where do rules live?": always the domain, never the
  service.
- A stable seam shared by every transport — the REST API, the web UI, the
  `seed_tasks` command, and tests all call the same methods.
- Immutable DTOs are safe value carriers; transports build them from strings.
- Command/query naming makes intent (mutate vs read) legible at a glance.

### Negative
- Another layer of indirection and DTO boilerplate between transport and domain.
- "CQRS" here is only the naming discipline, which can over-promise to readers
  expecting the full pattern (see below).

### Neutral
- The split is deliberately *lite*.

## Alternatives considered

- **Logic in views/serializers (no service)** — rejected; would duplicate
  orchestration across the REST and web transports and blur where rules live.
- **Full CQRS (separate read model / read database)** — rejected; absurd for this
  scale. We keep the cheap part (command/query naming) and skip the expensive part
  (a denormalized read side).
- **Passing raw dicts/kwargs instead of DTOs** — rejected; loses immutability and
  type clarity, and would leak domain enums into transports.

## Related

- [ADR-0002](0002-layered-hexagonal-architecture.md),
  [ADR-0008](0008-ports-repositories-mappers.md)
