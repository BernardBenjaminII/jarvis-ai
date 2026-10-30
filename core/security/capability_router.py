from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.security.arsenal import TOOLS


class CapabilityRouteError(ValueError):
    pass


@dataclass(frozen=True)
class CapabilityRoute:
    capability: str
    provider: str

    def to_dict(self) -> dict:
        return {
            "capability": self.capability,
            "provider": self.provider,
        }


# Provider preference is explicit and deterministic.
#
# R8.7A deliberately exposes only providers that the existing
# R5 live engine and authorization model can execute.
#
# Additional Arsenal providers remain discoverable but are not
# executable through this router until authorization and adapters
# are upgraded in a later revision.
LIVE_PROVIDER_PREFERENCE = {
    "subdomain_discovery": (
        "subfinder",
    ),
    "dns_resolution": (
        "dnsx",
    ),
    "http_probe": (
        "httpx",
    ),
}


def providers_for(capability: str) -> tuple[str, ...]:
    capability = str(capability).strip().lower()

    providers = [
        tool.id
        for tool in TOOLS
        if capability in tool.capabilities
    ]

    return tuple(providers)


def live_providers_for(capability: str) -> tuple[str, ...]:
    capability = str(capability).strip().lower()

    preferred = LIVE_PROVIDER_PREFERENCE.get(
        capability,
        (),
    )

    arsenal = set(providers_for(capability))

    return tuple(
        provider
        for provider in preferred
        if provider in arsenal
    )


def resolve_live_provider(
    capability: str,
    *,
    allowed_providers: Iterable[str] | None = None,
) -> CapabilityRoute:
    capability = str(capability).strip().lower()

    candidates = live_providers_for(capability)

    if allowed_providers is not None:
        allowed = {
            str(value).strip().lower()
            for value in allowed_providers
        }

        candidates = tuple(
            provider
            for provider in candidates
            if provider in allowed
        )

    if not candidates:
        raise CapabilityRouteError(
            f"No authorized live provider for capability: "
            f"{capability}"
        )

    return CapabilityRoute(
        capability=capability,
        provider=candidates[0],
    )


def build_live_plan(
    capabilities: Iterable[str],
    *,
    allowed_providers: Iterable[str],
) -> tuple[CapabilityRoute, ...]:
    routes = []

    for capability in capabilities:
        routes.append(
            resolve_live_provider(
                capability,
                allowed_providers=allowed_providers,
            )
        )

    return tuple(routes)
