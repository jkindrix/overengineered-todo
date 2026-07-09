# ADR-0003: Model identity and enumerations as value objects; keep the domain framework-free

- **Status:** Accepted
- **Date:** 2026-07-08
- **Deciders:** Initial author

## Context

The domain needs a small vocabulary — priority, status, and task identity — and a
guarantee that this vocabulary carries no framework or persistence coupling, so
the dependency rule of [ADR-0002](0002-layered-hexagonal-architecture.md) holds.

## Decision

`tasks/domain/` imports **only the Python standard library**. Within it:

- **`Priority`** is an `IntEnum` (`TRIVIAL=1 … CRITICAL=5`) so priorities order
  naturally and sort in the DB by a single integer column.
- **`TaskStatus`** is a string `Enum` (`draft`, `active`, …) — no meaningful order,
  and human-readable rows are far more debuggable than opaque integers.
- **`TaskId`** is a frozen dataclass wrapping a `UUID`, with `new()`/`parse()`
  helpers. The domain mints identity at construction time.
- Nondeterminism (`uuid4()`, `now()`) is isolated in tiny edge helpers
  (`TaskId.new`, `_utcnow`) so the rest of the domain is deterministic.

## Consequences

### Positive
- Self-documenting signatures (`get(task_id: TaskId)`), one place to parse ids.
- UUID identity lets an entity exist fully formed before it ever touches the DB,
  decoupling creation from persistence.
- Priority ordering and DB sorting come for free.
- The pure domain is trivially and quickly unit-testable.

### Negative
- `IntEnum` members behave as plain ints, which can leak where you didn't intend.
- UUID keys are larger and insert non-sequentially into indexes (negligible here).
- A dedicated identity type is a little more code than passing raw strings.

### Neutral
- Storing status as a string trades a few bytes for readability — a deliberate
  choice for a low-volume app.

## Alternatives considered

- **Auto-increment integer PKs** — rejected; identity would depend on the database
  assigning it on insert, breaking creation-before-persistence.
- **Raw `str`/`int` instead of value objects** — rejected; loses type safety and
  scatters parsing/validation.
- **`Priority` as a plain `Enum`** — rejected; we specifically wanted ordering.

## Related

- [ADR-0002](0002-layered-hexagonal-architecture.md),
  [ADR-0004](0004-rich-aggregate-and-state-machine.md)
