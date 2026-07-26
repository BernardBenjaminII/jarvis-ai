"""Registries for Integration metadata and projection providers."""

from __future__ import annotations

from typing import Any, Iterable

from .errors import (
    DuplicateCapabilityError,
    DuplicateProjectionProviderError,
    ProjectionProviderNotFoundError,
    UnknownCapabilityError,
)


class CapabilityRegistry:
    """Registry of executive capability definitions."""

    def __init__(self, capabilities: Iterable[Any] = ()) -> None:
        self._items: dict[str, Any] = {}
        for item in capabilities:
            self.register(item)

    def register(self, capability: Any) -> Any:
        capability_id = str(capability.capability_id).strip()
        if capability_id in self._items:
            raise DuplicateCapabilityError(capability_id)
        self._items[capability_id] = capability
        return capability

    def upsert(self, capability: Any) -> Any:
        capability_id = str(capability.capability_id).strip()
        self._items[capability_id] = capability
        return capability

    def get(self, capability_id: str) -> Any:
        try:
            return self._items[capability_id]
        except KeyError as exc:
            raise UnknownCapabilityError(capability_id) from exc

    def all(self) -> tuple[Any, ...]:
        return tuple(self._items[key] for key in sorted(self._items))

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._items))

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, capability_id: object) -> bool:
        return capability_id in self._items


class ProjectionRegistry:
    """Deterministic registry of Executive Projection providers."""

    def __init__(self, providers: Iterable[Any] = ()) -> None:
        self._providers: dict[str, Any] = {}
        for provider in providers:
            self.register(provider)

    @staticmethod
    def _projection_id(provider: Any) -> str:
        projection_id = str(
            getattr(provider, "projection_id", "")
        ).strip()
        if not projection_id:
            raise ValueError(
                "projection provider must define a non-empty projection_id"
            )
        if not callable(getattr(provider, "project", None)):
            raise TypeError(
                f"projection provider {projection_id!r} must define project()"
            )
        return projection_id

    def register(self, provider: Any) -> Any:
        projection_id = self._projection_id(provider)
        if projection_id in self._providers:
            raise DuplicateProjectionProviderError(projection_id)
        self._providers[projection_id] = provider
        return provider

    def upsert(self, provider: Any) -> Any:
        projection_id = self._projection_id(provider)
        self._providers[projection_id] = provider
        return provider

    def get(self, projection_id: str) -> Any:
        try:
            return self._providers[projection_id]
        except KeyError as exc:
            raise ProjectionProviderNotFoundError(projection_id) from exc

    def all(self) -> tuple[Any, ...]:
        return tuple(
            self._providers[key]
            for key in sorted(self._providers)
        )

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))

    def remove(self, projection_id: str) -> Any:
        try:
            return self._providers.pop(projection_id)
        except KeyError as exc:
            raise ProjectionProviderNotFoundError(projection_id) from exc

    def __len__(self) -> int:
        return len(self._providers)

    def __contains__(self, projection_id: object) -> bool:
        return projection_id in self._providers


__all__ = [
    "CapabilityRegistry",
    "ProjectionRegistry",
]
