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
    physical_files,
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


CANARY = (
    DEFAULT_KNOWLEDGE_ROOT
    / "military"
    / "doctrine"
    / "US_Army_FM_3-06.11_Urban_Terrain.pdf"
)


IDENTITY_LIFECYCLES = {
    "BRIDGE_TO_CANONICAL_DISCOVERY",
    "DISCOVER",
    "CHANGED_RUNTIME",
}


IDENTITY_ROLES = {
    "DOCUMENT",
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Genesis AS1 Pack 2 bounded "
            "layered-identity audit."
        )
    )

    parser.add_argument(
        "--knowledge-root",
        type=Path,
        default=DEFAULT_KNOWLEDGE_ROOT,
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
        "--limit",
        type=int,
        default=250,
        help=(
            "Maximum actionable document identities "
            "to resolve. The FM canary is always included."
        ),
    )

    parser.add_argument(
        "--shortlist",
        type=int,
        default=40,
        help=(
            "Maximum runtime content candidates fetched "
            "per identity resolution."
        ),
    )

    parser.add_argument(
        "--show",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--json",
        type=Path,
        default=None,
    )

    args = parser.parse_args()

    root = args.knowledge_root.resolve()

    started = time.monotonic()

    runtime = open_ro(args.runtime_db)
    legacy = open_ro(args.legacy_db)

    try:
        runtime_by_path, runtime_by_sha = (
            load_runtime_documents(runtime)
        )

        classifications = (
            load_classifications(runtime)
        )

        discovered = load_discovered(runtime)

        catalog_by_path, catalog_by_sha = (
            load_catalog_documents(runtime)
        )

        legacy_by_path, legacy_by_sha = (
            load_legacy_documents(
                legacy,
                root,
            )
        )

        known_sha = build_known_sha_index(
            runtime_by_sha,
            catalog_by_sha,
            legacy_by_sha,
        )

        runtime_identity = (
            RuntimeIdentityIndex(runtime)
        )

        resolver = (
            LayeredIdentityResolver(
                runtime_identity
            )
        )

        legacy_text = LegacyTextProvider(
            legacy
        )

        results = []

        verdict_counts = Counter()
        layer_counts = Counter()

        examined = 0
        eligible = 0

        canary_result = None

        for path in physical_files(root):
            item = classify_file(
                path=path,
                verify_existing=False,
                runtime_by_path=runtime_by_path,
                classifications=classifications,
                discovered=discovered,
                catalog_by_path=catalog_by_path,
                legacy_by_path=legacy_by_path,
                known_sha=known_sha,
            )

            if (
                item.lifecycle
                not in IDENTITY_LIFECYCLES
            ):
                continue

            if item.role not in IDENTITY_ROLES:
                continue

            eligible += 1

            try:
                is_canary = (
                    path.resolve()
                    == CANARY.resolve()
                )
            except OSError:
                is_canary = False

            if (
                examined >= args.limit
                and not is_canary
            ):
                continue

            examined += 1

            digest = item.sha256

            if not digest:
                try:
                    digest = sha256_file(path)
                except OSError:
                    digest = None

            text = get_candidate_text(
                path=path,
                legacy_text=legacy_text,
            )

            fingerprint = build_fingerprint(
                path=path,
                sha256=digest,
                text=text,
            )

            result = resolver.resolve(
                fingerprint=fingerprint,
                candidate_text=text,
                maximum_shortlist=args.shortlist,
            )

            verdict_counts[
                result.verdict.value
            ] += 1

            layer_counts[
                result.layer
            ] += 1

            record = {
                "lifecycle":
                    item.lifecycle,

                "role":
                    item.role,

                "handler":
                    item.handler,

                "fingerprint":
                    asdict(fingerprint),

                "identity":
                    asdict(result),
            }

            results.append(record)

            if is_canary:
                canary_result = record

        elapsed = (
            time.monotonic()
            - started
        )

        print()
        print("=" * 76)
        print(" GENESIS AS1")
        print(
            " PACK 2 — LAYERED IDENTITY "
            "RESOLVER AUDIT"
        )
        print("=" * 76)

        print()
        print(
            f"Identity-eligible documents .... "
            f"{eligible:,}"
        )

        print(
            f"Documents resolved this run .... "
            f"{examined:,}"
        )

        print(
            f"Runtime corpus candidates ...... "
            f"{len(runtime_identity.rows):,}"
        )

        print()
        print("Identity verdicts:")

        order = (
            IdentityVerdict.EXACT_DUPLICATE,
            IdentityVerdict.CONTENT_DUPLICATE,
            IdentityVerdict.NEAR_DUPLICATE,
            IdentityVerdict.STRUCTURAL_MATCH,
            IdentityVerdict.DISTINCT,
            IdentityVerdict.REVIEW,
            IdentityVerdict.UNRESOLVED,
        )

        for verdict in order:
            print(
                f"  {verdict.value:24} "
                f"{verdict_counts.get(verdict.value, 0):,}"
            )

        print()
        print("Decision layers:")

        for layer, count in (
            layer_counts.most_common()
        ):
            print(
                f"  {layer:24} "
                f"{count:,}"
            )

        if canary_result:
            identity = (
                canary_result["identity"]
            )

            fingerprint = (
                canary_result["fingerprint"]
            )

            print()
            print("FM 3-06.11 identity canary:")

            print(
                f"  lifecycle ............. "
                f"{canary_result['lifecycle']}"
            )

            print(
                f"  role .................. "
                f"{canary_result['role']}"
            )

            print(
                f"  normalized text ....... "
                + (
                    "AVAILABLE"
                    if fingerprint[
                        "normalized_content_sha256"
                    ]
                    else "UNAVAILABLE"
                )
            )

            print(
                f"  verdict ............... "
                f"{identity['verdict']}"
            )

            print(
                f"  layer ................. "
                f"{identity['layer']}"
            )

            print(
                f"  confidence ............ "
                f"{identity['confidence']:.3f}"
            )

            print(
                f"  matched path .......... "
                f"{identity['matched_path'] or '-'}"
            )

            print(
                f"  reason ................ "
                f"{identity['reason']}"
            )

        else:
            print()
            print("FM 3-06.11 identity canary:")
            print("  result ................ MISSING")

        if args.show > 0:
            print()
            print(
                "First identity decisions:"
            )

            for record in results[
                :args.show
            ]:
                identity = record[
                    "identity"
                ]

                fingerprint = record[
                    "fingerprint"
                ]

                print()
                print(
                    f"[{identity['verdict']}]"
                )

                print(
                    f"  candidate: "
                    f"{fingerprint['path']}"
                )

                print(
                    f"  lifecycle: "
                    f"{record['lifecycle']}"
                )

                print(
                    f"  layer    : "
                    f"{identity['layer']}"
                )

                print(
                    f"  match    : "
                    f"{identity['matched_path'] or '-'}"
                )

                print(
                    f"  reason   : "
                    f"{identity['reason']}"
                )

        if args.json:
            payload = {
                "schema":
                    "genesis-as1-pack2-identity-v1",

                "read_only": True,

                "knowledge_root":
                    str(root),

                "identity_eligible":
                    eligible,

                "resolved":
                    examined,

                "runtime_candidates":
                    len(runtime_identity.rows),

                "verdict_counts":
                    dict(verdict_counts),

                "layer_counts":
                    dict(layer_counts),

                "canary":
                    canary_result,

                "results":
                    results,

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
                f"JSON report: {args.json}"
            )

        print()
        print("Safety:")
        print("  Database writes ............. 0")
        print("  Source mutations ............ 0")
        print("  Runtime mutations ........... 0")

        print()
        print(
            f"Elapsed ........................ "
            f"{elapsed:.2f}s"
        )

        print()
        print("=" * 76)
        print(" GENESIS AS1 PACK 2 COMPLETE")
        print("=" * 76)

        return 0

    finally:
        runtime.close()
        legacy.close()


if __name__ == "__main__":
    raise SystemExit(main())
