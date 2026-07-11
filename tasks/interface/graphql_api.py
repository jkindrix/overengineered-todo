"""GraphQL transport (Strawberry) — a third adapter over the same core.

Queries and mutations map onto the *same* application service, command/query DTOs,
and presenters as the REST and web transports. Nothing below the interface layer
knows this exists (import-linter enforces it): GraphQL types are built from
presenter output, not the ORM. Its query/mutation split mirrors our CQRS-lite
command/query DTOs. See ADR-0018.
"""

from __future__ import annotations

from typing import Any

import strawberry

from tasks.application.dto import (
    ChangePriorityCommand,
    CreateTaskCommand,
    DeleteTaskCommand,
    EditTaskCommand,
    GetTaskQuery,
    ListTasksQuery,
    TransitionTaskCommand,
)
from tasks.infrastructure.container import get_task_service

from .presenters import present_task, present_tasks


@strawberry.type
class Task:
    id: str
    title: str
    description: str
    priority: str
    status: str
    is_terminal: bool
    allowed_transitions: list[str]
    created_at: str
    updated_at: str
    completed_at: str | None


def _to_task(data: dict[str, Any]) -> Task:
    return Task(
        id=data["id"],
        title=data["title"],
        description=data["description"],
        priority=data["priority"],
        status=data["status"],
        is_terminal=data["is_terminal"],
        allowed_transitions=data["allowed_transitions"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        completed_at=data["completed_at"],
    )


@strawberry.type
class Query:
    @strawberry.field
    def task(self, id: str) -> Task:
        found = get_task_service().get_task(GetTaskQuery(task_id=id))
        return _to_task(present_task(found))

    @strawberry.field
    def tasks(
        self,
        status: str | None = None,
        priority: str | None = None,
        search: str | None = None,
        order_by: str = "-created_at",
    ) -> list[Task]:
        results = get_task_service().list_tasks(
            ListTasksQuery(
                status=status, priority=priority, search=search, order_by=order_by
            )
        )
        return [_to_task(d) for d in present_tasks(results)]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_task(
        self, title: str, description: str = "", priority: str = "NORMAL"
    ) -> Task:
        created = get_task_service().create_task(
            CreateTaskCommand(title=title, description=description, priority=priority)
        )
        return _to_task(present_task(created))

    @strawberry.mutation
    def edit_task(
        self, id: str, title: str | None = None, description: str | None = None
    ) -> Task:
        edited = get_task_service().edit_task(
            EditTaskCommand(task_id=id, title=title, description=description)
        )
        return _to_task(present_task(edited))

    @strawberry.mutation
    def change_priority(self, id: str, priority: str) -> Task:
        changed = get_task_service().change_priority(
            ChangePriorityCommand(task_id=id, priority=priority)
        )
        return _to_task(present_task(changed))

    @strawberry.mutation
    def transition_task(self, id: str, target_status: str) -> Task:
        moved = get_task_service().transition_task(
            TransitionTaskCommand(task_id=id, target_status=target_status)
        )
        return _to_task(present_task(moved))

    @strawberry.mutation
    def delete_task(self, id: str) -> bool:
        get_task_service().delete_task(DeleteTaskCommand(task_id=id))
        return True


schema = strawberry.Schema(query=Query, mutation=Mutation)
