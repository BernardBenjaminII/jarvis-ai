from __future__ import annotations

from enum import Enum


GRAPH_FOUNDATION_SCHEMA_VERSION = "1.0.0"


class ConstitutionalGraphNodeType(str, Enum):
    ARTICLE = "article"
    REPOSITORY_ARTIFACT = "repository_artifact"
    DOMAIN = "domain"


class ConstitutionalGraphEdgeType(str, Enum):
    GOVERNS = "governs"
    OBSERVED_IN_DOMAIN = "observed_in_domain"
    BELONGS_TO_DOMAIN = "belongs_to_domain"
