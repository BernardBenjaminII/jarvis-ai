from __future__ import annotations

import argparse
import json
import sqlite3
import time

from collections import Counter
from dataclasses import asdict
from pathlib import Path

from dev.as1.corpus_maintenance import (
    DEFAULT_KNOWLEDGE_ROOT,
    DEFAULT_LEGACY_DB,
    DEFAULT_RUNTIME_DB,
    build_known_sha_index,
    classify_file,
    load_catalog_documents,
    load_classifications,
    load_discovered,
    load_legacy_documents,
    load_runtime_documents,
    open_ro,
)

from dev.as1.identity import (
    IdentityVerdict,
    LayeredIdentityResolver,
    LegacyTextProvider,
    RuntimeIdentityIndex,
    build_fingerprint,
    get_candidate_text,
    sha256_file,
)


# ============================================================
# Fixed real-corpus certification set.
#
# No recursive discovery is performed by this script.
# ============================================================

CANARIES = (
    (
        "FM_3_06_11",
        DEFAULT_KNOWLEDGE_ROOT
        / "military"
        / "doctrine"
        / "US_Army_FM_3-06.11_Urban_Terrain.pdf",
    ),
    (
        "PRACTICAL_ELECTRONICS",
        DEFAULT_KNOWLEDGE_ROOT
        / "engineering"
        / "electronics"
        / "Practical Electronics.pdf",
    ),
    (
        "IMPROVISED_ENGINEERING",
        DEFAULT_KNOWLEDGE_ROOT
        / "engineering"
        / "mechanical"
        / "Improvised Engineering.pdf",
    ),
    (
        "MAP_AND_COMPASS",
        DEFAULT_KNOWLEDGE_ROOT
        / "geography"
        / "maps"
        / "Map_And_Compass.pdf",
    ),
    (
        "FM_5_33",
        DEFAULT_KNOWLEDGE_ROOT
        / "geography"
        / "terrain"
        / "US_Army_FM_5-33_Terrain_Analysis.pdf",
    ),
)


# Certification safety limit.
#
# If an individual runtime candidate has more than this many
# characters, Pack 2-R2 will not load its full content blob.
#
# This affects certification only. It is NOT an identity rule.
MAX_RUNTIME_CONTENT_CHARS = 4_000_000


