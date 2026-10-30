import pytest

from core.bounty_programs import (
    ProgramScopeError,
    ProgramSnapshot,
    ProgramStore,
    normalize_asset,
    normalize_assets,
)


def test_normalizes_exact_dns():
    asset = normalize_asset(
        "API.Example.COM.",
        eligible=True,
    )

    assert asset.normalized == (
        "api.example.com"
    )

    assert asset.asset_type == "dns"


def test_normalizes_wildcard_dns():
    asset = normalize_asset(
        "*.Example.COM",
        eligible=True,
    )

    assert asset.normalized == (
        "*.example.com"
    )

    assert (
        asset.asset_type
        == "wildcard_dns"
    )


def test_rejects_url_as_dns_asset():
    with pytest.raises(
        ProgramScopeError
    ):
        normalize_asset(
            "https://example.com/path",
            eligible=True,
        ).normalized


def test_authorization_scope():
    assets = normalize_assets(
        in_scope=[
            "example.com",
            "*.example.com",
        ],
        out_of_scope=[
            "private.example.com",
        ],
    )

    snapshot = (
        ProgramSnapshot.reviewed_input(
            source="hackerone",
            handle="demo",
            name="Demo Program",
            source_url=(
                "https://example.invalid/demo"
            ),
            assets=assets,
            rules_text="Synthetic rules",
            source_material=(
                "Synthetic reviewed source"
            ),
        )
    )

    assert snapshot.authorization_scope() == {
        "include": [
            "*.example.com",
            "example.com",
        ],
        "exclude": [
            "private.example.com",
        ],
    }


def test_store_round_trip(tmp_path):
    store = ProgramStore(
        tmp_path / "programs.sqlite"
    )

    assets = normalize_assets(
        in_scope=[
            "api.example.com",
        ]
    )

    snapshot = (
        ProgramSnapshot.reviewed_input(
            source="manual",
            handle="demo",
            name="Demo",
            source_url="",
            assets=assets,
            source_material=(
                "Synthetic fixture"
            ),
        )
    )

    program_id = store.save(
        snapshot
    )

    loaded = store.get(
        program_id
    )

    assert loaded["name"] == "Demo"

    assert (
        loaded["snapshot"]
        ["authorization_scope"]
        ["include"]
        == ["api.example.com"]
    )


def test_hackerone_catalog_draft_is_non_executable(
    tmp_path,
):
    import json
    import time

    from core.bounty_catalog.store import Catalog
    from core.bounty_programs import (
        ProgramStore,
        hackerone_catalog_draft,
    )

    catalog = Catalog(
        tmp_path / "catalog.sqlite"
    )

    raw = json.dumps(
        {
            "data": [
                {
                    "type": "program",
                    "attributes": {
                        "handle": "draft-demo",
                        "name": "Draft Demo",
                        "offers_bounties": True,
                        "submission_state": "open",
                        "policy": (
                            "Synthetic policy requiring "
                            "scope review."
                        ),
                    },
                }
            ],
            "links": {},
        }
    ).encode()

    catalog.save(
        "hackerone-api",
        time.time(),
        [(1, raw, time.time())],
        "complete",
    )

    draft = hackerone_catalog_draft(
        catalog,
        "draft-demo",
    )

    evidence = draft.evidence()

    assert (
        evidence["testing_authorized"]
        is False
    )

    assert (
        evidence["execution_enabled"]
        is False
    )

    assert (
        evidence["structured_scope_reviewed"]
        is False
    )

    assert (
        evidence["authorization_scope"]
        is None
    )

    assert (
        "Synthetic policy"
        in evidence["policy_text"]
    )

    store = ProgramStore(
        tmp_path / "programs.sqlite"
    )

    draft_id = store.save_draft(
        draft
    )

    loaded = store.get_draft(
        draft_id
    )

    assert (
        loaded["draft"]
        ["handle"]
        == "draft-demo"
    )

    assert (
        loaded["draft"]
        ["execution_enabled"]
        is False
    )


def _r90c_draft(tmp_path):
    import json
    import time

    from core.bounty_catalog.store import Catalog
    from core.bounty_programs import (
        ProgramStore,
        hackerone_catalog_draft,
    )

    catalog = Catalog(
        tmp_path / "catalog-r90c.sqlite"
    )

    raw = json.dumps(
        {
            "data": [
                {
                    "type": "program",
                    "attributes": {
                        "handle":
                            "scope-demo",
                        "name":
                            "Scope Demo",
                        "offers_bounties":
                            True,
                        "submission_state":
                            "open",
                        "policy":
                            "Only test staging.example.com",
                    },
                }
            ],
            "links": {},
        }
    ).encode()

    catalog.save(
        "hackerone-api",
        time.time(),
        [(1, raw, time.time())],
        "complete",
    )

    draft = hackerone_catalog_draft(
        catalog,
        "scope-demo",
    )

    store = ProgramStore(
        tmp_path / "programs-r90c.sqlite"
    )

    draft_id = store.save_draft(
        draft
    )

    return store, draft_id


