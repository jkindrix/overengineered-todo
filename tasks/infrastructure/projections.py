"""CQRS read-model projections (ADR-0017).

A *projector* consumes domain events and maintains a denormalized read model
(`TaskStatistics`: live counts per status) optimized for a query that would
otherwise be a GROUP BY over the write model. A *query service* reads it. The
whole projection is rebuildable by replaying the event log — so if the
(post-commit, hence eventually-consistent) projector ever drifts, replay heals it.
"""

from __future__ import annotations

from django.db import transaction
from django.db.models import F

from tasks.domain.events import (
    DomainEvent,
    TaskCreated,
    TaskDeleted,
    TaskStatusChanged,
)
from tasks.domain.value_objects import TaskStatus

from .event_serialization import deserialize_event
from .models import DomainEventRecord, TaskStatistics


def _bump(status: str, delta: int) -> None:
    TaskStatistics.objects.get_or_create(status=status, defaults={"count": 0})
    TaskStatistics.objects.filter(status=status).update(count=F("count") + delta)


class StatisticsProjector:
    """Post-commit event subscriber that keeps the status-count read model current."""

    def __call__(self, event: DomainEvent) -> None:
        if isinstance(event, TaskCreated):
            _bump(TaskStatus.DRAFT.value, +1)
        elif isinstance(event, TaskStatusChanged):
            _bump(event.from_status, -1)
            _bump(event.to_status, +1)
        elif isinstance(event, TaskDeleted):
            _bump(event.status, -1)


class TaskStatisticsQuery:
    """The query side: read the projection (O(1)), never the write model."""

    def counts(self) -> dict[str, int]:
        rows = TaskStatistics.objects.all()
        return {row.status: row.count for row in rows if row.count}


def rebuild_statistics() -> None:
    """Rebuild the read model from scratch by replaying the entire event log."""
    projector = StatisticsProjector()
    with transaction.atomic():
        TaskStatistics.objects.all().delete()
        for record in DomainEventRecord.objects.order_by("id").iterator():
            event = deserialize_event(
                event_name=record.event_name,
                version=record.version,
                aggregate_id=record.aggregate_id,
                occurred_at=record.occurred_at,
                payload=record.payload,
            )
            projector(event)
