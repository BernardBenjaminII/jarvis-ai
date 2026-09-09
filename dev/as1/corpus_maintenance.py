from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from dev.as1.object_router import (
    ObjectRole,
    RouteDecision,
    route_object,
)


DEFAULT_PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

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


EXCLUDED_DIR_NAMES = {
    ".jarvis",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
}

EXCLUDED_FILE_NAMES = {
    ".DS_Store",
    "Thumbs.db",
}


@dataclass(frozen=True)
class FileObservation:
    path: str
    extension: str
    size_bytes: int
    mtime_ns: int

    lifecycle: str
    role: str | None
    handler: str | None
    text_admissible: bool | None

    reason: str

    sha256: str | None = None
    duplicate_paths: tuple[str, ...] = ()

    @property
    def combined(self) -> str:
        if self.role:
            return f"{self.lifecycle}+{self.role}"
        return self.lifecycle


@dataclass
class Census:
    physical_files: int = 0

    unchanged_runtime: int = 0
    changed_runtime: int = 0

    admit_classified: int = 0
    classify_required: int = 0
    bridge_required: int = 0
    discover_required: int = 0

    review: int = 0
    ignore: int = 0
    exact_duplicates: int = 0
    identity_failures: int = 0

    routed_actionable: int = 0


def open_ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(
    conn: sqlite3.Connection,
    name: str,
) -> bool:
    return (
        conn.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type IN ('table','view')
              AND name=?
            """,
            (name,),
        ).fetchone()
        is not None
    )


def columns(
    conn: sqlite3.Connection,
    table: str,
) -> set[str]:
    if not table_exists(conn, table):
        return set()

    return {
        str(row["name"])
        for row in conn.execute(
            f'PRAGMA table_info("{table}")'
        )
    }


def first_existing(
    names: Iterable[str],
    available: set[str],
) -> str | None:
    for name in names:
        if name in available:
            return name
    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def should_exclude(
    path: Path,
    root: Path,
) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True

    if path.name in EXCLUDED_FILE_NAMES:
        return True

    return any(
        part in EXCLUDED_DIR_NAMES
        for part in relative.parts[:-1]
    )


def physical_files(root: Path):
    for directory, dirs, names in os.walk(root):
        base = Path(directory)

        dirs[:] = [
            name
            for name in dirs
            if name not in EXCLUDED_DIR_NAMES
        ]

        for name in names:
            path = base / name

            if should_exclude(path, root):
                continue

            try:
                if path.is_file():
                    yield path
            except OSError:
                continue


def load_runtime_documents(
    conn: sqlite3.Connection,
):
    by_path: dict[str, dict] = {}
    by_sha: defaultdict[str, list[str]] = defaultdict(list)

    if not table_exists(conn, "runtime_documents"):
        return by_path, by_sha

    available = columns(
        conn,
        "runtime_documents",
    )

    wanted = [
        name
        for name in (
            "id",
            "file_path",
            "sha256",
            "title",
            "content_chars",
            "materialized_at",
            "updated_at",
        )
        if name in available
    ]

    sql = (
        "SELECT "
        + ", ".join(f'"{x}"' for x in wanted)
        + " FROM runtime_documents"
    )

    for row in conn.execute(sql):
        item = dict(row)

        path = str(item.get("file_path") or "")
        if not path:
            continue

        by_path[path] = item

        digest = str(item.get("sha256") or "")
        if digest:
            by_sha[digest].append(path)

    return by_path, by_sha


def load_classifications(
    conn: sqlite3.Connection,
):
    result: dict[str, dict] = {}

    if not table_exists(
        conn,
        "knowledge_classifications",
    ):
        return result

    available = columns(
        conn,
        "knowledge_classifications",
    )

    path_col = first_existing(
        (
            "file_path",
            "document_path",
            "path",
            "source_path",
        ),
        available,
    )

    if path_col is None:
        return result

    wanted = [
        name
        for name in (
            "id",
            "discovered_file_id",
            path_col,
            "knowledge_type",
            "domain",
            "subject",
            "confidence",
            "action",
            "reason",
        )
        if name in available
    ]

    sql = (
        "SELECT "
        + ", ".join(f'"{x}"' for x in wanted)
        + ' FROM "knowledge_classifications"'
    )

    for row in conn.execute(sql):
        item = dict(row)
        path = str(item.get(path_col) or "")

        if path:
            result[path] = item

    return result


def load_discovered(
    conn: sqlite3.Connection,
):
    result: dict[str, dict] = {}

    if not table_exists(
        conn,
        "discovered_files",
    ):
        return result

    available = columns(
        conn,
        "discovered_files",
    )

    path_col = first_existing(
        (
            "file_path",
            "document_path",
            "path",
            "absolute_path",
            "source_path",
            "local_path",
        ),
        available,
    )

    if path_col is None:
        return result

    wanted = [
        name
        for name in (
            "id",
            path_col,
            "sha256",
            "size_bytes",
            "mtime_ns",
            "modified_time",
            "extension",
            "filename",
        )
        if name in available
    ]

    sql = (
        "SELECT "
        + ", ".join(f'"{x}"' for x in wanted)
        + ' FROM "discovered_files"'
    )

    for row in conn.execute(sql):
        item = dict(row)
        path = str(item.get(path_col) or "")

        if path:
            result[path] = item

    return result


def load_catalog_documents(
    conn: sqlite3.Connection,
):
    by_path: dict[str, dict] = {}
    by_sha: defaultdict[str, list[str]] = defaultdict(list)

    if not table_exists(
        conn,
        "catalog_documents",
    ):
        return by_path, by_sha

    available = columns(
        conn,
        "catalog_documents",
    )

    wanted = [
        name
        for name in (
            "id",
            "file_path",
            "sha256",
            "title",
            "file_type",
            "size_bytes",
            "readable",
            "content_chars",
        )
        if name in available
    ]

    sql = (
        "SELECT "
        + ", ".join(f'"{x}"' for x in wanted)
        + ' FROM "catalog_documents"'
    )

    for row in conn.execute(sql):
        item = dict(row)
        path = str(item.get("file_path") or "")

        if not path:
            continue

        by_path[path] = item

        digest = str(item.get("sha256") or "")
        if digest:
            by_sha[digest].append(path)

    return by_path, by_sha


def load_legacy_documents(
    conn: sqlite3.Connection,
    knowledge_root: Path,
):
    by_path: dict[str, dict] = {}
    by_sha: defaultdict[str, list[str]] = defaultdict(list)

    if not table_exists(conn, "documents"):
        return by_path, by_sha

    available = columns(conn, "documents")

    path_col = first_existing(
        (
            "path",
            "file_path",
            "document_path",
            "source_path",
            "relative_path",
        ),
        available,
    )

    if path_col is None:
        return by_path, by_sha

    wanted = [
        name
        for name in (
            "id",
            path_col,
            "sha256",
            "filename",
            "extension",
            "size_bytes",
            "category",
            "status",
        )
        if name in available
    ]

    sql = (
        "SELECT "
        + ", ".join(f'"{x}"' for x in wanted)
        + ' FROM "documents"'
    )

    for row in conn.execute(sql):
        item = dict(row)

        raw = str(item.get(path_col) or "")
        if not raw:
            continue

        path = Path(raw)

        if not path.is_absolute():
            path = knowledge_root / path

        resolved = str(path)

        by_path[resolved] = item

        digest = str(item.get("sha256") or "")

        if digest:
            by_sha[digest].append(resolved)

    return by_path, by_sha


def build_known_sha_index(
    *indexes,
):
    merged: defaultdict[str, set[str]] = defaultdict(set)

    for index in indexes:
        for digest, paths in index.items():
            if not digest:
                continue

            for path in paths:
                merged[digest].add(path)

    return merged


def stat_matches_discovery(
    stat: os.stat_result,
    discovered: dict,
) -> bool | None:
    if not discovered:
        return None

    if discovered.get("size_bytes") is not None:
        try:
            if int(discovered["size_bytes"]) != stat.st_size:
                return False
        except (TypeError, ValueError):
            pass

    if discovered.get("mtime_ns") is not None:
        try:
            return (
                int(discovered["mtime_ns"])
                == stat.st_mtime_ns
            )
        except (TypeError, ValueError):
            pass

    if discovered.get("modified_time") is not None:
        try:
            old = float(discovered["modified_time"])

            return (
                abs(old - stat.st_mtime)
                < 0.001
            )
        except (TypeError, ValueError):
            pass

    if discovered.get("size_bytes") is not None:
        return True

    return None


def observation(
    *,
    path: Path,
    stat: os.stat_result,
    lifecycle: str,
    reason: str,
    route: RouteDecision | None = None,
    digest: str | None = None,
    duplicates: tuple[str, ...] = (),
) -> FileObservation:

    return FileObservation(
        path=str(path),
        extension=path.suffix.casefold(),
        size_bytes=stat.st_size,
        mtime_ns=stat.st_mtime_ns,
        lifecycle=lifecycle,
        role=(
            route.role.value
            if route is not None
            else None
        ),
        handler=(
            route.handler
            if route is not None
            else None
        ),
        text_admissible=(
            route.admissible_to_text_pipeline
            if route is not None
            else None
        ),
        reason=reason,
        sha256=digest,
        duplicate_paths=duplicates,
    )


def classify_file(
    *,
    path: Path,
    verify_existing: bool,
    runtime_by_path: dict,
    classifications: dict,
    discovered: dict,
    catalog_by_path: dict,
    legacy_by_path: dict,
    known_sha: dict,
) -> FileObservation:

    path_string = str(path)

    try:
        stat = path.stat()
    except OSError as exc:
        return FileObservation(
            path=path_string,
            extension=path.suffix.casefold(),
            size_bytes=0,
            mtime_ns=0,
            lifecycle="IDENTITY_FAILURE",
            role=None,
            handler=None,
            text_admissible=None,
            reason=f"Unable to stat file: {exc}",
        )

    runtime = runtime_by_path.get(path_string)

    # ========================================================
    # FAST PATH
    #
    # Existing runtime objects do not need routing during
    # ordinary incremental maintenance.
    # ========================================================

    if runtime is not None:
        discovery = discovered.get(path_string)

        changed = (
            stat_matches_discovery(
                stat,
                discovery or {},
            )
            is False
        )

        if verify_existing:
            try:
                current_sha = sha256_file(path)
            except OSError as exc:
                return observation(
                    path=path,
                    stat=stat,
                    lifecycle="IDENTITY_FAILURE",
                    reason=f"SHA-256 failed: {exc}",
                )

            stored_sha = str(
                runtime.get("sha256") or ""
            )

            changed = bool(
                stored_sha
                and current_sha != stored_sha
            )

            return observation(
                path=path,
                stat=stat,
                lifecycle=(
                    "CHANGED_RUNTIME"
                    if changed
                    else "UNCHANGED_RUNTIME"
                ),
                reason=(
                    "Full SHA-256 verification detected "
                    "runtime content drift."
                    if changed
                    else
                    "Runtime SHA-256 verified."
                ),
                digest=current_sha,
            )

        return observation(
            path=path,
            stat=stat,
            lifecycle=(
                "CHANGED_RUNTIME"
                if changed
                else "UNCHANGED_RUNTIME"
            ),
            reason=(
                "Discovery metadata indicates physical "
                "content changed."
                if changed
                else
                "Already represented in runtime; routing "
                "and hashing skipped in incremental mode."
            ),
        )

    # ========================================================
    # ACTIONABLE PATH
    #
    # Only non-runtime objects reach the object router.
    # ========================================================

    route = route_object(path)

    classification = classifications.get(path_string)
    discovery = discovered.get(path_string)
    catalog = catalog_by_path.get(path_string)
    legacy = legacy_by_path.get(path_string)

    if route.role == ObjectRole.INTERNAL:
        return observation(
            path=path,
            stat=stat,
            lifecycle="IGNORE",
            route=route,
            reason=route.reason,
        )

    # --------------------------------------------------------
    # Existing canonical classification.
    # --------------------------------------------------------

    if classification is not None:
        action = str(
            classification.get("action") or ""
        ).casefold()

        if action == "candidate":
            lifecycle = "ADMIT_CLASSIFIED"
            reason = (
                "Canonical classification marks this object "
                "as candidate, but runtime materialization "
                "is absent."
            )

        elif action == "review":
            lifecycle = "REVIEW"
            reason = (
                "Canonical classification requires review."
            )

        elif action == "ignore":
            lifecycle = "IGNORE"
            reason = (
                "Canonical classification explicitly "
                "ignores this object."
            )

        else:
            lifecycle = "REVIEW"
            reason = (
                f"Unknown canonical classification "
                f"action: {action!r}"
            )

        return observation(
            path=path,
            stat=stat,
            lifecycle=lifecycle,
            route=route,
            reason=reason,
        )

    # --------------------------------------------------------
    # Canonically discovered but never classified.
    # --------------------------------------------------------

    if discovery is not None:
        return observation(
            path=path,
            stat=stat,
            lifecycle="CLASSIFY",
            route=route,
            reason=(
                "Object exists in discovered_files but "
                "has no knowledge_classifications record."
            ),
        )

    # --------------------------------------------------------
    # Known older catalog object.
    #
    # This is the FM 3-06.11 condition.
    # --------------------------------------------------------

    known_record = catalog or legacy

    if known_record is not None:
        digest = str(
            known_record.get("sha256") or ""
        )

        if not digest:
            try:
                digest = sha256_file(path)
            except OSError as exc:
                return observation(
                    path=path,
                    stat=stat,
                    lifecycle="IDENTITY_FAILURE",
                    route=route,
                    reason=f"SHA-256 failed: {exc}",
                )

        duplicates = tuple(
            sorted(
                other
                for other
                in known_sha.get(digest, set())
                if (
                    other != path_string
                    and other in runtime_by_path
                )
            )
        )

        if duplicates:
            return observation(
                path=path,
                stat=stat,
                lifecycle="EXACT_DUPLICATE",
                route=route,
                reason=(
                    "Exact byte identity is already "
                    "represented in runtime under another path."
                ),
                digest=digest,
                duplicates=duplicates,
            )

        return observation(
            path=path,
            stat=stat,
            lifecycle=(
                "BRIDGE_TO_CANONICAL_DISCOVERY"
            ),
            route=route,
            reason=(
                "Known to a legacy/catalog path but absent "
                "from discovered_files, classification, and "
                "runtime. Route must be preserved while AS1 "
                "bridges it into canonical discovery."
            ),
            digest=digest,
        )

    # --------------------------------------------------------
    # Truly new physical object.
    #
    # Pack 1B still performs exact byte identity only.
    # Layered identity arrives in Pack 2.
    # --------------------------------------------------------

    try:
        digest = sha256_file(path)
    except OSError as exc:
        return observation(
            path=path,
            stat=stat,
            lifecycle="IDENTITY_FAILURE",
            route=route,
            reason=f"SHA-256 failed: {exc}",
        )

    duplicates = tuple(
        sorted(
            other
            for other
            in known_sha.get(digest, set())
            if other != path_string
        )
    )

    if duplicates:
        return observation(
            path=path,
            stat=stat,
            lifecycle="EXACT_DUPLICATE",
            route=route,
            reason=(
                "New physical path has exact byte identity "
                "with an existing known object."
            ),
            digest=digest,
            duplicates=duplicates,
        )

    return observation(
        path=path,
        stat=stat,
        lifecycle="DISCOVER",
        route=route,
        reason=(
            "New physical object not found in canonical "
            "or legacy indexes."
        ),
        digest=digest,
    )


def update_census(
    census: Census,
    item: FileObservation,
):
    mapping = {
        "UNCHANGED_RUNTIME":
            "unchanged_runtime",

        "CHANGED_RUNTIME":
            "changed_runtime",

        "ADMIT_CLASSIFIED":
            "admit_classified",

        "CLASSIFY":
            "classify_required",

        "BRIDGE_TO_CANONICAL_DISCOVERY":
            "bridge_required",

        "DISCOVER":
            "discover_required",

        "REVIEW":
            "review",

        "IGNORE":
            "ignore",

        "EXACT_DUPLICATE":
            "exact_duplicates",

        "IDENTITY_FAILURE":
            "identity_failures",
    }

    attr = mapping.get(item.lifecycle)

    if attr:
        setattr(
            census,
            attr,
            getattr(census, attr) + 1,
        )

    if item.role is not None:
        census.routed_actionable += 1


def print_summary(
    *,
    census: Census,
    lifecycle_counts: Counter,
    role_counts: Counter,
    handler_counts: Counter,
    combined_counts: Counter,
    runtime_count: int,
    classification_count: int,
    discovery_count: int,
    canary: FileObservation | None,
    elapsed: float,
):
    print()
    print("=" * 76)
    print(" GENESIS AS1 — CORPUS MAINTENANCE")
    print(
        " PACK 1B — INTEGRATED LIFECYCLE + "
        "OBJECT ROUTING"
    )
    print("=" * 76)

    print()
    print("Canonical state:")
    print(
        f"  discovered_files ............ "
        f"{discovery_count:,}"
    )
    print(
        f"  knowledge_classifications ... "
        f"{classification_count:,}"
    )
    print(
        f"  runtime_documents ........... "
        f"{runtime_count:,}"
    )

    print()
    print("Corpus scan:")
    print(
        f"  Physical files scanned ...... "
        f"{census.physical_files:,}"
    )
    print(
        f"  Runtime fast-path ........... "
        f"{census.unchanged_runtime:,}"
    )
    print(
        f"  Routed actionable objects ... "
        f"{census.routed_actionable:,}"
    )

    print()
    print("Lifecycle:")

    lifecycle_order = (
        "UNCHANGED_RUNTIME",
        "CHANGED_RUNTIME",
        "ADMIT_CLASSIFIED",
        "CLASSIFY",
        "BRIDGE_TO_CANONICAL_DISCOVERY",
        "DISCOVER",
        "EXACT_DUPLICATE",
        "REVIEW",
        "IGNORE",
        "IDENTITY_FAILURE",
    )

    for name in lifecycle_order:
        print(
            f"  {name:34} "
            f"{lifecycle_counts.get(name, 0):,}"
        )

    print()
    print("Object roles — actionable objects only:")

    role_order = (
        "DOCUMENT",
        "DATASET",
        "SOURCE_CODE",
        "WEB_ARCHIVE",
        "MEDIA",
        "METADATA",
        "INTERNAL",
        "UNKNOWN",
    )

    for name in role_order:
        print(
            f"  {name:34} "
            f"{role_counts.get(name, 0):,}"
        )

    print()
    print("Handlers:")

    for name, count in handler_counts.most_common():
        print(
            f"  {name:34} {count:,}"
        )

    print()
    print("Combined lifecycle + role:")

    for name, count in combined_counts.most_common():
        print(
            f"  {name:52} {count:,}"
        )

    if canary is not None:
        print()
        print("FM 3-06.11 canary:")
        print("  physical .............. PASS")
        print(
            f"  lifecycle ............. "
            f"{canary.lifecycle}"
        )
        print(
            f"  role .................. "
            f"{canary.role}"
        )
        print(
            f"  handler ............... "
            f"{canary.handler}"
        )
        print(
            f"  text admissible ....... "
            f"{str(canary.text_admissible).upper()}"
        )

        if canary.sha256:
            print(
                f"  sha256 ................ "
                f"{canary.sha256}"
            )

    else:
        print()
        print("FM 3-06.11 canary:")
        print("  physical .............. FAIL")

    blockers = (
        census.changed_runtime
        + census.identity_failures
    )

    print()
    print("Safety:")
    print("  Database writes ............. 0")
    print("  Source mutations ............ 0")
    print("  Runtime mutations ........... 0")

    print()
    print(
        "Pack 1B status ................. "
        + (
            "REVIEW REQUIRED"
            if blockers
            else "PASS"
        )
    )

    print(
        f"Elapsed ........................ "
        f"{elapsed:.2f}s"
    )

    print("=" * 76)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Genesis AS1 permanent incremental corpus "
            "assimilation and maintenance pipeline."
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
        "--dry-run",
        action="store_true",
        default=True,
        help=(
            "Pack 1B is always read-only."
        ),
    )

    parser.add_argument(
        "--verify-existing",
        action="store_true",
        help=(
            "Hash existing runtime objects as well. "
            "Slow full-validation mode."
        ),
    )

    parser.add_argument(
        "--show",
        type=int,
        default=30,
        help=(
            "Number of actionable observations to print."
        ),
    )

    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help=(
            "Optional compact Pack 1B JSON report."
        ),
    )

    args = parser.parse_args()

    root = args.knowledge_root.resolve()

    if not root.is_dir():
        print(
            f"ERROR: Knowledge root missing: {root}",
            file=sys.stderr,
        )
        return 2

    if not args.runtime_db.is_file():
        print(
            f"ERROR: Runtime DB missing: "
            f"{args.runtime_db}",
            file=sys.stderr,
        )
        return 2

    if not args.legacy_db.is_file():
        print(
            f"ERROR: Legacy DB missing: "
            f"{args.legacy_db}",
            file=sys.stderr,
        )
        return 2

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

        census = Census()

        lifecycle_counts = Counter()
        role_counts = Counter()
        handler_counts = Counter()
        combined_counts = Counter()

        actionable_examples: list[
            FileObservation
        ] = []

        canary_result = None

        # JSON deliberately remains compact unless examples
        # are explicitly requested through --show.
        for path in physical_files(root):
            census.physical_files += 1

            item = classify_file(
                path=path,
                verify_existing=args.verify_existing,
                runtime_by_path=runtime_by_path,
                classifications=classifications,
                discovered=discovered,
                catalog_by_path=catalog_by_path,
                legacy_by_path=legacy_by_path,
                known_sha=known_sha,
            )

            update_census(census, item)

            lifecycle_counts[item.lifecycle] += 1

            if item.role:
                role_counts[item.role] += 1

            if item.handler:
                handler_counts[item.handler] += 1

            combined_counts[item.combined] += 1

            if (
                item.lifecycle
                != "UNCHANGED_RUNTIME"
                and len(actionable_examples)
                < max(0, args.show)
            ):
                actionable_examples.append(item)

            try:
                is_canary = (
                    path.resolve()
                    == CANARY.resolve()
                )
            except OSError:
                is_canary = False

            if is_canary:
                canary_result = item

        elapsed = time.monotonic() - started

        print_summary(
            census=census,
            lifecycle_counts=lifecycle_counts,
            role_counts=role_counts,
            handler_counts=handler_counts,
            combined_counts=combined_counts,
            runtime_count=len(runtime_by_path),
            classification_count=len(
                classifications
            ),
            discovery_count=len(discovered),
            canary=canary_result,
            elapsed=elapsed,
        )

        if actionable_examples:
            print()
            print(
                "First actionable observations:"
            )

            for item in actionable_examples:
                print()
                print(
                    f"[{item.lifecycle}"
                    + (
                        f" + {item.role}]"
                        if item.role
                        else "]"
                    )
                )
                print(f"  {item.path}")
                print(
                    f"  handler : "
                    f"{item.handler or '-'}"
                )
                print(
                    f"  text    : "
                    f"{item.text_admissible}"
                )
                print(
                    f"  reason  : "
                    f"{item.reason}"
                )

                for duplicate in (
                    item.duplicate_paths[:3]
                ):
                    print(
                        f"  duplicate -> "
                        f"{duplicate}"
                    )

        if args.json is not None:
            payload = {
                "schema":
                    "genesis-as1-pack1b-v1",

                "mode":
                    (
                        "full-verification"
                        if args.verify_existing
                        else "incremental-dry-run"
                    ),

                "knowledge_root":
                    str(root),

                "runtime_database":
                    str(args.runtime_db.resolve()),

                "legacy_database":
                    str(args.legacy_db.resolve()),

                "elapsed_seconds":
                    elapsed,

                "census":
                    asdict(census),

                "lifecycle_counts":
                    dict(lifecycle_counts),

                "role_counts":
                    dict(role_counts),

                "handler_counts":
                    dict(handler_counts),

                "combined_counts":
                    dict(combined_counts),

                "canary":
                    (
                        asdict(canary_result)
                        if canary_result
                        else None
                    ),

                "examples": [
                    asdict(item)
                    for item
                    in actionable_examples
                ],
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
            print(
                f"JSON report: {args.json}"
            )

        return 0

    finally:
        runtime.close()
        legacy.close()


if __name__ == "__main__":
    raise SystemExit(main())
