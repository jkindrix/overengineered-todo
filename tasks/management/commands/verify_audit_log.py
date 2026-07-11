"""Management command: verify the tamper-evident audit-log hash chain.

    python manage.py verify_audit_log

Exits 0 if the chain is intact, 1 if tampering is detected (so it can gate CI or
a cron check). See ADR-0014.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from tasks.infrastructure.audit_chain import verify_chain


class Command(BaseCommand):
    help = "Verify the tamper-evident hash chain of the domain-event audit log."

    def handle(self, *args, **options) -> None:
        result = verify_chain()
        if result.ok:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Audit log intact: {result.checked} events, chain verified."
                )
            )
            return
        if result.first_bad_id is not None:
            raise CommandError(
                f"TAMPERING DETECTED: the hash chain breaks at event id "
                f"{result.first_bad_id} (after {result.checked} valid events)."
            )
        raise CommandError(f"TAMPERING DETECTED: {result.note}")
