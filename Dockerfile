# syntax=docker/dockerfile:1
# Multi-stage build for a self-contained local/demo image.
# NOTE: this runs Django's development server (the project is a local demo on
# SQLite). For a real deployment you'd add gunicorn + whitenoise/static serving
# and set DJANGO_DEBUG=False with a real SECRET_KEY (the app is already hardened
# for that — see config/settings.py).

FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim AS final
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SECRET_KEY=docker-local-dev-key
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
# Run as a non-root user.
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000"]
