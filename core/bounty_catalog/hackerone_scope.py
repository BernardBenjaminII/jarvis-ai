"""
JARVIS R9.10H

Read-only HackerOne structured-scope retrieval.

This module is intentionally separate from the existing
program-list catalog client.

Allowed network behavior:
- HTTPS only
- api.hackerone.com only
- GET only
- /v1/hackers/programs/{handle}/structured_scopes only
- sequential pagination only
- max 100 records/page
- no redirects
- no retries
- no target testing
- no authorization creation
"""

from __future__ import annotations

import base64
import http.client
import json
import re
import ssl
import time

from urllib.parse import (
    parse_qs,
    urlencode,
    urlsplit,
)


HOST = "api.hackerone.com"

MAX_BYTES = 2 * 1024 * 1024

_HANDLE_RE = re.compile(
    r"^[A-Za-z0-9_-]{1,100}$"
)


class StructuredScopeError(ValueError):
    pass


def _validate_handle(
    handle: str,
) -> str:
    handle = str(handle).strip()

    if not _HANDLE_RE.fullmatch(
        handle
    ):
        raise StructuredScopeError(
            "Invalid program handle"
        )

    return handle


def scope_path(
    handle: str,
    page: int,
) -> str:
    handle = _validate_handle(
        handle
    )

    if (
        type(page) is not int
        or page < 1
    ):
        raise StructuredScopeError(
            "Invalid scope page number"
        )

    base = (
        "/v1/hackers/programs/"
        + handle
        + "/structured_scopes"
    )

    return (
        base
        + "?"
        + urlencode({
            "page[number]": page,
            "page[size]": 100,
        })
    )


def scope_url(
    handle: str,
    page: int,
) -> str:
    return (
        "https://"
        + HOST
        + scope_path(
            handle,
            page,
        )
    )


def decode_scope_page(
    raw: bytes,
) -> tuple[list[dict], str | None]:
    if len(raw) > MAX_BYTES:
        raise StructuredScopeError(
            "Response exceeds 2 MiB"
        )

    try:
        document = json.loads(
            raw
        )
    except (
        ValueError,
        UnicodeError,
    ):
        raise StructuredScopeError(
            "Invalid JSON response"
        ) from None

    data = document.get("data")

    if not isinstance(
        data,
        list,
    ):
        raise StructuredScopeError(
            "Expected structured scope list"
        )

    if len(data) > 100:
        raise StructuredScopeError(
            "Unexpected scope page size"
        )

    rows = []

    for item in data:
        if not isinstance(
            item,
            dict,
        ):
            raise StructuredScopeError(
                "Invalid structured scope object"
            )

        if item.get("type") not in {
            "structured-scope",
            "structured_scope",
        }:
            raise StructuredScopeError(
                "Unexpected structured scope type"
            )

        scope_id = item.get("id")

        if not isinstance(
            scope_id,
            str,
        ) or not scope_id:
            raise StructuredScopeError(
                "Structured scope missing id"
            )

        attrs = item.get(
            "attributes"
        )

        if not isinstance(
            attrs,
            dict,
        ):
            raise StructuredScopeError(
                "Structured scope missing attributes"
            )

        identifier = attrs.get(
            "asset_identifier"
        )

        asset_type = attrs.get(
            "asset_type"
        )

        eligible_submission = attrs.get(
            "eligible_for_submission"
        )

        eligible_bounty = attrs.get(
            "eligible_for_bounty"
        )

        if not isinstance(
            identifier,
            str,
        ) or not identifier:
            raise StructuredScopeError(
                "Invalid asset identifier"
            )

        if not isinstance(
            asset_type,
            str,
        ) or not asset_type:
            raise StructuredScopeError(
                "Invalid asset type"
            )

        if type(
            eligible_submission
        ) is not bool:
            raise StructuredScopeError(
                "Invalid eligible_for_submission"
            )

        if type(
            eligible_bounty
        ) is not bool:
            raise StructuredScopeError(
                "Invalid eligible_for_bounty"
            )

        instruction = attrs.get(
            "instruction"
        )

        if (
            instruction is not None
            and not isinstance(
                instruction,
                str,
            )
        ):
            raise StructuredScopeError(
                "Invalid scope instruction"
            )

        rows.append({
            "id":
                scope_id,

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
                attrs.get(
                    "max_severity"
                ),

            "reference":
                attrs.get(
                    "reference"
                ),

            "created_at":
                attrs.get(
                    "created_at"
                ),

            "updated_at":
                attrs.get(
                    "updated_at"
                ),

            # Retrieval does not equal review.
            "structured_scope_reviewed":
                False,

            "testing_authorized":
                False,

            "execution_enabled":
                False,
        })

    links = document.get(
        "links",
        {}
    )

    if not isinstance(
        links,
        dict,
    ):
        raise StructuredScopeError(
            "Invalid pagination links"
        )

    return (
        rows,
        links.get("next"),
    )


