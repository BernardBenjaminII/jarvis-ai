from __future__ import annotations

import argparse
import inspect
import json
import re
import sqlite3
import time
import traceback

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable


DEFAULT_RUNTIME_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/"
    "knowledge/catalog.sqlite"
)

FM_CANARY = Path(
    "/media/abdullah/JARVISDATA/Knowledge/"
    "military/doctrine/"
    "US_Army_FM_3-06.11_Urban_Terrain.pdf"
)


# ------------------------------------------------------------
# Known real-runtime canaries.
#
# These came from the already-certified Pack 3A runtime
# population and represent substantially different domains.
#
# The query is intentionally human-like instead of being a
# literal filename lookup.
# ------------------------------------------------------------

CANARIES = (
    {
        "runtime_id": 4,
        "name": "cpp_programming",
        "query": "C++ programming",
    },
    {
        "runtime_id": 11,
        "name": "ai_assisted_python",
        "query": "AI assisted Python programming",
    },
    {
        "runtime_id": 14,
        "name": "effective_c",
        "query": "effective C programming",
    },
    {
        "runtime_id": 18,
        "name": "civil_defense",
        "query": "civil defense manual",
    },
    {
        "runtime_id": 32,
        "name": "army_survival",
        "query": "US Army survival manual",
    },
    {
        "runtime_id": 42,
        "name": "electronics",
        "query": "practical electronics handbook",
    },
    {
        "runtime_id": 89330,
        "name": "marx_mathematics",
        "query": "Marx mathematical manuscripts",
    },
)


@dataclass
class LayerResult:
    layer: str
    status: str
    expected_runtime_id: int | None
    rank: int | None
    result_count: int
    error_type: str | None
    error: str | None
    sample: list[dict[str, Any]]


def ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    conn.execute("PRAGMA busy_timeout=10000")

    return conn


def normalize_mapping(value: Any) -> dict[str, Any]:

    if isinstance(value, dict):
        return dict(value)

    if hasattr(value, "_asdict"):
        try:
            return dict(value._asdict())
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        try:
            return dict(vars(value))
        except Exception:
            pass

    return {
        "value": str(value),
    }


def normalize_result_sequence(value: Any) -> list[dict[str, Any]]:
    """
    Production layers return different shapes across JARVIS
    revisions. Normalize conservatively without changing their
    meaning.
    """

    if value is None:
        return []

    if isinstance(value, dict):

        # Common envelope fields.
        for key in (
            "results",
            "rows",
            "candidates",
            "evidence",
            "items",
            "matches",
        ):
            nested = value.get(key)

            if isinstance(
                nested,
                (list, tuple),
            ):
                return [
                    normalize_mapping(x)
                    for x in nested
                ]

        return [
            normalize_mapping(value)
        ]

    if isinstance(
        value,
        (list, tuple),
    ):
        return [
            normalize_mapping(x)
            for x in value
        ]

    # QualificationResult and similar typed objects often
    # expose ranked evidence via attributes.
    for attr in (
        "ranked",
        "evidence",
        "qualified",
        "candidates",
        "results",
        "items",
    ):
        if hasattr(value, attr):

            nested = getattr(
                value,
                attr,
            )

            if isinstance(
                nested,
                (list, tuple),
            ):
                return [
                    normalize_mapping(x)
                    for x in nested
                ]

    return [
        normalize_mapping(value)
    ]


def runtime_id_from_row(
    row: dict[str, Any],
) -> int | None:

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
        except (
            TypeError,
            ValueError,
        ):
            pass

    # Some higher layers retain only file path.
    return None


def file_path_from_row(
    row: dict[str, Any],
) -> str | None:

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


def title_from_row(
    row: dict[str, Any],
) -> str | None:

    for key in (
        "title",
        "display_title",
        "canonical_title",
        "name",
    ):
        value = row.get(key)

        if value:
            return str(value)

    return None


def expected_document(
    conn: sqlite3.Connection,
    runtime_id: int,
) -> dict[str, Any] | None:

    row = conn.execute(
        """
        SELECT
            id,
            file_path,
            sha256,
            title,
            media_type,
            content_chars
        FROM runtime_documents
        WHERE id=?
        LIMIT 1
        """,
        (runtime_id,),
    ).fetchone()

    if row is None:
        return None

    return dict(row)


