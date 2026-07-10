"""Property-based tests for the task lifecycle (Hypothesis stateful testing).

Where `test_domain.py` checks specific example transitions, this explores
*arbitrary* sequences of transitions and priority changes and asserts the
domain's invariants hold on every path Hypothesis can find:

  * status is always a valid state,
  * `completed_at` is set iff the task is COMPLETED,
  * every accepted change emits an event; every rejected one emits none,
  * a rejected (illegal) transition leaves the task unchanged.

These are pure-domain tests — no database, no Django.
"""

from __future__ import annotations

import pytest
from hypothesis import settings
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule
from hypothesis.strategies import sampled_from

from tasks.domain.entities import Task
from tasks.domain.exceptions import IllegalStateTransitionError
from tasks.domain.state_machine import can_transition
from tasks.domain.value_objects import Priority, TaskStatus


class TaskLifecycle(RuleBasedStateMachine):
    """A model that drives a real Task through random legal/illegal actions."""

    def __init__(self) -> None:
        super().__init__()
        self.task = Task.create(title="property")
        self.task.pull_events()  # discard the creation event

    # NB: the parameter is `to_status`, not `target` — `target` is a reserved
    # keyword in Hypothesis stateful rules (it designates a Bundle).
    @rule(to_status=sampled_from(list(TaskStatus)))
    def attempt_transition(self, to_status: TaskStatus) -> None:
        current = self.task.status
        # A move is legal if it's a no-op (same status) or the state machine
        # permits it. The domain must agree with this independent judgment.
        legal = to_status == current or can_transition(current, to_status)

        if legal:
            self.task.transition_to(to_status)
            assert self.task.status == to_status
            events = self.task.pull_events()
            if to_status != current:
                assert events, "an accepted transition must emit an event"
            else:
                assert not events, "a no-op transition must emit nothing"
        else:
            with pytest.raises(IllegalStateTransitionError):
                self.task.transition_to(to_status)
            assert self.task.status == current, "rejected -> unchanged"
            assert not self.task.pull_events(), "rejected -> no event"

    @rule(priority=sampled_from(list(Priority)))
    def change_priority(self, priority: Priority) -> None:
        current = self.task.priority
        self.task.change_priority(priority)
        assert self.task.priority == priority
        events = self.task.pull_events()
        assert bool(events) == (priority != current)

    @invariant()
    def status_is_always_valid(self) -> None:
        assert self.task.status in set(TaskStatus)

    @invariant()
    def completed_at_matches_status(self) -> None:
        if self.task.status == TaskStatus.COMPLETED:
            assert self.task.completed_at is not None
        else:
            assert self.task.completed_at is None


TestTaskLifecycle = TaskLifecycle.TestCase
# Explore more paths than the default, and don't fail on timing (CI can be slow).
TestTaskLifecycle.settings = settings(max_examples=200, deadline=None)
