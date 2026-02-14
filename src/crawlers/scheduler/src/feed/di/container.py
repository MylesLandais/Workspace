"""Dependency injection container."""

from typing import Dict, Any, Callable, TypeVar, Optional

T = TypeVar('T')


class DIContainer:
    """Simple dependency injection container."""
    
    def __init__(self):
        self._factories: Dict[str, tuple[Callable, bool]] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register(
        self,
        name: str,
        factory: Callable,
        singleton: bool = True
    ) -> None:
        """
        Register a service factory.
        
        Args:
            name: Service name
            factory: Factory function
            singleton: Whether to cache as singleton
        """
        self._factories[name] = (factory, singleton)
    
    def register_instance(self, name: str, instance: Any) -> None:
        """
        Register an existing instance.
        
        Args:
            name: Service name
            instance: Instance to register
        """
        self._singletons[name] = instance
    
    def get(self, name: str) -> T:
        """
        Get service instance.
        
        Args:
            name: Service name
            
        Returns:
            Service instance
        """
        if name in self._singletons:
            return self._singletons[name]
        
        if name not in self._factories:
            raise ValueError(f"Service '{name}' not registered")
        
        factory, is_singleton = self._factories[name]
        instance = factory()
        
        if is_singleton:
            self._singletons[name] = instance
        
        return instance
    
    def has(self, name: str) -> bool:
        """Check if service is registered."""
        return name in self._factories or name in self._singletons
    
    def clear(self) -> None:
        """Clear all singletons (useful for testing)."""
        self._singletons.clear()
