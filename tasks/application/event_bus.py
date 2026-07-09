"""A minimal synchronous, in-process event bus.

Handlers subscribe to a concrete event type (by class) and are invoked in
registration order when a matching event is published. A handler that raises is
isolated: its failure is logged and swallowed so one bad subscriber cannot break
the others or the originating use case. This is an application concern, so the
bus lives here and is exposed to the domain only via the EventPublisher port.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Callable, Sequence, Type

from tasks.domain.events import DomainEvent

logger = logging.getLogger("tasks.event_bus")

Handler = Callable[[DomainEvent], None]


class InMemoryEventBus:
    """Register handlers per event type and dispatch synchronously."""

    def __init__(self) -> None:
        self._handlers: dict[Type[DomainEvent], list[Handler]] = defaultdict(
            list
        )

    def subscribe(self, event_type: Type[DomainEvent], handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        handlers = self._handlers.get(type(event), [])
        for handler in handlers:
            try:
                handler(event)
            except Exception:  # noqa: BLE001 - isolate subscriber failures
                logger.exception(
                    "Event handler %r failed for event %s",
                    getattr(handler, "__qualname__", handler),
                    event.name,
                )

    def publish_all(self, events: Sequence[DomainEvent]) -> None:
        for event in events:
            self.publish(event)
