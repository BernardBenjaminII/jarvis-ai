from __future__ import annotations

import argparse
import dataclasses
import inspect
import json
import sqlite3
import time
import traceback

from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_RUNTIME_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/"
    "knowledge/catalog.sqlite"
)


CANARIES = (
    {
        "runtime_id": 4,
        "name": "cpp_programming",
        "query": "C++ programming",
        "r1c": "PASS",
    },
    {
        "runtime_id": 11,
        "name": "ai_assisted_python",
        "query": "AI assisted Python programming",
        "r1c": "QUALIFIED_SEARCH_RECALL_DROP",
    },
    {
        "runtime_id": 14,
        "name": "effective_c",
        "query": "effective C programming",
        "r1c": "PASS",
    },
    {
        "runtime_id": 18,
        "name": "civil_defense",
        "query": "civil defense manual",
        "r1c": "PASS",
    },
    {
        "runtime_id": 32,
        "name": "army_survival",
        "query": "US Army survival manual",
        "r1c": "PASS",
    },
    {
        "runtime_id": 42,
        "name": "electronics",
        "query": "practical electronics handbook",
        "r1c": "PASS",
    },
    {
        "runtime_id": 89330,
        "name": "marx_mathematics",
        "query": "Marx mathematical manuscripts",
        "r1c": "PASS",
    },
)


def ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def serial(value: Any) -> Any:
    """
    Convert arbitrary production objects to JSON-safe
    reconnaissance structures without modifying them.
    """

    if value is None:
        return None

    if isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, sqlite3.Row):
        return {
            key: serial(value[key])
            for key in value.keys()
        }

    if dataclasses.is_dataclass(value):
        try:
            return serial(
                dataclasses.asdict(value)
            )
        except Exception:
            pass

    if isinstance(value, dict):
        return {
            str(k): serial(v)
            for k, v in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            serial(x)
            for x in value
        ]

    if hasattr(value, "_asdict"):
        try:
            return serial(value._asdict())
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        try:
            return {
                key: serial(val)
                for key, val
                in vars(value).items()
                if not key.startswith("__")
            }
        except Exception:
            pass

    return repr(value)


def rows(value: Any) -> list[dict[str, Any]]:
    """
    Normalize common production result envelopes.
    """

    if value is None:
        return []

    if isinstance(value, list):
        return [
            x if isinstance(x, dict)
            else serial(x)
            for x in value
        ]

    if isinstance(value, tuple):
        return [
            x if isinstance(x, dict)
            else serial(x)
            for x in value
        ]

    if isinstance(value, dict):
        for key in (
            "results",
            "items",
            "candidates",
            "evidence",
            "qualified",
            "ranked",
            "matches",
        ):
            candidate = value.get(key)
            if isinstance(candidate, (list, tuple)):
                return [
                    x if isinstance(x, dict)
                    else serial(x)
                    for x in candidate
                ]
        return [value]

    for attr in (
        "results",
        "items",
        "candidates",
        "evidence",
        "qualified",
        "ranked",
        "matches",
    ):
        if hasattr(value, attr):
            candidate = getattr(value, attr)
            if isinstance(candidate, (list, tuple)):
                return [
                    x if isinstance(x, dict)
                    else serial(x)
                    for x in candidate
                ]

    converted = serial(value)

    if isinstance(converted, dict):
        return [converted]

    return []


