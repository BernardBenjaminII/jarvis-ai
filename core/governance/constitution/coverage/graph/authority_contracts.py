from __future__ import annotations

from enum import Enum


AUTHORITY_GRAPH_SCHEMA_VERSION = "1.0.0"


class AuthorityNodeKind(str, Enum):
    CONSTITUTIONAL_ARTICLE = "constitutional_article"
    AUTHORITY_CLASS = "authority_class"
    GOVERNED_ARTIFACT = "governed_artifact"
    GOVERNANCE_DOMAIN = "governance_domain"


class AuthorityEdgeKind(str, Enum):
    CLASSIFIED_AS = "classified_as"
    AUTHORIZES = "authorizes"
    EXERCISED_IN = "exercised_in"
    SUPPORTS_AUTHORITY_CLASS = "supports_authority_class"


class AuthorityClass(str, Enum):
    ACTIVE = "active"
    REVIEW = "review"
    COLD = "cold"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
