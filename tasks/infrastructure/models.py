"""Django ORM models — the persistence adapter's data schema.

These models are pure storage records. They are intentionally *not* the domain
entities: the repository maps between `TaskRecord` rows and `Task` aggregates.
Keeping them separate lets the domain evolve independently of the schema.
"""

from __future__ import annotations

import uuid

from django.db import models

from tasks.domain.value_objects import Priority, TaskStatus


class TaskRecord(models.Model):
    """Storage record for a Task aggregate."""

    # Status choices are derived from the domain enum so the two never drift.
    STATUS_CHOICES = [(s.value, s.label) for s in TaskStatus]
    PRIORITY_CHOICES = [(p.value, p.label) for p in Priority]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES, default=Priority.NORMAL.value
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=TaskStatus.DRAFT.value,
    )
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "tasks"
        db_table = "tasks_task"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - display helper
        return f"{self.title} [{self.status}]"


class DomainEventRecord(models.Model):
    """Append-only event store row (populated when event sourcing is enabled)."""

    id = models.BigAutoField(primary_key=True)
    aggregate_id = models.UUIDField(db_index=True)
    event_name = models.CharField(max_length=100, db_index=True)
    occurred_at = models.DateTimeField()
    payload = models.JSONField(default=dict)
    recorded_at = models.DateTimeField(auto_now_add=True)
    # Tamper-evident hash chain (SHA-256 hex). Each row's entry_hash seals its
    # content to the previous row's, so any edit/deletion of history is
    # detectable via `manage.py verify_audit_log`. See ADR-0014.
    prev_hash = models.CharField(max_length=64, blank=True, default="")
    entry_hash = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        app_label = "tasks"
        db_table = "tasks_domain_event"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["aggregate_id", "id"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - display helper
        return f"{self.event_name}@{self.aggregate_id}"
