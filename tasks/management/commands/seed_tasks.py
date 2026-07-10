"""Management command: seed the database with demonstration tasks.

Drives the *application service* (not the ORM directly) so seeded data flows
through the exact same use cases, validations, state machine and event pipeline
as real user actions — every seeded task leaves a proper audit trail.

Usage:
    python manage.py seed_tasks
    python manage.py seed_tasks --count 12 --wipe
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from tasks.application.dto import (
    CreateTaskCommand,
    TransitionTaskCommand,
)
from tasks.infrastructure.container import get_task_service
from tasks.infrastructure.models import DomainEventRecord, TaskRecord

# (title, description, priority, [status transitions to apply after creation])
_SEED_DATA = [
    (
        "Read the source of this app",
        "Marvel at how a TODO list acquired a hexagonal architecture.",
        "NORMAL",
        ["active"],
    ),
    (
        "Ship the quarterly report",
        "Blocked on finance sign-off.",
        "HIGH",
        ["active", "blocked"],
    ),
    (
        "Water the office plant",
        "It has feelings and a domain event stream.",
        "LOW",
        ["active", "completed"],
    ),
    (
        "Rotate production secrets",
        "Do this before the certificate expires.",
        "CRITICAL",
        ["active"],
    ),
    (
        "Write ADR for event sourcing",
        "Document why the TODO app has an event store.",
        "NORMAL",
        [],
    ),
    (
        "Deprecated: migrate off floppy disks",
        "Historical task retained for the audit log.",
        "TRIVIAL",
        ["active", "completed", "archived"],
    ),
]


class Command(BaseCommand):
    help = "Seed the database with demonstration tasks via the application service."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--count",
            type=int,
            default=len(_SEED_DATA),
            help="How many seed tasks to create (cycles through the samples).",
        )
        parser.add_argument(
            "--wipe",
            action="store_true",
            help="Delete existing tasks and events before seeding.",
        )

    def handle(self, *args, **options) -> None:
        service = get_task_service()

        if options["wipe"]:
            deleted_tasks, _ = TaskRecord.objects.all().delete()
            deleted_events, _ = DomainEventRecord.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(
                    f"Wiped {deleted_tasks} task rows and {deleted_events} event rows."
                )
            )

        count = max(0, options["count"])
        created = 0
        for index in range(count):
            title, description, priority, transitions = _SEED_DATA[
                index % len(_SEED_DATA)
            ]
            # De-duplicate titles when cycling past the sample set.
            suffix = "" if index < len(_SEED_DATA) else f" ({index + 1})"
            task = service.create_task(
                CreateTaskCommand(
                    title=f"{title}{suffix}",
                    description=description,
                    priority=priority,
                )
            )
            for target in transitions:
                service.transition_task(
                    TransitionTaskCommand(task_id=str(task.id), target_status=target)
                )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created} tasks. "
                f"Event store now holds {DomainEventRecord.objects.count()} events."
            )
        )
