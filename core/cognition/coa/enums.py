from __future__ import annotations
from enum import Enum

class CourseOfActionKind(str, Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    CONTINGENCY = "contingency"
    HOLD = "hold"

class CourseOfActionStatus(str, Enum):
    CANDIDATE = "candidate"
    INADMISSIBLE = "inadmissible"

class GenerationDisposition(str, Enum):
    GENERATED = "generated"
    DUPLICATE = "duplicate"
    DEFERRED = "deferred"

__all__ = ["CourseOfActionKind", "CourseOfActionStatus", "GenerationDisposition"]
