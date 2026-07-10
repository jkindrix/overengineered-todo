"""Translation of domain exceptions into DRF/HTTP responses.

The domain raises transport-agnostic errors; this handler maps them onto the
appropriate HTTP status codes so the API speaks correct HTTP without the domain
ever importing `rest_framework`.
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from tasks.domain.exceptions import (
    DomainError,
    IllegalStateTransitionError,
    TaskNotFoundError,
    TaskValidationError,
)

# Map each domain error type to an HTTP status code.
_STATUS_MAP = {
    TaskNotFoundError: status.HTTP_404_NOT_FOUND,
    IllegalStateTransitionError: status.HTTP_409_CONFLICT,
    TaskValidationError: status.HTTP_400_BAD_REQUEST,
    DomainError: status.HTTP_400_BAD_REQUEST,
}


def _status_for(exc: DomainError) -> int:
    for error_type, code in _STATUS_MAP.items():
        if isinstance(exc, error_type):
            return code
    return status.HTTP_400_BAD_REQUEST


def domain_exception_handler(exc, context):
    """DRF exception handler that understands the task domain's errors."""
    if isinstance(exc, DomainError):
        return Response(
            {
                "error": type(exc).__name__,
                "detail": str(exc),
            },
            status=_status_for(exc),
        )
    # Fall back to DRF's default handling for everything else.
    return drf_exception_handler(exc, context)
