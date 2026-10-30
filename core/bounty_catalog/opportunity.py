"""
JARVIS R9.9C

Read-only HackerOne program opportunity enrichment.

This module:

- reads already-stored catalog observations
- extracts program-policy signals
- estimates technical/revenue opportunity
- does NOT authorize testing
- does NOT create missions
- does NOT execute scanners
- does NOT create network traffic

Any parsed payout value is a policy-text mention only. It is
not treated as an authoritative structured bounty table.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


_AMOUNT_RE = re.compile(
    r"(?:\$|USD\s*)\s*"
    r"(\d{1,3}(?:,\d{3})+|\d+)",
    re.IGNORECASE,
)

_AUTOMATION_TERMS = (
    "scanner",
    "scanners",
    "automated",
    "automation",
    "crawler",
    "crawlers",
    "crawling",
    "script",
    "scripts",
    "bot",
    "bots",
)


_PERMIT_TERMS = (
    "allowed",
    "permitted",
    "welcome",
    "may use",
    "can use",
    "are allowed",
    "is allowed",
)


_RESTRICT_TERMS = (
    "prohibited",
    "not allowed",
    "do not",
    "must not",
    "forbidden",
    "disallowed",
)


@dataclass
class PolicySignals:
    payout_mentions: list[int]
    payout_max_mention: int | None
    automation_mentions: list[str]
    automation_permit_evidence: list[str]
    automation_restrict_evidence: list[str]
    automation_policy: str
    policy_confidence: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "payout_mentions":
                self.payout_mentions,

            "payout_max_mention":
                self.payout_max_mention,

            "payout_value_state":
                (
                    "policy_text_heuristic"
                    if self.payout_mentions
                    else "not_observed"
                ),

            "automation_mentions":
                self.automation_mentions,

            "automation_permit_evidence":
                self.automation_permit_evidence,

            "automation_restrict_evidence":
                self.automation_restrict_evidence,

            "automation_policy":
                self.automation_policy,

            "policy_confidence":
                self.policy_confidence,
        }


def _clean_excerpt(
    text: str,
    start: int,
    end: int,
    radius: int = 150,
) -> str:
    lo = max(
        0,
        start - radius,
    )

    hi = min(
        len(text),
        end + radius,
    )

    excerpt = text[
        lo:hi
    ]

    excerpt = re.sub(
        r"\s+",
        " ",
        excerpt,
    ).strip()

    return excerpt[:500]


def _dedupe(
    values: list[str],
) -> list[str]:
    seen = set()
    result = []

    for value in values:
        key = value.casefold()

        if key in seen:
            continue

        seen.add(key)
        result.append(value)

    return result


def parse_policy_signals(
    policy: str | None,
) -> PolicySignals:
    """
    R9.9F.1

    Classify automation policy using explicit phrases and
    sentence/clause context.

    Important:
    - "not permitted" always overrides the bare word "permitted"
    - rate limits imply conditional permission, not prohibition
    - report-quality restrictions are not equivalent to testing bans
    - this remains heuristic and never grants authorization
    """

    text = str(policy or "")
    lower = text.casefold()

    payout_mentions = []

    for match in _AMOUNT_RE.finditer(text):
        raw = match.group(1).replace(",", "")

        try:
            value = int(raw)
        except ValueError:
            continue

        if value >= 50:
            payout_mentions.append(value)

    payout_mentions = sorted(set(payout_mentions))

    # Split into sentence-ish policy units while retaining enough
    # surrounding meaning for bullets and headings.
    units = [
        re.sub(r"\s+", " ", part).strip()
        for part in re.split(
            r"(?<=[.!?])\s+|\n+|(?=\*\s)|(?=-\s)",
            text,
        )
        if part.strip()
    ]

    automation_units = []

    for unit in units:
        unit_lower = unit.casefold()

        if any(
            term in unit_lower
            for term in _AUTOMATION_TERMS
        ):
            automation_units.append(unit[:700])

    explicit_prohibit = []
    explicit_permit = []
    conditional_permit = []
    reporting_only = []

    prohibit_patterns = (
        r"\bautomated scanning\b.{0,80}\bnot permitted\b",
        r"\bautomated tools?\b.{0,80}\bnot permitted\b",
        r"\bscanners?\b.{0,80}\bnot permitted\b",
        r"\bautomation\b.{0,80}\bnot permitted\b",
        r"\bdo not use\b.{0,80}\b(?:scanner|automated|crawler|bot|script)",
        r"\bmust not\b.{0,80}\b(?:scanner|automated|crawler|bot|script)",
        r"\b(?:scanner|automated|crawler|bot|script).{0,80}\bprohibited\b",
        r"\bno automated scanning\b",
    )

    conditional_patterns = (
        r"\brate[- ]?limit\b.{0,180}\bautomated",
        r"\bautomated\b.{0,180}\brate[- ]?limit",
        r"\blimit automated testing\b",
        r"\bscanners?\b.{0,160}\bnarrow scope\b",
        r"\bscanners?\b.{0,160}\bauthorized\b",
        r"\bautomated tooling\b.{0,160}\bmaximum\b",
        r"\bautomated testing\b.{0,160}\bmaximum\b",
        r"\bfeel free to use\b.{0,120}\bscanners?\b",
    )

    explicit_permit_patterns = (
        r"\bautomated (?:testing|scanning|tools?)\b.{0,80}\b(?:allowed|permitted)\b",
        r"\b(?:scanners?|crawlers?|scripts?)\b.{0,80}\b(?:allowed|permitted)\b",
        r"\b(?:allowed|permitted)\b.{0,80}\b(?:scanner|automated|crawler|script)",
        r"\bmay use\b.{0,120}\b(?:scanners?|crawlers?|scripts?|automated tools?)\b",
        r"\bcan use\b.{0,120}\b(?:scanners?|crawlers?|scripts?|automated tools?)\b",
    )

    reporting_patterns = (
        r"\bscanner output\b.{0,150}\b(?:not accepted|not eligible|without manual validation)\b",
        r"\bautomated scanner output\b.{0,150}\bwithout manual validation\b",
        r"\breports? from automated scanners?\b.{0,150}\b(?:not accepted|not validated)\b",
        r"\bscanner-generated reports?\b",
    )

    for unit in automation_units:
        u = unit.casefold()

        prohibited = any(
            re.search(pattern, u, re.IGNORECASE)
            for pattern in prohibit_patterns
        )

        conditional = any(
            re.search(pattern, u, re.IGNORECASE)
            for pattern in conditional_patterns
        )

        report_restriction = any(
            re.search(pattern, u, re.IGNORECASE)
            for pattern in reporting_patterns
        )

        # Critical: negative phrases win before positive wording.
        if prohibited:
            explicit_prohibit.append(unit)
            continue

        if conditional:
            conditional_permit.append(unit)
            continue

        permitted = any(
            re.search(pattern, u, re.IGNORECASE)
            for pattern in explicit_permit_patterns
        )

        if permitted:
            explicit_permit.append(unit)
            continue

        if report_restriction:
            reporting_only.append(unit)

    explicit_prohibit = _dedupe(explicit_prohibit)[:8]
    explicit_permit = _dedupe(explicit_permit)[:8]
    conditional_permit = _dedupe(conditional_permit)[:8]
    reporting_only = _dedupe(reporting_only)[:8]
    automation_units = _dedupe(automation_units)[:12]

    if explicit_prohibit and (
        explicit_permit
        or conditional_permit
    ):
        automation_policy = (
            "mixed_context_review_required"
        )

    elif explicit_prohibit:
        automation_policy = (
            "explicitly_prohibited"
        )

    elif conditional_permit:
        automation_policy = (
            "conditionally_permitted"
        )

    elif explicit_permit:
        automation_policy = (
            "explicitly_permitted"
        )

    elif reporting_only:
        automation_policy = (
            "reporting_restriction_only"
        )

    else:
        automation_policy = (
            "not_explicitly_observed"
        )

    # Existing dataclass field names are retained for compatibility.
    # "permit evidence" includes conditional permission evidence.
    permit_evidence = _dedupe(
        explicit_permit
        + conditional_permit
    )[:8]

    restrict_evidence = _dedupe(
        explicit_prohibit
        + reporting_only
    )[:8]

    return PolicySignals(
        payout_mentions=payout_mentions,
        payout_max_mention=(
            max(payout_mentions)
            if payout_mentions
            else None
        ),
        automation_mentions=automation_units,
        automation_permit_evidence=permit_evidence,
        automation_restrict_evidence=restrict_evidence,
        automation_policy=automation_policy,
        policy_confidence=(
            "heuristic_requires_human_policy_review"
        ),
    )


def latest_raw_programs(
    catalog,
) -> list[dict[str, Any]]:
    """
    Read raw attributes from the newest HackerOne
    catalog run.

    No network request is made.
    """

    with catalog.connect() as db:
        run = db.execute(
            """
            SELECT id
            FROM runs
            WHERE source='hackerone-api'
            ORDER BY finished DESC,rowid DESC
            LIMIT 1
            """
        ).fetchone()

        if not run:
            return []

        pages = db.execute(
            """
            SELECT number, raw
            FROM pages
            WHERE run=?
            ORDER BY number
            """,
            (run["id"],),
        ).fetchall()

    result = []

    for page in pages:
        raw = page["raw"]

        if isinstance(
            raw,
            bytes,
        ):
            raw = raw.decode(
                "utf-8"
            )

        document = json.loads(
            raw
        )

        for item in document.get(
            "data",
            [],
        ):
            if not isinstance(
                item,
                dict,
            ):
                continue

            attrs = item.get(
                "attributes"
            )

            if not isinstance(
                attrs,
                dict,
            ):
                continue

            result.append(
                {
                    "id":
                        item.get("id"),

                    "page":
                        page["number"],

                    "attributes":
                        attrs,
                }
            )

    return result


def score_program(
    attributes: dict[str, Any],
) -> dict[str, Any]:
    policy = str(
        attributes.get(
            "policy"
        )
        or ""
    )

    signals = parse_policy_signals(
        policy
    )

    paid = (
        attributes.get(
            "offers_bounties"
        )
        is True
    )

    submission_open = (
        attributes.get(
            "submission_state"
        )
        == "open"
    )

    open_scope = (
        attributes.get(
            "open_scope"
        )
        is True
    )

    safe_harbor = (
        attributes.get(
            "gold_standard_safe_harbor"
        )
        is True
    )

    triage_active = (
        attributes.get(
            "triage_active"
        )
        is True
    )

    fast_payments = (
        attributes.get(
            "fast_payments"
        )
        is True
    )

    payout = (
        signals.payout_max_mention
    )

    automation_score = 0
    manual_score = 0
    payout_score = 0

    reasons = []
    blockers = []

    if paid:
        automation_score += 15
        manual_score += 20

        reasons.append(
            "Program offers bounties"
        )
    else:
        blockers.append(
            "Program is not currently marked as paid"
        )

    if submission_open:
        automation_score += 10
        manual_score += 12

        reasons.append(
            "Submissions currently open"
        )
    else:
        blockers.append(
            "Program submissions are not open"
        )

    if open_scope:
        automation_score += 18
        manual_score += 10

        reasons.append(
            "Program reports open scope"
        )

    if safe_harbor:
        automation_score += 6
        manual_score += 6

        reasons.append(
            "Gold Standard Safe Harbor reported"
        )

    if triage_active:
        automation_score += 5
        manual_score += 5

        reasons.append(
            "Triage reported active"
        )

    if fast_payments:
        payout_score += 5

        reasons.append(
            "Fast payments reported"
        )

    if payout:
        if payout >= 10000:
            payout_score += 40

        elif payout >= 5000:
            payout_score += 32

        elif payout >= 3000:
            payout_score += 24

        elif payout >= 1000:
            payout_score += 15

        else:
            payout_score += 7

    automation_policy = (
        signals.automation_policy
    )

    if (
        automation_policy
        == "explicitly_permitted"
    ):
        automation_score += 25

        reasons.append(
            "Policy contains explicit automation-permission evidence"
        )

    elif (
        automation_policy
        == "conditionally_permitted"
    ):
        automation_score += 18

        reasons.append(
            "Policy contains conditional automation-permission evidence"
        )

    elif (
        automation_policy
        == "explicitly_prohibited"
    ):
        automation_score -= 30

        blockers.append(
            "Policy explicitly prohibits relevant automation"
        )

    elif (
        automation_policy
        == "mixed_context_review_required"
    ):
        automation_score -= 8

        blockers.append(
            "Automation rules appear context-dependent"
        )

    elif (
        automation_policy
        == "reporting_restriction_only"
    ):
        automation_score += 4

        reasons.append(
            "Policy restricts scanner-only reporting, not necessarily testing"
        )

    # Manual hunting benefits from rich policy /
    # program surfaces even when automation is unclear.
    if len(policy) >= 2000:
        manual_score += 8

        reasons.append(
            "Detailed policy available for manual mission preparation"
        )

    elif len(policy) >= 500:
        manual_score += 4

    automation_score += (
        payout_score // 2
    )

    manual_score += (
        payout_score
    )

    automation_score = max(
        0,
        min(
            100,
            automation_score,
        ),
    )

    manual_score = max(
        0,
        min(
            100,
            manual_score,
        ),
    )

    if not paid or not submission_open:
        lane = "SKIP"

    elif (
        automation_policy
        == "explicitly_prohibited"
    ):
        if manual_score >= 65:
            lane = "MANUAL_A"
        elif manual_score >= 45:
            lane = "MANUAL_B"
        else:
            lane = "POLICY_REVIEW"

    elif (
        automation_policy
        == "mixed_context_review_required"
    ):
        if manual_score >= 65:
            lane = "MANUAL_A"
        elif manual_score >= 45:
            lane = "MANUAL_B"
        else:
            lane = "POLICY_REVIEW"

    elif (
        automation_policy
        in {
            "explicitly_permitted",
            "conditionally_permitted",
        }
    ):
        # Policy evidence is promising, but this is still only
        # discovery. Structured scope + capability authorization
        # are required before any execution lane can exist.
        lane = "POLICY_REVIEW"

    elif (
        automation_policy
        == "reporting_restriction_only"
    ):
        if manual_score >= 70:
            lane = "MANUAL_A"
        elif manual_score >= 50:
            lane = "MANUAL_B"
        else:
            lane = "POLICY_REVIEW"

    elif manual_score >= 70:
        lane = "MANUAL_A"

    elif manual_score >= 50:
        lane = "MANUAL_B"

    else:
        lane = "POLICY_REVIEW"

    return {
        "handle":
            attributes.get(
                "handle"
            ),

        "name":
            attributes.get(
                "name"
            ),

        "currency":
            attributes.get(
                "currency"
            ),

        "offers_bounties":
            paid,

        "submission_state":
            attributes.get(
                "submission_state"
            ),

        "visibility":
            attributes.get(
                "state"
            ),

        "open_scope":
            attributes.get(
                "open_scope"
            ),

        "gold_standard_safe_harbor":
            attributes.get(
                "gold_standard_safe_harbor"
            ),

        "fast_payments":
            attributes.get(
                "fast_payments"
            ),

        "triage_active":
            attributes.get(
                "triage_active"
            ),

        "started_accepting_at":
            attributes.get(
                "started_accepting_at"
            ),

        "automation_viability_score":
            automation_score,

        "manual_hunt_viability_score":
            manual_score,

        "payout_score":
            payout_score,

        "policy_reward_max_mention":
            payout,

        "policy_signals":
            signals.as_dict(),

        "lane":
            lane,

        "reasons":
            reasons,

        "blockers":
            blockers,

        # Critical boundary:
        "policy_review_required":
            True,

        "testing_authorized":
            False,

        "execution_enabled":
            False,

        "automatic_execution_ready":
            False,
    }


def rank_catalog(
    catalog,
) -> dict[str, Any]:
    raw = latest_raw_programs(
        catalog
    )

    opportunities = [
        score_program(
            item["attributes"]
        )
        for item in raw
    ]

    lane_order = {
        "POLICY_REVIEW": 0,
        "MANUAL_A": 1,
        "MANUAL_B": 2,
        "SKIP": 3,
    }

    opportunities.sort(
        key=lambda item: (
            lane_order.get(
                item["lane"],
                99,
            ),
            -max(
                item[
                    "automation_viability_score"
                ],
                item[
                    "manual_hunt_viability_score"
                ],
            ),
            -item["payout_score"],
            str(
                item.get("name")
                or ""
            ).casefold(),
        )
    )

    counts = {}

    for item in opportunities:
        counts[item["lane"]] = (
            counts.get(
                item["lane"],
                0,
            )
            + 1
        )

    return {
        "schema":
            "jarvis-bounty-program-opportunity-r9.9c",

        "source":
            "stored_hackerone_catalog",

        "program_count":
            len(opportunities),

        "lane_counts":
            counts,

        "network_requests":
            0,

        "testing_authorized":
            False,

        "execution_enabled":
            False,

        "payout_values_authoritative":
            False,

        "payout_note":
            (
                "Dollar amounts are heuristic mentions "
                "parsed from policy text and must be "
                "confirmed during human program review."
            ),

        "opportunities":
            opportunities,
    }
