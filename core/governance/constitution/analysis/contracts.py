from __future__ import annotations

from enum import Enum


ANALYSIS_SCHEMA_VERSION = "1.0.0"


class RelationshipType(str, Enum):
    DUPLICATES = "duplicates"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    REFINES = "refines"
    IMPLEMENTS = "implements"
    SUPERSEDES = "supersedes"
    REFERENCES = "references"
    DEPENDS_ON = "depends_on"
    DERIVED_FROM = "derived_from"
    EXCEPTION_TO = "exception_to"


class AuthorityLevel(str, Enum):
    CONSTITUTION = "constitution"
    ENGINEERING_CONSTITUTION = "engineering_constitution"
    POLICY = "policy"
    ADR = "adr"
    ARCHITECTURE = "architecture"
    WHITEPAPER = "whitepaper"
    OTHER = "other"


AUTHORITY_RANK = {
    AuthorityLevel.CONSTITUTION: 700,
    AuthorityLevel.ENGINEERING_CONSTITUTION: 650,
    AuthorityLevel.POLICY: 600,
    AuthorityLevel.ADR: 500,
    AuthorityLevel.ARCHITECTURE: 400,
    AuthorityLevel.WHITEPAPER: 300,
    AuthorityLevel.OTHER: 100,
}
