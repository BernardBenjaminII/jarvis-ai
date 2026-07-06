from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class AssimilationStage:
    name: str
    description: str
    runner: Callable[[], dict]
