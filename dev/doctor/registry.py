from .runtime import RuntimeCheck
from .environment import EnvironmentCheck
from .imports import ImportCheck


def discover():
    return [
        EnvironmentCheck(),
        RuntimeCheck(),
        ImportCheck(),
    ]
