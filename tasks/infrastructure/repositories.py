"""Django-backed implementation of the TaskRepository port."""

from __future__ import annotations

from collections.abc import Sequence

from django.db.models import Q

from tasks.domain.entities import Task
from tasks.domain.exceptions import TaskNotFoundError
from tasks.domain.value_objects import Priority, TaskId, TaskStatus

from .mappers import apply_entity_to_record, record_to_entity
from .models import TaskRecord

# Whitelist of fields the API/UI may sort by, mapped to ORM order expressions.
# This prevents arbitrary/injection-y ordering while giving a stable contract.
_ORDER_WHITELIST: dict[str, str] = {
    "created_at": "created_at",
    "-created_at": "-created_at",
    "updated_at": "updated_at",
    "-updated_at": "-updated_at",
    "priority": "priority",
    "-priority": "-priority",
    "title": "title",
    "-title": "-title",
}


class DjangoTaskRepository:
    """Persist and retrieve Task aggregates via the Django ORM."""

    def add(self, task: Task) -> None:
        record = apply_entity_to_record(task, TaskRecord())
        record.save(force_insert=True)

    def get(self, task_id: TaskId) -> Task:
        try:
            record = TaskRecord.objects.get(pk=task_id.value)
        except TaskRecord.DoesNotExist as exc:
            raise TaskNotFoundError(f"Task {task_id} does not exist.") from exc
        return record_to_entity(record)

    def save(self, task: Task) -> None:
        try:
            record = TaskRecord.objects.get(pk=task.id.value)
        except TaskRecord.DoesNotExist as exc:
            raise TaskNotFoundError(f"Task {task.id} does not exist.") from exc
        apply_entity_to_record(task, record)
        record.save(force_update=True)

    def delete(self, task_id: TaskId) -> None:
        TaskRecord.objects.filter(pk=task_id.value).delete()

    def list(
        self,
        *,
        status: TaskStatus | None = None,
        priority: Priority | None = None,
        search: str | None = None,
        order_by: str = "-created_at",
    ) -> Sequence[Task]:
        queryset = TaskRecord.objects.all()
        if status is not None:
            queryset = queryset.filter(status=status.value)
        if priority is not None:
            queryset = queryset.filter(priority=priority.value)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        ordering = _ORDER_WHITELIST.get(order_by, "-created_at")
        queryset = queryset.order_by(ordering)
        return [record_to_entity(record) for record in queryset]
