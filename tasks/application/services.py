"""The task application service — the use-case orchestration layer.

Each public method is one use case. The service is deliberately thin: it loads
aggregates through the repository port, invokes rich domain behavior, persists,
then drains and publishes the resulting domain events. All business rules live
in the domain; all wiring lives in the container. This class only coordinates.
"""
from __future__ import annotations

import logging
from typing import Sequence

from tasks.domain.entities import Task
from tasks.domain.events import DomainEvent
from tasks.domain.value_objects import Priority, TaskId, TaskStatus

from .dto import (
    ChangePriorityCommand,
    CreateTaskCommand,
    DeleteTaskCommand,
    EditTaskCommand,
    GetTaskQuery,
    ListTasksQuery,
    TransitionTaskCommand,
)
from .ports import EventPublisher, EventStore, TaskRepository, UnitOfWork

logger = logging.getLogger("tasks.services")


class TaskApplicationService:
    """Coordinates task use cases across the repository and event publisher."""

    def __init__(
        self,
        *,
        repository: TaskRepository,
        unit_of_work: UnitOfWork,
        event_store: EventStore,
        event_publisher: EventPublisher,
        strict_state_machine: bool = True,
        event_sourcing: bool = True,
    ) -> None:
        self._repository = repository
        self._uow = unit_of_work
        self._event_store = event_store
        self._events = event_publisher
        self._strict_state_machine = strict_state_machine
        self._event_sourcing = event_sourcing

    # -- Commands ------------------------------------------------------------
    def create_task(self, command: CreateTaskCommand) -> Task:
        task = Task.create(
            title=command.title,
            description=command.description,
            priority=Priority.from_name(command.priority),
        )
        events = self._commit(task, persist=self._repository.add)
        self._dispatch(events)
        logger.info("Created task %s (%s)", task.id, task.title)
        return task

    def edit_task(self, command: EditTaskCommand) -> Task:
        task = self._repository.get(TaskId.parse(command.task_id))
        task.edit_details(title=command.title, description=command.description)
        events = self._commit(task, persist=self._repository.save)
        self._dispatch(events)
        return task

    def change_priority(self, command: ChangePriorityCommand) -> Task:
        task = self._repository.get(TaskId.parse(command.task_id))
        task.change_priority(Priority.from_name(command.priority))
        events = self._commit(task, persist=self._repository.save)
        self._dispatch(events)
        return task

    def transition_task(self, command: TransitionTaskCommand) -> Task:
        task = self._repository.get(TaskId.parse(command.task_id))
        task.transition_to(
            TaskStatus.from_value(command.target_status),
            enforce=self._strict_state_machine,
        )
        events = self._commit(task, persist=self._repository.save)
        self._dispatch(events)
        logger.info("Task %s -> %s", task.id, task.status.value)
        return task

    def delete_task(self, command: DeleteTaskCommand) -> None:
        task_id = TaskId.parse(command.task_id)
        with self._uow.atomic():
            # get() first so a missing task raises TaskNotFoundError consistently.
            self._repository.get(task_id)
            self._repository.delete(task_id)
        logger.info("Deleted task %s", task_id)

    # -- Queries -------------------------------------------------------------
    def get_task(self, query: GetTaskQuery) -> Task:
        return self._repository.get(TaskId.parse(query.task_id))

    def list_tasks(self, query: ListTasksQuery) -> Sequence[Task]:
        status = (
            TaskStatus.from_value(query.status) if query.status else None
        )
        priority = (
            Priority.from_name(query.priority) if query.priority else None
        )
        return self._repository.list(
            status=status,
            priority=priority,
            search=query.search,
            order_by=query.order_by,
        )

    # -- Internal ------------------------------------------------------------
    def _commit(self, task: Task, *, persist) -> Sequence[DomainEvent]:
        """Persist the aggregate and its events in a single transaction.

        The repository write and the event-store append happen inside one unit
        of work, so state and history commit together or roll back together. If
        either write fails, the whole use case aborts and nothing is persisted —
        this is what closes the state/audit divergence gap. Events are drained
        here (inside the transaction) and returned for post-commit dispatch.
        """
        with self._uow.atomic():
            persist(task)
            events = task.pull_events()
            if self._event_sourcing and events:
                self._event_store.append(events)
        return events

    def _dispatch(self, events: Sequence[DomainEvent]) -> None:
        """Publish events to post-commit subscribers (logging, side-effects).

        Runs only after the transaction has committed. Subscriber failures are
        isolated by the bus and cannot affect already-persisted state.
        """
        if events:
            self._events.publish_all(events)
