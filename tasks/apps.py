"""App configuration and composition-root bootstrapping."""

from __future__ import annotations

import logging

from django.apps import AppConfig

logger = logging.getLogger("tasks")


class TasksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tasks"
    verbose_name = "Overly-Engineered TODO"

    def ready(self) -> None:
        """Warm the dependency-injection container once the app is loaded.

        Importing the models module here guarantees the ORM models (which live
        in the infrastructure sub-package rather than a top-level models.py) are
        registered with the app registry. Building the container wires the event
        bus subscribers exactly once at startup.
        """
        # Ensure models are registered with the app registry.
        from tasks.infrastructure import models  # noqa: F401

        # Build the container so event-bus subscriptions are established.
        from tasks.infrastructure.container import get_container

        get_container()
        logger.debug("Tasks app ready; DI container initialized.")
