class ExecutiveIntegrationError(RuntimeError):
    """Base integration failure."""
class DuplicateProjectionProviderError(ExecutiveIntegrationError):
    """Projection identifier was registered more than once."""
class ProjectionProviderNotFoundError(ExecutiveIntegrationError, KeyError):
    """Requested projection provider is absent."""
