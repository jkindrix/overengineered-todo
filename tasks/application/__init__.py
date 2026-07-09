"""Application layer.

Orchestrates domain behavior into use cases. Depends on the domain and on
abstract ports (interfaces); it must not depend on concrete infrastructure.
Wiring of concrete adapters happens in the infrastructure container.
"""
