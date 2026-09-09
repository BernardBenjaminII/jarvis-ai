from __future__ import annotations

import argparse
import csv
import inspect
import json
import re
import sqlite3
import time

from collections import Counter
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "genesis-recall-r1g-r2-v1"

SEARCH_LIMITS = (25, 100, 500)

# We are doing anatomy, not production mutation.
# Direct FTS probes are intentionally conservative and bounded.
DIRECT_FTS_LIMIT = 1000


# ============================================================
# GENERIC HELPERS
# ============================================================

def ro(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA query_only=ON")
    con.execute("PRAGMA busy_timeout=10000")
    return con


def qident(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def compact(value: str, limit: int = 180) -> str:
    value = re.sub(r"\s+", " ", safe_text(value)).strip()
    if len(value) <= limit:
        return value
    return value[:limit] + "..."


def result_id(row: dict[str, Any]) -> int | None:
    for key in (
        "document_id",
        "runtime_document_id",
        "runtime_id",
        "doc_id",
        "id",
    ):
        value = row.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            pass
    return None


def result_path(row: dict[str, Any]) -> str:
    for key in (
        "file_path",
        "source_path",
        "document_path",
        "path",
    ):
        value = row.get(key)
        if value:
            return str(value)
    return ""


def locate_target(
    rows: Iterable[dict[str, Any]],
    *,
    runtime_id: int,
    expected_path: str,
) -> int | None:
    for rank, row in enumerate(rows, start=1):
        if result_id(row) == runtime_id:
            return rank

        if (
            expected_path
            and result_path(row)
            and result_path(row) == expected_path
        ):
            return rank

    return None


# ============================================================
# RUNTIME DOCUMENT
# ============================================================

def runtime_document(
    con: sqlite3.Connection,
    runtime_id: int,
) -> dict[str, Any] | None:
    row = con.execute(
        """
        SELECT
            id,
            title,
            file_path,
            sha256,
            media_type,
            content_chars,
            substr(content_text, 1, 500) AS content_prefix
        FROM runtime_documents
        WHERE id=?
        LIMIT 1
        """,
        (runtime_id,),
    ).fetchone()

    return dict(row) if row is not None else None


# ============================================================
# SQLITE / FTS DISCOVERY
# ============================================================

def table_columns(
    con: sqlite3.Connection,
    table: str,
) -> list[dict[str, Any]]:
    rows = con.execute(
        f"PRAGMA table_info({qident(table)})"
    ).fetchall()

    return [dict(row) for row in rows]


def discover_fts_tables(
    con: sqlite3.Connection,
) -> list[dict[str, Any]]:
    rows = con.execute(
        """
        SELECT
            name,
            type,
            sql
        FROM sqlite_master
        WHERE
            type IN ('table','view')
            AND (
                lower(name) LIKE '%fts%'
                OR lower(COALESCE(sql,'')) LIKE '%fts5%'
                OR lower(COALESCE(sql,'')) LIKE '%fts4%'
            )
        ORDER BY name
        """
    ).fetchall()

    discovered = []

    # Exclude ordinary FTS shadow tables where possible.
    shadow_suffixes = (
        "_data",
        "_idx",
        "_docsize",
        "_config",
        "_content",
        "_segments",
        "_segdir",
        "_stat",
    )

    for row in rows:
        name = str(row["name"])
        sql = safe_text(row["sql"])

        virtual_fts = (
            "virtual table" in sql.casefold()
            and (
                "fts5" in sql.casefold()
                or "fts4" in sql.casefold()
                or "fts3" in sql.casefold()
            )
        )

        likely_shadow = any(
            name.casefold().endswith(suffix)
            for suffix in shadow_suffixes
        )

        if likely_shadow and not virtual_fts:
            continue

        columns = table_columns(con, name)

        discovered.append(
            {
                "name": name,
                "type": row["type"],
                "sql": sql,
                "virtual_fts": virtual_fts,
                "columns": columns,
            }
        )

    return discovered


def candidate_id_columns(
    columns: list[dict[str, Any]],
) -> list[str]:
    names = [str(c["name"]) for c in columns]

    priority = (
        "runtime_document_id",
        "document_id",
        "runtime_id",
        "doc_id",
        "id",
    )

    result = []

    for name in priority:
        if name in names:
            result.append(name)

    return result


def candidate_text_columns(
    columns: list[dict[str, Any]],
) -> list[str]:
    names = [str(c["name"]) for c in columns]

    priority = (
        "title",
        "content_text",
        "content",
        "text",
        "body",
        "file_path",
        "path",
        "source_path",
    )

    result = []

    for name in priority:
        if name in names:
            result.append(name)

    return result


def inspect_membership(
    con: sqlite3.Connection,
    table: dict[str, Any],
    runtime_id: int,
    expected_path: str,
    title: str,
) -> dict[str, Any]:
    name = table["name"]
    columns = table["columns"]

    id_columns = candidate_id_columns(columns)
    text_columns = candidate_text_columns(columns)

    result = {
        "table": name,
        "id_columns": id_columns,
        "text_columns": text_columns,
        "by_id": False,
        "by_rowid": False,
        "by_path": False,
        "by_title": False,
        "membership": False,
        "errors": [],
    }

    for col in id_columns:
        try:
            row = con.execute(
                f"""
                SELECT 1
                FROM {qident(name)}
                WHERE {qident(col)}=?
                LIMIT 1
                """,
                (runtime_id,),
            ).fetchone()

            if row is not None:
                result["by_id"] = True
                break

        except sqlite3.Error as exc:
            result["errors"].append(
                f"id:{col}:{exc}"
            )

    # Many FTS tables use rowid as the external document identity.
    try:
        row = con.execute(
            f"""
            SELECT 1
            FROM {qident(name)}
            WHERE rowid=?
            LIMIT 1
            """,
            (runtime_id,),
        ).fetchone()

        result["by_rowid"] = row is not None

    except sqlite3.Error as exc:
        result["errors"].append(
            f"rowid:{exc}"
        )

    for col in text_columns:
        if "path" not in col.casefold():
            continue

        try:
            row = con.execute(
                f"""
                SELECT 1
                FROM {qident(name)}
                WHERE {qident(col)}=?
                LIMIT 1
                """,
                (expected_path,),
            ).fetchone()

            if row is not None:
                result["by_path"] = True
                break

        except sqlite3.Error as exc:
            result["errors"].append(
                f"path:{col}:{exc}"
            )

    for col in text_columns:
        if col.casefold() != "title":
            continue

        try:
            row = con.execute(
                f"""
                SELECT 1
                FROM {qident(name)}
                WHERE {qident(col)}=?
                LIMIT 1
                """,
                (title,),
            ).fetchone()

            if row is not None:
                result["by_title"] = True
                break

        except sqlite3.Error as exc:
            result["errors"].append(
                f"title:{col}:{exc}"
            )

    result["membership"] = any(
        (
            result["by_id"],
            result["by_rowid"],
            result["by_path"],
            result["by_title"],
        )
    )

    return result


# ============================================================
# TOKENIZATION / QUERY PROBES
# ============================================================

def lexical_tokens(value: str) -> list[str]:
    # Diagnostic tokenizer only.
    # We do NOT claim this is SQLite FTS's exact tokenizer.
    return re.findall(
        r"[A-Za-z0-9]+",
        safe_text(value).casefold(),
    )


def unique_tokens(tokens: Iterable[str]) -> list[str]:
    seen = set()
    result = []

    for token in tokens:
        if not token or token in seen:
            continue
        seen.add(token)
        result.append(token)

    return result


def query_variants(
    original: str,
    normalized: str,
    relaxed: str,
    title: str,
) -> list[dict[str, str]]:
    variants = []

    def add(kind: str, value: str) -> None:
        value = re.sub(r"\s+", " ", safe_text(value)).strip()
        if not value:
            return

        folded = value.casefold()

        if any(
            item["value"].casefold() == folded
            for item in variants
        ):
            return

        variants.append(
            {
                "kind": kind,
                "value": value,
            }
        )

    add("original", original)
    add("normalized", normalized)
    add("relaxed", relaxed)
    add("runtime_title", title)

    tokens = unique_tokens(
        lexical_tokens(normalized)
    )

    if tokens:
        add(
            "normalized_tokens_and",
            " AND ".join(
                f'"{token}"'
                for token in tokens
            ),
        )

        add(
            "normalized_tokens_or",
            " OR ".join(
                f'"{token}"'
                for token in tokens
            ),
        )

        for token in tokens:
            if len(token) >= 3:
                add(
                    f"single_token:{token}",
                    f'"{token}"',
                )

    return variants


def direct_match_probe(
    con: sqlite3.Connection,
    table: dict[str, Any],
    query: str,
    *,
    runtime_id: int,
    expected_path: str,
) -> dict[str, Any]:
    name = table["name"]

    result = {
        "table": name,
        "query": query,
        "executed": False,
        "returned": 0,
        "target_rank": None,
        "target_present": False,
        "bm25_available": False,
        "target_bm25": None,
        "error": None,
    }

    # MATCH table-name is valid for real FTS virtual tables.
    if not table.get("virtual_fts"):
        result["error"] = "not_virtual_fts"
        return result

    columns = table["columns"]
    id_columns = candidate_id_columns(columns)
    text_columns = candidate_text_columns(columns)

    select_parts = ["rowid AS __rowid"]

    for col in id_columns:
        select_parts.append(
            f"{qident(col)} AS {qident('__' + col)}"
        )

    for col in text_columns:
        select_parts.append(
            f"{qident(col)} AS {qident('__' + col)}"
        )

    # First attempt with BM25.
    sql = f"""
        SELECT
            {", ".join(select_parts)},
            bm25({qident(name)}) AS __bm25
        FROM {qident(name)}
        WHERE {qident(name)} MATCH ?
        ORDER BY __bm25
        LIMIT ?
    """

    try:
        rows = con.execute(
            sql,
            (query, DIRECT_FTS_LIMIT),
        ).fetchall()

        result["bm25_available"] = True
        result["executed"] = True

    except sqlite3.Error:
        # Fallback for FTS implementations/configurations where bm25()
        # is unavailable.
        sql = f"""
            SELECT
                {", ".join(select_parts)}
            FROM {qident(name)}
            WHERE {qident(name)} MATCH ?
            LIMIT ?
        """

        try:
            rows = con.execute(
                sql,
                (query, DIRECT_FTS_LIMIT),
            ).fetchall()

            result["executed"] = True

        except sqlite3.Error as exc:
            result["error"] = str(exc)
            return result

    result["returned"] = len(rows)

    for rank, row in enumerate(rows, start=1):
        row_dict = dict(row)

        match = False

        try:
            if int(row_dict.get("__rowid")) == runtime_id:
                match = True
        except (TypeError, ValueError):
            pass

        if not match:
            for col in id_columns:
                value = row_dict.get("__" + col)
                try:
                    if int(value) == runtime_id:
                        match = True
                        break
                except (TypeError, ValueError):
                    pass

        if not match and expected_path:
            for col in text_columns:
                if "path" not in col.casefold():
                    continue

                if safe_text(
                    row_dict.get("__" + col)
                ) == expected_path:
                    match = True
                    break

        if match:
            result["target_present"] = True
            result["target_rank"] = rank

            if "__bm25" in row_dict:
                result["target_bm25"] = row_dict["__bm25"]

            break

    return result


# ============================================================
# PRODUCTION SEARCH PROBE
# ============================================================

def production_search_probe(
    search_catalog: Any,
    *,
    query: str,
    db_path: Path,
    runtime_id: int,
    expected_path: str,
) -> dict[str, Any]:
    horizons = {}

    best_rank = None
    best_limit = None

    for limit in SEARCH_LIMITS:
        try:
            rows = list(
                search_catalog(
                    query,
                    db_path=db_path,
                    limit=limit,
                )
            )

            rank = locate_target(
                rows,
                runtime_id=runtime_id,
                expected_path=expected_path,
            )

            horizons[str(limit)] = {
                "returned": len(rows),
                "target_rank": rank,
            }

            if (
                rank is not None
                and (
                    best_rank is None
                    or rank < best_rank
                )
            ):
                best_rank = rank
                best_limit = limit

        except Exception as exc:
            horizons[str(limit)] = {
                "returned": None,
                "target_rank": None,
                "error": repr(exc),
            }

    return {
        "horizons": horizons,
        "best_rank": best_rank,
        "best_limit": best_limit,
    }


# ============================================================
# FAILURE CLASSIFICATION
# ============================================================

def classify(
    *,
    memberships: list[dict[str, Any]],
    direct_probes: list[dict[str, Any]],
    production_probes: list[dict[str, Any]],
) -> tuple[str, str]:
    any_membership = any(
        item.get("membership")
        for item in memberships
    )

    successful_direct = [
        item
        for item in direct_probes
        if item.get("executed")
    ]

    direct_target_hits = [
        item
        for item in successful_direct
        if item.get("target_present")
    ]

    production_hits = [
        item
        for item in production_probes
        if item.get("best_rank") is not None
    ]

    if not any_membership:
        return (
            "NOT_INDEXED_OR_UNMAPPED",
            "target could not be mapped into discovered FTS structures",
        )

    if not successful_direct:
        return (
            "FTS_PROBE_UNAVAILABLE",
            "FTS membership exists but direct MATCH could not be executed",
        )

    if not direct_target_hits:
        return (
            "INDEXED_BUT_MATCH_EXPRESSION_FAILS",
            "target is represented in FTS but none of the bounded direct MATCH variants returned it",
        )

    best_direct_rank = min(
        int(item["target_rank"])
        for item in direct_target_hits
        if item.get("target_rank") is not None
    )

    if not production_hits:
        if best_direct_rank <= DIRECT_FTS_LIMIT:
            return (
                "SEARCH_WRAPPER_DROPPED_TARGET",
                "direct FTS MATCH finds target but production search_catalog does not",
            )

    if production_hits:
        best_production_rank = min(
            int(item["best_rank"])
            for item in production_hits
            if item.get("best_rank") is not None
        )

        if best_production_rank > 25:
            return (
                "MATCHED_BUT_RANKED_OUT",
                f"production search finds target only below normal candidate horizon; best rank={best_production_rank}",
            )

        return (
            "PRODUCTION_SEARCH_RECOVERABLE",
            f"production search finds target within normal horizon; best rank={best_production_rank}",
        )

    if best_direct_rank > 25:
        return (
            "FTS_MATCHED_BUT_RANKED_OUT",
            f"direct FTS finds target, but only at rank {best_direct_rank}",
        )

    return (
        "UNCLASSIFIED_RETRIEVAL_PATH",
        "target is directly retrievable but observed production behavior needs wrapper-level inspection",
    )


# ============================================================
# LOAD R1G-R1 FAILURES
# ============================================================

def load_unrecovered(path: Path) -> list[dict[str, Any]]:
    report = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    rows = []

    for item in report.get(
        "failure_results",
        []
    ):
        if item.get("recovery") == "NOT_RECOVERED":
            rows.append(item)

    return rows


# ============================================================
# MAIN
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--db",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--r1g-r1-report",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--report",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--tsv",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    from core.knowledge_catalog.search import search_catalog

    started = time.monotonic()

    failures = load_unrecovered(
        args.r1g_r1_report
    )

    con = ro(args.db)

    try:
        fts_tables = discover_fts_tables(con)

        print("=" * 68)
        print(" GENESIS RECALL R1G-R2")
        print(" FTS CANDIDATE GENERATION + RANKING ANATOMY")
        print("=" * 68)

        print()
        print("unrecovered R1G-R1 cases :", len(failures))
        print("discovered FTS structures:", len(fts_tables))

        for table in fts_tables:
            print()
            print("FTS:", table["name"])
            print("  virtual :", table["virtual_fts"])
            print(
                "  columns :",
                ", ".join(
                    str(c["name"])
                    for c in table["columns"]
                ),
            )

        # Capture production wrapper source for the artifact,
        # but do not modify it.
        try:
            production_source = inspect.getsource(
                search_catalog
            )
        except Exception as exc:
            production_source = (
                f"<source unavailable: {exc!r}>"
            )

        results = []
        classifications = Counter()

        print()
        print("=== FAILURE ANATOMY ===")

        for index, failure in enumerate(
            failures,
            start=1,
        ):
            runtime_id = int(
                failure["runtime_id"]
            )

            original_query = safe_text(
                failure.get("query")
            )

            normalized_query = safe_text(
                failure.get("normalized_query")
            )

            relaxed_query = safe_text(
                failure.get("relaxed_query")
            )

            doc = runtime_document(
                con,
                runtime_id,
            )

            print()
            print("-" * 68)
            print(
                f"[{index:02d}/{len(failures):02d}] "
                f"runtime_id={runtime_id}"
            )

            if doc is None:
                classification = "RUNTIME_DOCUMENT_MISSING"
                reason = "runtime_documents row is absent"

                classifications[classification] += 1

                results.append(
                    {
                        "runtime_id": runtime_id,
                        "query": original_query,
                        "classification": classification,
                        "reason": reason,
                    }
                )

                print("CLASSIFICATION :", classification)
                continue

            title = safe_text(doc["title"])
            path = safe_text(doc["file_path"])

            print("title          :", title)
            print("query          :", original_query)
            print("normalized     :", normalized_query)
            print("relaxed        :", relaxed_query)
            print("content chars  :", doc["content_chars"])
            print("media type     :", doc["media_type"])
            print(
                "content prefix :",
                compact(doc["content_prefix"]),
            )

            query_tokens = unique_tokens(
                lexical_tokens(normalized_query or original_query)
            )

            title_tokens = unique_tokens(
                lexical_tokens(title)
            )

            title_token_overlap = sorted(
                set(query_tokens)
                & set(title_tokens)
            )

            print("query tokens   :", query_tokens)
            print("title tokens   :", title_tokens)
            print("title overlap  :", title_token_overlap)

            # ------------------------------------------------
            # Membership
            # ------------------------------------------------

            memberships = []

            for table in fts_tables:
                membership = inspect_membership(
                    con,
                    table,
                    runtime_id,
                    path,
                    title,
                )
                memberships.append(membership)

            mapped_tables = [
                item["table"]
                for item in memberships
                if item.get("membership")
            ]

            print(
                "FTS membership :",
                mapped_tables if mapped_tables else "NONE",
            )

            # ------------------------------------------------
            # Query variants
            # ------------------------------------------------

            variants = query_variants(
                original_query,
                normalized_query,
                relaxed_query,
                title,
            )

            print("probe variants :", len(variants))

            # ------------------------------------------------
            # Direct FTS
            # ------------------------------------------------

            direct_probes = []

            for table in fts_tables:
                if not table.get("virtual_fts"):
                    continue

                for variant in variants:
                    probe = direct_match_probe(
                        con,
                        table,
                        variant["value"],
                        runtime_id=runtime_id,
                        expected_path=path,
                    )

                    probe["variant_kind"] = variant["kind"]

                    direct_probes.append(probe)

            direct_hits = [
                item
                for item in direct_probes
                if item.get("target_present")
            ]

            if direct_hits:
                best_direct = min(
                    direct_hits,
                    key=lambda item:
                        int(item["target_rank"]),
                )

                print(
                    "direct FTS     : HIT",
                    "table=",
                    best_direct["table"],
                    "variant=",
                    best_direct["variant_kind"],
                    "rank=",
                    best_direct["target_rank"],
                    "bm25=",
                    best_direct["target_bm25"],
                )
            else:
                print("direct FTS     : MISS")

            # ------------------------------------------------
            # Production wrapper
            # ------------------------------------------------

            production_probes = []

            for variant in variants:
                probe = production_search_probe(
                    search_catalog,
                    query=variant["value"],
                    db_path=args.db,
                    runtime_id=runtime_id,
                    expected_path=path,
                )

                probe["variant_kind"] = variant["kind"]
                probe["query"] = variant["value"]

                production_probes.append(probe)

            production_hits = [
                item
                for item in production_probes
                if item.get("best_rank") is not None
            ]

            if production_hits:
                best_production = min(
                    production_hits,
                    key=lambda item:
                        int(item["best_rank"]),
                )

                print(
                    "production     : HIT",
                    "variant=",
                    best_production["variant_kind"],
                    "rank=",
                    best_production["best_rank"],
                    "limit=",
                    best_production["best_limit"],
                )
            else:
                print("production     : MISS")

            # ------------------------------------------------
            # Classification
            # ------------------------------------------------

            classification, reason = classify(
                memberships=memberships,
                direct_probes=direct_probes,
                production_probes=production_probes,
            )

            classifications[classification] += 1

            print("CLASSIFICATION :", classification)
            print("REASON         :", reason)

            results.append(
                {
                    "runtime_id": runtime_id,
                    "title": title,
                    "file_path": path,
                    "sha256": doc["sha256"],
                    "media_type": doc["media_type"],
                    "content_chars": doc["content_chars"],
                    "content_prefix": doc["content_prefix"],
                    "original_query": original_query,
                    "normalized_query": normalized_query,
                    "relaxed_query": relaxed_query,
                    "query_tokens": query_tokens,
                    "title_tokens": title_tokens,
                    "title_token_overlap": title_token_overlap,
                    "memberships": memberships,
                    "variants": variants,
                    "direct_fts_probes": direct_probes,
                    "production_probes": production_probes,
                    "classification": classification,
                    "reason": reason,
                }
            )

        print()
        print("=" * 68)
        print(" R1G-R2 FAILURE CLASSIFICATION")
        print("=" * 68)

        for key, value in classifications.most_common():
            print(f"{key:42} : {value}")

        total = len(results)

        anatomy_complete = (
            total == 13
            and all(
                item.get("classification")
                not in (
                    None,
                    "",
                    "UNCLASSIFIED_RETRIEVAL_PATH",
                )
                for item in results
            )
        )

        elapsed = time.monotonic() - started

        print()
        print("cases expected        : 13")
        print("cases analyzed        :", total)
        print("FTS structures        :", len(fts_tables))
        print("anatomy complete      :", anatomy_complete)
        print("elapsed seconds       :", f"{elapsed:.2f}")
        print("production DB writes  : 0")
        print("production source edits: 0")
        print("=" * 68)

        report = {
            "schema": SCHEMA,
            "read_only": True,
            "expected_cases": 13,
            "cases_analyzed": total,
            "fts_structures": fts_tables,
            "production_search_source": production_source,
            "classification_counts": dict(classifications),
            "results": results,
            "anatomy_complete": anatomy_complete,
            "elapsed_seconds": elapsed,
        }

        args.report.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        args.report.write_text(
            json.dumps(
                report,
                indent=2,
                sort_keys=True,
                default=str,
            ) + "\n",
            encoding="utf-8",
        )

        fields = (
            "runtime_id",
            "classification",
            "reason",
            "original_query",
            "normalized_query",
            "title",
            "file_path",
            "content_chars",
        )

        with args.tsv.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fields,
                delimiter="\t",
            )

            writer.writeheader()

            for item in results:
                writer.writerow(
                    {
                        key: item.get(key)
                        for key in fields
                    }
                )

        return 0 if anatomy_complete else 1

    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
