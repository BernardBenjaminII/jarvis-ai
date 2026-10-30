from __future__ import annotations

import json

from core.bounty_authorization import AuthorizationStore


AIRTABLE_PROFILE = {
    "schema": "jarvis-bounty-profile-r6",
    "program": "airtable",
    "display_name": "Airtable",
    "reviewed_from": {
        "platform": "hackerone",
        "program_handle": "airtable",
        "policy_reviewed": True,
        "structured_scope_reviewed": True,
    },
    "automation_class": "green-recon-only",
    "capabilities": ["subfinder", "httpx"],
    "include": [
        "staging.airtable.com",
        "*.staging.airtable.com",
        "mcp.staging.airtable.com",
    ],
    "exclude": [
        "airtable.com",
        "blog.airtable.com",
        "support.airtable.com",
        "guide.airtable.com",
        "community.airtable.com",
    ],
    "special_scope_held_for_separate_review": [
        "api-staging.airtable.com",
        "*.staging-airtableblocks.com",
        "airtable.js SDK",
        "@airtable/mcp-cli",
    ],
    "prohibited_categories": [
        "production testing",
        "desktop applications",
        "mobile applications",
        "credential attacks",
        "social engineering",
        "denial of service",
        "third-party infrastructure without separate authorization",
        "user-leaked API keys",
        "generic scanner-output-only reporting",
    ],
    "report_noise_filters": [
        "generic Server or X-Powered-By disclosure",
        "missing generic HTTP security headers",
        "DNSSEC",
        "DMARC/DKIM/SPF",
        "password-policy observations",
        "non-sensitive internal IDs",
        "self-XSS without broader impact",
        "generic vulnerable third-party dependency findings without exploit impact",
    ],
    "human_gates": [
        "deeper investigation",
        "vulnerability validation",
        "proof-of-concept execution beyond routine recon",
        "report submission",
    ],
}


def source_material() -> str:
    return json.dumps(
        {
            "profile": AIRTABLE_PROFILE,
            "review_statement": (
                "Reviewed Airtable HackerOne policy and structured scope. "
                "Only conservative staging web/DNS recon is authorized; "
                "production remains explicitly excluded."
            ),
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def create_airtable_authorization(
    *,
    reviewer: str,
    ttl: int = 86400,
    store: AuthorizationStore | None = None,
) -> str:
    reviewer = str(reviewer).strip()
    if not reviewer:
        raise ValueError("Reviewer identity is required")

    if type(ttl) is not int or not 60 <= ttl <= 30 * 86400:
        raise ValueError("TTL must be between 60 seconds and 30 days")

    store = store or AuthorizationStore()

    return store.create(
        program=AIRTABLE_PROFILE["program"],
        include=list(AIRTABLE_PROFILE["include"]),
        exclude=list(AIRTABLE_PROFILE["exclude"]),
        capabilities=list(AIRTABLE_PROFILE["capabilities"]),
        reviewer=reviewer,
        source_material=source_material(),
        ttl=ttl,
    )