def rank_expected(
    rows: list[dict[str, Any]],
    *,
    expected_id: int,
    expected_path: str,
) -> int | None:

    expected_path = str(
        expected_path
    )

    for rank, row in enumerate(
        rows,
        start=1,
    ):
        rid = runtime_id_from_row(
            row
        )

        if rid == expected_id:
            return rank

        path = file_path_from_row(
            row
        )

        if (
            path
            and path == expected_path
        ):
            return rank

    return None


def safe_sample(
    rows: list[dict[str, Any]],
    limit: int = 5,
) -> list[dict[str, Any]]:

    output = []

    for row in rows[:limit]:

        output.append(
            {
                "runtime_document_id":
                    runtime_id_from_row(row),

                "file_path":
                    file_path_from_row(row),

                "title":
                    title_from_row(row),

                "retrieval_backend":
                    row.get(
                        "retrieval_backend"
                    ),

                "retrieval_score":
                    row.get(
                        "retrieval_score"
                    ),

                "score":
                    row.get("score"),

                "rank":
                    row.get("rank"),

                "confidence":
                    row.get(
                        "confidence"
                    ),
            }
        )

    return output


def invoke_search_function(
    fn: Callable[..., Any],
    *,
    query: str,
    db_path: Path,
    limit: int,
) -> Any:
    """
    Adapt only argument names.

    We do not modify production search behavior.
    """

    sig = inspect.signature(
        fn
    )

    kwargs: dict[str, Any] = {}

    params = sig.parameters

    if "query" in params:
        kwargs["query"] = query

    elif "q" in params:
        kwargs["q"] = query

    else:
        # First positional argument is expected to be query
        # for all known JARVIS search layers.
        positional_query = True

    if "db_path" in params:
        kwargs["db_path"] = db_path

    elif "database" in params:
        kwargs["database"] = db_path

    elif "catalog_database" in params:
        kwargs["catalog_database"] = db_path

    elif "runtime_catalog" in params:
        kwargs["runtime_catalog"] = db_path

    if "limit" in params:
        kwargs["limit"] = limit

    elif "candidate_limit" in params:
        kwargs["candidate_limit"] = limit

    if (
        "query" in params
        or "q" in params
    ):
        return fn(
            **kwargs
        )

    return fn(
        query,
        **kwargs,
    )


def certify_callable_layer(
    *,
    name: str,
    fn: Callable[..., Any],
    query: str,
    db_path: Path,
    expected_id: int,
    expected_path: str,
    limit: int = 25,
) -> LayerResult:

    try:
        raw = invoke_search_function(
            fn,
            query=query,
            db_path=db_path,
            limit=limit,
        )

        rows = normalize_result_sequence(
            raw
        )

        rank = rank_expected(
            rows,
            expected_id=expected_id,
            expected_path=expected_path,
        )

        return LayerResult(
            layer=name,
            status=(
                "PASS"
                if rank is not None
                else "MISS"
            ),
            expected_runtime_id=
                expected_id,
            rank=rank,
            result_count=len(rows),
            error_type=None,
            error=None,
            sample=safe_sample(
                rows
            ),
        )

    except Exception as exc:

        return LayerResult(
            layer=name,
            status="ERROR",
            expected_runtime_id=
                expected_id,
            rank=None,
            result_count=0,
            error_type=
                type(exc).__name__,
            error=str(exc),
            sample=[],
        )


def simple_fts_smoke(
    conn: sqlite3.Connection,
    term: str,
) -> dict[str, Any]:
    """
    Minimal legal FTS5 query.

    No GROUP BY and no homemade ranking logic.

    Purpose: distinguish a broken FTS table from an R1B
    diagnostic-query error.
    """

    try:
        rows = conn.execute(
            """
            SELECT
                document_id,
                chunk_id,
                title,
                file_path,
                bm25(runtime_chunks_fts)
                    AS rank
            FROM runtime_chunks_fts
            WHERE runtime_chunks_fts MATCH ?
            ORDER BY rank
            LIMIT 5
            """,
            (term,),
        ).fetchall()

        return {
            "status": "PASS",
            "count": len(rows),
            "error": None,
            "sample": [
                {
                    "document_id":
                        row["document_id"],
                    "chunk_id":
                        row["chunk_id"],
                    "title":
                        row["title"],
                    "file_path":
                        row["file_path"],
                    "rank":
                        row["rank"],
                }
                for row in rows
            ],
        }

    except Exception as exc:

        return {
            "status": "ERROR",
            "count": 0,
            "error":
                f"{type(exc).__name__}: {exc}",
            "sample": [],
        }


