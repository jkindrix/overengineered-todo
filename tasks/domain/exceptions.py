"""Domain-level exceptions.

These express rule violations in domain terms. The interface layer is
responsible for translating them into transport-appropriate responses (e.g.
HTTP status codes) — the domain itself knows nothing about HTTP.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain rule violations."""


class TaskNotFoundError(DomainError):
    """Raised when a task cannot be located by its identity."""


class IllegalStateTransitionError(DomainError):
    """Raised when a status transition violates the lifecycle state machine."""

    def __init__(self, *, current: str, requested: str) -> None:
        self.current = current
        self.requested = requested
        super().__init__(f"Cannot transition task from {current!r} to {requested!r}.")


class TaskValidationError(DomainError):
    """Raised when an invariant on a task's attributes is violated."""
