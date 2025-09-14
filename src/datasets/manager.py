"""
Dataset Manager
Discovers, loads, and manages all available dataset handlers.
"""
import importlib
import inspect
from pathlib import Path
from typing import Dict, Type, Optional

from src.datasets.base_handler import BaseDatasetHandler

class DatasetManager:
    """
    A manager that automatically discovers and provides access to dataset handlers.
    """

    def __init__(self, handlers_dir: Path = Path(__file__).parent / "handlers"):
        self._handlers: Dict[str, Type[BaseDatasetHandler]] = {}
        self._discover_handlers(handlers_dir)

    def _discover_handlers(self, handlers_dir: Path):
        """Dynamically imports and registers all dataset handlers."""
        if not handlers_dir.exists():
            handlers_dir.mkdir()
            # Create an __init__.py file to make it a package
            (handlers_dir / "__init__.py").touch()
            return

        for file_path in handlers_dir.glob("*_handler.py"):
            module_name = f"src.datasets.handlers.{file_path.stem}"
            try:
                module = importlib.import_module(module_name)
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseDatasetHandler) and obj is not BaseDatasetHandler:
                        handler_instance = obj()
                        if handler_instance.name:
                            self._handlers[handler_instance.name] = handler_instance
            except ImportError as e:
                print(f"Warning: Could not import handler from {file_path.name}: {e}")

    def list_datasets(self) -> list[str]:
        """Returns a list of available dataset names."""
        return list(self._handlers.keys())

    def get_handler(self, name: str) -> Optional[BaseDatasetHandler]:
        """
        Retrieves a dataset handler instance by name.

        Args:
            name (str): The name of the dataset.

        Returns:
            Optional[BaseDatasetHandler]: The handler instance, or None if not found.
        """
        return self._handlers.get(name)

if __name__ == "__main__":
    # Example usage
    manager = DatasetManager()
    print("Available datasets:", manager.list_datasets())

    vaporeon_handler = manager.get_handler("vaporeon")
    if vaporeon_handler:
        print("\nVaporeon Dataset Info:")
        print(vaporeon_handler.info())
        # The following line would download the dataset if it's not present
        # vaporeon_handler.get(Path("./evaluation_datasets"))
