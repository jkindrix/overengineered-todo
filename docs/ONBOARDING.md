# Onboarding

This guide gets you from a fresh clone to confidently making your first change.
Budget about 30 minutes. Read [ARCHITECTURE.md](ARCHITECTURE.md) alongside it.

## 1. Prerequisites

- Python 3.11+
- Nothing else. No database server, message broker, or Node toolchain. The app
  runs on SQLite with zero external services.

## 2. Run it locally

```bash
cd my-site

# --- Recommended: uv (fast, uses pyproject.toml + uv.lock) ---
uv sync                              # creates .venv and installs everything
source .venv/bin/activate            # Windows: .venv\Scripts\activate

# --- Or plain pip (equivalent) ---
# python3 -m venv .venv && source .venv/bin/activate
# pip install -r requirements-dev.txt

# (Optional) install git hooks that mirror CI
pre-commit install

# (Optional) create a local env file; the app also runs fine with none
cp .env.example .env

# Apply migrations, then load demo data through the real use cases
python manage.py migrate
python manage.py seed_tasks --wipe

# Run
python manage.py runserver
```

**Or run it in Docker** (no local Python needed):

```bash
docker compose up --build      # then open http://localhost:8000
```

Dependencies and all tool config live in `pyproject.toml` (the canonical source);
`requirements*.txt` are a pip-friendly mirror. Quality tooling: **ruff** (lint +
format), **mypy** (strict on the framework-free core), **pyright** (editor import
resolution), **import-linter** (architecture contracts), **pytest** + **Hypothesis**.
CI runs them all; `pre-commit run --all-files` runs them locally.

Open:

| URL | What |
|-----|------|
| http://127.0.0.1:8000/ | Web UI (the task board) |
| http://127.0.0.1:8000/api/tasks/ | Browsable REST API |
| http://127.0.0.1:8000/healthz/ | Health check (JSON) |
| http://127.0.0.1:8000/admin/ | Django admin (`createsuperuser` first) |

## 3. Run the tests

```bash
pytest
```

You should see the full suite pass in well under a second. The tests are your
safety net and your executable documentation — read them.

## 4. The mental model (read this twice)

There is **one core idea**: dependencies point inward, toward a framework-free
domain. Internalize the four layers and where each kind of code lives.

```
┌─────────────────────────────────────────────────────────────┐
│ interface/   HTTP, REST, web forms, health. Adapts transport │
│   depends on ▼                                               │
│ application/ Use cases, commands/queries, event bus.         │
│   depends on ▼                                               │
│ domain/      Entities, value objects, events, business rules │  ← imports NO framework
│   implemented by ▲                                           │
│ infrastructure/ Django ORM, repositories, DI container       │
└─────────────────────────────────────────────────────────────┘
```

**The one rule you must never break:** `domain/` may not import Django, the ORM,
or anything from `application/`, `infrastructure/`, or `interface/`. If you find
yourself wanting to `from django...` inside `tasks/domain/`, stop — the thing you
want belongs in another layer. See [ADR-0003](adr/0003-value-objects.md) and
[the golden rules](CONTRIBUTING.md#golden-rules).

### Where does my code go?

| I'm changing… | It goes in… |
|---------------|-------------|
| A business rule / invariant / what a status transition means | `tasks/domain/` |
| The steps of a use case (load → act → save → publish) | `tasks/application/services.py` |
| How data is stored or queried | `tasks/infrastructure/` |
| A REST endpoint, web page, or input validation | `tasks/interface/` |
| Wiring (which handler subscribes to which event) | `tasks/infrastructure/container.py` |

## 5. Follow one request all the way through

Trace "complete a task" end to end. Open these files in order:

1. `tasks/interface/api_views.py` → `TaskViewSet.transition` — validates input,
   builds a `TransitionTaskCommand`.
2. `tasks/application/services.py` → `transition_task` — loads the aggregate,
   calls domain behavior, saves, flushes events.
3. `tasks/domain/entities.py` → `Task.transition_to` — enforces the state
   machine, updates `completed_at`, records `TaskStatusChanged` + `TaskCompleted`.
4. `tasks/domain/state_machine.py` — the transition rules being enforced.
5. `tasks/infrastructure/repositories.py` → `DjangoTaskRepository.save` — maps the
   entity onto an ORM row and persists.
6. `tasks/application/event_bus.py` + `tasks/application/handlers.py` — the events
   get logged and appended to the audit store.

That path is the spine of the whole system. Everything else is a variation on it.

## 6. Glossary

| Term | Meaning here |
|------|--------------|
| **Aggregate / aggregate root** | The `Task` entity: the consistency boundary that owns its invariants and emits events. |
| **Value object** | Small immutable type compared by value: `Priority`, `TaskStatus`, `TaskId`. |
| **Domain event** | An immutable record that something happened (`TaskCompleted`). Emitted by the aggregate, published by the service. |
| **Port** | An abstract interface the application depends on (`TaskRepository`, `EventPublisher`) — a `typing.Protocol`. |
| **Adapter** | A concrete implementation of a port (`DjangoTaskRepository`). |
| **Repository** | The persistence port + its adapter; hides the ORM from the domain. |
| **Command / Query** | Immutable input DTOs: commands mutate, queries read (a light CQRS split). |
| **Application service** | The thin orchestrator; one public method per use case. |
| **Composition root** | The one place the object graph is wired: `infrastructure/container.py`. |
| **Presenter** | Renders a domain entity into a serializable dict for a transport. |
| **Mapper** | Converts between ORM records and domain entities. |

## 7. Your first change (guided)

A safe, representative first task: **add a `word_count` field to the presented
task** (derived, read-only) so the UI/API can show how long a description is.

1. Add the derived value in `tasks/interface/presenters.py` (`present_task`) —
   `"word_count": len(task.description.split())`.
2. Surface it in the API response (already automatic — the presenter is the API's
   output) and, if you like, in `templates/tasks/task_detail.html`.
3. Add a test in `tests/test_api.py` asserting the field appears.
4. Run `pytest`.

Notice what you did **not** have to touch: the domain, the ORM, the state machine.
That locality is the architecture paying you back. For a change that *does* reach
the domain, follow the full worked example in
[CONTRIBUTING.md](CONTRIBUTING.md#worked-example-add-a-due-date).

## 8. Where to go next

- [ARCHITECTURE.md](ARCHITECTURE.md) for the authoritative layer reference.
- [adr/](adr/README.md) whenever you ask "why is this like this?"
- [TECH_DEBT.md](TECH_DEBT.md) before you trust the word "audit" — there's a real
  transactional gap you should know about.
