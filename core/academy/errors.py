"""Executive Academy contract errors."""


class ExecutiveAcademyError(Exception):
    """Base error for Executive Academy contracts."""


class AcademyDormantError(ExecutiveAcademyError):
    """Raised when operational behavior is requested before activation."""


class AcademyContractValidationError(ExecutiveAcademyError):
    """Raised when a static Academy contract is invalid."""
