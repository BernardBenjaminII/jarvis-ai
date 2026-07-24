class EngineeringError(Exception):
    pass

class EngineeringValidationError(EngineeringError):
    pass

class EngineeringGovernanceError(EngineeringError):
    pass

class EngineeringEvidenceError(EngineeringError):
    pass

__all__ = [
    "EngineeringError", "EngineeringEvidenceError",
    "EngineeringGovernanceError", "EngineeringValidationError",
]
