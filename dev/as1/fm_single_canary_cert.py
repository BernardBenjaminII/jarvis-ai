from __future__ import annotations

import argparse
import json
import time
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
    LegacyTextProvider,
    build_fingerprint,
    get_candidate_text,
    sha256_file,
)

from dev.as1.targeted_identity import (
    TargetedRuntimeIdentityResolver,
)


CANARY = (
    DEFAULT_KNOWLEDGE_ROOT
    / "military"
    / "doctrine"
    / "US_Army_FM_3-06.11_Urban_Terrain.pdf"
)


def safe_sha(path: Path) -> str | None:
    try:
        return sha256_file(path)
    except OSError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Genesis AS1 Pack 2-R2-R2 single real-corpus "
            "identity certification for FM 3-06.11."
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
        "--max-candidates",
        type=int,
        default=6,
    )

    parser.add_argument(
        "--max-runtime-content-chars",
        type=int,
        default=4_000_000,
    )

    parser.add_argument(
        "--json",
        type=Path,
        default=None,
    )

    args = parser.parse_args()

    started = time.monotonic()

    print()
    print("=== 1. PHYSICAL CANARY ===")
    print("path:", CANARY)

    if not CANARY.is_file():
        print("physical: FAIL")
        print("reason  : FM 3-06.11 file is missing")
        return 2

    print("physical: PASS")

    runtime = open_ro(args.runtime_db)
    legacy = open_ro(args.legacy_db)

    try:
        print()
        print("=== 2. LOAD CANONICAL METADATA ===")

        runtime_by_path, runtime_by_sha = (
            load_runtime_documents(runtime)
        )

        classifications = load_classifications(runtime)
        discovered = load_discovered(runtime)

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

        print(
            "runtime paths              :",
            f"{len(runtime_by_path):,}",
        )
        print(
            "classifications            :",
            f"{len(classifications):,}",
        )
        print(
            "discovered                 :",
            f"{len(discovered):,}",
        )
        print(
            "catalog documents          :",
            f"{len(catalog_by_path):,}",
        )
        print(
            "legacy documents           :",
            f"{len(legacy_by_path):,}",
        )

        print()
        print("=== 3. PACK 1B LIFECYCLE + ROUTE ===")

        lifecycle = classify_file(
            path=CANARY,
            verify_existing=False,
            runtime_by_path=runtime_by_path,
            classifications=classifications,
            discovered=discovered,
            catalog_by_path=catalog_by_path,
            legacy_by_path=legacy_by_path,
            known_sha=known_sha,
        )

        print("lifecycle      :", lifecycle.lifecycle)
        print("role           :", lifecycle.role)
        print("handler        :", lifecycle.handler)
        print("text admissible:", lifecycle.text_admissible)
        print("reason         :", lifecycle.reason)

        if lifecycle.role != "DOCUMENT":
            print()
            print("CERTIFICATION: FAIL")
            print(
                "Reason: FM canary did not route as DOCUMENT."
            )
            return 3

        print()
        print("=== 4. CANDIDATE TEXT + FINGERPRINT ===")

        legacy_text = LegacyTextProvider(legacy)

        candidate_text = get_candidate_text(
            path=CANARY,
            legacy_text=legacy_text,
        )

        if candidate_text:
            print(
                "candidate text             : AVAILABLE"
            )
            print(
                "candidate raw chars        :",
                f"{len(candidate_text):,}",
            )
        else:
            print(
                "candidate text             : UNAVAILABLE"
            )

        digest = (
            lifecycle.sha256
            or safe_sha(CANARY)
        )

        fingerprint = build_fingerprint(
            path=CANARY,
            sha256=digest,
            text=candidate_text,
        )

        print(
            "sha256                     :",
            fingerprint.sha256 or "-",
        )
        print(
            "normalized content sha     :",
            fingerprint.normalized_content_sha256 or "-",
        )
        print(
            "normalized chars           :",
            (
                f"{fingerprint.normalized_chars:,}"
                if fingerprint.normalized_chars is not None
                else "-"
            ),
        )
        print(
            "simhash64                  :",
            (
                fingerprint.simhash64
                if fingerprint.simhash64 is not None
                else "-"
            ),
        )
        print(
            "normalized title           :",
            fingerprint.normalized_title,
        )

        print()
        print("=== 5. TARGETED SQL IDENTITY ===")

        resolver = TargetedRuntimeIdentityResolver(
            runtime,
            maximum_candidates=args.max_candidates,
            maximum_content_chars=(
                args.max_runtime_content_chars
            ),
        )

        exact = resolver.exact_sha(
            fingerprint.sha256
        )

        if exact is not None:
            print("exact SHA SQL hit         : YES")
            print(
                "exact matched path         :",
                exact.file_path,
            )
        else:
            print("exact SHA SQL hit         : NO")

        shortlist = resolver.candidates(
            fingerprint
        )

        print(
            "bounded shortlist count    :",
            len(shortlist),
        )

        for index, row in enumerate(
            shortlist,
            start=1,
        ):
            print()
            print(f"candidate #{index}")
            print("  id            :", row.id)
            print("  title         :", row.title)
            print("  content chars :", row.content_chars)
            print("  file path     :", row.file_path)

        print()
        print("=== 6. IDENTITY VERDICT ===")

        result = resolver.resolve(
            fingerprint=fingerprint,
            candidate_text=candidate_text,
        )

        print(
            "verdict                    :",
            result.verdict.value,
        )
        print(
            "layer                      :",
            result.layer,
        )
        print(
            "confidence                 :",
            f"{result.confidence:.3f}",
        )
        print(
            "matched path               :",
            result.matched_path or "-",
        )
        print(
            "reason                     :",
            result.reason,
        )
        print(
            "exact sha match            :",
            result.exact_sha_match,
        )
        print(
            "content hash match         :",
            result.content_hash_match,
        )
        print(
            "simhash distance           :",
            (
                result.simhash_distance
                if result.simhash_distance is not None
                else "-"
            ),
        )
        print(
            "structural score           :",
            (
                f"{result.structural_score:.3f}"
                if result.structural_score is not None
                else "-"
            ),
        )

        print()
        print("=== 7. CERTIFICATION RULES ===")

        status = "FAIL"
        certification_reason = ""

        if result.verdict in {
            IdentityVerdict.EXACT_DUPLICATE,
            IdentityVerdict.CONTENT_DUPLICATE,
            IdentityVerdict.NEAR_DUPLICATE,
            IdentityVerdict.STRUCTURAL_MATCH,
        }:
            if result.matched_path:
                status = "PASS"
                certification_reason = (
                    "Identity collision/variant was proven "
                    "and a runtime path was identified."
                )
            else:
                certification_reason = (
                    "Duplicate/variant verdict lacked a "
                    "matched runtime path."
                )

        elif result.verdict == IdentityVerdict.UNRESOLVED:
            status = "PASS_WITH_REVIEW"
            certification_reason = (
                "Bounded targeted SQL found no proven "
                "identity collision. This mode correctly "
                "refuses to claim global DISTINCT."
            )

        elif result.verdict == IdentityVerdict.DISTINCT:
            status = "FAIL"
            certification_reason = (
                "Targeted SQL mode must not claim global "
                "DISTINCT without the persistent fingerprint "
                "index."
            )

        else:
            certification_reason = (
                "Unexpected identity verdict."
            )

        print("certification status       :", status)
        print("certification reason       :", certification_reason)

        elapsed = time.monotonic() - started

        print()
        print("=== 8. SAFETY ===")
        print("recursive corpus scan      : 0")
        print("whole-runtime Python index : 0")
        print("database writes            : 0")
        print("source mutations           : 0")
        print("runtime mutations          : 0")
        print(
            "runtime content rows loaded:",
            resolver.content_rows_loaded,
        )
        print(
            "runtime content rows skipped:",
            resolver.content_rows_skipped,
        )
        print(
            "elapsed seconds            :",
            f"{elapsed:.2f}",
        )

        payload = {
            "schema":
                "genesis-as1-pack2-r2-r2-v1",

            "read_only":
                True,

            "canary":
                str(CANARY),

            "lifecycle":
                asdict(lifecycle),

            "fingerprint":
                asdict(fingerprint),

            "shortlist": [
                {
                    "id": row.id,
                    "file_path": row.file_path,
                    "sha256": row.sha256,
                    "title": row.title,
                    "content_chars": row.content_chars,
                }
                for row in shortlist
            ],

            "identity":
                asdict(result),

            "certification_status":
                status,

            "certification_reason":
                certification_reason,

            "runtime_content_rows_loaded":
                resolver.content_rows_loaded,

            "runtime_content_rows_skipped":
                resolver.content_rows_skipped,

            "elapsed_seconds":
                elapsed,
        }

        if args.json:
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
                "JSON report                :",
                args.json,
            )

        print()
        print("============================================================")

        if status == "PASS":
            print(
                " GENESIS AS1 PACK 2-R2-R2 CERTIFIED"
            )
        elif status == "PASS_WITH_REVIEW":
            print(
                " GENESIS AS1 PACK 2-R2-R2 CERTIFIED WITH REVIEW"
            )
        else:
            print(
                " GENESIS AS1 PACK 2-R2-R2 FAILED"
            )

        print(" READ ONLY — NO DATABASE WRITES")
        print("============================================================")

        return (
            0
            if status in {
                "PASS",
                "PASS_WITH_REVIEW",
            }
            else 1
        )

    finally:
        runtime.close()
        legacy.close()


if __name__ == "__main__":
    raise SystemExit(main())
