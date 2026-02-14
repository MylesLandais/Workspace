"""
Abstract Base Class for dataset handlers.
"""
from abc import ABC, abstractmethod
from pathlib import Path

class BaseDatasetHandler(ABC):
    """
    An abstract base class for dataset handlers. Each handler is responsible
    for managing a specific dataset, including downloading, verifying, and
    providing access to it.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the dataset (e.g., 'vaporeon', 'gophers')."""
        pass

    @abstractmethod
    def get(self, destination: Path) -> Path:
        """
        Ensures the dataset is available locally, downloading it if necessary.

        Args:
            destination (Path): The root directory where the dataset should be stored.

        Returns:
            Path: The path to the main dataset file or directory.
        """
        pass

    @abstractmethod
    def info(self) -> dict:
        """
        Returns a dictionary of metadata about the dataset.
        """
        pass

    def _ensure_dir(self, path: Path):
        """Helper method to create a directory if it doesn't exist."""
        path.mkdir(parents=True, exist_ok=True)
