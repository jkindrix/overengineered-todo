"""Dependency-injection container — the composition root.

Constructs and wires the object graph exactly once per process: the event bus
and its subscribers, the repository, and the application service. Feature flags
from Django settings decide which subscribers are attached and whether the state
machine is strictly enforced. Everything downstream receives its collaborators
by injection rather than reaching for globals.
"""
from __future__ import annotations

import logging
import threading

from django.conf import settings

from tasks.application.event_bus import InMemoryEventBus
from tasks.application.handlers import LoggingEventHandler
from tasks.application.services import TaskApplicationService
from tasks.domain.events import (
    TaskArchived,
    TaskCompleted,
    TaskCreated,
    TaskDetailsEdited,
    TaskPriorityChanged,
    TaskStatusChanged,
)

from .event_store import DjangoEventStore
from .repositories import DjangoTaskRepository
from .unit_of_work import DjangoUnitOfWork

logger = logging.getLogger("tasks.container")

# Every concrete domain event type, so subscribers can attach to all of them.
_ALL_EVENT_TYPES = (
    TaskCreated,
    TaskDetailsEdited,
    TaskStatusChanged,
    TaskPriorityChanged,
    TaskCompleted,
    TaskArchived,
)


class Container:
    """Holds the wired singletons for the process lifetime."""

    def __init__(self) -> None:
        flags = getattr(settings, "FEATURE_FLAGS", {})

        self.event_bus = InMemoryEventBus()
        self.repository = DjangoTaskRepository()
        self.unit_of_work = DjangoUnitOfWork()
        self.event_store = DjangoEventStore()

        # Post-commit subscribers. Durable audit persistence is transactional
        # (via the event store), so the bus now carries only side-effects.
        if flags.get("EVENT_LOGGING", True):
            logging_handler = LoggingEventHandler()
            for event_type in _ALL_EVENT_TYPES:
                self.event_bus.subscribe(event_type, logging_handler)

        self.task_service = TaskApplicationService(
            repository=self.repository,
            unit_of_work=self.unit_of_work,
            event_store=self.event_store,
            event_publisher=self.event_bus,
            strict_state_machine=flags.get("STRICT_STATE_MACHINE", True),
            event_sourcing=flags.get("EVENT_SOURCING", True),
        )
        logger.debug("Container constructed with flags=%s", flags)


# --- Process-wide singleton access (thread-safe lazy initialization) --------
_container: Container | None = None
_lock = threading.Lock()


def get_container() -> Container:
    """Return the process-wide container, constructing it on first use."""
    global _container
    if _container is None:
        with _lock:
            if _container is None:
                _container = Container()
    return _container


def get_task_service() -> TaskApplicationService:
    """Convenience accessor for the wired application service."""
    return get_container().task_service


def reset_container() -> None:
    """Tear down the singleton (used by tests to rebuild with fresh state)."""
    global _container
    with _lock:
        _container = None
