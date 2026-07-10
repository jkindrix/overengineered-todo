"""(De)serialization for event sourcing: stored rows <-> domain objects.

Turns `DomainEventRecord` rows back into domain events (so aggregates can be
rebuilt by replay) and Task aggregates into snapshot state (and back). Includes an
`upcast` hook that transforms old event versions into the current schema — the
answer to "events live forever, but their shape changes". See ADR-0016.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from tasks.domain.entities import Task
from tasks.domain.events import (
    DomainEvent,
    TaskArchived,
    TaskCompleted,
    TaskCreated,
    TaskDeleted,
    TaskDetailsEdited,
    TaskPriorityChanged,
    TaskStatusChanged,
)
from tasks.domain.value_objects import Priority, TaskId, TaskStatus

# Bump when an event's payload shape changes; add an `upcast` case for the old
# version. v2 added `description` to TaskCreated (v1 was audit-only).
CURRENT_EVENT_VERSION = 2

_EVENT_TYPES: dict[str, type[DomainEvent]] = {
    cls.__name__: cls
    for cls in (
        TaskCreated,
        TaskDetailsEdited,
        TaskStatusChanged,
        TaskPriorityChanged,
        TaskCompleted,
        TaskArchived,
        TaskDeleted,
    )
}


def upcast(event_name: str, version: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Transform a stored payload of an older version into the current schema."""
    payload = dict(payload)
    if event_name == "TaskCreated" and version < 2:
        # v1 TaskCreated predated event sourcing and carried no description.
        payload.setdefault("description", "")
    return payload


def deserialize_event(
    *,
    event_name: str,
    version: int,
    aggregate_id: Any,
    occurred_at: datetime,
    payload: dict[str, Any],
) -> DomainEvent:
    """Rebuild a domain event from a stored row (upcasting as needed)."""
    payload = upcast(event_name, version, payload)
    cls = _EVENT_TYPES[event_name]
    return cls(aggregate_id=str(aggregate_id), occurred_at=occurred_at, **payload)


def serialize_task(task: Task) -> dict[str, Any]:
    """Serialize a Task's state for a snapshot."""
    return {
        "id": str(task.id),
        "title": task.title,
        "description": task.description,
        "priority": task.priority.name,
        "status": task.status.value,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "completed_at": (task.completed_at.isoformat() if task.completed_at else None),
    }


def deserialize_task(state: dict[str, Any]) -> Task:
    """Rebuild a Task from snapshot state."""
    completed = state["completed_at"]
    return Task(
        id=TaskId.parse(state["id"]),
        title=state["title"],
        description=state["description"],
        priority=Priority[state["priority"]],
        status=TaskStatus(state["status"]),
        created_at=datetime.fromisoformat(state["created_at"]),
        updated_at=datetime.fromisoformat(state["updated_at"]),
        completed_at=datetime.fromisoformat(completed) if completed else None,
    )
