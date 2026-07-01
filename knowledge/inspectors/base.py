from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class BaseInspector(ABC):
    """
    Base class for all document inspectors.
    """

    extensions: tuple[str, ...] = ()

    @abstractmethod
    def inspect(self, path: Path) -> dict:
        """
        Return metadata about a document.
        """
        raise NotImplementedError

    def extract_text(self, path: Path) -> str:
        """
        Placeholder for Milestone 3.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement text extraction."
        )
