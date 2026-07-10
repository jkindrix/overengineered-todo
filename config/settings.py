"""
Django settings for the Overly-Engineered TODO application.

Configuration is environment-driven (twelve-factor style) with safe local
defaults so the project runs out of the box with SQLite and no external
services. See `.env.example` for every value the application reads.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Small helpers for reading typed values out of the environment
# ---------------------------------------------------------------------------
def env_bool(name: str, default: bool = False) -> bool:
    """Interpret common truthy strings from the environment as a boolean."""
    return os.environ.get(name, str(default)).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def env_list(name: str, default: str = "") -> list[str]:
    """Parse a comma-separated environment variable into a clean list."""
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# ---------------------------------------------------------------------------
# Core security / debug
# ---------------------------------------------------------------------------
# The insecure fallback exists solely so the app runs out of the box locally.
# A boot guard (below) refuses to start with it once DEBUG is off.
# Intentionally-insecure local dev default; the boot guard below refuses to
# start with this value when DEBUG is off (hence the bandit suppression).
INSECURE_DEFAULT_SECRET_KEY = "dev-insecure-change-me-0123456789abcdef"  # nosec B105

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", INSECURE_DEFAULT_SECRET_KEY)
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")


# ---------------------------------------------------------------------------
# Feature flags (read once here, consumed across the application)
# ---------------------------------------------------------------------------
FEATURE_FLAGS = {
    "EVENT_SOURCING": env_bool("FEATURE_EVENT_SOURCING", True),
    "EVENT_LOGGING": env_bool("FEATURE_EVENT_LOGGING", True),
    "STRICT_STATE_MACHINE": env_bool("FEATURE_STRICT_STATE_MACHINE", True),
}


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "django_filters",
    # Local
    "tasks.apps.TasksConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ---------------------------------------------------------------------------
# Database — SQLite for zero-dependency local runs
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "EXCEPTION_HANDLER": "tasks.interface.exceptions.domain_exception_handler",
}


# ---------------------------------------------------------------------------
# Logging — structured-ish console logging keyed off APP_LOG_LEVEL
# ---------------------------------------------------------------------------
APP_LOG_LEVEL = os.environ.get("APP_LOG_LEVEL", "INFO").upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
        },
    },
    "loggers": {
        "tasks": {
            "handlers": ["console"],
            "level": APP_LOG_LEVEL,
            "propagate": False,
        },
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
}


# ---------------------------------------------------------------------------
# Production hardening
#
# These defaults keep local development friction-free (plain HTTP, permissive)
# while enforcing a secure posture whenever DEBUG is off. Turning DEBUG off is
# the switch, but a real production deployment additionally requires:
#   * DJANGO_SECRET_KEY set to a strong, unique value (enforced by the boot
#     guard below — the app refuses to start otherwise), and
#   * DJANGO_ALLOWED_HOSTS set to the real hostname(s).
# With those in place, `manage.py check --deploy` passes clean.
# ---------------------------------------------------------------------------
# Sensible security headers that are safe in every environment.
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

if not DEBUG:
    # Boot guard: refuse to start in a non-debug environment while still using
    # the insecure development SECRET_KEY. Fail fast rather than run insecure.
    if SECRET_KEY == INSECURE_DEFAULT_SECRET_KEY:
        from django.core.exceptions import ImproperlyConfigured

        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY is unset or still the insecure development "
            "default while DEBUG is False. Set a strong, unique secret key "
            "before running with DEBUG off."
        )

    # HTTPS / transport security.
    SECURE_SSL_REDIRECT = True
    # Trust the X-Forwarded-Proto header set by a TLS-terminating proxy.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    # HSTS is an operational commitment: once a browser sees it, it will refuse
    # plain-HTTP for the whole max-age, and `preload`/`includeSubDomains` are
    # effectively one-way. They are therefore env-tunable so an operator can dial
    # the window down (or to 0) until the entire domain is confidently HTTPS-only.
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", 31_536_000))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = env_bool("DJANGO_HSTS_PRELOAD", True)

    # Secure-only cookies.
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
