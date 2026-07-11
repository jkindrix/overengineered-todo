"""Django-backed Event Store.

Implements the `EventStore` port: durably appends domain events to the
append-only `DomainEventRecord` table. It is called *inside* the unit of work, so
event rows are written in the same transaction as the aggregate — if either write
fails, both roll back. This replaces the previous fire-and-forget audit handler,
whose swallowed failures could leave state and history inconsistent.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from tasks.domain.events import DomainEvent

from .audit_chain import compute_entry_hash, update_head
from .event_serialization import CURRENT_EVENT_VERSION
from .models import DomainEventRecord


class DjangoEventStore:
    """Persist domain events transactionally to the event log."""

    def append(self, events: Sequence[DomainEvent]) -> None:
        if not events:
            return
        # Continue the tamper-evident chain from the current last row. Runs inside
        # the unit-of-work transaction; appends are serialized (see ADR-0014).
        prev_hash = (
            DomainEventRecord.objects.order_by("-id")
            .values_list("entry_hash", flat=True)
            .first()
            or ""
        )
        records = []
        for event in events:
            payload = _json_safe(event.payload())
            entry_hash = compute_entry_hash(
                prev_hash,
                aggregate_id=event.aggregate_id,
                event_name=event.name,
                occurred_at=event.occurred_at,
                payload=payload,
            )
            records.append(
                DomainEventRecord(
                    aggregate_id=event.aggregate_id,
                    event_name=event.name,
                    occurred_at=event.occurred_at,
                    payload=payload,
                    prev_hash=prev_hash,
                    entry_hash=entry_hash,
                    version=CURRENT_EVENT_VERSION,
                )
            )
            prev_hash = entry_hash
        DomainEventRecord.objects.bulk_create(records)
        # Advance the tamper-evidence anchor (detects trailing truncation).
        update_head(DomainEventRecord.objects.count(), prev_hash)


def _json_safe(payload: dict) -> dict[str, Any]:
    """Coerce payload values into JSON-serializable primitives."""
    safe: dict[str, Any] = {}
    for key, value in payload.items():
        safe[key] = list(value) if isinstance(value, tuple) else value
    return safe