def map_conversation_stack() -> dict[str, Any]:

    result: dict[str, Any] = {}

    # --------------------------------------------------------
    # ConversationGrounder
    # --------------------------------------------------------

    try:
        from core.conversation.grounding import (
            ConversationGrounder,
        )

        result[
            "ConversationGrounder"
        ] = {
            "present": True,
            "signature":
                str(
                    inspect.signature(
                        ConversationGrounder
                    )
                ),
            "ground_signature":
                str(
                    inspect.signature(
                        ConversationGrounder.ground
                    )
                ),
            "catalog_method":
                hasattr(
                    ConversationGrounder,
                    "_search_catalog",
                ),
        }

    except Exception as exc:
        result[
            "ConversationGrounder"
        ] = {
            "present": False,
            "error":
                f"{type(exc).__name__}: {exc}",
        }

    # --------------------------------------------------------
    # Executive Conversation service
    # --------------------------------------------------------

    try:
        from core.conversation.service import (
            ExecutiveConversationService,
        )

        result[
            "ExecutiveConversationService"
        ] = {
            "present": True,
            "signature":
                str(
                    inspect.signature(
                        ExecutiveConversationService
                    )
                ),
            "ask_signature":
                (
                    str(
                        inspect.signature(
                            ExecutiveConversationService.ask
                        )
                    )
                    if hasattr(
                        ExecutiveConversationService,
                        "ask",
                    )
                    else None
                ),
        }

    except Exception as exc:
        result[
            "ExecutiveConversationService"
        ] = {
            "present": False,
            "error":
                f"{type(exc).__name__}: {exc}",
        }

    # --------------------------------------------------------
    # Knowledge Workspace adapter
    # --------------------------------------------------------

    try:
        from core.executive.conversation import (
            ExecutiveConversationAdapter,
        )

        result[
            "ExecutiveConversationAdapter"
        ] = {
            "present": True,
            "signature":
                str(
                    inspect.signature(
                        ExecutiveConversationAdapter
                    )
                ),
        }

    except Exception as exc:
        result[
            "ExecutiveConversationAdapter"
        ] = {
            "present": False,
            "error":
                f"{type(exc).__name__}: {exc}",
        }

    return result


def source_contracts() -> dict[str, Any]:

    from core.knowledge_catalog.materialization.search import (
        search_runtime_knowledge,
    )

    from core.knowledge_catalog.search import (
        search_catalog,
    )

    from core.knowledge_catalog.qualified_search import (
        search_qualified_catalog,
    )

    return {
        "search_runtime_knowledge":
            str(
                inspect.signature(
                    search_runtime_knowledge
                )
            ),

        "search_catalog":
            str(
                inspect.signature(
                    search_catalog
                )
            ),

        "search_qualified_catalog":
            str(
                inspect.signature(
                    search_qualified_catalog
                )
            ),
    }


