"""Management command: rebuild CQRS read models from the event log.

    python manage.py rebuild_projections

The status-count projection is maintained incrementally by a post-commit
projector, so it can drift if a process dies between commit and projection. This
replays the whole event log to rebuild it from scratch. See ADR-0017.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from tasks.infrastructure.projections import TaskStatisticsQuery, rebuild_statistics


class Command(BaseCommand):
    help = "Rebuild the CQRS read-model projections by replaying the event log."

    def handle(self, *args, **options) -> None:
        rebuild_statistics()
        counts = TaskStatisticsQuery().counts()
        self.stdout.write(
            self.style.SUCCESS(f"Rebuilt statistics projection: {counts}")
        )
