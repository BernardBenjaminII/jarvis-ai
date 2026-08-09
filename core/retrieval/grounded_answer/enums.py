from enum import Enum

class AnswerKnowledgeState(str, Enum):
    KNOWN = "known"
    PARTIAL = "partial"
    UNKNOWN = "unknown"
    CONFLICTED = "conflicted"

class ConflictSeverity(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