class BoundedRuntimeIdentityIndex(
    RuntimeIdentityIndex
):
    """
    Certification-only runtime adapter.

    Prevents Pack 2-R2 from accidentally loading an enormous
    runtime content_text value while exercising the identity
    resolver.

    Production identity design will later use persistent
    fingerprints instead of repeatedly loading old text.
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        max_content_chars: int,
    ):
        self.max_content_chars = max_content_chars
        self.skipped_large_content = 0

        super().__init__(connection)

    def get_content_text(
        self,
        document_id: int,
    ) -> str | None:

        row = self.connection.execute(
            """
            SELECT
                content_chars,
                content_text
            FROM runtime_documents
            WHERE id=?
            LIMIT 1
            """,
            (document_id,),
        ).fetchone()

        if row is None:
            return None

        chars = row["content_chars"]

        try:
            chars_value = (
                int(chars)
                if chars is not None
                else 0
            )
        except (TypeError, ValueError):
            chars_value = 0

        if (
            chars_value > 0
            and chars_value > self.max_content_chars
        ):
            self.skipped_large_content += 1
            return None

        text = row["content_text"]

        if text is None:
            return None

        return str(text)


def file_sha_or_none(
    path: Path,
) -> str | None:
    try:
        return sha256_file(path)
    except OSError:
        return None


def certify_one(
    *,
    name: str,
    path: Path,
    resolver: LayeredIdentityResolver,
    legacy_text: LegacyTextProvider,
    shortlist: int,
    runtime_by_path: dict,
    classifications: dict,
    discovered: dict,
    catalog_by_path: dict,
    legacy_by_path: dict,
    known_sha: dict,
) -> dict:

    record = {
        "name": name,
        "path": str(path),
        "physical": False,
        "classification": None,
        "identity": None,
        "fingerprint": None,
        "status": "FAIL",
        "failure": None,
    }

    if not path.is_file():
        record["failure"] = (
            "Physical canary file is missing."
        )
        return record

    record["physical"] = True

    lifecycle = classify_file(
        path=path,
        verify_existing=False,
        runtime_by_path=runtime_by_path,
        classifications=classifications,
        discovered=discovered,
        catalog_by_path=catalog_by_path,
        legacy_by_path=legacy_by_path,
        known_sha=known_sha,
    )

    record["classification"] = asdict(
        lifecycle
    )

    # --------------------------------------------------------
    # Pack 2-R2 is specifically certifying document identity.
    # --------------------------------------------------------

    if lifecycle.role != "DOCUMENT":
        record["failure"] = (
            "Expected DOCUMENT role for certification "
            f"but received {lifecycle.role!r}."
        )
        return record

    # Existing healthy runtime documents do not need an
    # identity admission decision.
    if lifecycle.lifecycle == "UNCHANGED_RUNTIME":
        record["identity"] = {
            "verdict": "ALREADY_RUNTIME",
            "layer": "runtime_path",
            "confidence": 1.0,
            "matched_path": str(path),
            "reason": (
                "Document is already represented under "
                "its current runtime path."
            ),
        }

        record["status"] = "PASS"
        return record

    digest = (
        lifecycle.sha256
        or file_sha_or_none(path)
    )

    text = get_candidate_text(
        path=path,
        legacy_text=legacy_text,
    )

    fingerprint = build_fingerprint(
        path=path,
        sha256=digest,
        text=text,
    )

    record["fingerprint"] = asdict(
        fingerprint
    )

    result = resolver.resolve(
        fingerprint=fingerprint,
        candidate_text=text,
        maximum_shortlist=shortlist,
    )

    record["identity"] = asdict(
        result
    )

    # --------------------------------------------------------
    # Certification rules.
    #
    # These rules do NOT demand DISTINCT.
    #
    # A true duplicate is a valid identity result if the
    # matching runtime path is supplied.
    # --------------------------------------------------------

    verdict = result.verdict

    if verdict in {
        IdentityVerdict.EXACT_DUPLICATE,
        IdentityVerdict.CONTENT_DUPLICATE,
        IdentityVerdict.NEAR_DUPLICATE,
        IdentityVerdict.STRUCTURAL_MATCH,
    }:
        if not result.matched_path:
            record["failure"] = (
                f"{verdict.value} was returned without "
                "a matched runtime path."
            )
            return record

        record["status"] = "PASS"
        return record

    if verdict == IdentityVerdict.DISTINCT:
        if (
            fingerprint
            .normalized_content_sha256
            is None
        ):
            record["failure"] = (
                "DISTINCT was returned without a "
                "normalized-content fingerprint."
            )
            return record

        record["status"] = "PASS"
        return record

    if verdict == IdentityVerdict.UNRESOLVED:
        # UNRESOLVED is acceptable only when content truly
        # could not be obtained. It is not a false DISTINCT.
        if (
            fingerprint
            .normalized_content_sha256
            is None
        ):
            record["status"] = "PASS_WITH_REVIEW"
            return record

        record["failure"] = (
            "UNRESOLVED despite available normalized text."
        )
        return record

    record["failure"] = (
        f"Unexpected identity verdict: "
        f"{verdict.value}"
    )

    return record


def print_canary(
    record: dict,
):
    print()
    print(
        f"--- {record['name']} ---"
    )

    print(
        "physical ................. "
        + (
            "PASS"
            if record["physical"]
            else "FAIL"
        )
    )

    classification = record.get(
        "classification"
    )

    if classification:
        print(
            "lifecycle ................ "
            f"{classification['lifecycle']}"
        )

        print(
            "role ..................... "
            f"{classification['role']}"
        )

        print(
            "handler .................. "
            f"{classification['handler']}"
        )

    fingerprint = record.get(
        "fingerprint"
    )

    if fingerprint:
        print(
            "normalized text .......... "
            + (
                "AVAILABLE"
                if fingerprint[
                    "normalized_content_sha256"
                ]
                else "UNAVAILABLE"
            )
        )

        print(
            "normalized chars ......... "
            f"{fingerprint['normalized_chars'] or 0:,}"
        )

    identity = record.get(
        "identity"
    )

    if identity:
        verdict = identity.get(
            "verdict"
        )

        if hasattr(verdict, "value"):
            verdict = verdict.value

        print(
            "identity verdict .......... "
            f"{verdict}"
        )

        print(
            "identity layer ............ "
            f"{identity.get('layer')}"
        )

        confidence = identity.get(
            "confidence"
        )

        if confidence is not None:
            print(
                "confidence ................ "
                f"{float(confidence):.3f}"
            )

        print(
            "matched path .............. "
            f"{identity.get('matched_path') or '-'}"
        )

    print(
        "certification .............. "
        f"{record['status']}"
    )

    if record.get("failure"):
        print(
            "failure ................... "
            f"{record['failure']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Genesis AS1 Pack 2-R2 bounded "
            "real-corpus identity certification."
        )
    )

    parser.add_argument(
        "--runtime-db",
        type=Path,
        default=DEFAULT_RUNTIME_DB,
    )

    parser.add_argument(
        "--legacy-db",
        type=Path,
        default=DEFAULT_LEGACY_DB,
    )

    parser.add_argument(
        "--shortlist",
        type=int,
        default=6,
        help=(
            "Maximum runtime candidates whose identity "
            "may be investigated per canary."
        ),
    )

    parser.add_argument(
        "--max-runtime-content-chars",
        type=int,
        default=MAX_RUNTIME_CONTENT_CHARS,
    )

    parser.add_argument(
        "--json",
        type=Path,
        default=None,
    )

    args = parser.parse_args()

    started = time.monotonic()

    runtime = open_ro(
        args.runtime_db
    )

    legacy = open_ro(
        args.legacy_db
    )

    try:
        # ----------------------------------------------------
        # Load only metadata/index structures once.
        # ----------------------------------------------------

        runtime_by_path, runtime_by_sha = (
            load_runtime_documents(runtime)
        )

        classifications = (
            load_classifications(runtime)
        )

        discovered = (
            load_discovered(runtime)
        )

        catalog_by_path, catalog_by_sha = (
            load_catalog_documents(runtime)
        )

        legacy_by_path, legacy_by_sha = (
            load_legacy_documents(
                legacy,
                DEFAULT_KNOWLEDGE_ROOT,
            )
        )

        known_sha = build_known_sha_index(
            runtime_by_sha,
            catalog_by_sha,
            legacy_by_sha,
        )

        runtime_identity = (
            BoundedRuntimeIdentityIndex(
                runtime,
                max_content_chars=(
                    args.max_runtime_content_chars
                ),
            )
        )

        resolver = (
            LayeredIdentityResolver(
                runtime_identity
            )
        )

        legacy_text = (
            LegacyTextProvider(
                legacy
            )
        )

        results = []

        status_counts = Counter()
        verdict_counts = Counter()

        for name, path in CANARIES:
            result = certify_one(
                name=name,
                path=path,
                resolver=resolver,
                legacy_text=legacy_text,
                shortlist=args.shortlist,
                runtime_by_path=runtime_by_path,
                classifications=classifications,
                discovered=discovered,
                catalog_by_path=catalog_by_path,
                legacy_by_path=legacy_by_path,
                known_sha=known_sha,
            )

            results.append(result)

            status_counts[
                result["status"]
            ] += 1

            identity = result.get(
                "identity"
            )

            if identity:
                verdict = identity.get(
                    "verdict"
                )

                if hasattr(
                    verdict,
                    "value",
                ):
                    verdict = verdict.value

                if verdict:
                    verdict_counts[
                        str(verdict)
                    ] += 1

        elapsed = (
            time.monotonic()
            - started
        )

        print()
        print("=" * 76)
        print(" GENESIS AS1")
        print(
            " PACK 2-R2 — BOUNDED "
            "REAL-CORPUS IDENTITY CERTIFICATION"
        )
        print("=" * 76)

        print()
        print(
            "Real corpus canaries ......... "
            f"{len(results)}"
        )

        print(
            "Runtime identity metadata .... "
            f"{len(runtime_identity.rows):,}"
        )

        print(
            "Shortlist cap / canary ........ "
            f"{args.shortlist}"
        )

        print(
            "Runtime text safety cap ....... "
            f"{args.max_runtime_content_chars:,} chars"
        )

        print()
        print("Certification status:")

        for status, count in (
            status_counts.most_common()
        ):
            print(
                f"  {status:24} "
                f"{count:,}"
            )

        print()
        print("Identity verdicts:")

        for verdict, count in (
            verdict_counts.most_common()
        ):
            print(
                f"  {verdict:24} "
                f"{count:,}"
            )

        for record in results:
            print_canary(record)

        print()
        print(
            "Oversized runtime contents "
            "skipped ..................... "
            f"{runtime_identity.skipped_large_content:,}"
        )

        hard_failures = (
            status_counts.get(
                "FAIL",
                0,
            )
        )

        certification = (
            "PASS"
            if hard_failures == 0
            else "FAIL"
        )

        print()
        print("Safety:")
        print(
            "  Corpus recursion ............ 0"
        )
        print(
            "  Database writes ............. 0"
        )
        print(
            "  Source mutations ............ 0"
        )
        print(
            "  Runtime mutations ........... 0"
        )

        print()
        print(
            "PACK 2-R2 STATUS .............. "
            f"{certification}"
        )

        print(
            "Elapsed ....................... "
            f"{elapsed:.2f}s"
        )

        if args.json:
            payload = {
                "schema":
                    "genesis-as1-pack2-r2-v1",

                "read_only": True,

                "recursive_corpus_scan":
                    False,

                "shortlist_cap":
                    args.shortlist,

                "runtime_content_char_cap":
                    args.max_runtime_content_chars,

                "runtime_identity_metadata":
                    len(runtime_identity.rows),

                "status_counts":
                    dict(status_counts),

                "verdict_counts":
                    dict(verdict_counts),

                "oversized_runtime_contents_skipped":
                    runtime_identity
                    .skipped_large_content,

                "results":
                    results,

                "status":
                    certification,

                "elapsed_seconds":
                    elapsed,
            }

            args.json.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            args.json.write_text(
                json.dumps(
                    payload,
                    indent=2,
                    sort_keys=True,
                    default=str,
                ),
                encoding="utf-8",
            )

            print()
            print(
                f"JSON report: "
                f"{args.json}"
            )

        print()
        print("=" * 76)
        print(" GENESIS AS1 PACK 2-R2 COMPLETE")
        print("=" * 76)

        return (
            0
            if certification == "PASS"
            else 1
        )

    finally:
        runtime.close()
        legacy.close()


if __name__ == "__main__":
    raise SystemExit(main())
