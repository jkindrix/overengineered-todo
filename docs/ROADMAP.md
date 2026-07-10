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

## Execution order (dependency-sequenced)

**This section is the source of truth for sequencing.** It is mirrored by
`phase:N` labels on the GitHub issues, but the ordering is recoverable from this
file alone — so it survives even if the issue tracker or any conversation is lost.
Check items off as they land; a completed item links to its merge commit.

> A GitHub Projects board mirrors these phases (custom **Phase** field + built-in
> **Status**): <https://github.com/users/jkindrix/projects/2>. The board is a
> convenience view; **this doc + the `phase:N` labels remain authoritative**, since
> they live in git and survive anything.

**Phase 1 — Self-enforcement** ✅ **complete** — turned architectural *claims* into
CI-checked *guarantees*. Highest leverage, lowest risk; done first so everything
after is trustworthy.
- [x] #5 — import-linter: enforce the hexagonal dependency rule ⭐⚙️ M — `.importlinter` (3 contracts) + CI step
- [x] #6 — Hypothesis: property-based state-machine tests ⭐⚙️ M — `tests/test_state_machine_properties.py`

**Phase 2 — Clean under its own tooling** ✅ **complete** — the repo now passes its
own linters, types, security scans, and a multi-version test matrix.
*Order within the phase mattered:* packaging first (the config home).
- [x] #14 — `pyproject.toml` (PEP 621) + `uv` ⚙️ M — canonical config home, `uv.lock`, pytest migrated off `pytest.ini`
- [x] #12 — pyright config + `mypy --strict` (core) ⚙️ M — pyright resolves imports (0 errors); mypy strict on domain+application; both in CI/pre-commit
- [x] #13 — `ruff` + `pre-commit` ⚙️ S — ruff lint+format (whole tree), `.pre-commit-config.yaml`, CI lint step
- [x] #15 — CI matrix (py 3.11–3.13 × Django 5.2; 6.0 experimental) ⚙️ S — `quality` + matrixed `test` jobs
- [x] #16 — coverage gate + Codecov ⚙️ S — `fail_under=80` (branch cov), Codecov upload + badge
- [x] #17 — security scanning (bandit/pip-audit/CodeQL/Dependabot) ⚙️ M — + fixed 2 CVEs (pytest, python-dotenv)
- [x] #18 — Docker + compose + devcontainer ⚙️ M — image builds & serves; `docker compose up`; Codespaces-ready
- [x] #19 — conventional commits + semantic-release + CHANGELOG ⚙️ M — PSR config + `release.yml`, conventional-commit hook

**Phase 3 — Teach it** — make it read like a reference. *(4/5 done; #10 deferred
by decision — the docs site, contrast, diagrams, and code tour deliver the
teaching goal without it.)*
- [x] #9 — "50 lines vs. this" contrast ⭐ S — runnable `examples/fifty_lines.py` (67 lines) + `docs/fifty-lines-vs-this.md`
- [x] #7 — docs site (MkDocs Material, Diátaxis) ⭐ L — `mkdocs.yml` + auto API reference (mkdocstrings) + Mermaid; deployed to GitHub Pages
- [x] #8 — C4 diagrams ⭐ M — `docs/architecture-diagrams.md` (C4 context/container/component + request flow, Mermaid; validated)
- [x] #11 — annotated code tour + design journal ⭐ M — `docs/code-tour.md` (one request through 10 stops + why-it-accreted journal)
- [ ] #10 — chapter branches ⭐ L — **deferred** (issue open); large staged-history effort, revisit as its own focused task

**Phase 4 — Over-engineering showcase** — deliberate, each with an ROI note.
- [x] #23 — hash-chained tamper-evident audit log 🎭⭐ M — SHA-256 chain in the event store + `verify_audit_log` command + [ADR-0014](adr/0014-tamper-evident-audit-log.md)
- [ ] #20 — transactional outbox + relay + idempotency ⚙️🎭 L — **deferred**, to be built with #33 (needs an external consumer to be meaningful)
- [x] #24 — TLA+ spec, model-checked in CI 🎭⭐ L — `spec/TaskLifecycle.tla` + TLC CI job + [ADR-0015](adr/0015-formal-spec-tla-plus.md) + [verified 3 ways](verified-three-ways.md)
- [x] #22 — event sourcing (replay/snapshots/versioning) 🎭 L — Option B: `Task.rebuild`/`_apply` + `EventSourcedTaskRepository` + snapshots + upcasting, alongside the state table ([ADR-0016](adr/0016-event-sourcing.md), [docs](event-sourcing.md))
- [x] #21 — CQRS (read models/projections) 🎭 L — Option B: `TaskStatistics` projection + `StatisticsProjector` + `rebuild_projections`; also added `TaskDeleted` event ([ADR-0017](adr/0017-cqrs-read-model.md), [docs](cqrs.md))
- [ ] #26 — gRPC/GraphQL adapter 🎭 M
- [ ] #25 — polyglot port 🎭⭐ L *(largest; last)*

**Phase 5 — Product realism** — close the toy gap. *Order:* auth → authz →
multi-user features; background jobs before recurring/reminders.
- [ ] #27 — authentication (sessions→OIDC→passkeys) ⚙️ L *(prereq for the rest)*
- [ ] #28 — authorization (RBAC + object perms) ⚙️ M
- [ ] #30 — background jobs + scheduler ⚙️ M *(before recurring/reminders)*
- [ ] #29 — core features (tags/subtasks/deps/recurring/reminders) ⚙️ L
- [ ] #31 — WebSockets live updates ⚙️ M
- [ ] #32 — undo/redo via event log ⚙️⭐ M
- [ ] #33 — import/export + webhooks ⚙️ M — webhooks incorporate the transactional outbox (#20)
- [ ] #34 — PWA/offline + a11y + i18n ⚙️ L

**Phase 6 — GitHub process & governance** — over-engineer the repo's own processes.
*Quick wins already implemented* (no issue — landed directly): community-health
files (SECURITY / CoC / SUPPORT / GOVERNANCE / FUNDING / CITATION.cff / CODEOWNERS),
structured issue forms + PR template, `dependency-review` + OpenSSF `Scorecard` +
path `labeler` + non-blocking "domain-changed-without-ADR" workflows, CI
auto-cancel concurrency, and Discussions enabled. *Remaining (tracked as issues):*
- [ ] #39 — branch protection ruleset + required checks ⚙️ S *(decision: makes work PR-based)*
- [ ] #40 — merge queue 🎭 S
- [ ] #41 — reusable workflows / composite actions (DRY CI) ⚙️ M
- [ ] #42 — OS matrix (ubuntu/macos/windows) 🎭 S
- [ ] #43 — pin all Actions to SHAs ⚙️ M
- [ ] #44 — publish + sign Docker image (GHCR + cosign) ⚙️ M
- [ ] #45 — SLSA provenance + SBOM on releases 🎭 M
- [ ] #46 — Projects v2 automations (auto-add / auto-Done / iteration; add Phase 6 field option) ⚙️ M
- [ ] #47 — labels as code (label-sync) ⚙️ S
- [ ] #48 — scheduled maintenance (link-check / dep-drift / Django-EOL watcher) ⚙️ S
- [ ] #49 — PR preview deploys of the docs ⚙️ M
- [ ] #50 — RFC process in Discussions ⭐ S
- [ ] #51 — DORA metrics dashboard 🎭 L
- [ ] #52 — repo polish (social preview, stale/welcome bots, Codespaces prebuilds) 🎭 M

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
