"""Canonical vocabularies for Genesis II-A4 Evidence contracts."""

from __future__ import annotations

from enum import Enum


class StableStringEnum(str, Enum):
    """String-valued enum with stable serialization behavior."""

    def __str__(self) -> str:
        return self.value


class EvidenceSourceType(StableStringEnum):
    """Canonical categories describing where Evidence originated."""

    USER = "user"
    DOCUMENT = "document"
    DATABASE = "database"
    MEMORY = "memory"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    SENSOR = "sensor"
    TOOL = "tool"
    NETWORK_SERVICE = "network_service"
    ANALYST = "analyst"
    MODEL = "model"
    DERIVED = "derived"
    UNKNOWN = "unknown"


class EvidenceModality(StableStringEnum):
    """Epistemic modality of Evidence-bearing content."""

    OBSERVATIONAL = "observational"
    TESTIMONIAL = "testimonial"
    DOCUMENTARY = "documentary"
    INFERENTIAL = "inferential"
    CAUSAL = "causal"
    INTERVENTIONAL = "interventional"
    COUNTERFACTUAL = "counterfactual"
    PREDICTIVE = "predictive"
    NORMATIVE = "normative"
    PROCEDURAL = "procedural"


class EvidenceStatus(StableStringEnum):
    """Non-destructive standing of a canonical Evidence record."""

    ACTIVE = "active"
    QUALIFIED = "qualified"
    DISPUTED = "disputed"
    SUPERSEDED = "superseded"
    RETRACTED = "retracted"
    INVALIDATED = "invalidated"


class EvidenceRelationshipType(StableStringEnum):
    """Typed, directional relationships between Evidence records."""

    DERIVED_FROM = "derived_from"
    CORROBORATES = "corroborates"
    CONTRADICTS = "contradicts"
    DUPLICATES = "duplicates"
    SUPERSEDES = "supersedes"
    RETRACTS = "retracts"
    CORRECTS = "corrects"
    QUALIFIES = "qualifies"
    INVALIDATES = "invalidates"
    DEPENDS_ON = "depends_on"
    EXPLAINS = "explains"
    OBSERVED_DURING = "observed_during"
    SAME_ORIGIN_AS = "same_origin_as"


class UncertaintyKind(StableStringEnum):
    """Supported uncertainty representation families."""

    UNKNOWN = "unknown"
    QUALITATIVE = "qualitative"
    PROBABILITY = "probability"
    INTERVAL = "interval"
    LIKELIHOOD = "likelihood"
    BELIEF_FUNCTION = "belief_function"


class AssessmentMethod(StableStringEnum):
    """Method family used to produce an Evidence assessment."""

    HUMAN_REVIEW = "human_review"
    RULE_BASED = "rule_based"
    STATISTICAL = "statistical"
    PROBABILISTIC = "probabilistic"
    ARGUMENTATIVE = "argumentative"
    CAUSAL = "causal"
    MODEL_ASSISTED = "model_assisted"
    UNSPECIFIED = "unspecified"


class ClassificationLevel(StableStringEnum):
    """Sensitivity classification associated with Evidence content."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    COMPARTMENTED = "compartmented"
    PERSONALLY_SENSITIVE = "personally_sensitive"
    LEGALLY_PROTECTED = "legally_protected"
    OPERATIONALLY_SENSITIVE = "operationally_sensitive"
