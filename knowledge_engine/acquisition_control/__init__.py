"""
JARVIS acquisition-control public API.

Phase VII-B1 intentionally lives outside the frozen
``knowledge_engine.acquisition`` package.
"""

from .contracts import (
    AdmissionDecision,
    AdmissionPolicy,
    AdmissionReason,
    AdmissionStatus,
    NormalizedSource,
    SourceKind,
    SourceProposal,
    SourceTrustTier,
)
from .normalization import (
    SourceNormalizationError,
    build_source_fingerprint,
    is_within_root,
    normalize_source,
)
from .service import SourceAdmissionService

__all__ = [
    "AdmissionDecision",
    "AdmissionPolicy",
    "AdmissionReason",
    "AdmissionStatus",
    "NormalizedSource",
    "SourceAdmissionService",
    "SourceKind",
    "SourceNormalizationError",
    "SourceProposal",
    "SourceTrustTier",
    "build_source_fingerprint",
    "is_within_root",
    "normalize_source",
]
