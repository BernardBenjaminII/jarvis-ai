class ExecutionOrchestratorError(Exception):
    """Base error for Genesis IV-A9."""


class InvalidExecutionPlanError(ExecutionOrchestratorError):
    """Raised when a Mission Plan projection is structurally invalid."""


class IllegalExecutionTransitionError(ExecutionOrchestratorError):
    """Raised when an activity attempts an invalid lifecycle transition."""


class ExecutorUnavailableError(ExecutionOrchestratorError):
    """Raised when no executor is registered for a required capability."""


class ExecutionApprovalRequiredError(ExecutionOrchestratorError):
    """Raised when an activity requires explicit human approval."""
