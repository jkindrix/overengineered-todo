"""Presenters — render domain aggregates into transport-friendly shapes.

Keeps view/serializer code free of knowledge about the domain's internal value
objects. A `Task` becomes a plain dict suitable for JSON or template context.
"""
from __future__ import annotations

from typing import Any

from tasks.domain.entities import Task
from tasks.domain.state_machine import allowed_targets


def present_task(task: Task) -> dict[str, Any]:
    """Convert a Task aggregate into a serializable dictionary."""
    return {
        "id": str(task.id),
        "title": task.title,
        "description": task.description,
        "priority": task.priority.name,
        "priority_value": int(task.priority.value),
        "priority_label": task.priority.label,
        "status": task.status.value,
        "status_label": task.status.label,
        "is_terminal": task.status.is_terminal,
        "allowed_transitions": sorted(s.value for s in allowed_targets(task.status)),
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "completed_at": (
            task.completed_at.isoformat() if task.completed_at else None
        ),
    }


def present_tasks(tasks) -> list[dict[str, Any]]:
    return [present_task(task) for task in tasks]
