"""Interface layer.

Adapts external transports (HTTP/REST, server-rendered web, health checks) to
the application layer. Depends on the application service via the container and
on presenters to render domain aggregates; it never touches the ORM directly.
"""
