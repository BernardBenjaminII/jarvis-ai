"""Immutable Executive Academy constitutional contracts.

EAF-001 exposes static contracts only. It does not authorize runtime services.
"""

from dataclasses import dataclass, field
from typing import Tuple

from .enums import AcademyStatus, AuthorityTier, CompetencyState


@dataclass(frozen=True, slots=True)
class DepartmentContract:
    department_id: str
    name: str
    status: AcademyStatus = AcademyStatus.PLANNED


@dataclass(frozen=True, slots=True)
class JurisdictionContract:
    jurisdiction_id: str
    name: str
    coverage_percent: float = 0.0
    parent_id: str | None = None


@dataclass(frozen=True, slots=True)
class AuthorityContract:
    authority_id: str
    name: str
    tier: AuthorityTier


@dataclass(frozen=True, slots=True)
class CompetencyContract:
    competency_id: str
    name: str
    state: CompetencyState = CompetencyState.UNKNOWN
    known_gaps: Tuple[str, ...] = field(default_factory=tuple)
