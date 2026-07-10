# Documentation

Welcome to the **Overly-Engineered TODO** documentation. This tree exists to get
new engineers productive quickly and to preserve *why* the codebase is shaped the
way it is, so maintainers can change it safely.

> A note on tone: this project is a deliberately over-engineered to-do list. The
> patterns are real, faithfully implemented, and tested — but several of them are
> unjustified for a to-do app in production. The docs are candid about which
> patterns earn their keep and which are here to demonstrate a technique. See
> [ADR-0002](adr/0002-layered-hexagonal-architecture.md) and
> [TECH_DEBT.md](TECH_DEBT.md) for the honest accounting.

## Start here

| If you want to… | Read |
|-----------------|------|
| Get the app running and understand the mental model | [ONBOARDING.md](ONBOARDING.md) |
| Understand the layers, the dependency rule, and the request lifecycle | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Add a feature or fix a bug the "right" way | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Know *why* a decision was made (and what we rejected) | [adr/](adr/README.md) |
| See known weaknesses and deferred work | [TECH_DEBT.md](TECH_DEBT.md) |
| See where this is headed (and the teaching-tool ambition) | [ROADMAP.md](ROADMAP.md) |

## The 60-second overview

The code is organized into four concentric layers with dependencies pointing
strictly inward:

```
interface  ─┐  (HTTP/REST, web UI, health) — adapts transports
            ▼
application ─┐ (use cases, DTOs, event bus) — orchestrates
            ▼
   domain   ◄─ (entities, value objects, events, rules) — the pure core
            ▲
infrastructure ┘ (Django ORM, repositories, DI container) — implements ports
```

The domain at the center imports **no framework code**. Everything else depends
inward toward it. A single user action flows:

```
HTTP request → serializer/DTO → application service → domain aggregate
   → repository (persist) → domain events published → subscribers (log + audit)
```

## Document map

- **[ONBOARDING.md](ONBOARDING.md)** — setup, the mental model, a glossary, and a
  guided first change.
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — the authoritative reference: the
  dependency rule, every layer, the request lifecycle, the state machine, and a
  file-by-file map.
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — conventions, the golden rules, and a
  complete worked example of adding a new use case through every layer.
- **[TECH_DEBT.md](TECH_DEBT.md)** — the known-issues register, including the one
  real defect (non-transactional event writes) and the "event sourcing" naming
  correction.
- **[adr/](adr/README.md)** — Architecture Decision Records. One record per major
  decision, each with context, the decision, consequences, and the alternatives
  we rejected.