def test_review_draft_requires_acknowledgement(
    tmp_path,
):
    import pytest

    from core.bounty_programs import (
        ProgramReviewError,
        review_draft,
    )

    store, draft_id = _r90c_draft(
        tmp_path
    )

    with pytest.raises(
        ProgramReviewError
    ):
        review_draft(
            store=store,
            draft_id=draft_id,
            reviewer="reviewer",
            include=[
                "staging.example.com"
            ],
            acknowledge_policy_review=False,
        )


def test_review_draft_creates_non_executable_snapshot(
    tmp_path,
):
    from core.bounty_programs import (
        review_draft,
    )

    store, draft_id = _r90c_draft(
        tmp_path
    )

    program_id, snapshot = review_draft(
        store=store,
        draft_id=draft_id,
        reviewer="reviewer",
        include=[
            "staging.example.com",
            "*.staging.example.com",
        ],
        exclude=[
            "example.com",
        ],
        acknowledge_policy_review=True,
    )

    evidence = snapshot.evidence()

    assert program_id

    assert (
        evidence["structured_scope_reviewed"]
        is True
    )

    assert (
        evidence["testing_authorized"]
        is False
    )

    assert (
        evidence["execution_enabled"]
        is False
    )

    assert (
        evidence["source_draft_id"]
        == draft_id
    )

    assert (
        evidence["reviewer"]
        == "reviewer"
    )

    assert evidence[
        "authorization_scope"
    ] == {
        "include": [
            "*.staging.example.com",
            "staging.example.com",
        ],
        "exclude": [
            "example.com",
        ],
    }


def test_review_draft_rejects_include_exclude_overlap(
    tmp_path,
):
    import pytest

    from core.bounty_programs import (
        ProgramReviewError,
        review_draft,
    )

    store, draft_id = _r90c_draft(
        tmp_path
    )

    with pytest.raises(
        ProgramReviewError
    ):
        review_draft(
            store=store,
            draft_id=draft_id,
            reviewer="reviewer",
            include=[
                "staging.example.com",
            ],
            exclude=[
                "staging.example.com",
            ],
            acknowledge_policy_review=True,
        )


def test_review_draft_detects_tampered_source_digest(
    tmp_path,
):
    import json
    import pytest

    from core.bounty_programs import (
        ProgramReviewError,
        review_draft,
    )

    store, draft_id = _r90c_draft(
        tmp_path
    )

    with store.db() as db:
        row = db.execute(
            """
            SELECT draft_json
            FROM program_drafts
            WHERE id=?
            """,
            (draft_id,),
        ).fetchone()

        payload = json.loads(
            row["draft_json"]
        )

        payload["policy_text"] = (
            "tampered policy"
        )

        db.execute(
            """
            UPDATE program_drafts
            SET draft_json=?
            WHERE id=?
            """,
            (
                json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                draft_id,
            ),
        )

    with pytest.raises(
        ProgramReviewError
    ):
        review_draft(
            store=store,
            draft_id=draft_id,
            reviewer="reviewer",
            include=[
                "staging.example.com",
            ],
            acknowledge_policy_review=True,
        )


def _r90d_reviewed_program(tmp_path):
    import json
    import time

    from core.bounty_catalog.store import Catalog
    from core.bounty_programs import (
        ProgramStore,
        hackerone_catalog_draft,
        review_draft,
    )

    catalog = Catalog(
        tmp_path / "catalog-r90d.sqlite"
    )

    raw = json.dumps(
        {
            "data": [
                {
                    "type": "program",
                    "attributes": {
                        "handle":
                            "r90d-demo",
                        "name":
                            "R9.0D Demo",
                        "offers_bounties":
                            True,
                        "submission_state":
                            "open",
                        "policy":
                            "Only test staging.example.com",
                    },
                }
            ],
            "links": {},
        }
    ).encode()

    catalog.save(
        "hackerone-api",
        time.time(),
        [(1, raw, time.time())],
        "complete",
    )

    store = ProgramStore(
        tmp_path / "programs-r90d.sqlite"
    )

    draft = hackerone_catalog_draft(
        catalog,
        "r90d-demo",
    )

    draft_id = store.save_draft(
        draft
    )

    program_id, _snapshot = review_draft(
        store=store,
        draft_id=draft_id,
        reviewer="reviewer",
        include=[
            "staging.example.com",
            "*.staging.example.com",
        ],
        exclude=[
            "example.com",
        ],
        acknowledge_policy_review=True,
    )

    return store, program_id


