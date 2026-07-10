# CQRS: a read-model projection

**CQRS** (Command Query Responsibility Segregation) uses a *different model to write
than to read*. The write side stays normalized and consistent; the read side is one
or more **projections** — denormalized tables, each shaped for a specific query,
maintained by consuming events. This is also the answer to the question
[event sourcing](event-sourcing.md) left open: *how do you query an event stream?*
You project it. ([ADR-0017](adr/0017-cqrs-read-model.md).)

## The demonstration: live status counts

We add one read model, `TaskStatistics` — counts of tasks per status — turning a
`GROUP BY` over the write model into an **O(1) read**:

```python
get_container().statistics_query.counts()   # {"active": 3, "draft": 1, ...}
```

A **projector** (a post-commit event subscriber) keeps it current incrementally:

| Event | Effect on the read model |
|-------|--------------------------|
| `TaskCreated` | draft +1 |
| `TaskStatusChanged(from → to)` | from −1, to +1 |
| `TaskDeleted(status)` | status −1 |

*(Making the projection correct required emitting `TaskDeleted` on hard delete — so
deletions are now auditable and replayable too.)*

## Rebuildable — because it's derived, not authoritative

A projection is a *cache of a fold over events*. If it drifts, replay the log:

```bash
python manage.py rebuild_projections
```

Tests confirm both that the live projection **matches a `GROUP BY` over the write
model** (including after deletes) and that a rebuild reproduces the same counts.

## Eventual consistency (the honest part)

The projector runs **after** the write commits, so the read model briefly lags the
write — the defining trade-off of CQRS. `rebuild_projections` heals any drift, and
production systems often make projection async by design.

## Honest ROI

For a to-do app this is **🎭 the most over-engineered pattern here** — we already
have a perfectly good read model (`TaskRecord`), so a separate projection is largely
redundant. We now maintain **three** representations of a task (write table, event
stream, read projection) for a to-do list. It's kept purely to complete the
event-sourcing → CQRS teaching arc ([TECH_DEBT.md](TECH_DEBT.md)).
