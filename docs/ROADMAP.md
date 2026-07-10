# Roadmap

This roadmap catalogs ways to extend the Overly-Engineered TODO — and, more
importantly, states *why* each is or isn't worth doing. It exists because the
project's whole thesis is **architectural trade-off literacy**: applying heavy
patterns faithfully to a domain that doesn't need them, with candid ROI
accounting. A roadmap without that accounting would betray the point.

Work is organized into four **tracks**, each mapped to a GitHub milestone. The
full 15-axis catalog follows as an appendix.

## How to read this

Every item is tagged:

- ⭐ **teaching-lever** — materially advances the "authoritative teaching tool" goal
- ⚙️ **genuine** — a real production-grade improvement, over-engineering aside
- 🎭 **bit** — an over-engineering *demonstration*: low practical value, high
  pedagogical value (on-brand for this repo)

Effort: **S** (hours) · **M** (a day or two) · **L** (multi-day).

> **Guardrail.** Nothing here should quietly turn this into "how you should build a
> TODO app." The satire is load-bearing: every heavyweight addition must keep its
> honest ROI note, and the "50 lines vs this" contrast (Track A) must stay
> prominent. See [the positioning note](#is-this-an-authoritative-teaching-tool).

---

## Track A — Teaching Tool ⭐

*Milestone: **Teaching Tool**. Goal: make the concepts self-enforcing, navigable,
and comparative — not merely asserted.*

| Item | Tags | Effort |
|------|------|--------|
| `import-linter` enforcing the hexagonal dependency rule in CI | ⭐⚙️ | M |
| Hypothesis property-based tests modeling the state machine | ⭐⚙️ | M |
| MkDocs Material docs site on GitHub Pages, [Diátaxis](https://diataxis.fr/) structure | ⭐⚙️ | L |
| C4-model diagrams (Structurizr/Mermaid) rendered in the docs | ⭐ | M |
| "Same TODO in ~50 lines vs. this" side-by-side (`examples/fifty_lines.py`) | ⭐ | S |
| "Chapters" branches/tags — the architecture accreting step by step | ⭐ | L |
| Annotated code tour + narrative design journal | ⭐ | M |

**Why this track first for the teaching goal:** enforcement (import-linter,
Hypothesis) converts every architectural *claim* into a CI-checked *guarantee* —
the single biggest credibility multiplier.

## Track B — Engineering Rigor ⚙️

*Milestone: **Engineering Rigor**. Goal: spotless under its own tooling — a
teaching repo must not fail its own linters.*

| Item | Tags | Effort |
|------|------|--------|
| `pyrightconfig.json` + `mypy --strict`; close type gaps | ⚙️ | M |
| `ruff` (lint + format) + `pre-commit` hooks | ⚙️ | S |
| Migrate to `pyproject.toml` (PEP 621) + `uv` | ⚙️ | M |
| CI matrix: Python 3.11–3.13 × Django 5.2 LTS / 6.0 | ⚙️ | S |
| Coverage gate + Codecov badge | ⚙️ | S |
| Security scanning: `bandit`, `pip-audit`, CodeQL, Dependabot | ⚙️ | M |
| Dockerfile + docker-compose + devcontainer/Codespaces | ⚙️ | M |
| Conventional-commit enforcement + `semantic-release` + `CHANGELOG.md` | ⚙️ | M |

## Track C — Over-Engineering Showcase 🎭

*Milestone: **Over-Engineering Showcase**. Goal: faithful, tested implementations
of heavyweight patterns — each with a prominent "you almost never need this" note.*

| Item | Tags | Effort |
|------|------|--------|
| Transactional **outbox** + relay + idempotency keys | ⚙️🎭 | L |
| Full **CQRS**: separate read models + projections | 🎭 | L |
| **Real event sourcing**: rebuild-by-replay + snapshots + event versioning/upcasting | 🎭 | L |
| **Hash-chained tamper-evident** audit log | 🎭⭐ | M |
| **TLA+ / Alloy** spec of the state machine, model-checked in CI | 🎭⭐ | L |
| **Polyglot port** — reimplement the domain in a second language (Rust/Go/TS) | 🎭⭐ | L |
| gRPC and/or GraphQL adapter over the same application service | 🎭 | M |

## Track D — Product Realism ⚙️

*Milestone: **Product Realism**. Goal: close the "toy" gap (no auth, single-user)
that currently caps realism.*

| Item | Tags | Effort |
|------|------|--------|
| Authentication (sessions → OAuth2/OIDC → passkeys) | ⚙️ | L |
| Authorization: RBAC + object-level permissions (Casbin/OPA) | ⚙️ | M |
| Core features: tags, subtasks, dependencies, recurring tasks, reminders | ⚙️ | L |
| Background jobs (Celery/Dramatiq) + scheduled recurring tasks | ⚙️ | M |
| WebSockets live updates (Django Channels) | ⚙️ | M |
| Undo/redo powered by the event log | ⚙️⭐ | M |
| Import/export (CSV/JSON/iCal) + outbound webhooks | ⚙️ | M |
| PWA/offline + accessibility (WCAG) + i18n | ⚙️ | L |

---

## Is this an authoritative teaching tool?

**Yes for a specific niche; no as a broad canonical reference — and the niche is
open.**

The exact patterns here (hexagonal + DDD + event-driven Python: repositories,
Unit of Work, service layer) are already canonically taught by **"Architecture
Patterns with Python" (Percival & Gregory, *Cosmic Python*)**, free online and
widely cited. This project will not out-canon that book on the patterns themselves.

**The open niche it can own:** a reference on **deliberate over-engineering and
trade-off literacy** — *every* pattern applied faithfully to a domain that doesn't
need them, with honest ROI accounting for each. Cosmic Python teaches *when* to use
these patterns on a realistic domain; this teaches *what they cost and how to
judge them* by over-applying them on purpose. The candor (the
[tech-debt register](TECH_DEBT.md), ADRs that admit "no good reason", the
50-lines-vs-this contrast) is the differentiator.

### The path to authoritative (6 moves)

1. ⭐ **Make the concepts executable, not asserted** — `import-linter` + Hypothesis
   + a TLA+ spec, so CI fails on any violation of the architecture (Track A/C).
2. ⭐ **A hosted docs site** (Pages, Diátaxis) with rendered C4 diagrams and the
   50-lines contrast up front (Track A).
3. ⭐ **A narrative build-up** — "chapters" so a learner watches the architecture
   accrue, each an ADR + a diff + a test (Track A).
4. ⭐ **Comparative implementations** — an `mvc` branch beside `main`, ideally a
   second-language port, so trade-offs are *visible*, not described (Track C).
5. ⚙️ **Fix credibility papercuts** — pyright config, `mypy --strict`, `ruff`,
   `pre-commit`, CI matrix, coverage badge (Track B).
6. ⭐ **Keep the satire explicit** — a permanent "this is deliberately
   over-engineered" framing so no one mistakes it for a recommendation.

### Honest limits

- **No auth** and a **single implementation** cap realism and comparative value
  respectively — both fixable (Track C/D).
- "Authoritative" is earned socially (citations, course/talk use), not declared.
  The code can be *ready*; adoption is a community outcome, not an engineering task.
- Reaching "a polished, self-enforcing, documented teaching artifact in its niche"
  is a few-weekends effort. "Definitive-in-the-world" is a multi-year outcome.

---

## Appendix — the full 15-axis catalog

The tracks above curate the ~25–30 items worth doing. For completeness, the
exhaustive map (enrichment and jokes-with-a-point included):

1. **Domain/application:** specifications, domain services, policy objects, value
   objects, optimistic concurrency, CQRS, event sourcing, outbox, sagas,
   `Result`/`Either`, rule DSL.
2. **Interfaces/protocols:** GraphQL, WebSockets, gRPC, CLI, queue consumer,
   OpenAPI + generated SDKs, API versioning, cursor pagination, HATEOAS.
3. **Data/persistence:** PostgreSQL + constraints, `factory_boy`, full-text search,
   separate event-store DB, retention/GDPR, read replicas + pgbouncer.
4. **Testing/QA:** Hypothesis, `import-linter`, mutation testing, BDD, Playwright +
   a11y + visual regression, load tests, contract tests, fuzzing, coverage gate.
5. **Static analysis/types:** `mypy --strict`/pyright, `ruff`, `bandit`/`semgrep`,
   `radon`/`xenon`, `vulture`, `deptry`, `interrogate`.
6. **Build/dev-env:** `pyproject.toml` + `uv`, `justfile`, `pre-commit`,
   devcontainer/Codespaces, Docker/compose, Helm/Kustomize/Terraform, Nix.
7. **CI/CD:** test matrix, Dependabot/Renovate, CodeQL, `semantic-release`, PyPI +
   GHCR publish, SBOM/SLSA/cosign, Codecov, preview environments.
8. **Git hygiene:** commit-lint, signed commits, `.editorconfig`/`.gitattributes`,
   CODEOWNERS, SemVer tags + Releases, `CHANGELOG.md`.
9. **GitHub surface:** issue/PR/discussion templates, Discussions, Projects +
   milestones, labels, SECURITY/CoC/SUPPORT/GOVERNANCE/FUNDING, Pages, rulesets.
10. **Documentation:** docs site, Diátaxis, `mkdocstrings`, C4 diagrams,
    50-lines-vs-this, annotated tour, screencast, threat model, benchmarks.
11. **Security:** authN, authZ, tamper-evident log, secrets mgmt, hash-pinned deps,
    rate limiting, full header suite.
12. **Performance/scale:** Redis cache + event invalidation, async ASGI, N+1
    detection, profiling, singleton-as-scaling-smell discussion, perf gate.
13. **Product/UX:** accounts/teams/sharing, tags/subtasks/deps/recurring/reminders,
    search/saved-views/bulk, undo/redo, PWA/offline, command palette,
    import/export/webhooks, activity feed, i18n/RTL, WCAG AAA.
14. **Governance/process:** SemVer + deprecation + support policy, RFC process,
    maintainer guide, definition-of-done, release cadence/LTS.
15. **Out-there:** TLA+/Alloy spec, polyglot ports, chapter branches, comparative
    architecture branches, fitness functions, chaos testing, microservices +
    broker + mesh, CRDT offline sync, blockchain audit log, LLM task entry.
