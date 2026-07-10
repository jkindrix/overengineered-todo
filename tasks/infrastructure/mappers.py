"""Mappers between ORM records and domain aggregates.

The repository uses these to cross the boundary in both directions without
leaking ORM types into the domain or domain types into queries.
"""

from __future__ import annotations

from tasks.domain.entities import Task
from tasks.domain.value_objects import Priority, TaskId, TaskStatus

from .models import TaskRecord


def record_to_entity(record: TaskRecord) -> Task:
    """Rehydrate a domain `Task` from a stored `TaskRecord`."""
    return Task(
        id=TaskId.parse(record.id),
        title=record.title,
        description=record.description,
        priority=Priority(record.priority),
        status=TaskStatus.from_value(record.status),
        created_at=record.created_at,
        updated_at=record.updated_at,
        completed_at=record.completed_at,
    )


def apply_entity_to_record(entity: Task, record: TaskRecord) -> TaskRecord:
    """Copy the aggregate's state onto a (possibly new) ORM record."""
    record.id = entity.id.value
    record.title = entity.title
    record.description = entity.description
    record.priority = entity.priority.value
    record.status = entity.status.value
    record.created_at = entity.created_at
    record.updated_at = entity.updated_at
    record.completed_at = entity.completed_at
    return record
