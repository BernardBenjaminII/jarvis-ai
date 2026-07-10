"""Director registry used by the Mission Engine."""

from __future__ import annotations

from collections.abc import Iterable

from core.executive.contracts import DirectorHandler, DirectorNotRegisteredError


class DirectorRegistry:
    """Maps stable director names to executable handlers."""

    def __init__(self) -> None:
        self._handlers: dict[str, DirectorHandler] = {}

    def register(
        self,
        name: str,
        handler: DirectorHandler,
        *,
        replace: bool = False,
    ) -> None:
        normalized = self._normalize(name)
        if normalized in self._handlers and not replace:
            raise ValueError(f"Director already registered: {normalized}")
        self._handlers[normalized] = handler

    def unregister(self, name: str) -> None:
        self._handlers.pop(self._normalize(name), None)

    def resolve(self, name: str) -> DirectorHandler:
        normalized = self._normalize(name)
        try:
            return self._handlers[normalized]
        except KeyError as exc:
            raise DirectorNotRegisteredError(
                f"No director registered for '{normalized}'"
            ) from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))

    def contains(self, name: str) -> bool:
        return self._normalize(name) in self._handlers

    def require(self, names: Iterable[str]) -> None:
        missing = [name for name in names if not self.contains(name)]
        if missing:
            raise DirectorNotRegisteredError(
                "Missing required directors: " + ", ".join(sorted(missing))
            )

    @staticmethod
    def _normalize(name: str) -> str:
        normalized = name.strip().lower().replace(" ", "_")
        if not normalized:
            raise ValueError("Director name cannot be empty")
        return normalized