def _next_page(
    link: str | None,
    handle: str,
    current: int,
) -> int | None:
    if link is None:
        return None

    if not isinstance(
        link,
        str,
    ):
        raise StructuredScopeError(
            "Invalid next-page link"
        )

    expected_path = (
        "/v1/hackers/programs/"
        + _validate_handle(handle)
        + "/structured_scopes"
    )

    parsed = urlsplit(
        link
    )

    if (
        parsed.scheme != "https"
        or parsed.netloc != HOST
        or parsed.path
        != expected_path
        or parsed.fragment
    ):
        raise StructuredScopeError(
            "Unexpected scope pagination destination"
        )

    query = parse_qs(
        parsed.query
    )

    if set(query) - {
        "page[number]",
        "page[size]",
    }:
        raise StructuredScopeError(
            "Unexpected scope pagination parameters"
        )

    if query.get(
        "page[number]"
    ) != [
        str(current + 1)
    ]:
        raise StructuredScopeError(
            "Scope pagination is not sequential"
        )

    if (
        "page[size]" in query
        and query[
            "page[size]"
        ] != ["100"]
    ):
        raise StructuredScopeError(
            "Unexpected scope pagination size"
        )

    return current + 1


class StructuredScopeClient:
    def __init__(
        self,
        username: str,
        token: str,
    ):
        if (
            not username
            or not token
            or ":" in username
        ):
            raise StructuredScopeError(
                "API username and token are required"
            )

        self._auth = (
            "Basic "
            + base64.b64encode(
                (
                    username
                    + ":"
                    + token
                ).encode()
            ).decode()
        )

    def fetch(
        self,
        handle: str,
        page: int,
    ) -> bytes:
        path = scope_path(
            handle,
            page,
        )

        connection = (
            http.client.HTTPSConnection(
                HOST,
                timeout=15,
                context=(
                    ssl.create_default_context()
                ),
            )
        )

        try:
            connection.request(
                "GET",
                path,
                headers={
                    "Authorization":
                        self._auth,

                    "Accept":
                        "application/json",

                    "Accept-Encoding":
                        "identity",

                    "User-Agent":
                        "Jarvis-Structured-Scope/9.10H",
                },
            )

            response = (
                connection.getresponse()
            )

            if response.status != 200:
                if response.status in (
                    401,
                    403,
                ):
                    raise StructuredScopeError(
                        "Authentication or API access rejected"
                    )

                if response.status == 429:
                    raise StructuredScopeError(
                        "Rate limited; stopped without retry"
                    )

                raise StructuredScopeError(
                    "API HTTP status "
                    + str(
                        response.status
                    )
                )

            if (
                response.getheader(
                    "Content-Encoding",
                    "identity",
                )
                != "identity"
            ):
                raise StructuredScopeError(
                    "Unexpected response encoding"
                )

            body = bytearray()
            deadline = (
                time.monotonic()
                + 30
            )

            while True:
                remaining = (
                    MAX_BYTES
                    + 1
                    - len(body)
                )

                chunk = response.read1(
                    min(
                        65536,
                        remaining,
                    )
                )

                body.extend(
                    chunk
                )

                if len(body) > MAX_BYTES:
                    raise StructuredScopeError(
                        "Response exceeds 2 MiB"
                    )

                if (
                    time.monotonic()
                    > deadline
                ):
                    raise StructuredScopeError(
                        "Response body deadline exceeded"
                    )

                if not chunk:
                    break

            return bytes(body)

        except (
            OSError,
            http.client.HTTPException,
        ):
            raise StructuredScopeError(
                "API connection failed; no automatic retry"
            ) from None

        finally:
            connection.close()


def fetch_all_structured_scopes(
    client: StructuredScopeClient,
    handle: str,
    *,
    max_pages: int = 10,
) -> dict:
    if (
        type(max_pages) is not int
        or not 1 <= max_pages <= 20
    ):
        raise StructuredScopeError(
            "max_pages must be 1..20"
        )

    handle = _validate_handle(
        handle
    )

    page = 1
    pages = []
    scopes = []

    while True:
        raw = client.fetch(
            handle,
            page,
        )

        rows, next_link = (
            decode_scope_page(
                raw
            )
        )

        pages.append({
            "page":
                page,

            "url":
                scope_url(
                    handle,
                    page,
                ),

            "bytes":
                len(raw),
        })

        scopes.extend(
            rows
        )

        following = _next_page(
            next_link,
            handle,
            page,
        )

        if following is None:
            break

        if page >= max_pages:
            raise StructuredScopeError(
                "Structured scope pagination exceeds max_pages"
            )

        page = following

    return {
        "schema":
            "jarvis-hackerone-structured-scope-r9.10h",

        "handle":
            handle,

        "pages":
            pages,

        "scopes":
            scopes,

        "scope_count":
            len(scopes),

        "network_operation":
            "authenticated_get_only",

        "structured_scope_reviewed":
            False,

        "testing_authorized":
            False,

        "execution_enabled":
            False,
    }
