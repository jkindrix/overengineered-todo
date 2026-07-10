"""Domain events.

A domain event is an immutable record that something meaningful happened in the
domain. Entities accumulate events as they change; the application layer drains
and publishes them. Events carry primitive/serializable payloads so they can be
logged, persisted (event sourcing) or shipped to a message bus unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def _utcnow() -> datetime:
    """Timestamp helper. Isolated so tests can reason about it if needed."""
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """Base class for all domain events."""

    aggregate_id: str
    occurred_at: datetime = field(default_factory=_utcnow)

    @property
    def name(self) -> str:
        """The concrete event type name, used as a routing key on the bus."""
        return type(self).__name__

    def payload(self) -> dict[str, Any]:
        """Serializable attributes describing what happened (sans metadata)."""
        reserved = {"aggregate_id", "occurred_at"}
        return {
            key: getattr(self, key) for key in self.__slots__ if key not in reserved
        }


@dataclass(frozen=True, slots=True)
class TaskCreated(DomainEvent):
    title: str = ""
    description: str = ""
    priority: str = ""
    status: str = ""


@dataclass(frozen=True, slots=True)
class TaskDetailsEdited(DomainEvent):
    # `changed_fields` reads well in the audit log; `title`/`description` carry the
    # new values so the event is sufficient to *reconstruct* state (event sourcing,
    # ADR-0016). None means "this field was not changed by this event".
    changed_fields: tuple[str, ...] = ()
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class TaskStatusChanged(DomainEvent):
    from_status: str = ""
    to_status: str = ""


@dataclass(frozen=True, slots=True)
class TaskPriorityChanged(DomainEvent):
    from_priority: str = ""
    to_priority: str = ""


@dataclass(frozen=True, slots=True)
class TaskCompleted(DomainEvent):
    pass


@dataclass(frozen=True, slots=True)
class TaskArchived(DomainEvent):
    pass


@dataclass(frozen=True, slots=True)
class TaskDeleted(DomainEvent):
    # The status at deletion time, so read-model projections can decrement the
    # right bucket without tracking per-aggregate state.
    status: str = ""
