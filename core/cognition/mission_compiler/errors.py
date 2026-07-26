class MissionCompilerError(Exception):
    """Base error for Genesis IV-A8."""


class InvalidMissionSpecificationError(MissionCompilerError):
    """Raised when mission input violates the compiler contract."""


class MissionDependencyCycleError(MissionCompilerError):
    """Raised when the compiled execution graph contains a cycle."""


class OrphanPlanNodeError(MissionCompilerError):
    """Raised when a task or activity has no valid parent."""


class DecisionNotApprovedError(MissionCompilerError):
    """Raised when an unapproved Executive Decision is supplied."""
