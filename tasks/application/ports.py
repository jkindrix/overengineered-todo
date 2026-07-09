"""Ports — the abstract interfaces the application depends on.

These are the seams that keep the application layer ignorant of infrastructure.
Concrete adapters (Django repositories, the in-memory event bus, etc.) implement
these protocols and are injected via the container.
"""
from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Protocol, Sequence, runtime_checkable

from tasks.domain.entities import Task
from tasks.domain.events import DomainEvent
from tasks.domain.value_objects import Priority, TaskId, TaskStatus


@runtime_checkable
class TaskRepository(Protocol):
    """Persistence port for the Task aggregate."""

    def add(self, task: Task) -> None:
        """Persist a newly created aggregate."""

    def get(self, task_id: TaskId) -> Task:
        """Load an aggregate by identity, or raise TaskNotFoundError."""

    def save(self, task: Task) -> None:
        """Persist changes to an existing aggregate."""

    def delete(self, task_id: TaskId) -> None:
        """Remove an aggregate from storage."""

    def list(
        self,
        *,
        status: TaskStatus | None = None,
        priority: Priority | None = None,
        search: str | None = None,
        order_by: str = "-created_at",
    ) -> Sequence[Task]:
        """Return aggregates matching the given filters."""


@runtime_checkable
class UnitOfWork(Protocol):
    """Port defining a transactional boundary for a single use case.

    `atomic()` returns a context manager: everything written inside it (the
    aggregate *and* its events) commits together, or not at all. This is the
    seam that lets the application demand atomicity without importing Django.
    """

    def atomic(self) -> AbstractContextManager[None]:
        """Return a context manager that commits on success, rolls back on error."""


@runtime_checkable
class EventStore(Protocol):
    """Port for durably persisting domain events within the current transaction.

    Distinct from EventPublisher: the store is the *transactional* record of what
    happened (written inside the unit of work), whereas the publisher performs
    *post-commit* side-effects (logging, notifications) that may fail in isolation.
    """

    def append(self, events: Sequence[DomainEvent]) -> None:
        """Persist a batch of events. Called inside a unit of work."""


@runtime_checkable
class EventPublisher(Protocol):
    """Port for publishing domain events to interested subscribers.

    Dispatched *after* the unit of work commits; subscriber failures are isolated
    and must not affect persisted state.
    """

    def publish(self, event: DomainEvent) -> None:
        """Dispatch a single event to all matching handlers."""

    def publish_all(self, events: Sequence[DomainEvent]) -> None:
        """Dispatch a batch of events in order."""
