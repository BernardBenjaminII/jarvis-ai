"""R9.22B2: offline HackerOne + imported policy opportunity queue.

Read-only. No platform requests, testing authorization, mission creation,
reconnaissance or automatic execution.
"""

from __future__ import annotations

import math
import re
import time

from core.bounty_catalog.opportunity import rank_catalog
from core.bounty_agent.autonomy.program_opportunities_r922b import (
    OpportunityQueueError,
    build_imported_opportunity_queue,
)


_HANDLE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}\Z")


def build_unified_opportunity_queue(
    catalog,
    imported_records,
    *,
    now=None,
    max_age_seconds=86400,
):
    """Combine imported policies with a fresh, complete HackerOne snapshot."""

    imported = build_imported_opportunity_queue(imported_records)

    if now is None:
        now = time.time()

    if (
        isinstance(now, bool)
        or not isinstance(now, (int, float))
        or not math.isfinite(now)
    ):
        raise OpportunityQueueError("Invalid current time")

    if (
        type(max_age_seconds) is not int
        or not 1 <= max_age_seconds <= 2_592_000
    ):
        raise OpportunityQueueError("Invalid maximum snapshot age")

    with catalog.connect() as db:
        run = db.execute(
            """
            SELECT id, status, finished, error
            FROM runs
            WHERE source = 'hackerone-api'
            ORDER BY finished DESC, rowid DESC
            LIMIT 1
            """
        ).fetchone()

        page_count = (
            db.execute(
                "SELECT COUNT(*) FROM pages WHERE run = ?",
                (run["id"],),
            ).fetchone()[0]
            if run
            else 0
        )

    source = {
        "status": "missing",
        "run_id": None,
        "snapshot_age_seconds": None,
        "ranked_count": 0,
    }

    catalog_items = []

    if run:
        source["run_id"] = run["id"]

        finished = run["finished"]

        if (
            not isinstance(finished, (int, float))
            or not math.isfinite(finished)
        ):
            source["status"] = "invalid_timestamp"

        elif finished > now:
            source["status"] = "future_dated"

        else:
            age = now - finished
            source["snapshot_age_seconds"] = round(age, 3)

            if run["status"] != "complete" or run["error"]:
                source["status"] = "incomplete"

            elif page_count == 0:
                source["status"] = "empty_snapshot"

            elif age > max_age_seconds:
                source["status"] = "stale"

            else:
                source["status"] = "fresh"

    if source["status"] == "fresh":
        ranked = rank_catalog(catalog)

        if (
            ranked.get("source") != "stored_hackerone_catalog"
            or ranked.get("network_requests") != 0
            or ranked.get("testing_authorized") is not False
            or ranked.get("execution_enabled") is not False
            or ranked.get("payout_values_authoritative") is not False
        ):
            raise OpportunityQueueError(
                "Unsafe catalog ranking contract"
            )

        items = ranked.get("opportunities")

        if (
            not isinstance(items, list)
            or ranked.get("program_count") != len(items)
        ):
            raise OpportunityQueueError(
                "Invalid catalog ranking result"
            )

        seen = set()

        for item in items:
            if not isinstance(item, dict):
                raise OpportunityQueueError("Invalid ranked program")

            handle = item.get("handle")

            if not isinstance(handle, str) or not _HANDLE.fullmatch(handle):
                raise OpportunityQueueError("Invalid program handle")

            if handle.casefold() in seen:
                raise OpportunityQueueError("Duplicate program handle")

            seen.add(handle.casefold())

            if any(
                item.get(key) is not False
                for key in (
                    "testing_authorized",
                    "execution_enabled",
                    "automatic_execution_ready",
                )
            ):
                raise OpportunityQueueError(
                    "Ranking attempted to grant execution permission"
                )

            lane = item.get("lane")

            if lane not in {
                "POLICY_REVIEW", "MANUAL_A", "MANUAL_B", "SKIP"
            }:
                raise OpportunityQueueError("Unexpected ranking lane")

            name = item.get("name")
            if not isinstance(name, str) or not name.strip():
                name = handle

            catalog_items.append({
                "source": "hackerone_api_snapshot",
                "platform": "hackerone",
                "program": name,
                "handle": handle,
                "policy_url": f"https://hackerone.com/{handle}",
                "catalog_run_id": source["run_id"],
                "source_lane": lane,
                "automation_viability_score": item.get(
                    "automation_viability_score"
                ),
                "manual_hunt_viability_score": item.get(
                    "manual_hunt_viability_score"
                ),
                "payout_score": item.get("payout_score"),
                "policy_reward_max_mention": item.get(
                    "policy_reward_max_mention"
                ),
                "payout_values_authoritative": False,
                "program_eligibility": "unknown",
                "policy_review_status": "unverified",
                "recommendation": (
                    "skip_until_program_state_changes"
                    if lane == "SKIP"
                    else "human_policy_review_required"
                ),
                "testing_authorized": False,
                "execution_enabled": False,
                "automatic_execution_ready": False,
                "submission_authorized": False,
            })

        source["ranked_count"] = len(catalog_items)

    combined = catalog_items + imported["opportunities"]

    return {
        "schema": "jarvis.bounty.program_opportunities.r922b2",
        "mode": "offline_unified_opportunity_queue",
        "sources": {
            "hackerone_catalog": source,
            "manual_policy_import": {
                "status": "available",
                "count": imported["opportunity_count"],
            },
        },
        "opportunity_count": len(combined),
        "network_requests": 0,
        "testing_authorized": False,
        "automatic_execution_allowed": False,
        "submission_authorized": False,
        "opportunities": combined,
    }
