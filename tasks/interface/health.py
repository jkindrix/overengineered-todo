"""Liveness/readiness health endpoint.

Reports process health plus a quick database round-trip and the active feature
flags. Returns 200 when healthy and 503 when a dependency check fails.
"""

from __future__ import annotations

from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def health_view(request):
    checks: dict[str, str] = {}
    healthy = True

    # Database connectivity check.
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001 - report, don't crash the probe
        checks["database"] = f"error: {exc}"
        healthy = False

    body = {
        "status": "ok" if healthy else "degraded",
        "checks": checks,
        "feature_flags": getattr(settings, "FEATURE_FLAGS", {}),
    }
    return JsonResponse(body, status=200 if healthy else 503)
