"""REST API views.

A thin HTTP adapter over the application service. Each endpoint validates input
with a serializer, builds a command/query DTO, delegates to the service, and
renders the result through a presenter. No business logic lives here.
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

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
from .serializers import (
    ChangePrioritySerializer,
    CreateTaskSerializer,
    EditTaskSerializer,
    TransitionSerializer,
)


class TaskViewSet(ViewSet):
    """CRUD + lifecycle endpoints for tasks.

    Routes (registered manually in urls.py):
        GET    /api/tasks/                  -> list
        POST   /api/tasks/                  -> create
        GET    /api/tasks/{id}/             -> retrieve
        PATCH  /api/tasks/{id}/             -> partial_update (edit details)
        DELETE /api/tasks/{id}/             -> destroy
        POST   /api/tasks/{id}/priority/    -> change_priority
        POST   /api/tasks/{id}/transition/  -> transition
    """

    @property
    def service(self):
        return get_task_service()

    def list(self, request: Request) -> Response:
        query = ListTasksQuery(
            status=request.query_params.get("status"),
            priority=request.query_params.get("priority"),
            search=request.query_params.get("search"),
            order_by=request.query_params.get("order_by", "-created_at"),
        )
        tasks = self.service.list_tasks(query)
        # Honor the project-wide PAGE_SIZE (DRF settings) with a standard
        # count/next/previous/results envelope. `?page=` selects the page.
        paginator = PageNumberPagination()
        # paginate_queryset is typed for a Django QuerySet, but at runtime it
        # accepts any sliceable sequence — which our list of domain entities is.
        page = paginator.paginate_queryset(tasks, request, view=self)  # pyright: ignore[reportArgumentType]
        return paginator.get_paginated_response(present_tasks(page))

    def create(self, request: Request) -> Response:
        serializer = CreateTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = self.service.create_task(CreateTaskCommand(**serializer.validated_data))
        return Response(present_task(task), status=status.HTTP_201_CREATED)

    def retrieve(self, request: Request, pk: str) -> Response:
        task = self.service.get_task(GetTaskQuery(task_id=pk))
        return Response(present_task(task))

    def partial_update(self, request: Request, pk: str) -> Response:
        serializer = EditTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = self.service.edit_task(
            EditTaskCommand(task_id=pk, **serializer.validated_data)
        )
        return Response(present_task(task))

    def destroy(self, request: Request, pk: str) -> Response:
        self.service.delete_task(DeleteTaskCommand(task_id=pk))
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def priority(self, request: Request, pk: str) -> Response:
        serializer = ChangePrioritySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = self.service.change_priority(
            ChangePriorityCommand(
                task_id=pk, priority=serializer.validated_data["priority"]
            )
        )
        return Response(present_task(task))

    @action(detail=True, methods=["post"])
    def transition(self, request: Request, pk: str) -> Response:
        serializer = TransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = self.service.transition_task(
            TransitionTaskCommand(
                task_id=pk,
                target_status=serializer.validated_data["target_status"],
            )
        )
        return Response(present_task(task))
