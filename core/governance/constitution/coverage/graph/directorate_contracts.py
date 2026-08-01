from __future__ import annotations

from enum import Enum

DIRECTORATE_PROJECTION_SCHEMA_VERSION = "1.0.0"


class DirectorateNodeKind(str, Enum):
    DIRECTORATE = "directorate"
    RESPONSIBILITY = "responsibility"
    OWNERSHIP_DOMAIN = "ownership_domain"
    ORGANIZATIONAL_UNIT = "organizational_unit"


class DirectorateEdgeKind(str, Enum):
    OWNS = "owns"
    SUPERVISES = "supervises"
    RESPONSIBLE_FOR = "responsible_for"
    MAINTAINS = "maintains"
    OPERATES = "operates"
    CERTIFIES = "certifies"


CANONICAL_DIRECTORATES: tuple[tuple[str, str], ...] = (
    ("executive", "Executive Directorate"),
    ("governance", "Governance Directorate"),
    ("knowledge", "Knowledge Directorate"),
    ("reasoning", "Reasoning Directorate"),
    ("software_engineering", "Software Engineering Directorate"),
    ("planning", "Planning Directorate"),
    ("operations", "Operations Directorate"),
    ("intelligence_acquisition", "Intelligence Acquisition Directorate"),
)
