from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

from dev.as1.object_router import (
    ObjectRole,
    route_object,
)


DEFAULT_KNOWLEDGE_ROOT = Path(
    "/media/abdullah/JARVISDATA/Knowledge"
)

CANARY = (
    DEFAULT_KNOWLEDGE_ROOT
    / "military"
    / "doctrine"
    / "US_Army_FM_3-06.11_Urban_Terrain.pdf"
)


def walk_files(root: Path):
    for directory, dirs, files in os.walk(root):
        base = Path(directory)

        # Do not descend into JARVIS/system internals.
        dirs[:] = [
            name
            for name in dirs
            if name not in {
                ".jarvis",
                ".git",
                ".venv",
                "venv",
                "__pycache__",
                "node_modules",
            }
        ]

        for name in files:
            path = base / name

            try:
                if path.is_file():
                    yield path
            except OSError:
                continue


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Genesis AS1 Pack 1A corpus type-routing audit."
        )
    )

    parser.add_argument(
        "--knowledge-root",
        type=Path,
        default=DEFAULT_KNOWLEDGE_ROOT,
    )

    parser.add_argument(
        "--show",
        type=int,
        default=20,
        help=(
            "Show this many examples for each non-document "
            "role."
        ),
    )

    parser.add_argument(
        "--json",
        type=Path,
        default=None,
    )

    args = parser.parse_args()

    root = args.knowledge_root.resolve()

    if not root.is_dir():
        print(
            f"ERROR: Knowledge root missing: {root}"
        )
        return 2

    role_counts = Counter()
    handler_counts = Counter()
    extension_roles = defaultdict(Counter)
    examples = defaultdict(list)

    total = 0
    text_admissible = 0
    canary = None

    for path in walk_files(root):
        total += 1

        decision = route_object(path)

        role_counts[decision.role.value] += 1
        handler_counts[decision.handler] += 1

        suffix = path.suffix.casefold() or "<none>"

        extension_roles[suffix][
            decision.role.value
        ] += 1

        if decision.admissible_to_text_pipeline:
            text_admissible += 1

        if (
            len(examples[decision.role.value])
            < args.show
        ):
            examples[decision.role.value].append(
                {
                    "path": str(path),
                    "handler": decision.handler,
                    "reason": decision.reason,
                }
            )

        try:
            is_canary = (
                path.resolve() == CANARY.resolve()
            )
        except OSError:
            is_canary = False

        if is_canary:
            canary = {
                "path": str(path),
                "role": decision.role.value,
                "handler": decision.handler,
                "text_admissible":
                    decision.admissible_to_text_pipeline,
                "reason": decision.reason,
            }

    print()
    print("=" * 72)
    print(" GENESIS AS1")
    print(" PACK 1A — CORPUS TYPE ROUTING AUDIT")
    print("=" * 72)

    print()
    print(f"Physical files routed ........ {total:,}")
    print(
        f"Text-pipeline admissible ..... "
        f"{text_admissible:,}"
    )

    print()
    print("Object roles:")

    role_order = (
        ObjectRole.DOCUMENT,
        ObjectRole.DATASET,
        ObjectRole.SOURCE_CODE,
        ObjectRole.WEB_ARCHIVE,
        ObjectRole.MEDIA,
        ObjectRole.METADATA,
        ObjectRole.INTERNAL,
        ObjectRole.UNKNOWN,
    )

    for role in role_order:
        print(
            f"  {role.value:18} "
            f"{role_counts.get(role.value, 0):,}"
        )

    print()
    print("Handlers:")

    for handler, count in handler_counts.most_common():
        print(
            f"  {handler:28} {count:,}"
        )

    if canary is not None:
        print()
        print("FM 3-06.11 routing canary:")
        print("  physical .............. PASS")
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
        print(
            f"  reason ................ "
            f"{canary['reason']}"
        )
    else:
        print()
        print("FM 3-06.11 routing canary:")
        print("  physical .............. FAIL")

    print()
    print("Extension/role hotspots:")

    rows = []

    for extension, counts in extension_roles.items():
        total_ext = sum(counts.values())

        if total_ext < 5:
            continue

        dominant_role, dominant_count = (
            counts.most_common(1)[0]
        )

        rows.append(
            (
                total_ext,
                extension,
                dominant_role,
                dominant_count,
                dict(counts),
            )
        )

    for (
        total_ext,
        extension,
        dominant_role,
        dominant_count,
        counts,
    ) in sorted(
        rows,
        reverse=True,
    )[:40]:
        print(
            f"  {extension:12} "
            f"{total_ext:8,}  "
            f"{dominant_role:18} "
            f"{dominant_count:8,}  "
            f"{counts}"
        )

    print()
    print("Safety:")
    print("  Database writes ............. 0")
    print("  Source mutations ............ 0")
    print("  Runtime mutations ........... 0")

    if args.show > 0:
        for role in role_order:
            name = role.value

            if name == ObjectRole.DOCUMENT.value:
                continue

            items = examples.get(name, [])

            if not items:
                continue

            print()
            print(
                f"--- {name} EXAMPLES "
                f"(first {len(items)}) ---"
            )

            for item in items:
                print()
                print(item["path"])
                print(
                    f"  handler: {item['handler']}"
                )
                print(
                    f"  reason : {item['reason']}"
                )

    if args.json is not None:
        payload = {
            "schema": "genesis-as1-route-audit-v1",
            "knowledge_root": str(root),
            "physical_files": total,
            "text_pipeline_admissible":
                text_admissible,
            "role_counts": dict(role_counts),
            "handler_counts": dict(handler_counts),
            "canary": canary,
            "extension_roles": {
                extension: dict(counts)
                for extension, counts
                in extension_roles.items()
            },
            "examples": dict(examples),
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
    print("=" * 72)
    print(" PACK 1A ROUTING AUDIT COMPLETE")
    print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
