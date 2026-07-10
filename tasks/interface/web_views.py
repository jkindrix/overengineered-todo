"""Server-rendered web UI views.

A small, dependency-free HTML front end over the same application service the
REST API uses — proving the layered design supports multiple transports. Uses
Django's messages framework for user feedback and PRG (post/redirect/get) for
mutating actions.
"""

from __future__ import annotations

from django.contrib import messages
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from tasks.application.dto import (
    ChangePriorityCommand,
    CreateTaskCommand,
    DeleteTaskCommand,
    GetTaskQuery,
    ListTasksQuery,
    TransitionTaskCommand,
)
from tasks.domain.exceptions import DomainError, TaskNotFoundError
from tasks.domain.value_objects import Priority, TaskStatus
from tasks.infrastructure.container import get_task_service

from .presenters import present_task, present_tasks


def _service():
    return get_task_service()


def _status_summary(tasks: list[dict]) -> dict[str, int]:
    """Count tasks per status for the dashboard header."""
    summary = {s.value: 0 for s in TaskStatus}
    for task in tasks:
        summary[task["status"]] = summary.get(task["status"], 0) + 1
    return summary


@require_http_methods(["GET"])
def task_list_view(request: HttpRequest) -> HttpResponse:
    status = request.GET.get("status") or None
    priority = request.GET.get("priority") or None
    search = request.GET.get("search") or None
    order_by = request.GET.get("order_by", "-created_at")

    query = ListTasksQuery(
        status=status, priority=priority, search=search, order_by=order_by
    )
    try:
        tasks = present_tasks(_service().list_tasks(query))
    except DomainError as exc:
        # An invalid status/priority filter (e.g. a tampered or stale URL) must
        # not 500 this page. Drop the enum filters, keep the safe ones, and tell
        # the user, mirroring how the write actions handle bad input.
        messages.error(request, f"Ignored an invalid filter: {exc}")
        status = priority = None
        query = ListTasksQuery(
            status=None, priority=None, search=search, order_by=order_by
        )
        tasks = present_tasks(_service().list_tasks(query))

    context = {
        "tasks": tasks,
        "summary": _status_summary(tasks),
        "priorities": [p.name for p in Priority],
        "statuses": [s.value for s in TaskStatus],
        "filters": {
            # Reflect the filters actually applied (cleared ones show as reset).
            "status": status or "",
            "priority": priority or "",
            "search": search or "",
            "order_by": order_by,
        },
    }
    return render(request, "tasks/task_list.html", context)


@require_http_methods(["GET"])
def task_detail_view(request: HttpRequest, task_id: str) -> HttpResponse:
    try:
        task = _service().get_task(GetTaskQuery(task_id=task_id))
    except TaskNotFoundError as exc:
        raise Http404(str(exc)) from exc
    context = {
        "task": present_task(task),
        "priorities": [p.name for p in Priority],
    }
    return render(request, "tasks/task_detail.html", context)


@require_http_methods(["POST"])
def create_task_action(request: HttpRequest) -> HttpResponse:
    try:
        _service().create_task(
            CreateTaskCommand(
                title=request.POST.get("title", ""),
                description=request.POST.get("description", ""),
                priority=request.POST.get("priority", "NORMAL"),
            )
        )
        messages.success(request, "Task created.")
    except DomainError as exc:
        messages.error(request, str(exc))
    return redirect("web-task-list")


@require_http_methods(["POST"])
def transition_task_action(request: HttpRequest, task_id: str) -> HttpResponse:
    try:
        _service().transition_task(
            TransitionTaskCommand(
                task_id=task_id,
                target_status=request.POST.get("target_status", ""),
            )
        )
        messages.success(request, "Status updated.")
    except DomainError as exc:
        messages.error(request, str(exc))
    return redirect(request.POST.get("next") or "web-task-list")


@require_http_methods(["POST"])
def change_priority_action(request: HttpRequest, task_id: str) -> HttpResponse:
    try:
        _service().change_priority(
            ChangePriorityCommand(
                task_id=task_id,
                priority=request.POST.get("priority", "NORMAL"),
            )
        )
        messages.success(request, "Priority updated.")
    except DomainError as exc:
        messages.error(request, str(exc))
    return redirect(request.POST.get("next") or "web-task-list")


@require_http_methods(["POST"])
def delete_task_action(request: HttpRequest, task_id: str) -> HttpResponse:
    try:
        _service().delete_task(DeleteTaskCommand(task_id=task_id))
        messages.success(request, "Task deleted.")
    except DomainError as exc:
        messages.error(request, str(exc))
    return redirect("web-task-list")
