import time
import pytest

from core.bounty_authorization import AuthorizationStore, AuthorizationDenied


def test_authorization_round_trip(tmp_path):
    store = AuthorizationStore(tmp_path / "auth.sqlite")

    auth = store.create(
        program="demo",
        include=["example.com", "*.example.com"],
        exclude=["private.example.com"],
        capabilities=["subfinder", "httpx"],
        reviewer="tester",
        source_material="reviewed rules",
        ttl=3600,
    )

    scope = store.live_scope(auth)

    assert scope.program == "demo"
    assert scope.require("a.example.com", "httpx") == "a.example.com"


def test_revocation_blocks_use(tmp_path):
    store = AuthorizationStore(tmp_path / "auth.sqlite")

    auth = store.create(
        program="demo",
        include=["example.com"],
        reviewer="tester",
        source_material="reviewed rules",
        ttl=3600,
    )

    store.revoke(auth, "test")

    with pytest.raises(AuthorizationDenied):
        store.live_scope(auth)


def test_r87b_authorization_persists_capability_provider_split(
    tmp_path,
):
    store = AuthorizationStore(
        tmp_path / "auth.sqlite"
    )

    auth = store.create(
        program="r87b",
        include=["example.com"],
        logical_capabilities=[
            "subdomain_discovery",
            "http_probe",
        ],
        approved_providers=[
            "subfinder",
            "httpx",
        ],
        reviewer="tester",
        source_material="reviewed rules r87b",
        ttl=3600,
    )

    scope = store.live_scope(auth)

    assert scope.logical_capabilities == (
        "http_probe",
        "subdomain_discovery",
    )

    assert scope.approved_providers == (
        "httpx",
        "subfinder",
    )

    row = store.get(auth)

    import json

    payload = json.loads(
        row["scope_json"]
    )

    assert payload["logical_capabilities"] == [
        "http_probe",
        "subdomain_discovery",
    ]

    assert payload["approved_providers"] == [
        "httpx",
        "subfinder",
    ]


def test_r87b_loads_legacy_r5_authorization(tmp_path):
    store = AuthorizationStore(
        tmp_path / "auth.sqlite"
    )

    # Legacy create path intentionally uses only provider names.
    auth = store.create(
        program="legacy-r5",
        include=["example.com"],
        capabilities=[
            "subfinder",
            "httpx",
        ],
        reviewer="tester",
        source_material="legacy reviewed rules",
        ttl=3600,
    )

    scope = store.live_scope(auth)

    assert set(scope.logical_capabilities) == {
        "subdomain_discovery",
        "http_probe",
    }

    assert set(scope.approved_providers) == {
        "subfinder",
        "httpx",
    }
