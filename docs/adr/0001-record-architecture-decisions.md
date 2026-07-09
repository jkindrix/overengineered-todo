# ADR-0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-07-08
- **Deciders:** Initial author

## Context

This project applies a large number of non-obvious architectural patterns to a
deliberately trivial domain (a to-do list). Without a durable record of *why* each
choice was made, future maintainers cannot tell an intentional trade-off from an
accident, and the reasoning — which is the actual point of the project — would be
lost.

## Decision

We keep **Architecture Decision Records** in `docs/adr/`, one Markdown file per
significant decision, following a fixed template (Status / Context / Decision /
Consequences / Alternatives / Related). ADRs are immutable once accepted; a
decision is changed by adding a new, superseding ADR rather than editing the old
one.

## Consequences

### Positive
- The rationale and rejected alternatives are preserved next to the code.
- "Why is this like this?" has a canonical answer.
- New maintainers can change decisions deliberately.

### Negative
- ADRs must be written and kept current — a small ongoing discipline.

### Neutral
- ADRs record *decisions*, not tutorials; how-to lives in the other docs.

## Alternatives considered

- **Only prose docs (no ADRs)** — rejected; prose tends to describe the *what* and
  lose the *why* and the rejected options over time.
- **Comments in code only** — rejected; comments explain local intent but can't
  hold cross-cutting rationale or alternatives.

## Related

- [docs/README.md](../README.md), [_template.md](_template.md)
