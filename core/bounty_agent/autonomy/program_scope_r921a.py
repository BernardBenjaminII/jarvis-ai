"""R9.21A — Offline bug bounty program-scope intake.

Never fetches URLs, authorizes execution, or modifies missions.
Imported policy information remains unverified.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit

SCHEMA = "jarvis.bounty.program_scope.r921a"
PLATFORMS = {"hackerone", "bugcrowd", "intigriti"}

HOST_RE = re.compile(
    r"^(?=.{1,253}$)"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$"
)


class ScopeIntakeError(ValueError):
    pass


def normalize_host(value: str) -> str:
    if not isinstance(value, str):
        raise ScopeIntakeError("Hostname must be a string")

    host = value.strip().lower().rstrip(".")

    if not HOST_RE.fullmatch(host):
        raise ScopeIntakeError(
            "Only exact DNS hostnames are supported"
        )

    return host


def create_scope_draft(
    *,
    platform: str,
    program: str,
    policy_url: str,
    in_scope: list[str],
    out_of_scope: list[str],
    restrictions: list[str],
) -> dict:
    if platform not in PLATFORMS:
        raise ScopeIntakeError("Unsupported platform")

    if not isinstance(program, str) or not program.strip():
        raise ScopeIntakeError("Program name required")

    if not isinstance(policy_url, str):
        raise ScopeIntakeError("Policy URL required")

    parsed = urlsplit(policy_url)

    allowed_policy_hosts = {
        "hackerone": {
            "hackerone.com", "www.hackerone.com"
        },
        "bugcrowd": {
            "bugcrowd.com", "www.bugcrowd.com"
        },
        "intigriti": {
            "app.intigriti.com"
        },
    }[platform]

    if (
        parsed.scheme != "https"
        or parsed.hostname not in allowed_policy_hosts
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port is not None
    ):
        raise ScopeIntakeError(
            "Policy URL must reference the selected platform"
        )

    for collection in (in_scope, out_of_scope, restrictions):
        if not isinstance(collection, list):
            raise ScopeIntakeError("Invalid policy collection")

    if not in_scope:
        raise ScopeIntakeError("At least one asset is required")

    if not restrictions or any(
        not isinstance(r, str) or not r.strip()
        for r in restrictions
    ):
        raise ScopeIntakeError(
            "Testing restrictions must be explicitly recorded"
        )

    allowed = sorted(set(map(normalize_host, in_scope)))
    excluded = sorted(set(map(normalize_host, out_of_scope)))

    # Exclusions override inclusions.
    allowed = [h for h in allowed if h not in excluded]

    canonical = {
        "platform": platform,
        "program": program.strip(),
        "policy_url": policy_url,
        "in_scope": allowed,
        "out_of_scope": excluded,
        "restrictions": sorted(set(
            r.strip() for r in restrictions
        )),
    }

    digest = hashlib.sha256(
        json.dumps(
            canonical,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    return {
        "schema": SCHEMA,
        **canonical,
        "policy_sha256": digest,
        "imported_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "review_status": "unverified",
        "scope_verified": False,
        "execution_authorized": False,
        "submission_authorized": False,
    }


def assess_scope_target(draft: dict, hostname: str) -> dict:
    host = normalize_host(hostname)

    if (
        not isinstance(draft, dict)
        or draft.get("schema") != SCHEMA
        or draft.get("scope_verified") is not False
        or draft.get("execution_authorized") is not False
    ):
        raise ScopeIntakeError("Invalid scope draft")

    if host in draft["out_of_scope"]:
        classification = "explicitly_excluded"
    elif host in draft["in_scope"]:
        classification = "listed_in_unverified_draft"
    else:
        classification = "not_listed"

    return {
        "hostname": host,
        "classification": classification,
        "scope_verified": False,
        "testing_authorized": False,
        "execution_authorized": False,
        "human_review_required": True,
    }
