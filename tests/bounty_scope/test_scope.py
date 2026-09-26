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
