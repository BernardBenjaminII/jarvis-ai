"""Static Executive Academy enumerations for EAF-001."""

from enum import Enum


class AcademyStatus(str, Enum):
    PLANNED = "planned"
    DORMANT = "dormant"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    RETIRED = "retired"


class CompetencyState(str, Enum):
    UNKNOWN = "unknown"
    PLANNED = "planned"
    DEVELOPING = "developing"
    ASSESSED = "assessed"
    CERTIFIED = "certified"
    RESTRICTED = "restricted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class AuthorityTier(str, Enum):
    TIER_A = "tier_a"
    TIER_B = "tier_b"
    TIER_C = "tier_c"
    TIER_D = "tier_d"
    TIER_E = "tier_e"
