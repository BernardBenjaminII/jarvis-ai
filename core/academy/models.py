"""Static aggregate models for the dormant Executive Academy."""

from dataclasses import dataclass, field
from typing import Tuple

from .contracts import DepartmentContract, JurisdictionContract


@dataclass(frozen=True, slots=True)
class ExecutiveAcademyBaseline:
    version: str
    phase: str
    departments: Tuple[DepartmentContract, ...] = field(default_factory=tuple)
    jurisdictions: Tuple[JurisdictionContract, ...] = field(default_factory=tuple)
    runtime_enabled: bool = False
