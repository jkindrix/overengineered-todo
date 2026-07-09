"""Event handlers (post-commit subscribers).

These are cross-cutting reactions to domain events that run *after* the unit of
work commits: structured logging today, and things like notifications or webhooks
tomorrow. Because they run post-commit, their failures are isolated by the bus and
must not affect persisted state.

Durable audit persistence is deliberately NOT here — it is transactional and lives
in `infrastructure/event_store.py`, written inside the unit of work alongside the
state change. See ADR-0013.
"""
from __future__ import annotations

import logging

from tasks.domain.events import DomainEvent

logger = logging.getLogger("tasks.events")


class LoggingEventHandler:
    """Emit a structured log line for every domain event published."""

    def __call__(self, event: DomainEvent) -> None:
        logger.info(
            "event=%s aggregate=%s payload=%s",
            event.name,
            event.aggregate_id,
            event.payload(),
        )
