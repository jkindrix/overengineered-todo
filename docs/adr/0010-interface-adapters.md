# ADR-0010: Adapt transports in the interface layer (REST, web, health)

- **Status:** Accepted
- **Date:** 2026-07-08
- **Deciders:** Initial author

## Context

The application service must be reachable over HTTP as a REST API and as a
server-rendered web UI, and errors must map to correct HTTP semantics — all without
the domain knowing HTTP exists. We must decide how input, output, routing, and
errors are handled at the edge.

## Decision

The `interface/` layer holds thin transport adapters:

- **Input** is validated by DRF **serializers** (`serializers.py`) — used *only* for
  validation, with the domain enums as the source of truth for choices.
- **Output** is produced by **presenters** (`presenters.py`) that render a domain
  entity into a serializable dict (including derived fields like
  `allowed_transitions`). `list` paginates the presented results with DRF's
  `PageNumberPagination`, honoring the project-wide `PAGE_SIZE` and returning the
  standard `count`/`next`/`previous`/`results` envelope.
- **REST** uses a DRF `ViewSet` with **manual** `as_view({...})` route binding in
  `urls.py` (not a router), so the API surface is greppable in one file.
- **Errors:** `interface/exceptions.py` maps domain exceptions to HTTP status codes
  (`TaskNotFoundError→404`, `IllegalStateTransitionError→409`, validation→400),
  checked most-specific-first. The domain never imports `rest_framework`.
- **Web UI** is server-rendered with Post/Redirect/Get, CSRF tokens, Django
  messages, and no JavaScript build step.
- **Health:** `/healthz` performs a real `SELECT 1` and returns 503 on failure.

## Consequences

### Positive
- REST and web are two thin adapters over one service — the layering's payoff,
  demonstrated.
- HTTP concerns are quarantined at the edge; the domain stays transport-agnostic.
- Manual routing and validation-only serializers keep the surface explicit.
- PRG + CSRF give a correct, dependency-free UI that runs with only `pip install`.

### Negative
- Presenters mean output shaping is hand-written rather than derived from a
  `ModelSerializer`.
- Manual `as_view` binding is more verbose and hand-maintained than a router.
- The web UI has no client-side interactivity (no live updates/optimistic UI).

### Neutral
- `ModelSerializer` was never an option for output because our domain objects are
  entities, not ORM models.

## Alternatives considered

- **DRF `DefaultRouter`** — more concise; rejected in favor of explicit, greppable
  routes.
- **`ModelSerializer`/`ModelViewSet` for output** — rejected; assumes ORM models as
  the domain object, which we deliberately don't have ([ADR-0008](0008-ports-repositories-mappers.md)).
- **A JS SPA front end** — rejected; adds a build pipeline against the
  zero-dependency, runs-instantly goal. Server rendering fits the scope.

## Related

- [ADR-0007](0007-application-service-cqrs.md),
  [ADR-0008](0008-ports-repositories-mappers.md)
