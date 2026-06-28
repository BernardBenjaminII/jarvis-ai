from __future__ import annotations

from core.src.runtime.tool_registry import registry


class Dispatcher:
    """
    Thin wrapper around the Tool Registry.

    It does NOT perform planning.
    It simply forwards tool execution requests.
    """

    def __init__(self):
        self.registry = registry()

    def dispatch(self, tool: str, action: str, **kwargs):
        return self.registry.execute(
            tool,
            action=action,
            **kwargs,
        )


dispatcher = Dispatcher()


def dispatch(tool: str, action: str, **kwargs):
    return dispatcher.dispatch(
        tool,
        action,
        **kwargs,
    )
