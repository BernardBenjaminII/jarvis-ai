"""Genesis III-A4 cognitive workspace integration errors."""


class CognitiveWorkspaceIntegrationError(ValueError):
    """Base error for deterministic workspace integration failures."""


class IntegrationPersistenceError(CognitiveWorkspaceIntegrationError):
    """Raised when an integration result cannot be persisted safely."""
