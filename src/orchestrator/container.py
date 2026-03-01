"""Dependency Injection Container."""

from typing import Any, Type, TypeVar

T = TypeVar("T")

class DIContainer:
    """A lightweight dependency injection container."""

    def __init__(self) -> None:
        """Initialize the container."""
        # Using Type[Any] | str allows registering both by class type and by string name
        self._services: dict[Type[Any] | str, Any] = {}

    def register(self, interface: Type[T] | str, instance: T) -> None:
        """Register a service instance."""
        self._services[interface] = instance

    def resolve(self, interface: Type[T] | str) -> T:
        """Resolve a service by its interface or name."""
        if interface not in self._services:
            raise KeyError(f"Service '{interface}' is not registered in the DIContainer.")
        return self._services[interface]

    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
