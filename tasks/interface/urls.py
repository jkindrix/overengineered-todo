"""URL routing for the tasks interface layer (REST API + web UI)."""
from __future__ import annotations

from django.urls import path

from .api_views import TaskViewSet
from . import web_views

# Manually bind the ViewSet's actions to routes. A router would also work, but
# explicit wiring keeps the API surface obvious and greppable.
task_list = TaskViewSet.as_view({"get": "list", "post": "create"})
task_detail = TaskViewSet.as_view(
    {
        "get": "retrieve",
        "patch": "partial_update",
        "delete": "destroy",
    }
)
task_priority = TaskViewSet.as_view({"post": "priority"})
task_transition = TaskViewSet.as_view({"post": "transition"})

urlpatterns = [
    # --- Web UI ---------------------------------------------------------
    path("", web_views.task_list_view, name="web-task-list"),
    path("tasks/create", web_views.create_task_action, name="web-task-create"),
    path(
        "tasks/<uuid:task_id>",
        web_views.task_detail_view,
        name="web-task-detail",
    ),
    path(
        "tasks/<uuid:task_id>/transition",
        web_views.transition_task_action,
        name="web-task-transition",
    ),
    path(
        "tasks/<uuid:task_id>/priority",
        web_views.change_priority_action,
        name="web-task-priority",
    ),
    path(
        "tasks/<uuid:task_id>/delete",
        web_views.delete_task_action,
        name="web-task-delete",
    ),
    # --- REST API -------------------------------------------------------
    path("api/tasks/", task_list, name="api-task-list"),
    path("api/tasks/<uuid:pk>/", task_detail, name="api-task-detail"),
    path(
        "api/tasks/<uuid:pk>/priority/",
        task_priority,
        name="api-task-priority",
    ),
    path(
        "api/tasks/<uuid:pk>/transition/",
        task_transition,
        name="api-task-transition",
    ),
]
