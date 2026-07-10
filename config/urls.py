"""Root URL configuration.

Delegates the task-related routes to the `tasks` interface layer and exposes
the Django admin plus a lightweight liveness/readiness health endpoint.
"""

from django.contrib import admin
from django.urls import include, path

from tasks.interface.health import health_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", health_view, name="health"),
    path("", include("tasks.interface.urls")),
]
