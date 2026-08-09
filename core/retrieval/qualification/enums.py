from __future__ import annotations
from enum import Enum

class QualificationDecision(str, Enum):
    ACCEPTED = "accepted"
    REJECTED_LOW_RELEVANCE = "rejected_low_relevance"
    REJECTED_LOW_CONFIDENCE = "rejected_low_confidence"
    REJECTED_ENTITY_MISMATCH = "rejected_entity_mismatch"
    REJECTED_SUBJECT_MISMATCH = "rejected_subject_mismatch"
    REJECTED_EMPTY_RESULT = "rejected_empty_result"
