"""Executive Academy constitutional contracts.

EAF-001 is intentionally dormant and exposes no operational service.
"""

from .contracts import (
    AuthorityContract,
    CompetencyContract,
    DepartmentContract,
    JurisdictionContract,
)
from .enums import AcademyStatus, AuthorityTier, CompetencyState
from .errors import (
    AcademyContractValidationError,
    AcademyDormantError,
    ExecutiveAcademyError,
)
from .models import ExecutiveAcademyBaseline
from .registry import StaticRegistry

__all__ = [
    "AcademyContractValidationError",
    "AcademyDormantError",
    "AcademyStatus",
    "AuthorityContract",
    "AuthorityTier",
    "CompetencyContract",
    "CompetencyState",
    "DepartmentContract",
    "ExecutiveAcademyBaseline",
    "ExecutiveAcademyError",
    "JurisdictionContract",
    "StaticRegistry",
]
