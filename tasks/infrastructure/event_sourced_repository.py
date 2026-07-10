"""Event-sourced Task repository — reconstruct aggregates by replaying events.

A *demonstration* of event sourcing (ADR-0016): unlike `DjangoTaskRepository`
(which reads the current-state row), this loads a Task purely from its event
stream. The app still uses the state-based repository for reads/queries; this one
proves state is fully derivable from events, and enables time-travel and snapshots.
"""

from __future__ import annotations

from tasks.domain.entities import Task
from tasks.domain.exceptions import TaskNotFoundError
from tasks.domain.value_objects import TaskId

from .event_serialization import (
    deserialize_event,
    deserialize_task,
    serialize_task,
)
from .models import DomainEventRecord, TaskSnapshot


class EventSourcedTaskRepository:
    """Load Tasks by folding their event history (from the newest snapshot)."""

    def get(self, task_id: TaskId) -> Task:
        """Reconstruct the current state of a task from its events."""
        snapshot = (
            TaskSnapshot.objects.filter(aggregate_id=task_id.value)
            .order_by("-last_event_id")
            .first()
        )
        rows = DomainEventRecord.objects.filter(aggregate_id=task_id.value)
        if snapshot is not None:
            rows = rows.filter(id__gt=snapshot.last_event_id)
        events = [self._to_event(r) for r in rows.order_by("id")]

        if snapshot is None:
            if not events:
                raise TaskNotFoundError(f"No events for task {task_id}.")
            return Task.rebuild(events)

        task = deserialize_task(snapshot.state)
        for event in events:
            task._apply(event)
        return task

    def reconstitute_at(self, task_id: TaskId, event_id: int) -> Task:
        """Time-travel: the task's state as of (and including) `event_id`.

        Replays from the beginning (ignoring snapshots) up to the given row.
        """
        rows = DomainEventRecord.objects.filter(
            aggregate_id=task_id.value, id__lte=event_id
        ).order_by("id")
        events = [self._to_event(r) for r in rows]
        if not events:
            raise TaskNotFoundError(
                f"No events for task {task_id} up to event {event_id}."
            )
        return Task.rebuild(events)

    def take_snapshot(self, task_id: TaskId) -> TaskSnapshot:
        """Fold the full history into a snapshot for cheaper future reads."""
        last_id = (
            DomainEventRecord.objects.filter(aggregate_id=task_id.value)
            .order_by("-id")
            .values_list("id", flat=True)
            .first()
        )
        if last_id is None:
            raise TaskNotFoundError(f"No events for task {task_id}.")
        task = self.get(task_id)
        return TaskSnapshot.objects.create(
            aggregate_id=task_id.value,
            last_event_id=last_id,
            state=serialize_task(task),
        )

    @staticmethod
    def _to_event(record: DomainEventRecord):
        return deserialize_event(
            event_name=record.event_name,
            version=record.version,
            aggregate_id=record.aggregate_id,
            occurred_at=record.occurred_at,
            payload=record.payload,
        )
