from __future__ import annotations

from enum import Enum

CONSTITUTIONAL_EXTRACTION_SCHEMA_VERSION = "1.0.0"
ENGINE_VERSION = "GENESIS-VII-C1"


class ClaimModality(str, Enum):
    MUST = "must"
    SHALL = "shall"
    MUST_NOT = "must_not"
    SHALL_NOT = "shall_not"
    SHOULD = "should"
    SHOULD_NOT = "should_not"
    MAY = "may"
    PRINCIPLE = "principle"
    DECLARATION = "declaration"


class ConstitutionalDomain(str, Enum):
    EXECUTIVE = "executive"
    KNOWLEDGE = "knowledge"
    REASONING = "reasoning"
    MEMORY = "memory"
    PLANNING = "planning"
    EXECUTION = "execution"
    EXPERIENCE = "experience"
    ENGINEERING = "engineering"
    GOVERNANCE = "governance"
    SAFETY = "safety"
    SECURITY = "security"
    EVIDENCE = "evidence"
    ORGANIZATION = "organization"
    INTERFACE = "interface"
    GENERAL = "general"


class ExtractionStatus(str, Enum):
    CANDIDATE = "candidate"
    REVIEW_REQUIRED = "review_required"
    RATIFIED_SOURCE = "ratified_source"


class DiagnosticSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
