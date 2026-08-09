class GenesisRuntimeError(RuntimeError):
    """Base error for Genesis engineering-tool startup failures."""


class GenesisRepositoryNotFoundError(GenesisRuntimeError):
    """Raised when no canonical JARVIS repository can be located."""


class GenesisRepositoryValidationError(GenesisRuntimeError):
    """Raised when a candidate repository does not satisfy layout rules."""


class GenesisEnvironmentError(GenesisRuntimeError):
    """Raised when the active Python environment is unusable."""


class GenesisBootstrapError(GenesisRuntimeError):
    """Raised when canonical runtime initialization cannot complete."""
