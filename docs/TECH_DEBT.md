# Technical Debt & Known Issues

An honest register of weaknesses, deferred work, and places the implementation
diverges from what its patterns imply. Maintainers should read this before
extending the affected areas. Items are ordered by importance.

## 1. ~~Event writes are not transactional with state changes~~ — RESOLVED (2026-07-09)

**Status: Fixed.** State and events now commit atomically. Each use case runs inside
a **Unit of Work** (`DjangoUnitOfWork` → `transaction.atomic`); the aggregate write
and the **Event Store** append (`DjangoEventStore`) happen in one transaction, so
they commit or roll back together. The event bus was demoted to post-commit
side-effects, where its exception isolation can no longer corrupt state.

Verified by `tests/test_api.py::test_event_store_failure_rolls_back_state` (injects
an append failure and asserts nothing persists). See
[ADR-0013](adr/0013-transactional-unit-of-work-event-store.md).

**Remaining nuance (not a defect):** this is single-datastore transactional
durability, not a transactional *outbox*. An outbox would matter only for
at-least-once delivery to an *external* bus, which this app does not have. If one is
ever added, the outbox relay is the next step.

## 2. The *main app* is state-driven; event sourcing is a parallel demonstration

**In the running application, the `TaskRecord` row is the source of truth and the
events are a parallel history — a domain-event audit log.** All reads/queries go
through the state table.

The event-sourcing machinery (replay, snapshots, versioning, upcasting) *does*
exist, but as an **alternate demonstration** (`EventSourcedTaskRepository`) built in
[ADR-0016](adr/0016-event-sourcing.md) — see item #12 below. It is not what the app
uses to serve requests. So "we don't do event sourcing" is true of the *app's
behaviour*, not of the codebase, which demonstrates both.

The user-facing "Event-Sourced" label in the footer was corrected to "Audit-Logged"
(2026-07-09). The `FEATURE_EVENT_SOURCING` flag name is retained to avoid churning
the env contract; its docstring/comments describe it accurately as the audit log.
See [ADR-0006](adr/0006-event-log-and-transactional-gap.md).

## 3. `save()` / `get()` do an extra fetch

`DjangoTaskRepository.save()` fetches the row before updating so that a missing
task always raises `TaskNotFoundError` consistently. That's an extra query traded
for clean, uniform error semantics. A performance-minded version would issue a
single `UPDATE ... WHERE id=` and check the affected-row count. Fine at this scale;
revisit under write-heavy load. See
[ADR-0008](adr/0008-ports-repositories-mappers.md).

## 4. Process-wide singleton container complicates parallel test isolation

The DI container is a module-level singleton (`get_container`). It intentionally
holds process-wide state (the bus and its subscriptions), but that makes it a
controlled global. `reset_container()` exists for tests; be mindful when
introducing parallel test execution or per-request scoping. See
[ADR-0009](adr/0009-di-container.md).

## 5. `enforce` flag leaks configuration into a domain method

`Task.transition_to(target, enforce=...)` threads the `STRICT_STATE_MACHINE`
feature flag into a domain signature. It buys the ability to relax the rule
(migrations/admin) without deleting it, at the cost of a small impurity. A purist
refactor would move enforcement into a separate policy object. See
[ADR-0004](adr/0004-rich-aggregate-and-state-machine.md).

## 6. ~~Insecure default `SECRET_KEY`~~ — MITIGATED (2026-07-09)

`config/settings.py` still ships a development `SECRET_KEY` default so the app runs
with no `.env` — but a **boot guard** now raises `ImproperlyConfigured` if the app
is started with `DEBUG=False` while the key is still the insecure default. Combined
with the production-hardening block (secure cookies, SSL redirect, HSTS — all gated
on `not DEBUG`), `manage.py check --deploy` passes clean with a real key set. See
[ADR-0011](adr/0011-infrastructure-sqlite-config.md).

## 7. SQLite write concurrency

SQLite was chosen for zero-dependency local runs. It serializes writes and is
unsuitable for a multi-writer production deployment. The ORM abstracts the engine,
so moving to PostgreSQL is a settings change plus a migration test pass. See
[ADR-0011](adr/0011-infrastructure-sqlite-config.md).

## 8. ORM models live outside the conventional location

Models are in `tasks/infrastructure/models.py` (not a top-level `tasks/models.py`),
which required setting `app_label = "tasks"` explicitly and importing the module in
`apps.ready()`. This honors the layer layout but is non-idiomatic and can surprise
Django developers. See [ADR-0011](adr/0011-infrastructure-sqlite-config.md).

## 9. Schemaless event payloads

`DomainEventRecord.payload` is a `JSONField`. Flexible, but not queryable in a
typed way and unvalidated at the DB layer. Acceptable for an audit log; a
reporting requirement would motivate a typed projection.

## 10. Audit log is tamper-*evident*, not tamper-*proof*

The hash chain ([ADR-0014](adr/0014-tamper-evident-audit-log.md)) *detects* tampering
but does not *prevent* it. It catches: edits to any row, and deletions that leave a
subsequent row (the chain breaks). Bare hash chains **cannot** catch *trailing
truncation* (deleting the final rows leaves a valid shorter chain), so we added an
independently-stored **head anchor** (`AuditChainHead`: expected count + last hash)
that `verify_chain` checks — which catches truncation too.

Residual limits (conscious trade-offs for a demonstration): the anchor lives in the
same database, so an attacker who rewrites *both* the rows and the anchor still
evades detection — true tamper-*resistance* needs the anchor in external / write-once
/ signed storage, or an HMAC-signed chain keyed by a secret the attacker lacks. And
chained appends are serialized (fine on SQLite; PostgreSQL writers would need
row-locking).

## 11. The TLA+ spec can drift from the code

`spec/TaskLifecycle.tla` ([ADR-0015](adr/0015-formal-spec-tla-plus.md)) is
hand-written to mirror `tasks/domain/state_machine.py`; it is not generated from
the code. Editing the transition table without updating the spec would let them
diverge silently — the model check would still pass, but against a stale model. A
rigorous fix would generate one artifact from the other. Kept small and documented
as the mitigation.

## 12. Event sourcing is a demonstration, kept alongside the state table

The event-sourcing machinery ([ADR-0016](adr/0016-event-sourcing.md)) coexists with
the state-based `DjangoTaskRepository` — so **two representations** are maintained.
"Real" event sourcing would drop the state table and make events the sole truth,
but then every query needs a **projection**, i.e. it forces **CQRS (#21)**.
Reconstruction also matches on business state, not exact timestamps (those are
event-derived). Kept as a demonstration; the genuine payoff is undo/redo (#32).

## 13. Three representations of task data (CQRS)

With the CQRS read model ([ADR-0017](adr/0017-cqrs-read-model.md)) a task now exists
in **three** places: the write table (`TaskRecord`), the event stream, and the
`TaskStatistics` projection — for a to-do list. The projection is also *eventually
consistent* (the projector runs post-commit, and the bus swallows subscriber
failures), so it can briefly lag or drift; `rebuild_projections` heals it. Kept as a
demonstration; the app still reads counts from the write model.

## The meta-point

Most of this register exists because the app applies enterprise patterns to a
domain that doesn't need them — that is the intentional joke of the project. Items
**1** and **2** are the ones that would matter in any real system built on this
skeleton; the rest are conscious trade-offs appropriate to the scale. See
[ADR-0002](adr/0002-layered-hexagonal-architecture.md) for the honest accounting of
which patterns earn their keep.
