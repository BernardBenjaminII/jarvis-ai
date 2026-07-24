from __future__ import annotations
from core.integration.errors import DuplicateProjectionProviderError, ProjectionProviderNotFoundError
from core.integration.provider import ProjectionProvider

class ProjectionRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ProjectionProvider] = {}
    def register(self, provider: ProjectionProvider) -> None:
        projection_id = provider.projection_id.strip()
        if not projection_id:
            raise ValueError("Projection provider identifier cannot be empty.")
        if projection_id in self._providers:
            raise DuplicateProjectionProviderError(f"Projection provider already registered: {projection_id}")
        self._providers[projection_id] = provider
    def get(self, projection_id: str) -> ProjectionProvider:
        try:
            return self._providers[projection_id]
        except KeyError as exc:
            raise ProjectionProviderNotFoundError(projection_id) from exc
    def all(self) -> list[ProjectionProvider]:
        return [self._providers[key] for key in sorted(self._providers)]
    def identifiers(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))
    def __contains__(self, projection_id: object) -> bool:
        return projection_id in self._providers
    def __len__(self) -> int:
        return len(self._providers)
