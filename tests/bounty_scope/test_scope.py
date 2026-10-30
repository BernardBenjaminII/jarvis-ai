import pytest

from core.bounty_scope import LiveScope, ScopeDenied


def make_scope():
    return LiveScope.reviewed(
        program="demo",
        include=["example.com", "*.example.com"],
        exclude=["private.example.com"],
        allowed_capabilities=["subfinder", "httpx"],
        reviewed_by="tester",
        source_material="synthetic reviewed fixture",
    )


def test_exact_and_wildcard_scope():
    s = make_scope()

    assert s.require("example.com", "subfinder") == "example.com"
    assert s.require("WWW.Example.Com.", "httpx") == "www.example.com"


def test_exclusion_wins():
    s = make_scope()

    with pytest.raises(ScopeDenied):
        s.require("private.example.com", "httpx")


def test_outside_scope_denied():
    s = make_scope()

    with pytest.raises(ScopeDenied):
        s.require("example.org", "httpx")


def test_capability_denied():
    s = make_scope()

    with pytest.raises(ScopeDenied):
        s.require("example.com", "nuclei")


def test_filter_derived_hosts():
    s = make_scope()

    result = s.filter_hosts([
        "a.example.com",
        "private.example.com",
        "outside.example.org",
    ])

    assert result["accepted"] == ["a.example.com"]

    assert set(result["rejected"]) == {
        "outside.example.org",
        "private.example.com",
    }


def test_logical_capability_and_provider_are_separate():
    s = LiveScope.reviewed(
        program="demo-r87b",
        include=["example.com"],
        logical_capabilities=[
            "subdomain_discovery",
            "http_probe",
        ],
        approved_providers=[
            "subfinder",
            "httpx",
        ],
        reviewed_by="tester",
        source_material="r8.7b synthetic fixture",
    )

    assert (
        s.require_capability("subdomain_discovery")
        == "subdomain_discovery"
    )

    assert (
        s.require_capability("http_probe")
        == "http_probe"
    )

    assert s.approved_providers == (
        "httpx",
        "subfinder",
    )

    assert (
        s.require("example.com", "httpx")
        == "example.com"
    )


def test_logical_capability_denied_independently():
    s = LiveScope.reviewed(
        program="demo-r87b",
        include=["example.com"],
        logical_capabilities=[
            "subdomain_discovery",
        ],
        approved_providers=[
            "subfinder",
        ],
        reviewed_by="tester",
        source_material="r8.7b synthetic fixture",
    )

    with pytest.raises(ScopeDenied):
        s.require_capability("http_probe")


def test_dns_resolution_capability_and_provider():
    s = LiveScope.reviewed(
        program="dns-r88a",
        include=[
            "example.com",
            "*.example.com",
        ],
        logical_capabilities=[
            "dns_resolution",
        ],
        approved_providers=[
            "dnsx",
        ],
        reviewed_by="tester",
        source_material="dns r8.8a fixture",
    )

    assert (
        s.require_capability(
            "dns_resolution"
        )
        == "dns_resolution"
    )

    assert s.approved_providers == (
        "dnsx",
    )

    assert (
        s.require(
            "a.example.com",
            "dnsx",
        )
        == "a.example.com"
    )
