from enum import Enum

class DecisionDisposition(str, Enum):
    RECOMMENDED = "recommended"
    DEFERRED = "deferred"
    REJECTED = "rejected"
    ESCALATION_REQUIRED = "escalation_required"

class DecisionStatus(str, Enum):
    PROVISIONAL = "provisional"
    COMPLETE = "complete"
    ARCHIVED = "archived"

class DecisionRepositoryDisposition(str, Enum):
    CREATED = "created"
    DUPLICATE = "duplicate"
