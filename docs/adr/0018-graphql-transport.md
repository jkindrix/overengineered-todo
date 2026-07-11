# ADR-0018: Add a GraphQL transport (Strawberry)

- **Status:** Accepted
- **Date:** 2026-07-10
- **Deciders:** Initial author

## Context

The app already exposes two transports — a REST API (DRF) and a server-rendered web
UI — both thin adapters over one `TaskApplicationService`. The central claim of the
ports-and-adapters architecture is that a *third* transport should be easy and touch
nothing below the interface layer. #26 makes that concrete with a genuinely
different API paradigm.

The issue offered "gRPC and/or GraphQL". **GraphQL (Strawberry)** was chosen:

- It lives inside Django as one URL, is fully testable via the Django test client,
  and needs no codegen or separate server.
- Its **query/mutation** split mirrors our CQRS-lite **command/query** DTOs — a
  clean teaching alignment.
- gRPC's real strengths (binary perf, streaming, polyglot) are irrelevant to a
  to-do app, and its polyglot angle belongs to #25.

## Decision

Add a GraphQL schema (`tasks/interface/graphql_api.py`) with Strawberry:

- `Task` type built from **presenter output** (not the ORM — keeping the read path
  ORM-agnostic and faithful to the layering).
- **Queries** `task(id)` / `tasks(status, priority, search, orderBy)` → call
  `service.get_task` / `list_tasks`.
- **Mutations** `createTask` / `editTask` / `changePriority` / `transitionTask` /
  `deleteTask` → build command DTOs → call the service.
- Mounted at `/graphql/` (GraphiQL playground in DEBUG only), CSRF-exempt (it's an
  API; authentication arrives with #27). Domain errors surface as GraphQL errors.

Resolvers use the **same** container, service, DTOs, and presenters as REST and web.

## Consequences

### Positive
- A third transport reusing the identical core — the **cleanest demonstration of
  the ports-and-adapters payoff** on the board. `import-linter` confirms
  `graphql_api` sits entirely in the interface layer (contracts still 3/3 kept).
- Purely additive: REST and web UI unchanged. Verified end-to-end (create/query/
  list/transition/delete, and an illegal transition surfacing the domain message).

### Negative / caveats
- A GraphQL API is **🎭 redundant for a to-do app** — REST already serves it.
- Adds a runtime dependency (`strawberry-graphql`).
- CSRF-exempt and unauthenticated for now (an API posture; auth is #27). The
  GraphiQL playground is disabled outside DEBUG.

## Alternatives considered

- **gRPC** — more infrastructure (separate server + protoc codegen), weaker
  in-Django demonstration, and its polyglot strength overlaps #25. Rejected here.
- **Both** — unnecessary; GraphQL alone makes the point.

## Related

- [ADR-0007](0007-application-service-cqrs.md) (command/query DTOs),
  [ADR-0010](0010-interface-adapters.md) (interface adapters); issue #25 (polyglot),
  #27 (auth).
