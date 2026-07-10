# ADR-0015: Formally verify the state machine with TLA+

- **Status:** Accepted
- **Date:** 2026-07-10
- **Deciders:** Initial author

## Context

The task lifecycle state machine is already guarded two ways: example tests
(`test_domain.py`) and Hypothesis stateful property tests
(`test_state_machine_properties.py`, [ADR-0012](0012-testing-strategy.md) / #6).
Both check *behaviors* — specific and random sequences respectively. Neither is
*exhaustive*.

A **model checker** explores the entire reachable state space and proves an
invariant holds in every state (or returns a counterexample). It is overkill for a
5-state machine that is already well tested — but it is a uniquely instructive
demonstration, and it completes a "verified three ways" teaching story.

## Decision

Add a TLA+ spec of the lifecycle (`spec/TaskLifecycle.tla` + `.cfg`) and check it
with **TLC** in a CI job (`.github/workflows/model-check.yml`). The spec models the
same transition table as `tasks/domain/state_machine.py` and the `completed_at`
rule from `Task.transition_to`, and checks:

- **Safety:** `TypeOK`; `completed_at` set iff COMPLETED; ARCHIVED terminal; no
  dead ends (every non-terminal state can reach ARCHIVED).
- **Liveness:** under weak fairness on archiving, a task is *always eventually*
  archivable — it can never get permanently stuck (`<>(status = "ARCHIVED")`).

TLC exits non-zero on a violation, so the CI job genuinely gates. `-deadlock` is
passed because ARCHIVED is an intentional terminal state.

## Consequences

### Positive
- The lifecycle is now verified **three ways** — example, property-based, and
  formal — a rare and illuminating teaching artifact ([verified-three-ways](../verified-three-ways.md)).
- Exhaustive over the whole state space; TLC produces a counterexample trace on
  failure (verified: breaking the `completed_at` rule yields a 3-state counterexample).
- Zero risk to the running system — the spec is a parallel artifact; no code,
  schema, or behavior changes.

### Negative / caveats
- **Drift risk.** The spec is *hand-written to mirror* the Python transition table,
  not generated from it. Editing `state_machine.py` without updating the spec would
  let them diverge silently. Mitigated by documenting the correspondence and keeping
  both tiny; a fully rigorous setup would generate one from the other. Recorded in
  [TECH_DEBT.md](../TECH_DEBT.md).
- Adds a Java-based CI job (setup-java + fetch TLC + run) — ~1 minute, isolated to
  its own workflow.
- Practical bug-finding value here is **nil** (the machine is trivial and already
  tested) — this is a 🎭 demonstration with ⭐ teaching value.

## Alternatives considered

- **Alloy** — relational/structural modeling; less natural for temporal (liveness)
  properties and more GUI-oriented. Weaker fit for a state machine.
- **Skip it** — rely on Hypothesis as the maximal-rigor tier. Defensible; forgoes
  the three-ways showcase.

## Related

- [ADR-0012](0012-testing-strategy.md) (testing strategy),
  [verified-three-ways.md](../verified-three-ways.md), `spec/TaskLifecycle.tla`
