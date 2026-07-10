"""The Task aggregate root.

`Task` is a rich domain entity: it owns its invariants, enforces the lifecycle
state machine, and records domain events describing what changed. It has no
knowledge of persistence — repositories map it to and from storage.

Business rules are expressed as methods that mutate state *and* append the
corresponding event, so no state change can occur without a matching event.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from . import events as ev
from . import state_machine
from .exceptions import IllegalStateTransitionError, TaskValidationError
from .value_objects import Priority, TaskId, TaskStatus

MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 5_000


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(eq=False)
class Task:
    """Aggregate root representing a single unit of work to be done."""

    id: TaskId
    title: str
    description: str
    priority: Priority
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    # Events accumulated since the entity was loaded/created. Drained by the
    # application layer after the aggregate is persisted.
    _pending_events: list[ev.DomainEvent] = field(
        default_factory=list, repr=False, compare=False
    )

    # -- Construction --------------------------------------------------------
    @classmethod
    def create(
        cls,
        *,
        title: str,
        description: str = "",
        priority: Priority = Priority.NORMAL,
    ) -> Task:
        """Factory for a brand-new task. Emits a TaskCreated event."""
        clean_title = cls._validate_title(title)
        clean_description = cls._validate_description(description)
        now = _utcnow()
        task = cls(
            id=TaskId.new(),
            title=clean_title,
            description=clean_description,
            priority=priority,
            status=TaskStatus.DRAFT,
            created_at=now,
            updated_at=now,
        )
        task._record(
            ev.TaskCreated(
                aggregate_id=str(task.id),
                title=task.title,
                description=task.description,
                priority=task.priority.name,
                status=task.status.value,
            )
        )
        return task

    # -- Behavior ------------------------------------------------------------
    def edit_details(
        self, *, title: str | None = None, description: str | None = None
    ) -> None:
        """Edit mutable descriptive fields. Emits TaskDetailsEdited if changed."""
        changed: list[str] = []
        if title is not None:
            new_title = self._validate_title(title)
            if new_title != self.title:
                self.title = new_title
                changed.append("title")
        if description is not None:
            new_description = self._validate_description(description)
            if new_description != self.description:
                self.description = new_description
                changed.append("description")

        if changed:
            self._touch()
            self._record(
                ev.TaskDetailsEdited(
                    aggregate_id=str(self.id),
                    changed_fields=tuple(changed),
                    title=self.title if "title" in changed else None,
                    description=(
                        self.description if "description" in changed else None
                    ),
                )
            )

    def change_priority(self, priority: Priority) -> None:
        """Reprioritize the task. Emits TaskPriorityChanged if it differs."""
        if priority == self.priority:
            return
        previous = self.priority
        self.priority = priority
        self._touch()
        self._record(
            ev.TaskPriorityChanged(
                aggregate_id=str(self.id),
                from_priority=previous.name,
                to_priority=priority.name,
            )
        )

    def transition_to(self, target: TaskStatus, *, enforce: bool = True) -> None:
        """Move the task to a new status, honoring the state machine.

        `enforce` allows the strict-state-machine feature flag to be threaded
        through from the application layer.
        """
        if target == self.status:
            return
        if enforce and not state_machine.can_transition(self.status, target):
            raise IllegalStateTransitionError(
                current=self.status.value, requested=target.value
            )

        previous = self.status
        self.status = target
        self._touch()

        # Maintain the completion timestamp invariant alongside the status.
        if target == TaskStatus.COMPLETED:
            self.completed_at = self.updated_at
        elif previous == TaskStatus.COMPLETED:
            self.completed_at = None

        self._record(
            ev.TaskStatusChanged(
                aggregate_id=str(self.id),
                from_status=previous.value,
                to_status=target.value,
            )
        )

        # Emit additional semantic events for notable destination states.
        if target == TaskStatus.COMPLETED:
            self._record(ev.TaskCompleted(aggregate_id=str(self.id)))
        elif target == TaskStatus.ARCHIVED:
            self._record(ev.TaskArchived(aggregate_id=str(self.id)))

    # Convenience intents that read well at call sites.
    def start(self) -> None:
        self.transition_to(TaskStatus.ACTIVE)

    def block(self) -> None:
        self.transition_to(TaskStatus.BLOCKED)

    def complete(self) -> None:
        self.transition_to(TaskStatus.COMPLETED)

    def archive(self) -> None:
        self.transition_to(TaskStatus.ARCHIVED)

    def mark_deleted(self) -> None:
        """Record that the task was hard-deleted (so the history — and any
        event-fed read model — reflects the deletion). Emits TaskDeleted."""
        self._touch()
        self._record(
            ev.TaskDeleted(aggregate_id=str(self.id), status=self.status.value)
        )

    # -- Event plumbing ------------------------------------------------------
    def pull_events(self) -> list[ev.DomainEvent]:
        """Return and clear the pending events (drained after persistence)."""
        drained = list(self._pending_events)
        self._pending_events.clear()
        return drained

    def _record(self, event: ev.DomainEvent) -> None:
        self._pending_events.append(event)

    # -- Event sourcing: reconstruct state by replaying events ---------------
    @classmethod
    def rebuild(cls, events: list[ev.DomainEvent]) -> Task:
        """Reconstruct a Task purely from its event stream (ADR-0016).

        The first event must be TaskCreated; the rest are folded in via `_apply`.
        Timestamps are event-derived (`occurred_at`), so a rebuilt task equals the
        stored one on business state, not necessarily to the microsecond.
        """
        task: Task | None = None
        for event in events:
            if isinstance(event, ev.TaskCreated):
                task = cls(
                    id=TaskId.parse(event.aggregate_id),
                    title=event.title,
                    description=event.description,
                    priority=Priority[event.priority],
                    status=TaskStatus(event.status),
                    created_at=event.occurred_at,
                    updated_at=event.occurred_at,
                )
            elif task is None:
                raise TaskValidationError("Event stream must begin with TaskCreated.")
            else:
                task._apply(event)
        if task is None:
            raise TaskValidationError("Cannot rebuild from an empty event stream.")
        task._pending_events.clear()  # reconstruction emits nothing
        return task

    def _apply(self, event: ev.DomainEvent) -> None:
        """Mutate state from a historical event — no validation, no new events."""
        if isinstance(event, ev.TaskDetailsEdited):
            if event.title is not None:
                self.title = event.title
            if event.description is not None:
                self.description = event.description
        elif isinstance(event, ev.TaskStatusChanged):
            self.status = TaskStatus(event.to_status)
            if event.to_status == TaskStatus.COMPLETED.value:
                self.completed_at = event.occurred_at
            elif event.from_status == TaskStatus.COMPLETED.value:
                self.completed_at = None
        elif isinstance(event, ev.TaskPriorityChanged):
            self.priority = Priority[event.to_priority]
        # TaskCompleted / TaskArchived / TaskDeleted carry no state beyond what
        # earlier events set (a deleted task is detected by the repository).
        self.updated_at = event.occurred_at

    # -- Internal helpers ----------------------------------------------------
    def _touch(self) -> None:
        self.updated_at = _utcnow()

    @staticmethod
    def _validate_title(title: str) -> str:
        clean = (title or "").strip()
        if not clean:
            raise TaskValidationError("Title must not be empty.")
        if len(clean) > MAX_TITLE_LENGTH:
            raise TaskValidationError(
                f"Title must be at most {MAX_TITLE_LENGTH} characters."
            )
        return clean

    @staticmethod
    def _validate_description(description: str) -> str:
        clean = (description or "").strip()
        if len(clean) > MAX_DESCRIPTION_LENGTH:
            raise TaskValidationError(
                f"Description must be at most {MAX_DESCRIPTION_LENGTH} characters."
            )
        return clean
