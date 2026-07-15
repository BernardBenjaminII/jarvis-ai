"""
JARVIS acquisition providers.
"""

from knowledge_engine.acquisition.providers.base import (
    AcquisitionProvider,
)
from knowledge_engine.acquisition.providers.filesystem import (
    FilesystemAcquisitionProvider,
)

__all__ = [
    "AcquisitionProvider",
    "FilesystemAcquisitionProvider",
]
