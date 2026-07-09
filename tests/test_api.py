"""End-to-end API tests through the full stack (DB, ORM, DRF, event store)."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from django.test import Client

from tasks.infrastructure.event_store import DjangoEventStore
from tasks.infrastructure.models import DomainEventRecord, TaskRecord


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.mark.django_db
def test_create_and_list_task(client):
    resp = client.post(
        "/api/tasks/",
        data={"title": "API task", "priority": "HIGH"},
        content_type="application/json",
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "API task"
    assert body["status"] == "draft"

    list_resp = client.get("/api/tasks/")
    assert list_resp.status_code == 200
    assert list_resp.json()["count"] == 1


@pytest.mark.django_db
def test_list_is_paginated(client):
    for i in range(25):
        client.post(
            "/api/tasks/",
            data={"title": f"task {i}"},
            content_type="application/json",
        )
    page1 = client.get("/api/tasks/").json()
    assert page1["count"] == 25            # total across all pages
    assert len(page1["results"]) == 20     # PAGE_SIZE
    assert page1["next"] is not None       # a second page exists
    assert page1["previous"] is None

    page2 = client.get("/api/tasks/?page=2").json()
    assert len(page2["results"]) == 5
    assert page2["next"] is None


@pytest.mark.django_db
def test_full_lifecycle_writes_event_store(client):
    task_id = client.post(
        "/api/tasks/",
        data={"title": "Lifecycle"},
        content_type="application/json",
    ).json()["id"]

    client.post(
        f"/api/tasks/{task_id}/transition/",
        data={"target_status": "active"},
        content_type="application/json",
    )
    complete = client.post(
        f"/api/tasks/{task_id}/transition/",
        data={"target_status": "completed"},
        content_type="application/json",
    )
    assert complete.status_code == 200
    assert complete.json()["status"] == "completed"
    assert complete.json()["completed_at"] is not None

    # Event sourcing is on by default: creation + transitions were recorded.
    assert DomainEventRecord.objects.filter(aggregate_id=task_id).count() >= 3


@pytest.mark.django_db
def test_illegal_transition_returns_409(client):
    task_id = client.post(
        "/api/tasks/",
        data={"title": "Illegal"},
        content_type="application/json",
    ).json()["id"]
    # Draft -> Completed is not allowed.
    resp = client.post(
        f"/api/tasks/{task_id}/transition/",
        data={"target_status": "completed"},
        content_type="application/json",
    )
    assert resp.status_code == 409
    assert resp.json()["error"] == "IllegalStateTransitionError"


@pytest.mark.django_db
def test_missing_task_returns_404(client):
    resp = client.get("/api/tasks/00000000-0000-0000-0000-000000000000/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_delete_removes_task(client):
    task_id = client.post(
        "/api/tasks/",
        data={"title": "Delete me"},
        content_type="application/json",
    ).json()["id"]
    resp = client.delete(f"/api/tasks/{task_id}/")
    assert resp.status_code == 204
    assert not TaskRecord.objects.filter(pk=task_id).exists()


@pytest.mark.django_db
def test_web_board_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Overly-Engineered" in resp.content


@pytest.mark.django_db
def test_api_rejects_bad_enum_input_with_400(client):
    # Tampered/malformed enum values must be a clean 400, never a 500.
    task_id = client.post(
        "/api/tasks/", data={"title": "T"}, content_type="application/json"
    ).json()["id"]
    bad_priority = client.post(
        f"/api/tasks/{task_id}/priority/",
        data={"priority": "BOGUS"},
        content_type="application/json",
    )
    assert bad_priority.status_code == 400
    bad_status = client.post(
        f"/api/tasks/{task_id}/transition/",
        data={"target_status": "BOGUS"},
        content_type="application/json",
    )
    assert bad_status.status_code == 400


@pytest.mark.django_db
def test_web_forms_reject_bad_input_without_500(client):
    # Regression: bad enum values posted to the web actions must be handled
    # (PRG redirect with an error message), not crash with a 500.
    task_id = client.post(
        "/api/tasks/", data={"title": "T"}, content_type="application/json"
    ).json()["id"]

    create = client.post("/tasks/create", {"title": "x", "priority": "BOGUS"})
    assert create.status_code == 302  # redirect, not 500

    transition = client.post(
        f"/tasks/{task_id}/transition", {"target_status": "BOGUS"}
    )
    assert transition.status_code == 302

    priority = client.post(f"/tasks/{task_id}/priority", {"priority": "BOGUS"})
    assert priority.status_code == 302


@pytest.mark.django_db
def test_event_store_failure_rolls_back_state(client):
    # The core transactional guarantee: if the audit/event write fails, the
    # state write must roll back too, leaving nothing persisted.
    before = TaskRecord.objects.count()
    events_before = DomainEventRecord.objects.count()

    inner = Client(raise_request_exception=False)
    with patch.object(
        DjangoEventStore, "append", side_effect=RuntimeError("boom")
    ):
        resp = inner.post(
            "/api/tasks/",
            data={"title": "should not persist"},
            content_type="application/json",
        )

    assert resp.status_code == 500  # the failure surfaced, not swallowed
    # Neither the task nor any event row survived — the transaction rolled back.
    assert TaskRecord.objects.count() == before
    assert DomainEventRecord.objects.count() == events_before
    assert not TaskRecord.objects.filter(title="should not persist").exists()


@pytest.mark.django_db
def test_health_endpoint(client):
    resp = client.get("/healthz/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["checks"]["database"] == "ok"
