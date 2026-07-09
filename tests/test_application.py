"""Application-service tests using a fake in-memory repository.

These verify use-case orchestration and event publishing without a database,
exercising the ports/adapters seam directly.
"""
from __future__ import annotations

from contextlib import nullcontext

import pytest

from tasks.application.dto import (
    CreateTaskCommand,
    DeleteTaskCommand,
    TransitionTaskCommand,
)
from tasks.application.event_bus import InMemoryEventBus
from tasks.application.services import TaskApplicationService
from tasks.domain.entities import Task
from tasks.domain.events import DomainEvent
from tasks.domain.exceptions import (
    IllegalStateTransitionError,
    TaskNotFoundError,
)
from tasks.domain.value_objects import Priority, TaskId, TaskStatus


class FakeRepository:
    """In-memory TaskRepository test double."""

    def __init__(self) -> None:
        self._store: dict[str, Task] = {}

    def add(self, task: Task) -> None:
        self._store[str(task.id)] = task

    def get(self, task_id: TaskId) -> Task:
        try:
            return self._store[str(task_id)]
        except KeyError as exc:
            raise TaskNotFoundError(str(task_id)) from exc

    def save(self, task: Task) -> None:
        if str(task.id) not in self._store:
            raise TaskNotFoundError(str(task.id))
        self._store[str(task.id)] = task

    def delete(self, task_id: TaskId) -> None:
        self._store.pop(str(task_id), None)

    def list(self, *, status=None, priority=None, search=None, order_by="-created_at"):
        items = list(self._store.values())
        if status is not None:
            items = [t for t in items if t.status is status]
        if priority is not None:
            items = [t for t in items if t.priority is priority]
        if search:
            items = [t for t in items if search.lower() in t.title.lower()]
        return items


class FakeUnitOfWork:
    """No-op transactional boundary for in-memory tests."""

    def atomic(self):
        return nullcontext()


class FakeEventStore:
    """Records appended events so tests can assert on the persisted history."""

    def __init__(self) -> None:
        self.appended: list[DomainEvent] = []

    def append(self, events) -> None:
        self.appended.extend(events)


@pytest.fixture
def wiring():
    bus = InMemoryEventBus()
    captured: list[DomainEvent] = []
    for event_type in DomainEvent.__subclasses__():
        bus.subscribe(event_type, captured.append)
    store = FakeEventStore()
    service = TaskApplicationService(
        repository=FakeRepository(),
        unit_of_work=FakeUnitOfWork(),
        event_store=store,
        event_publisher=bus,
        strict_state_machine=True,
    )
    return service, captured, store


def test_create_task_publishes_and_stores_created_event(wiring):
    service, captured, store = wiring
    task = service.create_task(
        CreateTaskCommand(title="Do the thing", priority="HIGH")
    )
    assert task.priority is Priority.HIGH
    # Published to post-commit subscribers...
    assert any(e.name == "TaskCreated" for e in captured)
    # ...and durably appended to the transactional event store.
    assert any(e.name == "TaskCreated" for e in store.appended)


def test_transition_flow_publishes_events(wiring):
    service, captured, _ = wiring
    task = service.create_task(CreateTaskCommand(title="Flow"))
    service.transition_task(
        TransitionTaskCommand(task_id=str(task.id), target_status="active")
    )
    service.transition_task(
        TransitionTaskCommand(task_id=str(task.id), target_status="completed")
    )
    names = [e.name for e in captured]
    assert "TaskStatusChanged" in names
    assert "TaskCompleted" in names


def test_illegal_transition_raises(wiring):
    service, _, _ = wiring
    task = service.create_task(CreateTaskCommand(title="Nope"))
    with pytest.raises(IllegalStateTransitionError):
        service.transition_task(
            TransitionTaskCommand(task_id=str(task.id), target_status="completed")
        )


def test_delete_missing_task_raises(wiring):
    service, _, _ = wiring
    with pytest.raises(TaskNotFoundError):
        service.delete_task(
            DeleteTaskCommand(task_id="00000000-0000-0000-0000-000000000000")
        )
