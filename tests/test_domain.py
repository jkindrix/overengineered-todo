"""Unit tests for the pure domain layer (no database required)."""
from __future__ import annotations

import pytest

from tasks.domain.entities import Task
from tasks.domain.events import (
    TaskCompleted,
    TaskCreated,
    TaskStatusChanged,
)
from tasks.domain.exceptions import (
    IllegalStateTransitionError,
    TaskValidationError,
)
from tasks.domain.state_machine import allowed_targets, can_transition
from tasks.domain.value_objects import Priority, TaskStatus


def test_create_emits_created_event_and_starts_in_draft():
    task = Task.create(title="  Write tests  ", priority=Priority.HIGH)
    assert task.title == "Write tests"  # trimmed
    assert task.status is TaskStatus.DRAFT
    events = task.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], TaskCreated)
    # Events are drained after pulling.
    assert task.pull_events() == []


def test_blank_title_is_rejected():
    with pytest.raises(TaskValidationError):
        Task.create(title="   ")


def test_valid_transition_records_status_change():
    task = Task.create(title="A task")
    task.pull_events()  # discard creation event
    task.transition_to(TaskStatus.ACTIVE)
    events = task.pull_events()
    assert [type(e) for e in events] == [TaskStatusChanged]
    assert task.status is TaskStatus.ACTIVE


def test_completing_sets_completed_at_and_emits_completed_event():
    task = Task.create(title="A task")
    task.transition_to(TaskStatus.ACTIVE)
    task.pull_events()
    task.transition_to(TaskStatus.COMPLETED)
    assert task.completed_at is not None
    events = task.pull_events()
    assert any(isinstance(e, TaskCompleted) for e in events)


def test_reopening_completed_task_clears_completed_at():
    task = Task.create(title="A task")
    task.transition_to(TaskStatus.ACTIVE)
    task.transition_to(TaskStatus.COMPLETED)
    task.transition_to(TaskStatus.ACTIVE)  # reopen
    assert task.completed_at is None


def test_illegal_transition_is_rejected():
    task = Task.create(title="A task")  # DRAFT
    with pytest.raises(IllegalStateTransitionError):
        task.transition_to(TaskStatus.COMPLETED)  # can't complete a draft


def test_transition_can_be_forced_when_enforcement_disabled():
    task = Task.create(title="A task")  # DRAFT
    task.transition_to(TaskStatus.COMPLETED, enforce=False)
    assert task.status is TaskStatus.COMPLETED


def test_state_machine_tables():
    assert can_transition(TaskStatus.DRAFT, TaskStatus.ACTIVE)
    assert not can_transition(TaskStatus.ARCHIVED, TaskStatus.ACTIVE)
    assert not can_transition(TaskStatus.ACTIVE, TaskStatus.ACTIVE)  # no self
    assert TaskStatus.ARCHIVED in allowed_targets(TaskStatus.ACTIVE)


def test_priority_change_is_idempotent_without_event():
    task = Task.create(title="A task", priority=Priority.NORMAL)
    task.pull_events()
    task.change_priority(Priority.NORMAL)  # same -> no-op
    assert task.pull_events() == []
    task.change_priority(Priority.CRITICAL)
    assert len(task.pull_events()) == 1


def test_priority_ordering():
    assert Priority.CRITICAL > Priority.LOW
    assert Priority.from_name("high") is Priority.HIGH


def test_bad_enum_values_raise_domain_errors_not_valueerror():
    # Untrusted input must surface as a DomainError so transports can map it to
    # a 400, rather than escaping as an unhandled ValueError (-> HTTP 500).
    with pytest.raises(TaskValidationError):
        Priority.from_name("BOGUS")
    with pytest.raises(TaskValidationError):
        TaskStatus.from_value("BOGUS")
