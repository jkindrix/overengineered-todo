"""Tests for the CQRS status-count read model / projection (ADR-0017)."""

from __future__ import annotations

import pytest
from django.db.models import Count

from tasks.application.dto import (
    CreateTaskCommand,
    DeleteTaskCommand,
    TransitionTaskCommand,
)
from tasks.infrastructure.container import get_container
from tasks.infrastructure.models import TaskRecord, TaskStatistics
from tasks.infrastructure.projections import (
    TaskStatisticsQuery,
    rebuild_statistics,
)


def _write_model_counts() -> dict[str, int]:
    return {
        r["status"]: r["count"]
        for r in TaskRecord.objects.values("status").annotate(count=Count("id"))
    }


@pytest.mark.django_db
def test_projection_matches_the_write_model():
    svc = get_container().task_service
    a = svc.create_task(CreateTaskCommand(title="a"))
    svc.transition_task(
        TransitionTaskCommand(task_id=str(a.id), target_status="active")
    )
    svc.create_task(CreateTaskCommand(title="b"))
    doomed = svc.create_task(CreateTaskCommand(title="c"))
    svc.delete_task(DeleteTaskCommand(task_id=str(doomed.id)))  # exercises TaskDeleted

    # The read model (maintained incrementally by the projector) agrees with a
    # GROUP BY over the write model.
    assert TaskStatisticsQuery().counts() == _write_model_counts()


@pytest.mark.django_db
def test_rebuild_reproduces_counts_from_the_event_log():
    svc = get_container().task_service
    x = svc.create_task(CreateTaskCommand(title="x"))
    svc.transition_task(
        TransitionTaskCommand(task_id=str(x.id), target_status="active")
    )

    # Simulate projection drift, then heal it by replaying the event log.
    TaskStatistics.objects.all().delete()
    assert TaskStatisticsQuery().counts() == {}

    rebuild_statistics()
    assert TaskStatisticsQuery().counts() == _write_model_counts()
