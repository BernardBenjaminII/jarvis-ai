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
