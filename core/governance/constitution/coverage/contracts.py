from __future__ import annotations

from enum import Enum

COVERAGE_INTELLIGENCE_SCHEMA_VERSION = "1.0.0"

class CoverageClassification(str, Enum):
    EXERCISED = "exercised"
    UNDERUTILIZED = "underutilized"
    UNUSED = "unused"

class RepositoryCoverageStatus(str, Enum):
    GOVERNED = "governed"
    PARTIALLY_GOVERNED = "partially_governed"
    UNGOVERNED = "ungoverned"

DEFAULT_GOVERNED_DOMAINS = ("architecture","engineering","execution","experience","executive","governance","knowledge","memory","planning","reasoning","security")
DEFAULT_LOW_USAGE_THRESHOLD = 2
DEFAULT_PARTIAL_DOMAIN_COVERAGE_THRESHOLD = 0.50
DEFAULT_GOVERNED_DOMAIN_COVERAGE_THRESHOLD = 0.80
