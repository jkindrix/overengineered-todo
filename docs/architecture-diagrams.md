# Architecture diagrams (C4)

These are [C4-model](https://c4model.com/) views — Context, Container, Component —
rendered with Mermaid (they display inline on GitHub and in the docs site). Read
them alongside [ARCHITECTURE.md](ARCHITECTURE.md), which is the prose reference.

## Level 1 — System context

*Who uses the system and what it depends on.*

```mermaid
C4Context
title System Context — Overly-Engineered TODO
Person(user, "User", "Creates and manages tasks")
System(todo, "Overly-Engineered TODO", "Tracks tasks via a web UI and a REST API")
SystemDb(db, "SQLite", "Tasks and the append-only domain-event log")
Rel(user, todo, "Uses", "HTTPS")
Rel(todo, db, "Reads / writes", "SQL")
```

## Level 2 — Containers

*The runtime pieces inside the system.* Both transports are thin adapters over the
**one** application core.

```mermaid
C4Container
title Container diagram — Overly-Engineered TODO
Person(user, "User")
System_Boundary(sys, "Overly-Engineered TODO") {
  Container(web, "Web UI", "Django templates", "Server-rendered task board (PRG forms)")
  Container(api, "REST API", "Django REST Framework", "JSON API + browsable API")
  Container(app, "Application core", "Python (hexagonal)", "Use cases, domain, wiring")
  ContainerDb(db, "SQLite", "Database", "tasks_task + tasks_domain_event")
}
Rel(user, web, "Uses", "HTTPS")
Rel(user, api, "Calls", "HTTPS / JSON")
Rel(web, app, "Invokes use cases")
Rel(api, app, "Invokes use cases")
Rel(app, db, "Persists via the ORM", "SQL")
```

## Level 3 — Components (inside the application core)

*How the layers fit together.* Dependencies point inward toward the framework-free
domain; the `import-linter` contracts enforce exactly these arrows.

```mermaid
C4Component
title Component diagram — the application core
Container_Boundary(core, "Application core") {
  Component(iface, "Interface adapters", "api_views, web_views, serializers, presenters", "REST + web + health")
  Component(svc, "TaskApplicationService", "application", "One method per use case; runs the unit of work")
  Component(domain, "Domain", "Task aggregate, state machine, events", "All business rules")
  Component(repo, "DjangoTaskRepository", "infrastructure", "Implements the persistence port")
  Component(uow, "UnitOfWork + EventStore", "infrastructure", "Transactional state + audit writes")
  Component(bus, "Event bus", "application", "Post-commit subscribers (logging)")
}
ContainerDb(db, "SQLite", "Database")
Rel(iface, svc, "calls (via commands/queries)")
Rel(svc, domain, "invokes behavior")
Rel(svc, repo, "loads / saves (port)")
Rel(svc, uow, "commits within")
Rel(svc, bus, "publishes after commit")
Rel(repo, db, "SQL")
Rel(uow, db, "SQL (one transaction)")
```

## The request lifecycle

*One mutating request, end to end* (see also
[ARCHITECTURE.md](ARCHITECTURE.md#request-lifecycle)).

```mermaid
flowchart TD
  A[HTTP request] --> B[Interface: validate input, build a Command DTO]
  B --> C[Application service]
  C --> D[Domain aggregate: enforce rules, mutate, record events]
  D --> E{unit of work · atomic}
  E --> F[Repository: persist state]
  E --> G[Event store: append events]
  F --> H[(SQLite)]
  G --> H
  E -->|commit| I[Event bus: post-commit logging / side-effects]
  I --> J[Presenter: render JSON or redirect]
```
