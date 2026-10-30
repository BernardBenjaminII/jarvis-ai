import pytest

from core.bounty_authorization import AuthorizationStore
from core.bounty_profiles.airtable import (
    AIRTABLE_PROFILE,
    create_airtable_authorization,
)


def test_airtable_profile_is_conservative():
    assert "staging.airtable.com" in AIRTABLE_PROFILE["include"]
    assert "*.staging.airtable.com" in AIRTABLE_PROFILE["include"]
    assert "mcp.staging.airtable.com" in AIRTABLE_PROFILE["include"]

    assert "airtable.com" in AIRTABLE_PROFILE["exclude"]
    assert "*.airtable.com" not in AIRTABLE_PROFILE["exclude"]

    assert "api-staging.airtable.com" not in AIRTABLE_PROFILE["include"]
    assert "*.staging-airtableblocks.com" not in AIRTABLE_PROFILE["include"]

    assert AIRTABLE_PROFILE["capabilities"] == ["subfinder", "httpx"]


def test_created_authorization_accepts_staging_and_rejects_production(tmp_path):
    store = AuthorizationStore(tmp_path / "auth.sqlite")

    auth_id = create_airtable_authorization(
        reviewer="human-reviewer",
        ttl=3600,
        store=store,
    )

    scope = store.live_scope(auth_id)

    assert scope.require(
        "staging.airtable.com",
        "subfinder",
    ) == "staging.airtable.com"

    assert scope.require(
        "api.staging.airtable.com",
        "httpx",
    ) == "api.staging.airtable.com"

    with pytest.raises(Exception):
        scope.require("airtable.com", "httpx")

    with pytest.raises(Exception):
        scope.require("www.airtable.com", "httpx")

    with pytest.raises(Exception):
        scope.require("blog.airtable.com", "httpx")


def test_special_assets_remain_held(tmp_path):
    store = AuthorizationStore(tmp_path / "auth.sqlite")

    auth_id = create_airtable_authorization(
        reviewer="human-reviewer",
        ttl=3600,
        store=store,
    )

    scope = store.live_scope(auth_id)

    with pytest.raises(Exception):
        scope.require("api-staging.airtable.com", "httpx")

    with pytest.raises(Exception):
        scope.require("foo.staging-airtableblocks.com", "httpx")
