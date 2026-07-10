# 50 lines vs. this

The single most useful thing this repository can teach is *what all the patterns
cost*. So here is the same to-do app twice.

- **The 50-line version:** [`examples/fifty_lines.py`](../examples/fifty_lines.py)
  — **67 non-blank lines, one file.** Create, list, toggle, delete. It runs:

  ```bash
  python examples/fifty_lines.py runserver   # then open http://localhost:8000
  ```

- **This repository:** **~1,450 lines of application code across 38 files**, plus
  **407 lines of tests**, **21 docs** and **13 ADRs**.

Both do the same job for the user. That ratio — **roughly 20× the code** — is the
subject of this page.

## What the extra ~1,400 lines buy (and what they cost)

Each row is a pattern the big version adds. The **ROI** column is the honest
verdict *for a to-do app* — most are ⭐ (educational) rather than ⚙️ (worth it here).

| Concern | 50-line version | This repo | Worth it for a TODO? |
|--------|-----------------|-----------|----------------------|
| Business rules | Inline in views | Rich `Task` aggregate + invariants | ⚙️ if rules grow; ⭐ here |
| Task lifecycle | A `done` boolean | 5-state machine, illegal transitions → 409 | ⭐ (a boolean is plenty) |
| Persistence | `Task.objects` directly | Repository + mappers over ORM | ⭐ (the ORM *is* the repository) |
| Framework coupling | Total (and fine) | Domain imports zero Django | ⭐ (nothing to decouple from) |
| History / audit | None | Transactional event store | ⭐ unless you truly need audit |
| Events | None | Domain events + in-process bus | ⭐ |
| Reads vs writes | Same code | CQRS-lite command/query DTOs | ⭐ |
| Wiring | Import and call | DI container / composition root | ⭐ |
| Transports | One (HTML) | REST API + web UI + health, one service | ⚙️ if you need an API |
| Validation | `if title:` | Serializers + domain validation, 400s | ⚙️ at the API edge |
| Config | Hardcoded | Env-driven + feature flags + prod hardening | ⚙️ for real deploys |
| Tests | None | 28 tests, 3 tiers, property-based + rollback | ⚙️ always worth *some* |
| Types | None | mypy-strict core + pyright | ⚙️ as it grows |

## What the 50 lines genuinely *can't* do

Being honest in both directions — the small version has real limits the moment the
problem stops being a toy:

- **No audit trail.** You cannot answer "who completed this and when?" retroactively.
- **No API.** Only server-rendered HTML; no programmatic clients.
- **Rules live in views.** A second entry point (an API, a CLI, a job) would
  duplicate or bypass them.
- **Nothing is tested**, so every change is a manual gamble.
- **The lifecycle is a boolean** — no "blocked", no "archived", no guarded
  transitions.

The layered version's value is precisely that it makes each of these a *localized*
change instead of a rewrite. That is the payoff you are buying — and for most
to-do lists, you are not buying it.

## The verdict

> **If you actually need a to-do app, ship the 50 lines.** They are correct,
> readable, and done.

This repository is not a recommendation to build to-do apps this way. It is a
faithful, working demonstration of the patterns — applied to a domain small enough
that you can hold the whole thing in your head while you study each one. The
[ADRs](adr/README.md) justify every pattern *and admit where it isn't justified*;
[TECH_DEBT.md](TECH_DEBT.md) lists what's still deliberately imperfect. Read those
next to `examples/fifty_lines.py` and the trade-offs become concrete.

The right lesson is not "always do this" or "never do this." It is: **know what
each pattern costs, so you can tell when the problem has grown big enough to earn
it.**
