"""Tests for the event-sourcing demonstration (ADR-0016)."""

from __future__ import annotations

import pytest

from tasks.application.dto import (
    CreateTaskCommand,
    EditTaskCommand,
    TransitionTaskCommand,
)
from tasks.domain.entities import Task
from tasks.domain.events import TaskStatusChanged
from tasks.domain.exceptions import TaskValidationError
from tasks.domain.value_objects import TaskStatus
from tasks.infrastructure.container import get_task_service
from tasks.infrastructure.event_serialization import upcast
from tasks.infrastructure.event_sourced_repository import EventSourcedTaskRepository
from tasks.infrastructure.models import DomainEventRecord, TaskSnapshot
from tasks.infrastructure.repositories import DjangoTaskRepository


def _event_ids(task_id):
    return list(
        DomainEventRecord.objects.filter(aggregate_id=task_id.value)
        .order_by("id")
        .values_list("id", flat=True)
    )


@pytest.mark.django_db
def test_rebuild_matches_stored_state():
    svc = get_task_service()
    task = svc.create_task(
        CreateTaskCommand(title="Rebuild me", description="original", priority="HIGH")
    )
    svc.edit_task(EditTaskCommand(task_id=str(task.id), description="edited"))
    svc.transition_task(
        TransitionTaskCommand(task_id=str(task.id), target_status="active")
    )
    svc.transition_task(
        TransitionTaskCommand(task_id=str(task.id), target_status="completed")
    )

    stored = DjangoTaskRepository().get(task.id)
    rebuilt = EventSourcedTaskRepository().get(task.id)

    # Business state is fully reconstructed from events (the edited description
    # survives — proof the events are "fat" enough).
    assert (rebuilt.title, rebuilt.description, rebuilt.priority, rebuilt.status) == (
        stored.title,
        stored.description,
        stored.priority,
        stored.status,
    )
    assert (rebuilt.completed_at is None) == (stored.completed_at is None)


@pytest.mark.django_db
def test_time_travel_to_a_past_event():
    svc = get_task_service()
    task = svc.create_task(CreateTaskCommand(title="Time travel"))
    svc.transition_task(
        TransitionTaskCommand(task_id=str(task.id), target_status="active")
    )
    svc.transition_task(
        TransitionTaskCommand(task_id=str(task.id), target_status="completed")
    )

    repo = EventSourcedTaskRepository()
    ids = _event_ids(task.id)

    # As of the "activated" event, the task was ACTIVE and not yet completed.
    past = repo.reconstitute_at(task.id, ids[1])
    assert past.status is TaskStatus.ACTIVE
    assert past.completed_at is None

    # Its current state is COMPLETED.
    assert repo.get(task.id).status is TaskStatus.COMPLETED


@pytest.mark.django_db
def test_snapshot_then_later_events_combine():
    svc = get_task_service()
    task = svc.create_task(CreateTaskCommand(title="Snapshot"))
    svc.transition_task(
        TransitionTaskCommand(task_id=str(task.id), target_status="active")
    )

    repo = EventSourcedTaskRepository()
    repo.take_snapshot(task.id)  # snapshot at ACTIVE
    assert TaskSnapshot.objects.filter(aggregate_id=task.id.value).exists()

    # Events after the snapshot must still be applied on top of it.
    svc.transition_task(
        TransitionTaskCommand(task_id=str(task.id), target_status="completed")
    )
    reloaded = repo.get(task.id)
    assert reloaded.status is TaskStatus.COMPLETED
    assert reloaded.completed_at is not None


def test_upcast_adds_missing_description_to_v1_created():
    v1 = {"title": "old", "priority": "NORMAL", "status": "draft"}  # no description
    assert upcast("TaskCreated", 1, v1)["description"] == ""
    # Current-version payloads pass through unchanged.
    v2 = {"title": "x", "description": "d", "priority": "NORMAL", "status": "draft"}
    assert upcast("TaskCreated", 2, v2) == v2


def test_rebuild_requires_created_first():
    with pytest.raises(TaskValidationError):
        Task.rebuild(
            [
                TaskStatusChanged(
                    aggregate_id="x", from_status="draft", to_status="active"
                )
            ]
        )
