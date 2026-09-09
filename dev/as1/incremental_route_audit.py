from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from dev.as1.object_router import route_object


DEFAULT_KNOWLEDGE_ROOT = Path(
    "/media/abdullah/JARVISDATA/Knowledge"
)

DEFAULT_RUNTIME_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

DEFAULT_LEGACY_DB = Path(
    "/media/abdullah/JARVISDATA/Knowledge/.jarvis/catalog.sqlite"
)

CANARY = (
    DEFAULT_KNOWLEDGE_ROOT
    / "military"
    / "doctrine"
    / "US_Army_FM_3-06.11_Urban_Terrain.pdf"
)


def ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn, table: str) -> bool:
    return (
        conn.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type IN ('table','view')
              AND name=?
            """,
            (table,),
        ).fetchone()
        is not None
    )


def load_runtime_paths(conn) -> set[str]:
    if not table_exists(conn, "runtime_documents"):
        return set()

    return {
        str(row["file_path"])
        for row in conn.execute(
            """
            SELECT file_path
            FROM runtime_documents
            WHERE file_path IS NOT NULL
            """
        )
    }


def load_classifications(conn) -> dict[str, dict]:
    if not table_exists(conn, "knowledge_classifications"):
        return {}

    result = {}

    for row in conn.execute(
        """
        SELECT
            file_path,
            action,
            knowledge_type,
            domain,
            subject,
            reason
        FROM knowledge_classifications
        WHERE file_path IS NOT NULL
        """
    ):
        result[str(row["file_path"])] = dict(row)

    return result


def load_discovered_paths(conn) -> set[str]:
    if not table_exists(conn, "discovered_files"):
        return set()

    cols = {
        str(r["name"])
        for r in conn.execute(
            'PRAGMA table_info("discovered_files")'
        )
    }

    path_col = next(
        (
            c
            for c in (
                "file_path",
                "path",
                "absolute_path",
                "document_path",
                "source_path",
                "local_path",
            )
            if c in cols
        ),
        None,
    )

    if not path_col:
        return set()

    return {
        str(row[0])
        for row in conn.execute(
            f'''
            SELECT "{path_col}"
            FROM discovered_files
            WHERE "{path_col}" IS NOT NULL
            '''
        )
    }


def load_catalog_paths(conn) -> set[str]:
    if not table_exists(conn, "catalog_documents"):
        return set()

    return {
        str(row["file_path"])
        for row in conn.execute(
            """
            SELECT file_path
            FROM catalog_documents
            WHERE file_path IS NOT NULL
            """
        )
    }


def load_legacy_paths(
    conn,
    knowledge_root: Path,
) -> set[str]:
    if not table_exists(conn, "documents"):
        return set()

    cols = {
        str(r["name"])
        for r in conn.execute(
            'PRAGMA table_info("documents")'
        )
    }

    path_col = next(
        (
            c
            for c in (
                "path",
                "file_path",
                "document_path",
                "relative_path",
            )
            if c in cols
        ),
        None,
    )

    if not path_col:
        return set()

    result = set()

    for row in conn.execute(
        f'''
        SELECT "{path_col}"
        FROM documents
        WHERE "{path_col}" IS NOT NULL
        '''
    ):
        p = Path(str(row[0]))

        if not p.is_absolute():
            p = knowledge_root / p

        result.add(str(p))

    return result


def candidate_paths(
    *,
    runtime_paths: set[str],
    classifications: dict[str, dict],
    discovered_paths: set[str],
    catalog_paths: set[str],
    legacy_paths: set[str],
) -> list[tuple[str, str]]:
    """
    Return only paths requiring routing attention.

    Existing healthy runtime objects are deliberately excluded.
    """

    out: dict[str, str] = {}

    # Classified but not runtime.
    for path, classification in classifications.items():
        if path in runtime_paths:
            continue

        action = str(
            classification.get("action") or ""
        ).casefold()

        if action == "candidate":
            out[path] = "ADMIT_CLASSIFIED"
        elif action == "review":
            out[path] = "REVIEW"
        elif action == "ignore":
            out[path] = "IGNORE"
        else:
            out[path] = "REVIEW"

    # Discovered but not classified/runtime.
    for path in discovered_paths:
        if path in runtime_paths:
            continue
        if path in classifications:
            continue

        out.setdefault(path, "CLASSIFY")

    # Known legacy/catalog objects never admitted into
    # canonical discovery.
    for path in catalog_paths | legacy_paths:
        if path in runtime_paths:
            continue
        if path in classifications:
            continue
        if path in discovered_paths:
            continue

        out.setdefault(
            path,
            "BRIDGE_TO_CANONICAL_DISCOVERY",
        )

    return sorted(
        out.items(),
        key=lambda item: item[0].casefold(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Genesis AS1 Pack 1A-R1 incremental "
            "object-routing audit."
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
        "--show",
        type=int,
        default=15,
    )

    parser.add_argument(
        "--json",
        type=Path,
        default=None,
    )

    args = parser.parse_args()

    root = args.knowledge_root.resolve()

    runtime = ro(args.runtime_db)
    legacy = ro(args.legacy_db)

    try:
        runtime_paths = load_runtime_paths(runtime)
        classifications = load_classifications(runtime)
        discovered_paths = load_discovered_paths(runtime)
        catalog_paths = load_catalog_paths(runtime)
        legacy_paths = load_legacy_paths(
            legacy,
            root,
        )

        candidates = candidate_paths(
            runtime_paths=runtime_paths,
            classifications=classifications,
            discovered_paths=discovered_paths,
            catalog_paths=catalog_paths,
            legacy_paths=legacy_paths,
        )

        lifecycle_counts = Counter()
        role_counts = Counter()
        handler_counts = Counter()
        combined_counts = Counter()
        missing_physical = 0
        examples = defaultdict(list)
        canary = None

        for raw_path, lifecycle in candidates:
            lifecycle_counts[lifecycle] += 1

            path = Path(raw_path)

            if not path.is_file():
                missing_physical += 1
                combined_counts[
                    f"{lifecycle}+MISSING_PHYSICAL"
                ] += 1
                continue

            decision = route_object(path)

            role = decision.role.value
            handler = decision.handler

            role_counts[role] += 1
            handler_counts[handler] += 1

            combined = f"{lifecycle}+{role}"
            combined_counts[combined] += 1

            if len(examples[combined]) < args.show:
                examples[combined].append(
                    {
                        "path": str(path),
                        "handler": handler,
                        "reason": decision.reason,
                        "text_admissible":
                            decision.admissible_to_text_pipeline,
                    }
                )

            try:
                is_canary = (
                    path.resolve()
                    == CANARY.resolve()
                )
            except OSError:
                is_canary = False

            if is_canary:
                canary = {
                    "path": str(path),
                    "lifecycle": lifecycle,
                    "role": role,
                    "handler": handler,
                    "text_admissible":
                        decision.admissible_to_text_pipeline,
                    "reason": decision.reason,
                }

        print()
        print("=" * 72)
        print(" GENESIS AS1")
        print(" PACK 1A-R1 — INCREMENTAL ROUTING AUDIT")
        print("=" * 72)

        print()
        print(
            f"Runtime paths skipped ........ "
            f"{len(runtime_paths):,}"
        )
        print(
            f"Actionable paths routed ...... "
            f"{len(candidates):,}"
        )
        print(
            f"Missing physical paths ....... "
            f"{missing_physical:,}"
        )

        print()
        print("Lifecycle population:")

        for name, count in lifecycle_counts.most_common():
            print(
                f"  {name:34} {count:,}"
            )

        print()
        print("Object roles:")

        for name, count in role_counts.most_common():
            print(
                f"  {name:34} {count:,}"
            )

        print()
        print("Combined lifecycle + role:")

        for name, count in combined_counts.most_common():
            print(
                f"  {name:44} {count:,}"
            )

        print()
        print("Handlers:")

        for name, count in handler_counts.most_common():
            print(
                f"  {name:34} {count:,}"
            )

        if canary:
            print()
            print("FM 3-06.11 canary:")
            print("  physical .............. PASS")
            print(
                f"  lifecycle ............. "
                f"{canary['lifecycle']}"
            )
            print(
                f"  role .................. "
                f"{canary['role']}"
            )
            print(
                f"  handler ............... "
                f"{canary['handler']}"
            )
            print(
                f"  text admissible ....... "
                f"{str(canary['text_admissible']).upper()}"
            )
        else:
            print()
            print("FM 3-06.11 canary:")
            print("  found ................. NO")

        if args.show > 0:
            print()
            print("Actionable routing examples:")

            for key in sorted(examples):
                print()
                print(f"--- {key} ---")

                for item in examples[key]:
                    print(item["path"])
                    print(
                        f"  handler: {item['handler']}"
                    )
                    print(
                        f"  text   : "
                        f"{item['text_admissible']}"
                    )

        if args.json:
            payload = {
                "schema":
                    "genesis-as1-incremental-route-audit-v1",
                "runtime_paths_skipped":
                    len(runtime_paths),
                "actionable_paths":
                    len(candidates),
                "missing_physical":
                    missing_physical,
                "lifecycle_counts":
                    dict(lifecycle_counts),
                "role_counts":
                    dict(role_counts),
                "combined_counts":
                    dict(combined_counts),
                "handler_counts":
                    dict(handler_counts),
                "canary":
                    canary,
                "examples":
                    dict(examples),
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
                ),
                encoding="utf-8",
            )

            print()
            print(f"JSON report: {args.json}")

        print()
        print("Safety:")
        print("  Database writes ............. 0")
        print("  Source mutations ............ 0")
        print("  Runtime mutations ........... 0")

        print()
        print("=" * 72)
        print(" PACK 1A-R1 COMPLETE")
        print("=" * 72)

        return 0

    finally:
        runtime.close()
        legacy.close()


if __name__ == "__main__":
    raise SystemExit(main())
