"""Tamper-evident hash chain over the domain-event audit log.

Each `DomainEventRecord` stores `entry_hash = SHA256(prev_hash + canonical(row))`,
linking every event to the one before it. Altering or deleting any past row breaks
the chain from that point on, which `verify_chain` (and the `verify_audit_log`
management command) detect. This makes tampering *detectable*, not impossible.

See ADR-0014 for the rationale, ROI, and caveats (ordering/concurrency, and the
HMAC upgrade path for tamper-*resistance*).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .models import DomainEventRecord


def compute_entry_hash(
    prev_hash: str,
    *,
    aggregate_id: Any,
    event_name: str,
    occurred_at: datetime,
    payload: dict[str, Any],
) -> str:
    """Return the SHA-256 hex digest sealing this event to the previous one.

    The material is a canonical (key-sorted, whitespace-free) JSON encoding of the
    event's content, prefixed with the previous entry's hash.
    """
    material = json.dumps(
        {
            "aggregate_id": str(aggregate_id),
            "event_name": event_name,
            "occurred_at": occurred_at.isoformat(),
            "payload": payload,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256((prev_hash + material).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Outcome of verifying the audit-log hash chain."""

    ok: bool
    checked: int
    first_bad_id: int | None = None
    note: str = ""


def update_head(count: int, head_hash: str) -> None:
    """Record the expected chain head (row count + last hash). Called on append."""
    from .models import AuditChainHead

    AuditChainHead.objects.update_or_create(
        id=1, defaults={"count": count, "head_hash": head_hash}
    )


def verify_chain() -> VerificationResult:
    """Walk the audit log in order and confirm every link is intact.

    Detects edits and deletions that leave a subsequent record (the chain breaks),
    and — via the independently-stored head anchor — *trailing truncation*
    (deleting the final rows), which a bare chain cannot detect.
    """
    from .models import AuditChainHead

    prev_hash = ""
    checked = 0
    for record in DomainEventRecord.objects.order_by("id").iterator():
        expected = compute_entry_hash(
            prev_hash,
            aggregate_id=record.aggregate_id,
            event_name=record.event_name,
            occurred_at=record.occurred_at,
            payload=record.payload,
        )
        if record.prev_hash != prev_hash or record.entry_hash != expected:
            return VerificationResult(ok=False, checked=checked, first_bad_id=record.id)
        prev_hash = record.entry_hash
        checked += 1

    # Anchor check: the surviving chain may be internally valid yet truncated.
    head = AuditChainHead.objects.filter(id=1).first()
    if head is not None and (head.count != checked or head.head_hash != prev_hash):
        return VerificationResult(
            ok=False,
            checked=checked,
            note=(
                f"chain head mismatch: expected {head.count} events ending "
                f"{head.head_hash[:12]}…, found {checked} ending "
                f"{(prev_hash or '∅')[:12]}… — trailing rows were truncated."
            ),
        )
    return VerificationResult(ok=True, checked=checked)
