import json

import pytest

from core.bounty_catalog.hackerone_scope import (
    HOST,
    StructuredScopeError,
    _next_page,
    decode_scope_page,
    fetch_all_structured_scopes,
    scope_path,
    scope_url,
)


def _page(
    data,
    *,
    next_link=None,
):
    return json.dumps(
        {
            "data": data,
            "links": {
                "next": next_link,
            },
        }
    ).encode()


def _scope(
    *,
    scope_id="1",
    identifier="www.example.com",
    asset_type="URL",
    eligible_submission=True,
    eligible_bounty=True,
    instruction=None,
):
    return {
        "id": scope_id,
        "type": "structured-scope",
        "attributes": {
            "asset_identifier":
                identifier,

            "asset_type":
                asset_type,

            "eligible_for_submission":
                eligible_submission,

            "eligible_for_bounty":
                eligible_bounty,

            "instruction":
                instruction,

            "max_severity":
                "critical",

            "reference":
                None,

            "created_at":
                "2026-01-01T00:00:00Z",

            "updated_at":
                "2026-01-02T00:00:00Z",
        },
    }


def test_r910h_scope_path_is_fixed_to_hackerone_scope_endpoint():
    path = scope_path(
        "whatnot",
        1,
    )

    assert path.startswith(
        "/v1/hackers/programs/whatnot/structured_scopes?"
    )

    assert "page%5Bnumber%5D=1" in path
    assert "page%5Bsize%5D=100" in path


def test_r910h_scope_url_uses_only_hackerone_host():
    url = scope_url(
        "whatnot",
        2,
    )

    assert url.startswith(
        "https://api.hackerone.com/"
    )

    assert HOST == "api.hackerone.com"


def test_r910h_rejects_invalid_handle():
    with pytest.raises(
        StructuredScopeError
    ):
        scope_path(
            "https://evil.example/",
            1,
        )


def test_r910h_decode_valid_scope():
    raw = _page([
        _scope(
            identifier="api.whatnot.com",
            asset_type="URL",
            eligible_submission=True,
            eligible_bounty=True,
            instruction="Test carefully.",
        )
    ])

    rows, next_link = decode_scope_page(
        raw
    )

    assert next_link is None
    assert len(rows) == 1

    row = rows[0]

    assert (
        row["asset_identifier"]
        == "api.whatnot.com"
    )

    assert row["asset_type"] == "URL"

    assert (
        row["eligible_for_submission"]
        is True
    )

    assert (
        row["eligible_for_bounty"]
        is True
    )

    assert (
        row["structured_scope_reviewed"]
        is False
    )

    assert (
        row["testing_authorized"]
        is False
    )

    assert (
        row["execution_enabled"]
        is False
    )


def test_r910h_rejects_wrong_object_type():
    raw = _page([
        {
            "id": "1",
            "type": "program",
            "attributes": {},
        }
    ])

    with pytest.raises(
        StructuredScopeError
    ):
        decode_scope_page(
            raw
        )


def test_r910h_rejects_non_boolean_eligibility():
    raw = _page([
        _scope(
            eligible_bounty="yes",
        )
    ])

    with pytest.raises(
        StructuredScopeError
    ):
        decode_scope_page(
            raw
        )


def test_r910h_next_page_accepts_only_sequential_hackerone_url():
    link = (
        "https://api.hackerone.com/"
        "v1/hackers/programs/whatnot/structured_scopes"
        "?page%5Bnumber%5D=2&page%5Bsize%5D=100"
    )

    assert (
        _next_page(
            link,
            "whatnot",
            1,
        )
        == 2
    )


def test_r910h_next_page_rejects_external_host():
    link = (
        "https://evil.example/"
        "v1/hackers/programs/whatnot/structured_scopes"
        "?page%5Bnumber%5D=2&page%5Bsize%5D=100"
    )

    with pytest.raises(
        StructuredScopeError
    ):
        _next_page(
            link,
            "whatnot",
            1,
        )


def test_r910h_next_page_rejects_wrong_program():
    link = (
        "https://api.hackerone.com/"
        "v1/hackers/programs/other/structured_scopes"
        "?page%5Bnumber%5D=2&page%5Bsize%5D=100"
    )

    with pytest.raises(
        StructuredScopeError
    ):
        _next_page(
            link,
            "whatnot",
            1,
        )


def test_r910h_next_page_rejects_nonsequential_page():
    link = (
        "https://api.hackerone.com/"
        "v1/hackers/programs/whatnot/structured_scopes"
        "?page%5Bnumber%5D=3&page%5Bsize%5D=100"
    )

    with pytest.raises(
        StructuredScopeError
    ):
        _next_page(
            link,
            "whatnot",
            1,
        )


def test_r910h_fetch_all_is_analysis_only():
    class FakeClient:
        def fetch(
            self,
            handle,
            page,
        ):
            assert handle == "whatnot"
            assert page == 1

            return _page([
                _scope(
                    identifier="www.whatnot.com",
                    asset_type="URL",
                ),
                _scope(
                    scope_id="2",
                    identifier="*.whatnot.com",
                    asset_type="WILDCARD",
                ),
            ])

    result = fetch_all_structured_scopes(
        FakeClient(),
        "whatnot",
        max_pages=3,
    )

    assert result["scope_count"] == 2

    assert (
        result["network_operation"]
        == "authenticated_get_only"
    )

    assert (
        result["structured_scope_reviewed"]
        is False
    )

    assert (
        result["testing_authorized"]
        is False
    )

    assert (
        result["execution_enabled"]
        is False
    )


def test_r910h_fetch_all_sequential_pagination():
    class FakeClient:
        def fetch(
            self,
            handle,
            page,
        ):
            if page == 1:
                return _page(
                    [
                        _scope(
                            identifier="a.whatnot.com",
                        )
                    ],
                    next_link=(
                        "https://api.hackerone.com/"
                        "v1/hackers/programs/whatnot/"
                        "structured_scopes"
                        "?page%5Bnumber%5D=2"
                        "&page%5Bsize%5D=100"
                    ),
                )

            if page == 2:
                return _page([
                    _scope(
                        scope_id="2",
                        identifier="b.whatnot.com",
                    )
                ])

            raise AssertionError(
                "unexpected page"
            )

    result = fetch_all_structured_scopes(
        FakeClient(),
        "whatnot",
        max_pages=3,
    )

    assert result["scope_count"] == 2

    assert [
        page["page"]
        for page in result["pages"]
    ] == [1, 2]


def test_r910h_max_page_guard():
    class FakeClient:
        def fetch(
            self,
            handle,
            page,
        ):
            next_page = page + 1

            return _page(
                [
                    _scope(
                        scope_id=str(page),
                        identifier=(
                            f"{page}.whatnot.com"
                        ),
                    )
                ],
                next_link=(
                    "https://api.hackerone.com/"
                    "v1/hackers/programs/whatnot/"
                    "structured_scopes"
                    f"?page%5Bnumber%5D={next_page}"
                    "&page%5Bsize%5D=100"
                ),
            )

    with pytest.raises(
        StructuredScopeError
    ):
        fetch_all_structured_scopes(
            FakeClient(),
            "whatnot",
            max_pages=1,
        )
