# Overly-Engineered TODO

[![CI](https://github.com/jkindrix/overengineered-todo/actions/workflows/ci.yml/badge.svg)](https://github.com/jkindrix/overengineered-todo/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![Django 5.2 LTS](https://img.shields.io/badge/django-5.2%20LTS-092e20)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A humble to-do list that took itself far too seriously.

It is a fully local Django web application whose only real job is tracking
tasks — implemented with a **clean/hexagonal architecture**, a **rich domain
model**, **domain events**, an append-only **domain-event audit log**, a **finite
state machine** for the task lifecycle, a **light CQRS** command/query split,
the **repository pattern**, a hand-rolled **dependency-injection container**,
**feature flags**, a **REST API**, a server-rendered **web UI**, and a health
check. It runs on SQLite with **zero external services**.

> Is any of this necessary for a TODO app? Absolutely not. That's the joke.
> Is every layer real, wired up, and tested? Yes.

---

## Documentation

Full onboarding and maintainer documentation lives in **[`docs/`](docs/README.md)**:

- **[Onboarding](docs/ONBOARDING.md)** — setup, the mental model, glossary, and a guided first change.
- **[Architecture reference](docs/ARCHITECTURE.md)** — layers, the dependency rule, request lifecycle, and a file-by-file map.
- **[Contributing & maintenance](docs/CONTRIBUTING.md)** — the golden rules and a worked "add a feature end-to-end" example.
- **[Architecture Decision Records](docs/adr/README.md)** — *why* each choice was made, with trade-offs and rejected alternatives.
- **[Tech debt & known issues](docs/TECH_DEBT.md)** — the honest register of resolved items and remaining trade-offs.

---

## Architecture

The code is organized into four concentric layers. Dependencies point strictly
inward — the domain knows nothing about Django.

```
tasks/
├── domain/           # Pure business core. No Django, no I/O.
│   ├── value_objects.py   # Priority, TaskStatus, TaskId
│   ├── entities.py        # Task aggregate root (invariants + events)
│   ├── events.py          # TaskCreated, TaskStatusChanged, ...
│   ├── state_machine.py   # Allowed lifecycle transitions
│   └── exceptions.py      # Domain errors (transport-agnostic)
│
├── application/      # Use-case orchestration. Depends on domain + ports.
│   ├── ports.py           # TaskRepository / UnitOfWork / EventStore / EventPublisher
│   ├── dto.py             # Commands (writes) & Queries (reads) — CQRS-lite
│   ├── services.py        # TaskApplicationService (one method per use case)
│   ├── event_bus.py       # Synchronous in-memory pub/sub (post-commit)
│   └── handlers.py        # Post-commit subscribers (structured logging)
│
├── infrastructure/   # Concrete adapters. The only layer that imports Django.
│   ├── models.py          # ORM records (TaskRecord, DomainEventRecord)
│   ├── mappers.py         # ORM record <-> domain entity
│   ├── repositories.py    # DjangoTaskRepository (implements the port)
│   ├── unit_of_work.py    # DjangoUnitOfWork (transaction.atomic boundary)
│   ├── event_store.py     # DjangoEventStore (transactional audit append)
│   └── container.py       # DI composition root; wires the object graph
│
└── interface/        # Transport adapters (HTTP/REST, web UI, health).
    ├── serializers.py     # DRF input validation
    ├── presenters.py      # Domain entity -> serializable dict
    ├── api_views.py       # DRF ViewSet
    ├── web_views.py       # Server-rendered pages + form actions
    ├── exceptions.py      # Domain error -> HTTP status mapping
    ├── health.py          # /healthz liveness+readiness probe
    └── urls.py            # Routes
```

**The flow of a single click:** a web form or REST call →
`serializer`/DTO → `TaskApplicationService` → `Task` aggregate (enforces
invariants + records events) → inside one **unit of work**,
`DjangoTaskRepository` persists the state *and* `DjangoEventStore` appends the
events (atomically) → after commit, events are published on the `event_bus` where
`LoggingEventHandler` logs them. State and audit trail commit or roll back together.

### The task lifecycle state machine

```
DRAFT ──▶ ACTIVE ──▶ COMPLETED
  │         │  ▲          │
  │         ▼  └──────────┘
  │       BLOCKED
  ▼         │
ARCHIVED ◀──┴──◀── (any non-terminal state)
```

Illegal transitions (e.g. `DRAFT → COMPLETED`) are rejected by the domain and
surface as HTTP `409 Conflict` from the API.

---

## Requirements

- Python 3.11+
- No database server, message broker, or other external dependency.

## Quick start

```bash
# 1. From the project root, create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) create your local env file
cp .env.example .env

# 4. Apply migrations
python manage.py migrate

# 5. (Optional) load demonstration data through the real use cases
python manage.py seed_tasks --wipe

# 6. Run it
python manage.py runserver
```

Then open:

| URL | What |
|-----|------|
| http://127.0.0.1:8000/ | Web UI (the task board) |
| http://127.0.0.1:8000/api/tasks/ | Browsable REST API |
| http://127.0.0.1:8000/healthz/ | Health check (JSON) |
| http://127.0.0.1:8000/admin/ | Django admin (see below) |

### Admin access (optional)

```bash
python manage.py createsuperuser
```

The admin exposes both the task records and the read-only event store.

---

## REST API

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/tasks/` | List tasks. Filters: `?status=`, `?priority=`, `?search=`, `?order_by=` |
| `POST` | `/api/tasks/` | Create a task (`title`, `description?`, `priority?`) |
| `GET` | `/api/tasks/{id}/` | Retrieve one task |
| `PATCH` | `/api/tasks/{id}/` | Edit `title` / `description` |
| `DELETE` | `/api/tasks/{id}/` | Delete a task |
| `POST` | `/api/tasks/{id}/priority/` | Change priority (`{"priority": "HIGH"}`) |
| `POST` | `/api/tasks/{id}/transition/` | Change status (`{"target_status": "active"}`) |

Example:

```bash
# Create
curl -s -X POST http://127.0.0.1:8000/api/tasks/ \
  -H 'Content-Type: application/json' \
  -d '{"title": "Buy milk", "priority": "HIGH"}'

# Move it through its lifecycle
curl -s -X POST http://127.0.0.1:8000/api/tasks/<id>/transition/ \
  -H 'Content-Type: application/json' -d '{"target_status": "active"}'
```

Priorities: `TRIVIAL, LOW, NORMAL, HIGH, CRITICAL`.
Statuses: `draft, active, blocked, completed, archived`.

---

## Feature flags

Set in the environment (see `.env.example`). Read once at startup by the DI
container.

| Flag | Default | Effect |
|------|---------|--------|
| `FEATURE_EVENT_SOURCING` | `True` | Persist every domain event to the event store |
| `FEATURE_EVENT_LOGGING` | `True` | Emit a structured log line per event |
| `FEATURE_STRICT_STATE_MACHINE` | `True` | Enforce lifecycle transition rules |

---

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The suite covers three levels: pure domain unit tests (no DB), application-service
tests against an in-memory fake repository (ports/adapters seam), and full-stack
API/web tests hitting the database and event store.

---

## Design notes / FAQ

- **Why are ORM models separate from domain entities?** So the domain can evolve
  independently of the schema. The repository maps between them via `mappers.py`.
- **Why an event bus for a TODO app?** No good reason. But it decouples post-commit
  side-effects (logging today, notifications later) from the use cases. Durable
  audit persistence is *not* on the bus — it goes through the transactional
  `EventStore` inside the unit of work, so state and history commit together.
- **Where does `uuid4`/`now()` live?** Only at the true edges (identity minting,
  timestamps), isolated in small helpers, keeping the rest deterministic.
- **Is this how you'd build a real TODO app?** No — a real one is ~50 lines. This
  is a loving demonstration of enterprise patterns applied with a straight face.

---

## License

Released under the [MIT License](LICENSE). © 2026 Justin Kindrix.
