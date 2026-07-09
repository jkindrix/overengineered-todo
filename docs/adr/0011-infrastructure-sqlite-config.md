# ADR-0011: SQLite persistence, models in the infrastructure package, env-driven config

- **Status:** Accepted
- **Date:** 2026-07-08
- **Deciders:** Initial author

## Context

The app must run on a developer's machine with **zero external services**, while
remaining production-shaped and configurable. We must choose a datastore, decide
where ORM models physically live given the layer layout, and settle how
configuration is supplied.

## Decision

- **Datastore: SQLite.** A single file, no server; the ORM abstracts the engine.
- **ORM models live in `tasks/infrastructure/models.py`**, not a conventional
  top-level `tasks/models.py`, to honor the layer layout. This requires setting
  `app_label = "tasks"` explicitly and importing the module in `apps.ready()` so the
  app registry discovers them. Indexes on `status`, `priority`, `-created_at` match
  the actual query paths.
- **Configuration is environment-driven** (twelve-factor) with typed helpers
  (`env_bool`, `env_list`), an optional `.env` via `python-dotenv`, a `FEATURE_FLAGS`
  dict, structured console logging, and **safe local defaults** so the app runs with
  no `.env` at all. `.env.example` documents every value read.

## Consequences

### Positive
- Runs instantly with `pip install` and nothing else — the hard requirement.
- Configurable and production-shaped without code changes; flags toggle behavior.
- Moving to PostgreSQL later is a settings change plus a migration test pass.
- Indexes are purposeful, not speculative.

### Negative
- SQLite serializes writes — unsuitable for multi-writer production
  (see [TECH_DEBT.md](../TECH_DEBT.md) #7).
- Models outside the conventional location are non-idiomatic and can surprise
  Django developers (#8).
- A hardcoded insecure default `SECRET_KEY` remains for zero-config local runs, but
  a **boot guard** now refuses to start when `DEBUG=False` and the key is still the
  default; production security settings (secure cookies, SSL redirect, HSTS) are
  gated on `not DEBUG`, so `check --deploy` passes clean with a real key (#5, #6).

### Neutral
- Feature flags are read once at startup by the container
  ([ADR-0009](0009-di-container.md)), not per request.

## Alternatives considered

- **PostgreSQL/MySQL locally** — rejected; would require a running server, breaking
  the zero-dependency goal. The ORM keeps the door open to switch later.
- **Top-level `tasks/models.py`** — idiomatic and friction-free; rejected to keep
  infrastructure concerns physically together with the rest of the layer.
- **Settings hardcoded in `settings.py`** — rejected; not portable across
  environments and mixes secrets with code.

## Related

- [ADR-0002](0002-layered-hexagonal-architecture.md),
  [ADR-0008](0008-ports-repositories-mappers.md), [TECH_DEBT.md](../TECH_DEBT.md)