def test_r90d_authorization_bridge_round_trip(
    tmp_path,
):
    from core.bounty_authorization import (
        AuthorizationStore,
    )
    from core.bounty_programs import (
        authorize_reviewed_program,
    )

    programs, program_id = (
        _r90d_reviewed_program(
            tmp_path
        )
    )

    auths = AuthorizationStore(
        tmp_path / "auth-r90d.sqlite"
    )

    auth_id = authorize_reviewed_program(
        program_store=programs,
        authorization_store=auths,
        program_id=program_id,
        reviewer="reviewer",
        logical_capabilities=[
            "subdomain_discovery",
            "dns_resolution",
            "http_probe",
        ],
        approved_providers=[
            "subfinder",
            "dnsx",
            "httpx",
        ],
        ttl=3600,
    )

    scope = auths.live_scope(
        auth_id
    )

    assert scope.program == "r90d-demo"

    assert set(
        scope.logical_capabilities
    ) == {
        "subdomain_discovery",
        "dns_resolution",
        "http_probe",
    }

    assert set(
        scope.approved_providers
    ) == {
        "subfinder",
        "dnsx",
        "httpx",
    }

    assert scope.permits_host(
        "staging.example.com"
    )

    assert scope.permits_host(
        "api.staging.example.com"
    )

    assert not scope.permits_host(
        "example.com"
    )


def test_r90d_rejects_reviewer_mismatch(
    tmp_path,
):
    import pytest

    from core.bounty_authorization import (
        AuthorizationStore,
    )
    from core.bounty_programs import (
        AuthorizationBridgeError,
        authorize_reviewed_program,
    )

    programs, program_id = (
        _r90d_reviewed_program(
            tmp_path
        )
    )

    auths = AuthorizationStore(
        tmp_path / "auth.sqlite"
    )

    with pytest.raises(
        AuthorizationBridgeError
    ):
        authorize_reviewed_program(
            program_store=programs,
            authorization_store=auths,
            program_id=program_id,
            reviewer="someone-else",
            logical_capabilities=[
                "http_probe",
            ],
            approved_providers=[
                "httpx",
            ],
            ttl=3600,
        )


def test_r90d_requires_provider_for_each_capability(
    tmp_path,
):
    import pytest

    from core.bounty_authorization import (
        AuthorizationStore,
    )
    from core.bounty_programs import (
        AuthorizationBridgeError,
        authorize_reviewed_program,
    )

    programs, program_id = (
        _r90d_reviewed_program(
            tmp_path
        )
    )

    auths = AuthorizationStore(
        tmp_path / "auth.sqlite"
    )

    with pytest.raises(
        AuthorizationBridgeError
    ):
        authorize_reviewed_program(
            program_store=programs,
            authorization_store=auths,
            program_id=program_id,
            reviewer="reviewer",
            logical_capabilities=[
                "subdomain_discovery",
                "dns_resolution",
            ],
            approved_providers=[
                "subfinder",
            ],
            ttl=3600,
        )


def test_r90d_detects_scope_tampering(
    tmp_path,
):
    import json
    import pytest

    from core.bounty_authorization import (
        AuthorizationStore,
    )
    from core.bounty_programs import (
        AuthorizationBridgeError,
        authorize_reviewed_program,
    )

    programs, program_id = (
        _r90d_reviewed_program(
            tmp_path
        )
    )

    with programs.db() as db:
        row = db.execute(
            """
            SELECT snapshot_json
            FROM programs
            WHERE id=?
            """,
            (program_id,),
        ).fetchone()

        snapshot = json.loads(
            row["snapshot_json"]
        )

        snapshot[
            "authorization_scope"
        ]["include"].append(
            "production.example.com"
        )

        db.execute(
            """
            UPDATE programs
            SET snapshot_json=?
            WHERE id=?
            """,
            (
                json.dumps(
                    snapshot,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                program_id,
            ),
        )

    auths = AuthorizationStore(
        tmp_path / "auth.sqlite"
    )

    with pytest.raises(
        AuthorizationBridgeError
    ):
        authorize_reviewed_program(
            program_store=programs,
            authorization_store=auths,
            program_id=program_id,
            reviewer="reviewer",
            logical_capabilities=[
                "http_probe",
            ],
            approved_providers=[
                "httpx",
            ],
            ttl=3600,
        )
