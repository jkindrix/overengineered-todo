# The state machine, verified three ways

The task lifecycle — five states (`DRAFT → ACTIVE → BLOCKED / COMPLETED →
ARCHIVED`) — is tiny. That makes it the perfect specimen for showing **three
escalating techniques for gaining confidence in code**, on one thing you can hold
in your head. Each is stronger and more expensive than the last.

## 1. Example-based tests — "does it work for these cases?"

`tests/test_domain.py`. You pick specific scenarios and assert the outcome:
"draft→completed is rejected", "completing sets `completed_at`". Fast, concrete,
and the first thing you write — but it only covers the cases you *thought of*.

```python
def test_illegal_transition_is_rejected():
    task = Task.create(title="A task")           # DRAFT
    with pytest.raises(IllegalStateTransitionError):
        task.transition_to(TaskStatus.COMPLETED)  # can't complete a draft
```

## 2. Property-based tests — "does it work for *lots* of random cases?"

`tests/test_state_machine_properties.py` (Hypothesis, [ADR-0012](adr/0012-testing-strategy.md)).
Instead of examples, you state a *property* that must always hold, and Hypothesis
generates hundreds of random action sequences trying to break it:

```python
@invariant()
def completed_at_matches_status(self):
    if self.task.status == TaskStatus.COMPLETED:
        assert self.task.completed_at is not None
    else:
        assert self.task.completed_at is None
```

This finds cases you'd never enumerate by hand — but it *samples* the space; it
can't prove there's no bad case, only fail to find one.

## 3. Formal model checking — "is a bad state *impossible*?"

`spec/TaskLifecycle.tla` (TLA+, checked by TLC in CI, [ADR-0015](adr/0015-formal-spec-tla-plus.md)).
You describe the machine mathematically and the checker explores **every reachable
state** — exhaustively, not by sampling — proving the invariants hold or returning a
**counterexample trace**:

```tla
CompletedInvariant == completedAt <=> (status = "COMPLETED")
EventuallyArchived  == <>(status = "ARCHIVED")   \* liveness: never stuck
```

For this machine TLC explores all **5 states** and confirms every safety invariant
plus the liveness property. Break the `completed_at` rule and it reports the exact
3-step trace that reaches `status = COMPLETED, completedAt = FALSE`.

## When is each worth it?

| Technique | Coverage | Cost | Use it when… |
|-----------|----------|------|--------------|
| Example tests | The cases you list | Cheap | Always — the baseline |
| Property tests | Many random cases | Moderate | Logic with invariants / lots of input combinations |
| Model checking | The **whole** state space | High (a spec + a checker) | Concurrent/distributed protocols, or safety-critical state machines |

**The honest verdict for this app:** techniques 1 and 2 are already plenty for a
5-state machine. Technique 3 finds no bug here — it earns its place purely as a
demonstration of *what exhaustive verification looks like* and *when* the cost is
justified (spoiler: when a subtle concurrency bug would be catastrophic and
untestable — which a to-do list is not).
