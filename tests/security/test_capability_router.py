import pytest

from core.security.capability_router import (
    CapabilityRouteError,
    build_live_plan,
    live_providers_for,
    providers_for,
    resolve_live_provider,
)


def test_arsenal_provider_mapping():
    assert "subfinder" in providers_for(
        "subdomain_discovery"
    )

    assert "httpx" in providers_for(
        "http_probe"
    )

    assert "katana" in providers_for(
        "web_crawling"
    )


def test_r87a_live_provider_allowlist():
    assert live_providers_for(
        "subdomain_discovery"
    ) == ("subfinder",)

    assert live_providers_for(
        "http_probe"
    ) == ("httpx",)

    # Arsenal knows Katana, but R5 execution does not yet.
    assert live_providers_for(
        "web_crawling"
    ) == ()


def test_resolve_live_provider_respects_authorization():
    route = resolve_live_provider(
        "http_probe",
        allowed_providers=["subfinder", "httpx"],
    )

    assert route.capability == "http_probe"
    assert route.provider == "httpx"


def test_resolve_live_provider_fails_closed():
    with pytest.raises(CapabilityRouteError):
        resolve_live_provider(
            "http_probe",
            allowed_providers=["subfinder"],
        )


def test_build_live_plan():
    plan = build_live_plan(
        [
            "subdomain_discovery",
            "http_probe",
        ],
        allowed_providers=[
            "subfinder",
            "httpx",
        ],
    )

    assert [
        item.to_dict()
        for item in plan
    ] == [
        {
            "capability": "subdomain_discovery",
            "provider": "subfinder",
        },
        {
            "capability": "http_probe",
            "provider": "httpx",
        },
    ]


def test_dns_resolution_routes_to_dnsx():
    route = resolve_live_provider(
        "dns_resolution",
        allowed_providers=[
            "dnsx",
        ],
    )

    assert route.capability == "dns_resolution"
    assert route.provider == "dnsx"
