from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import time

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


DEFAULT_RUNTIME_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

DEFAULT_STATE_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/as1_identity.sqlite"
)

RESOLVER_VERSION = "as1-pack3b-v1"

# ------------------------------------------------------------
# Identity relationship classes
# ------------------------------------------------------------

REL_EXACT_SHA = "exact_sha"
REL_NORMALIZED_CONTENT = "normalized_content"
REL_STRUCTURAL = "structural"
REL_DISTINCT = "distinct"
REL_AMBIGUOUS = "ambiguous"

RELATIONSHIPS = {
    REL_EXACT_SHA,
    REL_NORMALIZED_CONTENT,
    REL_STRUCTURAL,
    REL_DISTINCT,
    REL_AMBIGUOUS,
}

# Structural similarity is intentionally conservative.
#
# Pack 3B is allowed to identify candidates and persist evidence.
# It must NOT aggressively collapse uncertain records.
STRUCTURAL_AUTO_THRESHOLD = 0.985
STRUCTURAL_REVIEW_THRESHOLD = 0.900

TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


@dataclass(frozen=True)
class Fingerprint:
    runtime_document_id: int
    sha256: Optional[str]
    content_fp: Optional[str]
    structural_fp: Optional[str]
    char_count: Optional[int]
    token_count: Optional[int]


@dataclass(frozen=True)
class Resolution:
    left_id: int
    right_id: int
    relationship: str
    confidence: float
    evidence: dict


def connect_ro(path: Path) -> sqlite3.Connection:
    uri = f"file:{path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def connect_state(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=FULL")

    return conn


def table_columns(
    conn: sqlite3.Connection,
    table: str,
) -> set[str]:
    rows = conn.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    return {str(row["name"]) for row in rows}


