"""Infrastructure layer.

Concrete adapters that fulfill the application's ports: Django ORM models,
repository implementations, and the dependency-injection container that wires
everything together. This is the only layer permitted to depend on Django.
"""
