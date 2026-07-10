"""Value objects for the task domain.

Value objects are immutable and compared by value. They encapsulate the small
but meaningful vocabulary of the domain: priorities, statuses and identities.
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass

from .exceptions import TaskValidationError


class Priority(enum.IntEnum):
    """Task priority, ordered so higher members sort as more urgent."""

    TRIVIAL = 1
    LOW = 2
    NORMAL = 3
    HIGH = 4
    CRITICAL = 5

    @property
    def label(self) -> str:
        return self.name.title()

    @classmethod
    def from_name(cls, name: str) -> Priority:
        # Raises a domain error (not ValueError) so untrusted input from any
        # transport surfaces as a catchable validation failure -> HTTP 400,
        # rather than escaping as an unhandled 500.
        try:
            return cls[name.strip().upper()]
        except KeyError as exc:
            raise TaskValidationError(f"Unknown priority: {name!r}") from exc


class TaskStatus(enum.Enum):
    """The lifecycle states a task may occupy."""

    DRAFT = "draft"
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    ARCHIVED = "archived"

    @property
    def label(self) -> str:
        return self.value.title()

    @property
    def is_terminal(self) -> bool:
        """Terminal states permit no further transitions."""
        return self in {TaskStatus.ARCHIVED}

    @classmethod
    def from_value(cls, value: str) -> TaskStatus:
        # See Priority.from_name: untrusted input yields a domain error, not a
        # bare ValueError, so it is caught and mapped to HTTP 400 uniformly.
        try:
            return cls(value.strip().lower())
        except ValueError as exc:
            raise TaskValidationError(f"Unknown status: {value!r}") from exc


@dataclass(frozen=True, slots=True)
class TaskId:
    """A stable, opaque identity for a task, backed by a UUID."""

    value: uuid.UUID

    @classmethod
    def new(cls) -> TaskId:
        # uuid4 is used at the true edge of the system (identity minting), which
        # is one of the few legitimate homes for nondeterminism in the domain.
        return cls(uuid.uuid4())

    @classmethod
    def parse(cls, raw: str | uuid.UUID) -> TaskId:
        if isinstance(raw, uuid.UUID):
            return cls(raw)
        return cls(uuid.UUID(str(raw)))

    def __str__(self) -> str:  # pragma: no cover - trivial
        return str(self.value)