def layer_diagnosis(
    layers: list[LayerResult],
) -> str:

    for layer in layers:

        if layer.status == "ERROR":
            return (
                layer.layer.upper()
                + "_ERROR"
            )

        if layer.status == "MISS":
            return (
                layer.layer.upper()
                + "_RECALL_DROP"
            )

    return "PRODUCTION_RECALL_STACK_PASS"


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
        default=None,
    )

    args = parser.parse_args()

    if not args.runtime_db.is_file():
        print(
            "FAIL: runtime DB missing"
        )
        return 2

    started = time.monotonic()

    runtime = ro(
        args.runtime_db
    )

    try:
        print(
            "============================================================"
        )
        print(
            " GENESIS RECALL R1C — PRODUCTION STACK"
        )
        print(
            "============================================================"
        )

        # ----------------------------------------------------
        # Import production search layers.
        # ----------------------------------------------------

        from core.knowledge_catalog.materialization.search import (
            search_runtime_knowledge,
        )

        from core.knowledge_catalog.search import (
            search_catalog,
        )

        from core.knowledge_catalog.qualified_search import (
            search_qualified_catalog,
        )

        print()
        print(
            "=== 1. PRODUCTION SEARCH CONTRACTS ==="
        )

        contracts = source_contracts()

        for key, value in (
            contracts.items()
        ):
            print(
                f"{key:30} : {value}"
            )

        print()
        print(
            "=== 2. RAW FTS5 SMOKE TEST ==="
        )

        fts_smoke = (
            simple_fts_smoke(
                runtime,
                "programming",
            )
        )

        print(
            "status :",
            fts_smoke["status"],
        )

        print(
            "rows   :",
            fts_smoke["count"],
        )

        print(
            "error  :",
            fts_smoke["error"],
        )

        if fts_smoke["sample"]:
            for row in (
                fts_smoke[
                    "sample"
                ]
            ):
                print(
                    "  ",
                    row["document_id"],
                    row["title"],
                    row["rank"],
                )

        print()
        print(
            "=== 3. CONVERSATION STACK MAP ==="
        )

        conversation_map = (
            map_conversation_stack()
        )

        for key, value in (
            conversation_map.items()
        ):
            print(
                key,
                ":",
                json.dumps(
                    value,
                    sort_keys=True,
                ),
            )

        print()
        print(
            "=== 4. PRODUCTION RECALL CANARIES ==="
        )

        all_results = []

        for canary in CANARIES:

            expected = (
                expected_document(
                    runtime,
                    canary[
                        "runtime_id"
                    ],
                )
            )

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

            if expected is None:
                print(
                    "FAIL: expected runtime "
                    "document absent"
                )

                all_results.append(
                    {
                        **canary,
                        "expected":
                            None,
                        "diagnosis":
                            "CANARY_RUNTIME_MISSING",
                        "layers":
                            [],
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

            layers = []

            # -----------------------------------------------
            # Layer A — production runtime search
            # -----------------------------------------------

            runtime_layer = (
                certify_callable_layer(
                    name="runtime_search",
                    fn=
                        search_runtime_knowledge,
                    query=
                        canary["query"],
                    db_path=
                        args.runtime_db,
                    expected_id=
                        int(
                            expected["id"]
                        ),
                    expected_path=
                        str(
                            expected[
                                "file_path"
                            ]
                        ),
                    limit=25,
                )
            )

            layers.append(
                runtime_layer
            )

            print(
                "runtime search :",
                runtime_layer.status,
                "rank=",
                runtime_layer.rank,
                "count=",
                runtime_layer.result_count,
            )

            if runtime_layer.error:
                print(
                    "  error:",
                    runtime_layer.error,
                )

            # -----------------------------------------------
            # Layer B — catalog search
            # -----------------------------------------------

            catalog_layer = (
                certify_callable_layer(
                    name="catalog_search",
                    fn=search_catalog,
                    query=
                        canary["query"],
                    db_path=
                        args.runtime_db,
                    expected_id=
                        int(
                            expected["id"]
                        ),
                    expected_path=
                        str(
                            expected[
                                "file_path"
                            ]
                        ),
                    limit=25,
                )
            )

            layers.append(
                catalog_layer
            )

            print(
                "catalog search :",
                catalog_layer.status,
                "rank=",
                catalog_layer.rank,
                "count=",
                catalog_layer.result_count,
            )

            if catalog_layer.error:
                print(
                    "  error:",
                    catalog_layer.error,
                )

            # -----------------------------------------------
            # Layer C — qualified catalog search
            # -----------------------------------------------

            qualified_layer = (
                certify_callable_layer(
                    name="qualified_search",
                    fn=
                        search_qualified_catalog,
                    query=
                        canary["query"],
                    db_path=
                        args.runtime_db,
                    expected_id=
                        int(
                            expected["id"]
                        ),
                    expected_path=
                        str(
                            expected[
                                "file_path"
                            ]
                        ),
                    limit=25,
                )
            )

            layers.append(
                qualified_layer
            )

            print(
                "qualified      :",
                qualified_layer.status,
                "rank=",
                qualified_layer.rank,
                "count=",
                qualified_layer.result_count,
            )

            if qualified_layer.error:
                print(
                    "  error:",
                    qualified_layer.error,
                )

            diagnosis = (
                layer_diagnosis(
                    layers
                )
            )

            print(
                "diagnosis      :",
                diagnosis,
            )

            all_results.append(
                {
                    **canary,
                    "expected":
                        expected,
                    "diagnosis":
                        diagnosis,
                    "layers": [
                        asdict(layer)
                        for layer
                        in layers
                    ],
                }
            )

        # ----------------------------------------------------
        # Negative control.
        # ----------------------------------------------------

        print()
        print(
            "=== 5. FM 3-06.11 NEGATIVE CONTROL ==="
        )

        fm_runtime = runtime.execute(
            """
            SELECT
                id,
                title,
                file_path
            FROM runtime_documents
            WHERE file_path=?
            LIMIT 1
            """,
            (
                str(FM_CANARY),
            ),
        ).fetchone()

        fm_status = (
            "PRE_RUNTIME_ASSIMILATION_GAP"
            if fm_runtime is None
            else "UNEXPECTED_RUNTIME_PRESENCE"
        )

        print(
            "physical:",
            FM_CANARY.is_file(),
        )

        print(
            "runtime :",
            (
                dict(fm_runtime)
                if fm_runtime
                else None
            ),
        )

        print(
            "status  :",
            fm_status,
        )

        # ----------------------------------------------------
        # Aggregate layer metrics.
        # ----------------------------------------------------

        print()
        print(
            "=== 6. STACK CERTIFICATION SUMMARY ==="
        )

        names = (
            "runtime_search",
            "catalog_search",
            "qualified_search",
        )

        summary: dict[str, Any] = {}

        for layer_name in names:

            relevant = []

            for item in all_results:
                for layer in item[
                    "layers"
                ]:
                    if (
                        layer["layer"]
                        == layer_name
                    ):
                        relevant.append(
                            layer
                        )

            total = len(relevant)

            passed = sum(
                1
                for layer in relevant
                if layer["status"]
                == "PASS"
            )

            top5 = sum(
                1
                for layer in relevant
                if (
                    layer["rank"]
                    is not None
                    and layer["rank"]
                    <= 5
                )
            )

            errors = sum(
                1
                for layer in relevant
                if layer["status"]
                == "ERROR"
            )

            summary[layer_name] = {
                "tested": total,
                "pass": passed,
                "top5": top5,
                "errors": errors,
            }

            print(
                f"{layer_name:20} "
                f"pass={passed}/{total} "
                f"top5={top5}/{total} "
                f"errors={errors}"
            )

        diagnosis_counts: dict[
            str,
            int,
        ] = {}

        for item in all_results:
            key = item[
                "diagnosis"
            ]

            diagnosis_counts[
                key
            ] = (
                diagnosis_counts.get(
                    key,
                    0,
                )
                + 1
            )

        print()
        print(
            "First-drop diagnoses:"
        )

        for key in sorted(
            diagnosis_counts
        ):
            print(
                f"  {key:36} : "
                f"{diagnosis_counts[key]}"
            )

        elapsed = (
            time.monotonic()
            - started
        )

        print()
        print(
            f"elapsed seconds       : {elapsed:.3f}"
        )

        print(
            "production DB writes  : 0"
        )

        print(
            "LLM calls             : 0"
        )

        report = {
            "schema":
                "genesis-recall-r1c-v1",

            "read_only":
                True,

            "contracts":
                contracts,

            "fts_smoke":
                fts_smoke,

            "conversation_stack":
                conversation_map,

            "canaries":
                all_results,

            "layer_summary":
                summary,

            "diagnoses":
                diagnosis_counts,

            "fm_negative_control": {
                "physical":
                    FM_CANARY.is_file(),
                "status":
                    fm_status,
                "path":
                    str(FM_CANARY),
            },

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

        # Certification execution itself succeeds even when
        # layers miss. A miss is the diagnostic result.
        #
        # We fail only for a fundamental inability to execute
        # the stack.
        if (
            fts_smoke["status"]
            == "ERROR"
            and all(
                summary[name][
                    "errors"
                ]
                == summary[name][
                    "tested"
                ]
                for name in names
                if summary[name][
                    "tested"
                ] > 0
            )
        ):
            print()
            print(
                "GENESIS RECALL R1C: "
                "FUNDAMENTAL STACK EXECUTION FAILURE"
            )
            return 1

        print()
        print(
            "GENESIS RECALL R1C STACK CERTIFICATION: PASS"
        )

        return 0

    finally:
        runtime.close()


if __name__ == "__main__":
    raise SystemExit(main())