def first_existing(
    columns: set[str],
    candidates: Iterable[str],
) -> Optional[str]:
    for name in candidates:
        if name in columns:
            return name
    return None


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS as1_identity_groups (
            group_id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_runtime_document_id INTEGER NOT NULL,
            group_kind TEXT NOT NULL,
            resolver_version TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE UNIQUE INDEX IF NOT EXISTS
        ux_as1_identity_groups_canonical
        ON as1_identity_groups(
            canonical_runtime_document_id,
            group_kind,
            resolver_version
        );

        CREATE TABLE IF NOT EXISTS as1_identity_members (
            runtime_document_id INTEGER PRIMARY KEY,
            group_id INTEGER NOT NULL,
            canonical_runtime_document_id INTEGER NOT NULL,
            relationship_to_canonical TEXT NOT NULL,
            confidence REAL NOT NULL,
            resolver_version TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            resolved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(group_id)
                REFERENCES as1_identity_groups(group_id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS
        ix_as1_identity_members_group
        ON as1_identity_members(group_id);

        CREATE INDEX IF NOT EXISTS
        ix_as1_identity_members_canonical
        ON as1_identity_members(canonical_runtime_document_id);

        CREATE TABLE IF NOT EXISTS as1_identity_edges (
            left_runtime_document_id INTEGER NOT NULL,
            right_runtime_document_id INTEGER NOT NULL,
            relationship TEXT NOT NULL,
            confidence REAL NOT NULL,
            resolver_version TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            PRIMARY KEY(
                left_runtime_document_id,
                right_runtime_document_id,
                relationship,
                resolver_version
            ),

            CHECK(left_runtime_document_id < right_runtime_document_id)
        );

        CREATE INDEX IF NOT EXISTS
        ix_as1_identity_edges_relationship
        ON as1_identity_edges(relationship);

        CREATE TABLE IF NOT EXISTS as1_identity_resolution_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            resolver_version TEXT NOT NULL,
            started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            finished_at TEXT,
            status TEXT NOT NULL,
            fingerprints_examined INTEGER NOT NULL DEFAULT 0,
            exact_groups INTEGER NOT NULL DEFAULT 0,
            content_groups INTEGER NOT NULL DEFAULT 0,
            structural_edges INTEGER NOT NULL DEFAULT 0,
            ambiguous_edges INTEGER NOT NULL DEFAULT 0,
            singleton_groups INTEGER NOT NULL DEFAULT 0,
            notes TEXT
        );
        """
    )

    conn.commit()


def discover_fingerprint_layout(
    conn: sqlite3.Connection,
) -> dict[str, str | None]:
    candidates = [
        "as1_identity_fingerprints",
        "as1_runtime_fingerprints",
        "runtime_fingerprints",
        "fingerprints",
        "document_fingerprints",
    ]

    table = None

    for candidate in candidates:
        row = conn.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type='table' AND name=?
            """,
            (candidate,),
        ).fetchone()

        if row:
            table = candidate
            break

    if table is None:
        rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
            """
        ).fetchall()

        for row in rows:
            name = str(row["name"])
            cols = table_columns(conn, name)

            has_runtime_id = bool(
                {
                    "runtime_document_id",
                    "document_id",
                    "runtime_id",
                }
                & cols
            )

            has_content = bool(
                {
                    "content_fp",
                    "content_fingerprint",
                    "normalized_content_fp",
                    "normalized_fingerprint",
                }
                & cols
            )

            if has_runtime_id and has_content:
                table = name
                break

    if table is None:
        raise RuntimeError(
            "Unable to discover AS1 fingerprint table."
        )

    cols = table_columns(conn, table)

    runtime_id = first_existing(
        cols,
        (
            "runtime_document_id",
            "document_id",
            "runtime_id",
        ),
    )

    sha256 = first_existing(
        cols,
        (
            "sha256",
            "sha256_hex",
            "raw_sha256",
            "source_sha256",
            "file_sha256",
        ),
    )

    content_fp = first_existing(
        cols,
        (
            "normalized_content_sha256",
            "content_fp",
            "content_fingerprint",
            "normalized_content_fp",
            "normalized_fingerprint",
        ),
    )

    structural_fp = first_existing(
        cols,
        (
            "structural_fp",
            "structure_fp",
            "structural_fingerprint",
            "simhash64_hex",
        ),
    )

    char_count = first_existing(
        cols,
        (
            "normalized_chars",
            "char_count",
            "character_count",
            "content_chars",
            "chars",
        ),
    )

    token_count = first_existing(
        cols,
        (
            "token_count",
            "tokens",
            "word_count",
        ),
    )

    if runtime_id is None:
        raise RuntimeError(
            f"Fingerprint table {table!r} lacks runtime document id."
        )

    if content_fp is None:
        raise RuntimeError(
            f"Fingerprint table {table!r} lacks normalized content fingerprint."
        )

    return {
        "table": table,
        "runtime_id": runtime_id,
        "sha256": sha256,
        "content_fp": content_fp,
        "structural_fp": structural_fp,
        "char_count": char_count,
        "token_count": token_count,
    }


def load_fingerprints(
    conn: sqlite3.Connection,
    limit: Optional[int] = None,
) -> list[Fingerprint]:
    layout = discover_fingerprint_layout(conn)

    def expr(column: Optional[str], alias: str) -> str:
        if column is None:
            return f"NULL AS {alias}"
        return f'"{column}" AS {alias}'

    sql = f"""
        SELECT
            "{layout['runtime_id']}" AS runtime_document_id,
            {expr(layout['sha256'], 'sha256')},
            "{layout['content_fp']}" AS content_fp,
            {expr(layout['structural_fp'], 'structural_fp')},
            {expr(layout['char_count'], 'char_count')},
            {expr(layout['token_count'], 'token_count')}
        FROM "{layout['table']}"
        WHERE source_kind = ?
          AND fingerprint_version = ?
          AND "{layout['runtime_id']}" IS NOT NULL
        ORDER BY "{layout['runtime_id']}"
    """

    params: tuple = (
        "runtime",
        "as1-fingerprint-v1",
    )

    if limit is not None:
        sql += " LIMIT ?"
        params = params + (limit,)

    rows = conn.execute(sql, params).fetchall()

    result: list[Fingerprint] = []

    for row in rows:
        result.append(
            Fingerprint(
                runtime_document_id=int(row["runtime_document_id"]),
                sha256=(
                    str(row["sha256"])
                    if row["sha256"] is not None
                    else None
                ),
                content_fp=(
                    str(row["content_fp"])
                    if row["content_fp"] is not None
                    else None
                ),
                structural_fp=(
                    str(row["structural_fp"])
                    if row["structural_fp"] is not None
                    else None
                ),
                char_count=(
                    int(row["char_count"])
                    if row["char_count"] is not None
                    else None
                ),
                token_count=(
                    int(row["token_count"])
                    if row["token_count"] is not None
                    else None
                ),
            )
        )

    return result


def group_nonempty(
    fingerprints: Iterable[Fingerprint],
    attr: str,
) -> dict[str, list[Fingerprint]]:
    groups: dict[str, list[Fingerprint]] = {}

    for fp in fingerprints:
        value = getattr(fp, attr)

        if value is None:
            continue

        value = str(value).strip()

        if not value:
            continue

        groups.setdefault(value, []).append(fp)

    return groups


def length_similarity(
    left: Optional[int],
    right: Optional[int],
) -> Optional[float]:
    if left is None or right is None:
        return None

    if left <= 0 or right <= 0:
        return None

    return min(left, right) / max(left, right)


def structural_similarity(
    left: Fingerprint,
    right: Fingerprint,
) -> float:
    scores: list[float] = []

    char_score = length_similarity(
        left.char_count,
        right.char_count,
    )

    if char_score is not None:
        scores.append(char_score)

    token_score = length_similarity(
        left.token_count,
        right.token_count,
    )

    if token_score is not None:
        scores.append(token_score)

    if (
        left.structural_fp
        and right.structural_fp
        and left.structural_fp == right.structural_fp
    ):
        scores.append(1.0)

    if not scores:
        return 0.0

    return sum(scores) / len(scores)


def ordered_pair(a: int, b: int) -> tuple[int, int]:
    if a < b:
        return a, b
    return b, a


def persist_edge(
    conn: sqlite3.Connection,
    resolution: Resolution,
) -> None:
    left, right = ordered_pair(
        resolution.left_id,
        resolution.right_id,
    )

    conn.execute(
        """
        INSERT INTO as1_identity_edges (
            left_runtime_document_id,
            right_runtime_document_id,
            relationship,
            confidence,
            resolver_version,
            evidence_json
        )
        VALUES (?, ?, ?, ?, ?, ?)

        ON CONFLICT(
            left_runtime_document_id,
            right_runtime_document_id,
            relationship,
            resolver_version
        )
        DO UPDATE SET
            confidence=excluded.confidence,
            evidence_json=excluded.evidence_json
        """,
        (
            left,
            right,
            resolution.relationship,
            resolution.confidence,
            RESOLVER_VERSION,
            json.dumps(
                resolution.evidence,
                sort_keys=True,
                separators=(",", ":"),
            ),
        ),
    )


def ensure_group(
    conn: sqlite3.Connection,
    canonical_id: int,
    group_kind: str,
) -> int:
    conn.execute(
        """
        INSERT OR IGNORE INTO as1_identity_groups (
            canonical_runtime_document_id,
            group_kind,
            resolver_version
        )
        VALUES (?, ?, ?)
        """,
        (
            canonical_id,
            group_kind,
            RESOLVER_VERSION,
        ),
    )

    row = conn.execute(
        """
        SELECT group_id
        FROM as1_identity_groups
        WHERE canonical_runtime_document_id=?
          AND group_kind=?
          AND resolver_version=?
        """,
        (
            canonical_id,
            group_kind,
            RESOLVER_VERSION,
        ),
    ).fetchone()

    if row is None:
        raise RuntimeError("Unable to create identity group.")

    return int(row["group_id"])


def persist_member(
    conn: sqlite3.Connection,
    runtime_document_id: int,
    group_id: int,
    canonical_id: int,
    relationship: str,
    confidence: float,
    evidence: dict,
) -> None:
    conn.execute(
        """
        INSERT INTO as1_identity_members (
            runtime_document_id,
            group_id,
            canonical_runtime_document_id,
            relationship_to_canonical,
            confidence,
            resolver_version,
            evidence_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(runtime_document_id)
        DO UPDATE SET
            group_id=excluded.group_id,
            canonical_runtime_document_id=
                excluded.canonical_runtime_document_id,
            relationship_to_canonical=
                excluded.relationship_to_canonical,
            confidence=excluded.confidence,
            resolver_version=excluded.resolver_version,
            evidence_json=excluded.evidence_json,
            resolved_at=CURRENT_TIMESTAMP
        """,
        (
            runtime_document_id,
            group_id,
            canonical_id,
            relationship,
            confidence,
            RESOLVER_VERSION,
            json.dumps(
                evidence,
                sort_keys=True,
                separators=(",", ":"),
            ),
        ),
    )


class UnionFind:
    def __init__(self, ids: Iterable[int]) -> None:
        self.parent = {i: i for i in ids}

    def find(self, value: int) -> int:
        parent = self.parent[value]

        if parent != value:
            self.parent[value] = self.find(parent)

        return self.parent[value]

    def union(self, a: int, b: int) -> None:
        ra = self.find(a)
        rb = self.find(b)

        if ra == rb:
            return

        # Deterministic canonical preference:
        # lowest runtime document id wins.
        if ra < rb:
            self.parent[rb] = ra
        else:
            self.parent[ra] = rb


def resolve(
    fingerprints: list[Fingerprint],
    conn: sqlite3.Connection,
) -> dict[str, int]:
    ids = [fp.runtime_document_id for fp in fingerprints]

    uf = UnionFind(ids)

    exact_edges: list[Resolution] = []
    content_edges: list[Resolution] = []
    structural_edges: list[Resolution] = []
    ambiguous_edges: list[Resolution] = []

    # --------------------------------------------------------
    # Layer 1 — exact raw SHA identity
    # --------------------------------------------------------

    sha_groups = group_nonempty(
        fingerprints,
        "sha256",
    )

    exact_group_count = 0

    for sha, members in sha_groups.items():
        if len(members) < 2:
            continue

        exact_group_count += 1
        canonical = min(
            member.runtime_document_id
            for member in members
        )

        for member in members:
            if member.runtime_document_id == canonical:
                continue

            uf.union(
                canonical,
                member.runtime_document_id,
            )

            exact_edges.append(
                Resolution(
                    left_id=canonical,
                    right_id=member.runtime_document_id,
                    relationship=REL_EXACT_SHA,
                    confidence=1.0,
                    evidence={
                        "sha256": sha,
                    },
                )
            )

    # --------------------------------------------------------
    # Layer 2 — normalized-content identity
    # --------------------------------------------------------

    content_groups = group_nonempty(
        fingerprints,
        "content_fp",
    )

    content_group_count = 0

    for content_fp, members in content_groups.items():
        if len(members) < 2:
            continue

        roots = {
            uf.find(member.runtime_document_id)
            for member in members
        }

        if len(roots) < 2:
            continue

        content_group_count += 1

        canonical = min(
            member.runtime_document_id
            for member in members
        )

        for member in members:
            if member.runtime_document_id == canonical:
                continue

            if (
                uf.find(canonical)
                == uf.find(member.runtime_document_id)
            ):
                continue

            uf.union(
                canonical,
                member.runtime_document_id,
            )

            content_edges.append(
                Resolution(
                    left_id=canonical,
                    right_id=member.runtime_document_id,
                    relationship=REL_NORMALIZED_CONTENT,
                    confidence=1.0,
                    evidence={
                        "content_fp": content_fp,
                    },
                )
            )

    # --------------------------------------------------------
    # Layer 3 — bounded structural candidate resolution
    #
    # IMPORTANT:
    # This is NOT O(N^2).
    #
    # Candidates are generated only from equal structural
    # fingerprints where structural_fp exists.
    #
    # If the current fingerprint schema does not yet contain
    # structural_fp, this layer safely resolves zero edges.
    # --------------------------------------------------------

    # Pack 3 fingerprint storage currently supplies SimHash
    # in the structural_fp slot. SimHash is candidate evidence,
    # not deterministic identity. Pack 3B-R2 therefore does not
    # auto-merge on structural_fp equality. A later bounded
    # Hamming-distance resolver will consume it safely.
    structural_groups: dict[str, list[Fingerprint]] = {}

    by_id = {
        fp.runtime_document_id: fp
        for fp in fingerprints
    }

    for structural_fp, members in structural_groups.items():
        if len(members) < 2:
            continue

        ordered = sorted(
            members,
            key=lambda x: x.runtime_document_id,
        )

        anchor = ordered[0]

        for candidate in ordered[1:]:
            if (
                uf.find(anchor.runtime_document_id)
                == uf.find(candidate.runtime_document_id)
            ):
                continue

            similarity = structural_similarity(
                anchor,
                candidate,
            )

            evidence = {
                "structural_fp": structural_fp,
                "char_count_left": anchor.char_count,
                "char_count_right": candidate.char_count,
                "token_count_left": anchor.token_count,
                "token_count_right": candidate.token_count,
                "similarity": round(similarity, 6),
            }

            if similarity >= STRUCTURAL_AUTO_THRESHOLD:
                uf.union(
                    anchor.runtime_document_id,
                    candidate.runtime_document_id,
                )

                structural_edges.append(
                    Resolution(
                        left_id=anchor.runtime_document_id,
                        right_id=candidate.runtime_document_id,
                        relationship=REL_STRUCTURAL,
                        confidence=similarity,
                        evidence=evidence,
                    )
                )

            elif similarity >= STRUCTURAL_REVIEW_THRESHOLD:
                ambiguous_edges.append(
                    Resolution(
                        left_id=anchor.runtime_document_id,
                        right_id=candidate.runtime_document_id,
                        relationship=REL_AMBIGUOUS,
                        confidence=similarity,
                        evidence=evidence,
                    )
                )

    # --------------------------------------------------------
    # Persist evidence edges
    # --------------------------------------------------------

    for edge in exact_edges:
        persist_edge(conn, edge)

    for edge in content_edges:
        persist_edge(conn, edge)

    for edge in structural_edges:
        persist_edge(conn, edge)

    for edge in ambiguous_edges:
        persist_edge(conn, edge)

    # --------------------------------------------------------
    # Build final deterministic groups
    # --------------------------------------------------------

    components: dict[int, list[int]] = {}

    for runtime_id in ids:
        root = uf.find(runtime_id)
        components.setdefault(root, []).append(runtime_id)

    singleton_groups = 0

    for _, member_ids in sorted(components.items()):
        canonical_id = min(member_ids)

        if len(member_ids) == 1:
            group_kind = REL_DISTINCT
            singleton_groups += 1
        else:
            group_kind = "duplicate_cluster"

        group_id = ensure_group(
            conn,
            canonical_id,
            group_kind,
        )

        for runtime_id in sorted(member_ids):
            if runtime_id == canonical_id:
                relationship = (
                    REL_DISTINCT
                    if len(member_ids) == 1
                    else "canonical"
                )
                confidence = 1.0
                evidence = {
                    "component_size": len(member_ids),
                    "canonical": True,
                }

            else:
                # Determine strongest known relationship
                # between this member and the component.
                row = conn.execute(
                    """
                    SELECT
                        relationship,
                        confidence,
                        evidence_json
                    FROM as1_identity_edges
                    WHERE resolver_version=?
                      AND (
                            left_runtime_document_id=?
                         OR right_runtime_document_id=?
                      )
                      AND (
                            left_runtime_document_id IN (
                                SELECT value
                                FROM json_each(?)
                            )
                         OR right_runtime_document_id IN (
                                SELECT value
                                FROM json_each(?)
                            )
                      )
                    ORDER BY
                        CASE relationship
                            WHEN 'exact_sha' THEN 1
                            WHEN 'normalized_content' THEN 2
                            WHEN 'structural' THEN 3
                            WHEN 'ambiguous' THEN 4
                            ELSE 5
                        END,
                        confidence DESC
                    LIMIT 1
                    """,
                    (
                        RESOLVER_VERSION,
                        runtime_id,
                        runtime_id,
                        json.dumps(member_ids),
                        json.dumps(member_ids),
                    ),
                ).fetchone()

                if row is None:
                    relationship = "duplicate_cluster"
                    confidence = 1.0
                    evidence = {
                        "component_size": len(member_ids),
                    }
                else:
                    relationship = str(row["relationship"])
                    confidence = float(row["confidence"])

                    try:
                        evidence = json.loads(
                            row["evidence_json"]
                        )
                    except Exception:
                        evidence = {
                            "component_size": len(member_ids),
                        }

            persist_member(
                conn=conn,
                runtime_document_id=runtime_id,
                group_id=group_id,
                canonical_id=canonical_id,
                relationship=relationship,
                confidence=confidence,
                evidence=evidence,
            )

    conn.commit()

    return {
        "fingerprints_examined": len(fingerprints),
        "exact_groups": exact_group_count,
        "content_groups": content_group_count,
        "structural_edges": len(structural_edges),
        "ambiguous_edges": len(ambiguous_edges),
        "singleton_groups": singleton_groups,
        "components": len(components),
    }


def start_run(conn: sqlite3.Connection) -> int:
    cur = conn.execute(
        """
        INSERT INTO as1_identity_resolution_runs (
            resolver_version,
            status
        )
        VALUES (?, 'running')
        """,
        (RESOLVER_VERSION,),
    )

    conn.commit()

    return int(cur.lastrowid)


def finish_run(
    conn: sqlite3.Connection,
    run_id: int,
    status: str,
    stats: dict[str, int],
    notes: str,
) -> None:
    conn.execute(
        """
        UPDATE as1_identity_resolution_runs
        SET
            finished_at=CURRENT_TIMESTAMP,
            status=?,
            fingerprints_examined=?,
            exact_groups=?,
            content_groups=?,
            structural_edges=?,
            ambiguous_edges=?,
            singleton_groups=?,
            notes=?
        WHERE run_id=?
        """,
        (
            status,
            stats.get("fingerprints_examined", 0),
            stats.get("exact_groups", 0),
            stats.get("content_groups", 0),
            stats.get("structural_edges", 0),
            stats.get("ambiguous_edges", 0),
            stats.get("singleton_groups", 0),
            notes,
            run_id,
        ),
    )

    conn.commit()


def integrity_check(conn: sqlite3.Connection) -> str:
    row = conn.execute(
        "PRAGMA integrity_check"
    ).fetchone()

    if row is None:
        return "unknown"

    return str(row[0])


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Genesis AS1 Pack 3B global durable identity resolver"
        )
    )

    parser.add_argument(
        "--runtime-db",
        type=Path,
        default=DEFAULT_RUNTIME_DB,
    )

    parser.add_argument(
        "--state-db",
        type=Path,
        default=DEFAULT_STATE_DB,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Maximum populated fingerprint rows to resolve. "
            "Used for controlled certification."
        ),
    )

    args = parser.parse_args()

    started = time.monotonic()

    if not args.runtime_db.exists():
        print(
            f"FAIL: runtime DB missing: {args.runtime_db}",
            file=sys.stderr if False else None,
        )
        return 2

    if not args.state_db.exists():
        print(
            f"FAIL: state DB missing: {args.state_db}"
        )
        return 2

    state = connect_state(args.state_db)

    try:
        ensure_schema(state)

        layout = discover_fingerprint_layout(state)

        print(
            "============================================================"
        )
        print(
            " GENESIS AS1 PACK 3B — GLOBAL DURABLE IDENTITY RESOLVER"
        )
        print(
            "============================================================"
        )
        print(f"resolver version       : {RESOLVER_VERSION}")
        print(f"fingerprint table      : {layout['table']}")
        print(f"runtime id column      : {layout['runtime_id']}")
        print(f"sha column             : {layout['sha256']}")
        print(f"content fp column      : {layout['content_fp']}")
        print(f"structural fp column   : {layout['structural_fp']}")
        print(f"limit                  : {args.limit}")
        print("production DB writes   : 0")
        print("AS1 sidecar writes     : YES")
        print()

        run_id = start_run(state)

        try:
            fingerprints = load_fingerprints(
                state,
                limit=args.limit,
            )

            if not fingerprints:
                finish_run(
                    state,
                    run_id,
                    "pass",
                    {},
                    "No populated fingerprints available.",
                )

                print("No fingerprints available.")
                print("IDENTITY RESOLUTION STATUS: PASS")
                return 0

            stats = resolve(
                fingerprints,
                state,
            )

            integrity = integrity_check(state)

            if integrity != "ok":
                finish_run(
                    state,
                    run_id,
                    "fail",
                    stats,
                    f"Integrity failure: {integrity}",
                )

                print(
                    f"FAIL: sidecar integrity: {integrity}"
                )
                return 3

            elapsed = time.monotonic() - started

            notes = (
                f"components={stats['components']}; "
                f"elapsed={elapsed:.3f}s; "
                f"integrity={integrity}"
            )

            finish_run(
                state,
                run_id,
                "pass",
                stats,
                notes,
            )

            print("=== RESOLUTION RESULT ===")
            print(
                f"fingerprints examined : "
                f"{stats['fingerprints_examined']:,}"
            )
            print(
                f"exact SHA groups      : "
                f"{stats['exact_groups']:,}"
            )
            print(
                f"content groups        : "
                f"{stats['content_groups']:,}"
            )
            print(
                f"structural edges      : "
                f"{stats['structural_edges']:,}"
            )
            print(
                f"ambiguous edges       : "
                f"{stats['ambiguous_edges']:,}"
            )
            print(
                f"singleton groups      : "
                f"{stats['singleton_groups']:,}"
            )
            print(
                f"identity components   : "
                f"{stats['components']:,}"
            )
            print(f"sidecar integrity     : {integrity}")
            print(f"elapsed seconds       : {elapsed:.3f}")
            print("production DB writes  : 0")
            print("AS1 sidecar writes    : YES")
            print()
            print("IDENTITY RESOLUTION STATUS: PASS")

            return 0

        except Exception as exc:
            finish_run(
                state,
                run_id,
                "fail",
                {},
                f"{type(exc).__name__}: {exc}",
            )

            print(
                f"IDENTITY RESOLUTION STATUS: FAIL"
            )
            print(
                f"{type(exc).__name__}: {exc}"
            )

            return 1

    finally:
        state.close()


if __name__ == "__main__":
    raise SystemExit(main())
