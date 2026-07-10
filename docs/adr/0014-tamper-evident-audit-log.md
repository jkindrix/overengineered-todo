# ADR-0014: Make the audit log tamper-evident with a hash chain

- **Status:** Accepted
- **Date:** 2026-07-10
- **Deciders:** Initial author

## Context

The domain-event audit log ([ADR-0006](0006-event-log-and-transactional-gap.md),
[ADR-0013](0013-transactional-unit-of-work-event-store.md)) is an append-only table.
"Append-only" is a *convention*, not a guarantee: anyone with database access can
`UPDATE` or `DELETE` a past row silently. For a log whose whole value is being a
trustworthy history, that is a gap — you cannot prove the history wasn't doctored.

This is not a real requirement for a to-do app; it is a deliberate, self-contained
demonstration of a genuinely useful technique (the opener for the
over-engineering phase).

## Decision

Each `DomainEventRecord` stores a **hash chain**: two columns, `prev_hash` and
`entry_hash`, where

```
entry_hash = SHA256(prev_hash + canonical_json(aggregate_id, event_name, occurred_at, payload))
```

`DjangoEventStore.append` reads the current last row's `entry_hash` and chains the
new batch onto it, inside the existing unit-of-work transaction. A single **global
chain** links every event in insertion order.

`tasks.infrastructure.audit_chain.verify_chain()` walks the log and recomputes the
chain, returning the id of the first row whose hashes don't match. The
`manage.py verify_audit_log` command wraps it (exit 1 on tampering) so a human, a
cron job, or CI can check it.

## Consequences

### Positive
- **Tampering is detectable.** Editing or deleting any past row breaks the chain
  from that point; `verify_chain` pinpoints the first bad row. Verified by tests
  (edited field, edited payload, deleted row).
- Self-contained: the change lives entirely in infrastructure — the domain,
  application, and interface layers are untouched.
- No user-facing or behavioral change; adds one capability.

### Negative / caveats
- **Tamper-*evident*, not tamper-*proof*.** An attacker who can write to the DB can
  edit a row *and* recompute the rest of the chain, restoring consistency. Closing
  that requires a secret the attacker lacks — see the HMAC alternative below — or
  truly write-once storage. Recorded in [TECH_DEBT.md](../TECH_DEBT.md).
- **Appends are serialized.** Each append reads the previous hash, so concurrent
  appends must be ordered. Fine on SQLite (already serialized) and within our
  transaction; on high-concurrency PostgreSQL you'd need row-locking or a
  sequence-based ordering.
- Slightly more complex event store; one migration adds two columns.
- The hash covers the stored, JSON-safe payload and the ISO-8601 `occurred_at`; the
  write-time and read-time encodings must round-trip identically (they do on
  SQLite; a datastore that alters datetime precision would need normalization).

### Neutral
- Existing local rows written before this change have empty hashes; reseed
  (`seed_tasks --wipe`) or backfill to establish a valid chain. Test databases are
  built fresh, so tests are unaffected.

## Alternatives considered

- **Do nothing** — keep the plain append-only table. Zero cost, zero property.
  Rejected only because the demonstration is the point.
- **Sequence number + row-count check** — detects deletions but not edits. Weaker.
- **HMAC-signed chain** — hash with a secret key so an attacker without the key
  cannot forge a valid replacement chain (tamper-*resistant*, not just evident).
  A small, natural upgrade; deferred because key management is its own concern.
- **Merkle trees / external notarization / write-once storage** — stronger but
  heavier; overkill even for the bit.

## Related

- [ADR-0006](0006-event-log-and-transactional-gap.md),
  [ADR-0013](0013-transactional-unit-of-work-event-store.md),
  [TECH_DEBT.md](../TECH_DEBT.md)
