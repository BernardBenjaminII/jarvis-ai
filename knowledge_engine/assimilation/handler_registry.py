from __future__ import annotations

from typing import Dict

from knowledge_engine.assimilation.handlers.base import AssimilationHandler


class HandlerRegistry:
    """
    Registry of assimilation handlers.

    Each object_type maps to exactly one handler.
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, AssimilationHandler] = {}

    def register(
        self,
        handler: AssimilationHandler,
    ) -> None:

        object_type = handler.object_type

        if object_type in self._handlers:
            raise ValueError(
                f"Handler already registered for '{object_type}'."
            )

        self._handlers[object_type] = handler

    def get(
        self,
        object_type: str,
    ) -> AssimilationHandler:

        try:
            return self._handlers[object_type]
        except KeyError as exc:
            raise LookupError(
                f"No handler registered for '{object_type}'."
            ) from exc

    def supports(
        self,
        object_type: str,
    ) -> bool:

        return object_type in self._handlers

    def object_types(self) -> list[str]:

        return sorted(self._handlers.keys())