def runtime_id(row: dict[str, Any]) -> int | None:
    for key in (
        "runtime_document_id",
        "document_id",
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


def row_path(row: dict[str, Any]) -> str | None:
    for key in (
        "file_path",
        "path",
        "document_path",
        "source_path",
    ):
        value = row.get(key)
        if value:
            return str(value)

    return None


def expected_document(
    conn: sqlite3.Connection,
    rid: int,
) -> dict[str, Any] | None:

    result = conn.execute(
        """
        SELECT
            id,
            file_path,
            sha256,
            title,
            media_type,
            content_chars,
            materialized_at,
            updated_at
        FROM runtime_documents
        WHERE id=?
        LIMIT 1
        """,
        (rid,),
    ).fetchone()

    return (
        dict(result)
        if result is not None
        else None
    )


def rank_of(
    result_rows: list[dict[str, Any]],
    expected: dict[str, Any],
) -> int | None:

    expected_id = int(expected["id"])
    expected_path = str(expected["file_path"])

    for rank, row in enumerate(
        result_rows,
        start=1,
    ):
        if runtime_id(row) == expected_id:
            return rank

        path = row_path(row)

        if path and path == expected_path:
            return rank

    return None


def find_expected_row(
    result_rows: list[dict[str, Any]],
    expected: dict[str, Any],
) -> dict[str, Any] | None:

    expected_id = int(expected["id"])
    expected_path = str(expected["file_path"])

    for row in result_rows:

        if runtime_id(row) == expected_id:
            return row

        path = row_path(row)

        if path and path == expected_path:
            return row

    return None


def module_inventory(module: Any) -> dict[str, Any]:

    inventory: dict[str, Any] = {
        "module":
            getattr(module, "__name__", None),

        "file":
            getattr(module, "__file__", None),

        "classes": {},
        "functions": {},
        "constants": {},
    }

    for name, obj in inspect.getmembers(module):

        if name.startswith("__"):
            continue

        try:
            if inspect.isclass(obj):
                if getattr(obj, "__module__", None) == module.__name__:
                    methods = {}

                    for mname, method in inspect.getmembers(
                        obj,
                        predicate=inspect.isfunction,
                    ):
                        if mname.startswith("__"):
                            continue

                        try:
                            methods[mname] = str(
                                inspect.signature(method)
                            )
                        except Exception:
                            methods[mname] = "?"

                    inventory["classes"][name] = {
                        "signature":
                            safe_signature(obj),
                        "methods":
                            methods,
                    }

            elif inspect.isfunction(obj):
                if getattr(obj, "__module__", None) == module.__name__:
                    inventory["functions"][name] = (
                        safe_signature(obj)
                    )

            elif name.isupper():
                if isinstance(
                    obj,
                    (
                        str,
                        int,
                        float,
                        bool,
                        tuple,
                        list,
                        dict,
                        type(None),
                    ),
                ):
                    inventory["constants"][name] = serial(obj)

        except Exception:
            pass

    return inventory


def safe_signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception:
        return "?"


def source_excerpt(obj: Any) -> str | None:
    try:
        return inspect.getsource(obj)
    except Exception:
        return None


def inspect_engine(engine: Any) -> dict[str, Any]:

    result = {
        "class":
            f"{type(engine).__module__}.{type(engine).__name__}",

        "state":
            serial(
                getattr(engine, "__dict__", {})
            ),

        "methods": {},
    }

    for name, method in inspect.getmembers(
        engine,
        predicate=callable,
    ):
        if name.startswith("__"):
            continue

        if name.startswith("_") and name not in (
            "_qualify",
            "_score",
            "_evaluate",
            "_accept",
            "_reject",
        ):
            continue

        try:
            result["methods"][name] = (
                safe_signature(method)
            )
        except Exception:
            pass

    return result


def table_inventory(
    conn: sqlite3.Connection,
) -> dict[str, Any]:

    tables = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type IN ('table', 'view')
        ORDER BY name
        """
    ).fetchall()

    output: dict[str, Any] = {}

    for item in tables:
        name = item["name"]

        try:
            columns = conn.execute(
                f'PRAGMA table_info("{name}")'
            ).fetchall()

            output[name] = [
                {
                    "name": c["name"],
                    "type": c["type"],
                    "notnull": c["notnull"],
                    "pk": c["pk"],
                }
                for c in columns
            ]

        except Exception as exc:
            output[name] = {
                "error":
                    f"{type(exc).__name__}: {exc}"
            }

    return output


def candidate_catalog_presence(
    conn: sqlite3.Connection,
    expected: dict[str, Any],
    inventory: dict[str, Any],
) -> dict[str, Any]:
    """
    Determine where the runtime document is represented across
    likely higher catalog/qualification tables.

    This is schema-adaptive and read-only. It only queries
    tables with obviously relevant identity/path columns.
    """

    expected_id = int(expected["id"])
    expected_path = str(expected["file_path"])
    expected_sha = str(expected["sha256"])

    result: dict[str, Any] = {}

    id_names = {
        "runtime_document_id",
        "document_id",
        "runtime_id",
    }

    path_names = {
        "file_path",
        "path",
        "document_path",
        "source_path",
    }

    sha_names = {
        "sha256",
        "content_sha256",
        "document_sha256",
    }

    for table, cols in inventory.items():

        if not isinstance(cols, list):
            continue

        names = {
            str(c["name"])
            for c in cols
        }

        id_cols = sorted(
            names & id_names
        )

        path_cols = sorted(
            names & path_names
        )

        sha_cols = sorted(
            names & sha_names
        )

        predicates = []
        params: list[Any] = []

        for col in id_cols:
            predicates.append(
                f'"{col}" = ?'
            )
            params.append(expected_id)

        for col in path_cols:
            predicates.append(
                f'"{col}" = ?'
            )
            params.append(expected_path)

        for col in sha_cols:
            predicates.append(
                f'"{col}" = ?'
            )
            params.append(expected_sha)

        if not predicates:
            continue

        # Avoid FTS shadow tables and obvious high-volume chunk
        # bodies. We're mapping document/catalog awareness,
        # not repeating retrieval.
        lower = table.lower()

        if (
            lower.startswith("runtime_chunks_fts_")
            or lower in {
                "runtime_chunks",
                "runtime_chunks_fts",
            }
        ):
            continue

        try:
            query = (
                f'SELECT COUNT(*) AS n '
                f'FROM "{table}" '
                f'WHERE '
                + " OR ".join(predicates)
            )

            count = conn.execute(
                query,
                params,
            ).fetchone()["n"]

            result[table] = {
                "count": int(count),
                "identity_columns": {
                    "id": id_cols,
                    "path": path_cols,
                    "sha": sha_cols,
                },
            }

        except Exception as exc:
            result[table] = {
                "error":
                    f"{type(exc).__name__}: {exc}"
            }

    return result


def nonzero_presence(
    presence: dict[str, Any],
) -> list[str]:

    output = []

    for table, info in presence.items():
        if (
            isinstance(info, dict)
            and int(info.get("count", 0)) > 0
        ):
            output.append(table)

    return sorted(output)


def diff_rows(
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> dict[str, Any]:

    if before is None:
        before = {}

    if after is None:
        after = {}

    keys = sorted(
        set(before) | set(after)
    )

    diff = {}

    for key in keys:
        a = before.get(key)
        b = after.get(key)

        if a != b:
            diff[key] = {
                "catalog":
                    serial(a),
                "qualified":
                    serial(b),
            }

    return diff


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--runtime-db",
        type=Path,
        default=DEFAULT_RUNTIME_DB,
    )

    parser.add_argument(
        "--json",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    if not args.runtime_db.is_file():
        print("FAIL: runtime DB missing")
        return 2

    started = time.monotonic()

    conn = ro(args.runtime_db)

    try:
        # ----------------------------------------------------
        # Import exact production components.
        # ----------------------------------------------------

        import core.knowledge_catalog.qualified_search as qs

        from core.knowledge_catalog.search import (
            search_catalog,
        )

        from core.knowledge_catalog.qualified_search import (
            search_qualified_catalog,
        )

        print(
            "============================================================"
        )
        print(
            " GENESIS RECALL R1D"
        )
        print(
            " QUALIFICATION GATE & CATALOG AWARENESS"
        )
        print(
            "============================================================"
        )

        # ----------------------------------------------------
        # 1. Qualification implementation inventory
        # ----------------------------------------------------

        print()
        print(
            "=== 1. QUALIFICATION IMPLEMENTATION INVENTORY ==="
        )

        inventory = module_inventory(qs)

        print(
            "module:",
            inventory["module"],
        )

        print(
            "file  :",
            inventory["file"],
        )

        print()
        print("Functions:")

        for name, sig in inventory[
            "functions"
        ].items():
            print(
                f"  {name}{sig}"
            )

        print()
        print("Classes:")

        for name, info in inventory[
            "classes"
        ].items():
            print(
                f"  {name}{info['signature']}"
            )

            for mname, msig in info[
                "methods"
            ].items():
                print(
                    f"      {mname}{msig}"
                )

        print()
        print("Constants:")

        for name, value in inventory[
            "constants"
        ].items():
            print(
                f"  {name} = {value}"
            )

        # ----------------------------------------------------
        # 2. Qualification engine state
        # ----------------------------------------------------

        print()
        print(
            "=== 2. QUALIFICATION ENGINE STATE ==="
        )

        engine = None
        engine_error = None

        engine_class = getattr(
            qs,
            "QualificationEngine",
            None,
        )

        if engine_class is None:
            print(
                "QualificationEngine: NOT EXPORTED"
            )
        else:
            try:
                engine = engine_class()

                engine_state = inspect_engine(
                    engine
                )

                print(
                    json.dumps(
                        engine_state,
                        indent=2,
                        sort_keys=True,
                        default=str,
                    )
                )

            except Exception as exc:
                engine_error = (
                    f"{type(exc).__name__}: {exc}"
                )

                print(
                    "ENGINE INIT ERROR:",
                    engine_error,
                )

        # ----------------------------------------------------
        # 3. Runtime schema / catalog awareness inventory
        # ----------------------------------------------------

        print()
        print(
            "=== 3. CATALOG AWARENESS SCHEMA ==="
        )

        db_inventory = table_inventory(
            conn
        )

        for table, cols in db_inventory.items():

            if not isinstance(cols, list):
                continue

            interesting = {
                c["name"]
                for c in cols
            }

            if interesting & {
                "runtime_document_id",
                "document_id",
                "runtime_id",
                "file_path",
                "path",
                "sha256",
                "qualification_state",
                "status",
                "confidence",
                "authority",
                "quality",
            }:
                print(
                    f"{table}: "
                    + ", ".join(
                        c["name"]
                        for c in cols
                    )
                )

        # ----------------------------------------------------
        # 4. Canary comparison
        # ----------------------------------------------------

        print()
        print(
            "=== 4. QUALIFICATION CANARY COMPARISON ==="
        )

        reports = []

        for canary in CANARIES:

            print()
            print(
                "------------------------------------------------------------"
            )

            print(
                "CANARY:",
                canary["name"],
            )

            print(
                "query :",
                canary["query"],
            )

            expected = expected_document(
                conn,
                canary["runtime_id"],
            )

            if expected is None:

                print(
                    "FAIL: runtime canary missing"
                )

                reports.append(
                    {
                        **canary,
                        "status":
                            "RUNTIME_CANARY_MISSING",
                    }
                )

                continue

            print(
                "runtime id :",
                expected["id"],
            )

            print(
                "title      :",
                expected["title"],
            )

            # -----------------------------------------------
            # Catalog retrieval before qualification
            # -----------------------------------------------

            try:
                catalog_raw = search_catalog(
                    canary["query"],
                    db_path=args.runtime_db,
                    limit=25,
                )

                catalog_rows = rows(
                    catalog_raw
                )

                catalog_rank = rank_of(
                    catalog_rows,
                    expected,
                )

                catalog_expected = find_expected_row(
                    catalog_rows,
                    expected,
                )

                print(
                    "catalog rank :",
                    catalog_rank,
                )

                print(
                    "catalog rows :",
                    len(catalog_rows),
                )

            except Exception as exc:

                catalog_rows = []
                catalog_rank = None
                catalog_expected = None

                print(
                    "CATALOG ERROR:",
                    f"{type(exc).__name__}: {exc}",
                )

            # -----------------------------------------------
            # Production qualification
            # -----------------------------------------------

            try:
                kwargs = {
                    "db_path":
                        args.runtime_db,
                    "limit":
                        25,
                }

                if engine is not None:
                    kwargs["engine"] = engine

                qualified_raw = (
                    search_qualified_catalog(
                        canary["query"],
                        **kwargs,
                    )
                )

                qualified_rows = rows(
                    qualified_raw
                )

                qualified_rank = rank_of(
                    qualified_rows,
                    expected,
                )

                qualified_expected = (
                    find_expected_row(
                        qualified_rows,
                        expected,
                    )
                )

                print(
                    "qualified rank:",
                    qualified_rank,
                )

                print(
                    "qualified rows:",
                    len(qualified_rows),
                )

            except Exception as exc:

                qualified_rows = []
                qualified_rank = None
                qualified_expected = None

                print(
                    "QUALIFIED ERROR:",
                    f"{type(exc).__name__}: {exc}",
                )

            # -----------------------------------------------
            # Exact before/after candidate state
            # -----------------------------------------------

            print()
            print(
                "Candidate before qualification:"
            )

            print(
                json.dumps(
                    serial(
                        catalog_expected
                    ),
                    indent=2,
                    sort_keys=True,
                    default=str,
                )
            )

            print()
            print(
                "Candidate after qualification:"
            )

            print(
                json.dumps(
                    serial(
                        qualified_expected
                    ),
                    indent=2,
                    sort_keys=True,
                    default=str,
                )
            )

            candidate_diff = diff_rows(
                catalog_expected,
                qualified_expected,
            )

            # -----------------------------------------------
            # Catalog-awareness presence
            # -----------------------------------------------

            presence = (
                candidate_catalog_presence(
                    conn,
                    expected,
                    db_inventory,
                )
            )

            represented = (
                nonzero_presence(
                    presence
                )
            )

            print()
            print(
                "Catalog-aware tables:"
            )

            if represented:
                for table in represented:
                    print(
                        "  ",
                        table,
                        presence[table][
                            "count"
                        ],
                    )
            else:
                print(
                    "  NONE FOUND"
                )

            # -----------------------------------------------
            # Classify the observed boundary.
            # -----------------------------------------------

            if catalog_rank is None:

                diagnosis = (
                    "PRE_QUALIFICATION_RETRIEVAL_MISS"
                )

            elif qualified_rank is not None:

                diagnosis = (
                    "QUALIFICATION_ACCEPTED"
                )

            elif len(qualified_rows) == 0:

                diagnosis = (
                    "QUALIFICATION_ZERO_RESULT_DROP"
                )

            else:

                diagnosis = (
                    "QUALIFICATION_CANDIDATE_DROP"
                )

            print()
            print(
                "DIAGNOSIS:",
                diagnosis,
            )

            reports.append(
                {
                    **canary,

                    "expected":
                        expected,

                    "catalog": {
                        "rank":
                            catalog_rank,
                        "count":
                            len(catalog_rows),
                        "candidate":
                            serial(
                                catalog_expected
                            ),
                    },

                    "qualified": {
                        "rank":
                            qualified_rank,
                        "count":
                            len(qualified_rows),
                        "candidate":
                            serial(
                                qualified_expected
                            ),
                    },

                    "candidate_diff":
                        candidate_diff,

                    "catalog_awareness": {
                        "represented_tables":
                            represented,
                        "presence":
                            presence,
                    },

                    "diagnosis":
                        diagnosis,
                }
            )

        # ----------------------------------------------------
        # 5. Accepted vs rejected structural comparison
        # ----------------------------------------------------

        print()
        print(
            "=== 5. ACCEPTED VS REJECTED COMPARISON ==="
        )

        accepted = [
            item
            for item in reports
            if item.get(
                "diagnosis"
            ) == "QUALIFICATION_ACCEPTED"
        ]

        rejected = [
            item
            for item in reports
            if item.get(
                "diagnosis"
            ) in {
                "QUALIFICATION_ZERO_RESULT_DROP",
                "QUALIFICATION_CANDIDATE_DROP",
            }
        ]

        print(
            "accepted:",
            len(accepted),
        )

        print(
            "rejected:",
            len(rejected),
        )

        accepted_tables = Counter()

        rejected_tables = Counter()

        for item in accepted:
            for table in (
                item.get(
                    "catalog_awareness",
                    {}
                ).get(
                    "represented_tables",
                    []
                )
            ):
                accepted_tables[
                    table
                ] += 1

        for item in rejected:
            for table in (
                item.get(
                    "catalog_awareness",
                    {}
                ).get(
                    "represented_tables",
                    []
                )
            ):
                rejected_tables[
                    table
                ] += 1

        print()
        print(
            "Table representation:"
        )

        all_tables = sorted(
            set(accepted_tables)
            | set(rejected_tables)
        )

        for table in all_tables:
            print(
                f"  {table:40} "
                f"accepted={accepted_tables[table]} "
                f"rejected={rejected_tables[table]}"
            )

        # ----------------------------------------------------
        # 6. Qualification source excerpts
        # ----------------------------------------------------

        print()
        print(
            "=== 6. QUALIFICATION DECISION SOURCE ==="
        )

        decision_sources = {}

        targets = [
            "search_qualified_catalog",
            "QualificationEngine",
        ]

        for target in targets:

            obj = getattr(
                qs,
                target,
                None,
            )

            if obj is None:
                continue

            excerpt = source_excerpt(
                obj
            )

            decision_sources[
                target
            ] = excerpt

            print()
            print(
                f"--- {target} ---"
            )

            if excerpt:
                print(excerpt)
            else:
                print(
                    "SOURCE UNAVAILABLE"
                )

        # ----------------------------------------------------
        # 7. Summary
        # ----------------------------------------------------

        print()
        print(
            "=== 7. R1D SUMMARY ==="
        )

        diagnoses = Counter(
            item.get(
                "diagnosis",
                "UNKNOWN",
            )
            for item in reports
        )

        for name, count in sorted(
            diagnoses.items()
        ):
            print(
                f"{name:40} : {count}"
            )

        failed_canary = next(
            (
                item
                for item in reports
                if item.get("runtime_id")
                == 11
            ),
            None,
        )

        print()
        print(
            "AI-assisted Python boundary:"
        )

        if failed_canary:
            print(
                "  catalog rank    :",
                failed_canary.get(
                    "catalog",
                    {}
                ).get("rank"),
            )

            print(
                "  qualified rank  :",
                failed_canary.get(
                    "qualified",
                    {}
                ).get("rank"),
            )

            print(
                "  qualified count :",
                failed_canary.get(
                    "qualified",
                    {}
                ).get("count"),
            )

            print(
                "  represented in  :",
                ", ".join(
                    failed_canary.get(
                        "catalog_awareness",
                        {}
                    ).get(
                        "represented_tables",
                        []
                    )
                )
                or "NONE",
            )

            print(
                "  diagnosis       :",
                failed_canary.get(
                    "diagnosis"
                ),
            )

        elapsed = (
            time.monotonic()
            - started
        )

        report = {
            "schema":
                "genesis-recall-r1d-v1",

            "read_only":
                True,

            "production_db_writes":
                0,

            "llm_calls":
                0,

            "qualification_inventory":
                inventory,

            "qualification_engine":
                (
                    inspect_engine(engine)
                    if engine is not None
                    else {
                        "error":
                            engine_error,
                    }
                ),

            "database_schema":
                db_inventory,

            "canaries":
                reports,

            "accepted_table_counts":
                dict(accepted_tables),

            "rejected_table_counts":
                dict(rejected_tables),

            "decision_sources":
                decision_sources,

            "diagnoses":
                dict(diagnoses),

            "elapsed_seconds":
                elapsed,
        }

        args.json.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        args.json.write_text(
            json.dumps(
                report,
                indent=2,
                sort_keys=True,
                default=str,
            ),
            encoding="utf-8",
        )

        print()
        print(
            "JSON report:",
            args.json,
        )

        print(
            f"elapsed seconds: {elapsed:.3f}"
        )

        print()
        print(
            "GENESIS RECALL R1D RECONNAISSANCE: PASS"
        )

        return 0

    except Exception:

        print()
        print(
            "R1D FUNDAMENTAL EXECUTION ERROR"
        )

        traceback.print_exc()

        return 1

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
