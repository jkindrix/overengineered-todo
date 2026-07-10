"""Commands, queries and result DTOs (a light CQRS separation).

Commands express an intent to change state; queries express an intent to read.
Both are plain, immutable data carriers so the transport layer (DRF, web views,
management commands, tests) can construct them without touching the domain.
"""

from __future__ import annotations

from dataclasses import dataclass


# --- Commands (writes) ------------------------------------------------------
@dataclass(frozen=True, slots=True)
class CreateTaskCommand:
    title: str
    description: str = ""
    priority: str = "NORMAL"


@dataclass(frozen=True, slots=True)
class EditTaskCommand:
    task_id: str
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class ChangePriorityCommand:
    task_id: str
    priority: str


@dataclass(frozen=True, slots=True)
class TransitionTaskCommand:
    task_id: str
    target_status: str


@dataclass(frozen=True, slots=True)
class DeleteTaskCommand:
    task_id: str


# --- Queries (reads) --------------------------------------------------------
@dataclass(frozen=True, slots=True)
class ListTasksQuery:
    status: str | None = None
    priority: str | None = None
    search: str | None = None
    order_by: str = "-created_at"


@dataclass(frozen=True, slots=True)
class GetTaskQuery:
    task_id: str
