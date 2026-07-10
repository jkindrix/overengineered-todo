"""Django-backed Unit of Work.

Implements the `UnitOfWork` port using Django's `transaction.atomic`. Everything
written inside `atomic()` — the aggregate row and its event rows — commits as one
transaction, or rolls back together on any error. This is what makes state and
audit history consistent (closes the divergence gap in ADR-0006 / ADR-0013).
"""

from __future__ import annotations

from contextlib import AbstractContextManager

from django.db import transaction


class DjangoUnitOfWork:
    """A transactional boundary backed by the default database connection."""

    def atomic(self) -> AbstractContextManager[None]:
        return transaction.atomic()
