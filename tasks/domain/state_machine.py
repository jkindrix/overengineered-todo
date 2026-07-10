"""The task lifecycle state machine.

Centralizes the allowed status transitions so the rule lives in exactly one
place. Both the domain entity and any diagnostic tooling consult this table.
"""

from __future__ import annotations

from .value_objects import TaskStatus

# Directed graph of permitted transitions: state -> set of reachable states.
_ALLOWED_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.DRAFT: frozenset({TaskStatus.ACTIVE, TaskStatus.ARCHIVED}),
    TaskStatus.ACTIVE: frozenset(
        {TaskStatus.BLOCKED, TaskStatus.COMPLETED, TaskStatus.ARCHIVED}
    ),
    TaskStatus.BLOCKED: frozenset({TaskStatus.ACTIVE, TaskStatus.ARCHIVED}),
    TaskStatus.COMPLETED: frozenset({TaskStatus.ACTIVE, TaskStatus.ARCHIVED}),
    TaskStatus.ARCHIVED: frozenset(),  # terminal
}


def can_transition(current: TaskStatus, requested: TaskStatus) -> bool:
    """Return True if moving from `current` to `requested` is permitted."""
    if current == requested:
        return False
    return requested in _ALLOWED_TRANSITIONS.get(current, frozenset())


def allowed_targets(current: TaskStatus) -> frozenset[TaskStatus]:
    """Return the set of states reachable from `current` in one transition."""
    return _ALLOWED_TRANSITIONS.get(current, frozenset())
