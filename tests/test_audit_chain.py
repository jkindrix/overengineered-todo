"""Tests for the tamper-evident audit-log hash chain (ADR-0014)."""

from __future__ import annotations

import pytest

from tasks.application.dto import CreateTaskCommand, TransitionTaskCommand
from tasks.infrastructure.audit_chain import verify_chain
from tasks.infrastructure.container import get_task_service
from tasks.infrastructure.models import DomainEventRecord


def _make_history() -> None:
    """Drive real events through the service: created + active + completed."""
    service = get_task_service()
    task = service.create_task(CreateTaskCommand(title="chain me"))
    service.transition_task(
        TransitionTaskCommand(task_id=str(task.id), target_status="active")
    )
    service.transition_task(
        TransitionTaskCommand(task_id=str(task.id), target_status="completed")
    )


@pytest.mark.django_db
def test_clean_chain_verifies():
    _make_history()
    result = verify_chain()
    assert result.ok
    # TaskCreated + TaskStatusChanged + (TaskStatusChanged + TaskCompleted)
    assert result.checked == 4


@pytest.mark.django_db
def test_edited_row_is_detected():
    _make_history()
    victim = DomainEventRecord.objects.order_by("id")[1]
    victim.event_name = "TamperedEvent"
    victim.save(update_fields=["event_name"])

    result = verify_chain()
    assert not result.ok
    assert result.first_bad_id == victim.id


@pytest.mark.django_db
def test_edited_payload_is_detected():
    _make_history()
    victim = DomainEventRecord.objects.order_by("id").first()
    victim.payload = {**victim.payload, "title": "smuggled change"}
    victim.save(update_fields=["payload"])

    result = verify_chain()
    assert not result.ok
    assert result.first_bad_id == victim.id


@pytest.mark.django_db
def test_deleted_row_is_detected():
    _make_history()
    ids = list(DomainEventRecord.objects.order_by("id").values_list("id", flat=True))
    DomainEventRecord.objects.filter(id=ids[1]).delete()  # remove a middle row

    result = verify_chain()
    assert not result.ok
    # The break surfaces at the row that followed the deleted one.
    assert result.first_bad_id == ids[2]
