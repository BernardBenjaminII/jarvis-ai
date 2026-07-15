"""
Registry for JARVIS acquisition providers.
"""

from __future__ import annotations

from knowledge_engine.acquisition.providers.base import (
    AcquisitionProvider,
)


class AcquisitionProviderRegistry:
    """Map stable provider IDs to concrete provider instances."""

    def __init__(self) -> None:
        self._providers: dict[
            str,
            AcquisitionProvider,
        ] = {}

    def register(
        self,
        provider: AcquisitionProvider,
    ) -> None:
        provider_id = provider.provider_id.strip()

        if not provider_id:
            raise ValueError(
                "provider_id must not be empty"
            )

        if provider_id in self._providers:
            raise ValueError(
                f"Provider already registered: {provider_id}"
            )

        self._providers[provider_id] = provider

    def get(
        self,
        provider_id: str,
    ) -> AcquisitionProvider:
        normalized = provider_id.strip()

        try:
            return self._providers[normalized]
        except KeyError as exc:
            raise LookupError(
                f"No acquisition provider registered: {normalized}"
            ) from exc

    def supports(
        self,
        provider_id: str,
    ) -> bool:
        return provider_id.strip() in self._providers

    def provider_ids(self) -> tuple[str, ...]:
        return tuple(
            sorted(self._providers)
        )
