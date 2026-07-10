"""Django admin registration for the storage records."""

from __future__ import annotations

from django.contrib import admin

from tasks.infrastructure.models import DomainEventRecord, TaskRecord


@admin.register(TaskRecord)
class TaskRecordAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "priority", "created_at", "updated_at")
    list_filter = ("status", "priority")
    search_fields = ("title", "description")
    readonly_fields = ("id", "created_at", "updated_at", "completed_at")
    ordering = ("-created_at",)


@admin.register(DomainEventRecord)
class DomainEventRecordAdmin(admin.ModelAdmin):
    list_display = ("event_name", "aggregate_id", "occurred_at", "recorded_at")
    list_filter = ("event_name",)
    search_fields = ("aggregate_id", "event_name")
    readonly_fields = (
        "aggregate_id",
        "event_name",
        "occurred_at",
        "payload",
        "recorded_at",
    )
    ordering = ("-id",)

    def has_add_permission(self, request) -> bool:
        # The event store is append-only via the domain; block manual creation.
        return False
