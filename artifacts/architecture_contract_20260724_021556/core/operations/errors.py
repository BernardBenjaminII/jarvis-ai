"""Errors raised by the JARVIS Operations interface."""


class OperationsError(RuntimeError):
    """Base class for Operations failures."""


class OperationsProviderError(OperationsError):
    """A backing provider could not produce an operational view."""


class InvalidOperationsEventError(OperationsError):
    """An event violated the Operations event contract."""
