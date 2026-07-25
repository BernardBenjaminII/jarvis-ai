class ExecutiveDecisionError(Exception):
    """Base error for executive decision operations."""

class InvalidDecisionInputError(ExecutiveDecisionError, ValueError):
    """Raised when decision inputs violate the contract."""

class InvalidDecisionRecordError(ExecutiveDecisionError, ValueError):
    """Raised when a decision record violates the contract."""

class DecisionNotFoundError(ExecutiveDecisionError, LookupError):
    """Raised when a decision record cannot be found."""

class DecisionRepositoryClosedError(ExecutiveDecisionError):
    """Raised when a closed repository is accessed."""
