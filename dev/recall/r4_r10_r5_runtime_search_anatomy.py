from __future__ import annotations

import ast
import csv
import inspect
import json
import math
import sqlite3
import sys
import time
import types

from collections import Counter
from pathlib import Path
from typing import Any, Mapping


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

OUTDIR = PROJECT / "artifacts/genesis_recall"

DETAIL_IN = (
    OUTDIR
    / "r4_r10_r4_candidate_generation_rank_origin.tsv"
)

REPORT = (
    OUTDIR
    / "r4_r10_r5_runtime_search_anatomy.json"
)

DETAIL = (
    OUTDIR
    / "r4_r10_r5_runtime_search_anatomy.tsv"
)

SQL_TRACE = (
    OUTDIR
    / "r4_r10_r5_sql_trace.tsv"
)

CALL_TRACE = (
    OUTDIR
    / "r4_r10_r5_runtime_helper_trace.tsv"
)

SCORE_TRACE = (
    OUTDIR
    / "r4_r10_r5_score_trace.tsv"
)

MISSING_TRACE = (
    OUTDIR
    / "r4_r10_r5_two_case_generation_failure.tsv"
)

SOURCE_MAP = (
    OUTDIR
    / "r4_r10_r5_runtime_search_source_map.txt"
)

TRACE = (
    OUTDIR
    / "r4_r10_r5_runtime_search_trace.txt"
)


sys.path.insert(
    0,
    str(PROJECT),
)


import core.knowledge_catalog.search as search_module

from core.knowledge_catalog.search import (
    search_runtime_knowledge,
)


EXPECTED = 9

EXPECTED_CLASSES = {
    "SEARCH_RANK_HORIZON_FAILURE": 7,
    "CANDIDATE_NOT_GENERATED": 2,
}

MISSING_IDS = {
    "79286",
    "85384",
}


# ============================================================
# HELPERS
# ============================================================

def read_tsv(
    path: Path,
) -> list[dict[str, str]]:

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:

        return list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )


def write_tsv(
    path: Path,
    rows: list[dict[str, Any]],
) -> None:

    if not rows:
        path.write_text(
            "",
            encoding="utf-8",
        )
        return

    fields = []
    seen = set()

    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(rows)


def to_map(
    value: Any,
) -> dict[str, Any]:

    if isinstance(
        value,
        Mapping,
    ):
        return dict(value)

    if isinstance(
        value,
        sqlite3.Row,
    ):
        return dict(value)

    if hasattr(
        value,
        "keys",
    ):
        try:
            return {
                key: value[key]
                for key in value.keys()
            }
        except Exception:
            pass

    if hasattr(
        value,
        "_asdict",
    ):
        try:
            return dict(
                value._asdict()
            )
        except Exception:
            pass

    try:
        return dict(
            vars(value)
        )
    except Exception:
        return {}


def text(
    value: Any,
) -> str:

    if value is None:
        return ""

    return str(
        value
    ).strip()


def first_present(
    row: Mapping[str, Any],
    *names: str,
) -> str:

    lowered = {
        str(k).casefold(): k
        for k in row.keys()
    }

    for name in names:

        actual = lowered.get(
            name.casefold()
        )

        if actual is None:
            continue

        value = row.get(
            actual
        )

        if value not in (
            None,
            "",
        ):
            return text(value)

    return ""


def identity_equal(
    left: Any,
    right: Any,
) -> bool:

    a = text(left)
    b = text(right)

    if not a or not b:
        return False

    if a.casefold() == b.casefold():
        return True

    try:
        return int(a) == int(b)
    except Exception:
        return False


def document_id_from(
    value: Any,
) -> str:

    row = to_map(value)

    return first_present(
        row,
        "document_id",
        "runtime_document_id",
        "doc_id",
    )


def chunk_id_from(
    value: Any,
) -> str:

    row = to_map(value)

    return first_present(
        row,
        "chunk_id",
        "source_id",
        "id",
    )


def score_fields(
    value: Any,
) -> dict[str, Any]:

    row = to_map(value)

    result = {}

    for key, item in row.items():

        low = str(key).casefold()

        if any(
            marker in low
            for marker in (
                "score",
                "rank",
                "confidence",
                "bm25",
                "weight",
                "similarity",
                "distance",
                "coverage",
            )
        ):
            result[str(key)] = item

    return result


def safe_json(
    value: Any,
) -> str:

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
    except Exception:
        return repr(value)


def summarize_iterable(
    value: Any,
    target_id: str,
) -> dict[str, Any]:

    summary = {
        "count": "",
        "target_present": False,
        "target_rank": "",
        "target_chunk_id": "",
        "target_scores_json": "",
    }

    if not isinstance(
        value,
        (
            list,
            tuple,
        ),
    ):
        return summary

    summary["count"] = len(value)

    for rank, item in enumerate(
        value,
        start=1,
    ):

        if identity_equal(
            document_id_from(item),
            target_id,
        ):

            summary["target_present"] = True
            summary["target_rank"] = rank
            summary["target_chunk_id"] = (
                chunk_id_from(item)
            )
            summary["target_scores_json"] = safe_json(
                score_fields(item)
            )

            break

    return summary


# ============================================================
# RESOLVE IMPLEMENTATION MODULE
# ============================================================

runtime_fn = search_runtime_knowledge

runtime_module_name = runtime_fn.__module__

runtime_module = sys.modules[
    runtime_module_name
]

runtime_file = inspect.getsourcefile(
    runtime_fn
)

if not runtime_file:
    raise RuntimeError(
        "unable to resolve search_runtime_knowledge source file"
    )

runtime_file_path = Path(
    runtime_file
)

runtime_source = runtime_file_path.read_text(
    encoding="utf-8"
)

runtime_tree = ast.parse(
    runtime_source
)


# ============================================================
# FIND FUNCTION AST
# ============================================================

runtime_node = None

for node in ast.walk(
    runtime_tree
):

    if isinstance(
        node,
        (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
        ),
    ) and node.name == runtime_fn.__name__:

        runtime_node = node
        break


if runtime_node is None:
    raise RuntimeError(
        "search_runtime_knowledge AST node unavailable"
    )


def call_name(
    call: ast.Call,
) -> str:

    fn = call.func

    if isinstance(
        fn,
        ast.Name,
    ):
        return fn.id

    if isinstance(
        fn,
        ast.Attribute,
    ):

        pieces = []
        current = fn

        while isinstance(
            current,
            ast.Attribute,
        ):
            pieces.append(
                current.attr
            )
            current = current.value

        if isinstance(
            current,
            ast.Name,
        ):
            pieces.append(
                current.id
            )

        return ".".join(
            reversed(
                pieces
            )
        )

    return ast.dump(
        fn,
        include_attributes=False,
    )


runtime_direct_calls = []

for node in ast.walk(
    runtime_node
):

    if isinstance(
        node,
        ast.Call,
    ):
        runtime_direct_calls.append(
            (
                node.lineno,
                call_name(node),
            )
        )


# ============================================================
# STATIC STRING / SQL EXTRACTION
# ============================================================

string_literals = []

for node in ast.walk(
    runtime_node
):

    if (
        isinstance(
            node,
            ast.Constant,
        )
        and
        isinstance(
            node.value,
            str,
        )
    ):

        value = node.value.strip()

        if value:
            string_literals.append(
                (
                    node.lineno,
                    value,
                )
            )


sql_like_literals = [
    (
        lineno,
        value,
    )
    for lineno, value in string_literals
    if any(
        marker in value.casefold()
        for marker in (
            "select ",
            " from ",
            " match ",
            " where ",
            " order by ",
            " limit ",
            "with ",
        )
    )
]


# ============================================================
# IDENTIFY MODULE-LOCAL CALLABLES
# ============================================================

helper_names = []

for _lineno, name in runtime_direct_calls:

    root = name.split(".")[0]

    if root not in vars(
        runtime_module
    ):
        continue

    obj = vars(
        runtime_module
    )[root]

    if not callable(obj):
        continue

    if obj is runtime_fn:
        continue

    obj_module = getattr(
        obj,
        "__module__",
        "",
    )

    # Trace only functions belonging to the runtime-search
    # implementation module itself. External library calls are
    # captured through SQL proxy / source map instead.
    if obj_module == runtime_module_name:

        helper_names.append(
            root
        )


helper_names = sorted(
    set(
        helper_names
    )
)


# ============================================================
# ACTIVE TRACE STATE
# ============================================================

active = {
    "case": None,
    "query": None,
    "target_id": None,
    "classification": None,
}


call_events = []

sql_events = []

score_events = []


# ============================================================
# HELPER WRAPPERS
# ============================================================

helper_originals = {}


def wrap_helper(
    name: str,
    fn: Any,
):

    def wrapper(
        *args,
        **kwargs,
    ):

        started = time.perf_counter()

        result = fn(
            *args,
            **kwargs,
        )

        elapsed = (
            time.perf_counter()
            - started
        )

        summary = summarize_iterable(
            result,
            active["target_id"],
        )

        event = {
            "case":
                active["case"],

            "classification":
                active["classification"],

            "query":
                active["query"],

            "target_id":
                active["target_id"],

            "helper":
                name,

            "elapsed_ms":
                round(
                    elapsed * 1000.0,
                    4,
                ),

            "args_repr":
                repr(args)[:1500],

            "kwargs_repr":
                repr(kwargs)[:1500],

            "return_type":
                type(result).__name__,

            "return_repr":
                repr(result)[:2000],

            "candidate_count":
                summary["count"],

            "target_present":
                summary["target_present"],

            "target_rank":
                summary["target_rank"],

            "target_chunk_id":
                summary["target_chunk_id"],

            "target_scores_json":
                summary["target_scores_json"],
        }

        call_events.append(
            event
        )


        # Scalar helper outputs involving score-like names.
        low_name = name.casefold()

        if any(
            marker in low_name
            for marker in (
                "score",
                "rank",
                "confidence",
                "weight",
                "similar",
                "normalize",
                "token",
                "query",
                "match",
            )
        ):

            score_events.append(
                {
                    "case":
                        active["case"],

                    "classification":
                        active["classification"],

                    "query":
                        active["query"],

                    "target_id":
                        active["target_id"],

                    "helper":
                        name,

                    "args_repr":
                        repr(args)[:1500],

                    "kwargs_repr":
                        repr(kwargs)[:1500],

                    "result_repr":
                        repr(result)[:2000],
                }
            )


        return result


    wrapper.__name__ = getattr(
        fn,
        "__name__",
        name,
    )

    wrapper.__qualname__ = getattr(
        fn,
        "__qualname__",
        name,
    )

    wrapper.__doc__ = getattr(
        fn,
        "__doc__",
        None,
    )

    return wrapper


for name in helper_names:

    fn = getattr(
        runtime_module,
        name,
    )

    helper_originals[
        name
    ] = fn

    setattr(
        runtime_module,
        name,
        wrap_helper(
            name,
            fn,
        ),
    )


# ============================================================
# SQLITE PROXY
# ============================================================

class CursorProxy:

    def __init__(
        self,
        cursor: Any,
        sql: str,
        params: Any,
    ):

        self._cursor = cursor
        self._sql = sql
        self._params = params


    def _record_rows(
        self,
        rows: list[Any],
        method: str,
    ) -> None:

        target_id = active[
            "target_id"
        ]

        target_present = False
        target_rank = ""
        target_chunk_id = ""
        target_scores = {}

        for rank, row in enumerate(
            rows,
            start=1,
        ):

            if identity_equal(
                document_id_from(row),
                target_id,
            ):

                target_present = True
                target_rank = rank
                target_chunk_id = (
                    chunk_id_from(row)
                )
                target_scores = (
                    score_fields(row)
                )
                break


        sql_events.append(
            {
                "case":
                    active["case"],

                "classification":
                    active["classification"],

                "query":
                    active["query"],

                "target_id":
                    target_id,

                "fetch_method":
                    method,

                "sql":
                    self._sql,

                "params_repr":
                    repr(
                        self._params
                    )[:3000],

                "row_count":
                    len(rows),

                "target_present":
                    target_present,

                "target_row_rank":
                    target_rank,

                "target_chunk_id":
                    target_chunk_id,

                "target_scores_json":
                    safe_json(
                        target_scores
                    ),
            }
        )


    def fetchall(
        self,
    ):

        rows = self._cursor.fetchall()

        self._record_rows(
            rows,
            "fetchall",
        )

        return rows


    def fetchone(
        self,
    ):

        row = self._cursor.fetchone()

        rows = (
            []
            if row is None
            else [row]
        )

        self._record_rows(
            rows,
            "fetchone",
        )

        return row


    def fetchmany(
        self,
        size=None,
    ):

        if size is None:
            rows = self._cursor.fetchmany()
        else:
            rows = self._cursor.fetchmany(
                size
            )

        self._record_rows(
            rows,
            "fetchmany",
        )

        return rows


    def __iter__(
        self,
    ):
        return iter(
            self._cursor
        )


    def __getattr__(
        self,
        name: str,
    ):
        return getattr(
            self._cursor,
            name,
        )


class ConnectionProxy:

    def __init__(
        self,
        connection: Any,
    ):

        object.__setattr__(
            self,
            "_connection",
            connection,
        )


    def execute(
        self,
        sql,
        parameters=(),
    ):

        cursor = self._connection.execute(
            sql,
            parameters,
        )

        return CursorProxy(
            cursor,
            str(sql),
            parameters,
        )


    def executemany(
        self,
        sql,
        seq_of_parameters,
    ):

        # Harness must not permit mutation-oriented executemany.
        normalized = str(
            sql
        ).strip().upper()

        if normalized.startswith(
            (
                "INSERT ",
                "UPDATE ",
                "DELETE ",
                "REPLACE ",
                "CREATE ",
                "DROP ",
                "ALTER ",
            )
        ):
            raise RuntimeError(
                "R4-R10-R5 blocked mutation SQL"
            )

        cursor = self._connection.executemany(
            sql,
            seq_of_parameters,
        )

        return CursorProxy(
            cursor,
            str(sql),
            "<executemany>",
        )


    def __enter__(
        self,
    ):

        self._connection.__enter__()

        return self


    def __exit__(
        self,
        exc_type,
        exc,
        tb,
    ):

        return self._connection.__exit__(
            exc_type,
            exc,
            tb,
        )


    def __getattr__(
        self,
        name: str,
    ):

        return getattr(
            self._connection,
            name,
        )


    def __setattr__(
        self,
        name: str,
        value: Any,
    ):

        if name == "_connection":

            object.__setattr__(
                self,
                name,
                value,
            )

        else:

            setattr(
                self._connection,
                name,
                value,
            )


real_sqlite_connect = sqlite3.connect


def traced_connect(
    database,
    *args,
    **kwargs,
):

    # Force read-only mode for the production catalog.
    db_text = str(
        database
    )

    target_db = str(
        DB
    )

    if (
        db_text == target_db
        or
        db_text.endswith(
            "/catalog.sqlite"
        )
    ):

        connection = real_sqlite_connect(
            f"file:{target_db}?mode=ro",
            uri=True,
        )

        connection.execute(
            "PRAGMA query_only=ON"
        )

        return ConnectionProxy(
            connection
        )


    connection = real_sqlite_connect(
        database,
        *args,
        **kwargs,
    )

    return ConnectionProxy(
        connection
    )


# ------------------------------------------------------------
# Replace sqlite interface only inside implementation module.
# ------------------------------------------------------------

sqlite_proxy_installed = False
original_module_sqlite = None
original_module_connect = None


if (
    hasattr(
        runtime_module,
        "sqlite3",
    )
    and
    getattr(
        runtime_module,
        "sqlite3"
    )
    is sqlite3
):

    original_module_sqlite = (
        runtime_module.sqlite3
    )

    sqlite_namespace = types.SimpleNamespace()

    for attr in dir(
        sqlite3
    ):

        try:
            setattr(
                sqlite_namespace,
                attr,
                getattr(
                    sqlite3,
                    attr,
                ),
            )
        except Exception:
            pass

    sqlite_namespace.connect = (
        traced_connect
    )

    runtime_module.sqlite3 = (
        sqlite_namespace
    )

    sqlite_proxy_installed = True


elif (
    hasattr(
        runtime_module,
        "connect",
    )
    and
    getattr(
        runtime_module,
        "connect"
    )
    is sqlite3.connect
):

    original_module_connect = (
        runtime_module.connect
    )

    runtime_module.connect = (
        traced_connect
    )

    sqlite_proxy_installed = True


# ============================================================
# RUN NINE TARGETS
# ============================================================

targets = read_tsv(
    DETAIL_IN
)


if len(
    targets
) != EXPECTED:

    raise RuntimeError(
        f"expected 9 targets, got {len(targets)}"
    )


class_census = Counter(
    row[
        "classification"
    ]
    for row in targets
)


if dict(
    class_census
) != EXPECTED_CLASSES:

    raise RuntimeError(
        f"unexpected R4-R10-R4 classes: {dict(class_census)}"
    )


detail_rows = []

trace_lines = []

started = time.time()


for index, row in enumerate(
    targets,
    start=1,
):

    query = row[
        "query"
    ]

    target_id = row[
        "document_id"
    ]

    classification = row[
        "classification"
    ]


    active[
        "case"
    ] = index

    active[
        "query"
    ] = query

    active[
        "target_id"
    ] = target_id

    active[
        "classification"
    ] = classification


    call_before = len(
        call_events
    )

    sql_before = len(
        sql_events
    )

    score_before = len(
        score_events
    )


    result = list(
        runtime_fn(
            query,
            db_path=DB,
            limit=2000,
        )
    )


    case_calls = call_events[
        call_before:
    ]

    case_sql = sql_events[
        sql_before:
    ]

    case_scores = score_events[
        score_before:
    ]


    final_rank = None
    final_chunk = ""
    final_confidence = None
    final_scores = {}


    for rank, candidate in enumerate(
        result,
        start=1,
    ):

        if identity_equal(
            document_id_from(
                candidate
            ),
            target_id,
        ):

            final_rank = rank

            final_chunk = chunk_id_from(
                candidate
            )

            final_scores = score_fields(
                candidate
            )

            mapped = to_map(
                candidate
            )

            confidence = mapped.get(
                "confidence"
            )

            if confidence is not None:

                try:
                    final_confidence = float(
                        confidence
                    )
                except Exception:
                    final_confidence = None

            break


    target_sql_events = [
        event
        for event in case_sql
        if event[
            "target_present"
        ] in (
            True,
            "True",
        )
    ]


    first_target_sql = (
        target_sql_events[0]
        if target_sql_events
        else None
    )


    sql_target_present = bool(
        first_target_sql
    )


    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    if classification == "SEARCH_RANK_HORIZON_FAILURE":

        if (
            final_rank is not None
            and
            sql_target_present
        ):

            anatomy_class = (
                "SQL_MATCH_LOW_RANK"
            )

        elif (
            final_rank is not None
            and
            not sql_target_present
        ):

            anatomy_class = (
                "POST_SQL_GENERATION_OR_UNTRACED_SQL"
            )

        else:

            anatomy_class = (
                "R4_R10_R4_REPRODUCTION_MISMATCH"
            )


    elif classification == "CANDIDATE_NOT_GENERATED":

        if sql_target_present:

            anatomy_class = (
                "SQL_MATCHED_BUT_NOT_RETURNED"
            )

        elif case_sql:

            anatomy_class = (
                "SQL_QUERY_DID_NOT_MATCH_TARGET"
            )

        else:

            anatomy_class = (
                "NO_SQL_TRACE_OR_NON_SQL_GENERATOR"
            )


    else:

        anatomy_class = (
            "UNEXPECTED_INPUT_CLASS"
        )


    sql_texts = [
        event[
            "sql"
        ]
        for event in case_sql
    ]


    sql_params = [
        event[
            "params_repr"
        ]
        for event in case_sql
    ]


    detail_rows.append(
        {
            "case":
                index,

            "document_id":
                target_id,

            "query":
                query,

            "r4_r10_r4_class":
                classification,

            "runtime_module":
                runtime_module_name,

            "runtime_source_file":
                str(
                    runtime_file_path
                ),

            "runtime_returned":
                len(
                    result
                ),

            "target_final_found":
                final_rank
                is not None,

            "target_final_rank":
                final_rank
                or "",

            "target_chunk_id":
                final_chunk,

            "target_confidence":
                (
                    final_confidence
                    if final_confidence
                    is not None
                    else ""
                ),

            "target_scores_json":
                safe_json(
                    final_scores
                ),

            "sql_statements":
                len(
                    case_sql
                ),

            "sql_target_present":
                sql_target_present,

            "first_target_sql_rank":
                (
                    first_target_sql[
                        "target_row_rank"
                    ]
                    if first_target_sql
                    else ""
                ),

            "first_target_sql":
                (
                    first_target_sql[
                        "sql"
                    ]
                    if first_target_sql
                    else ""
                ),

            "first_target_sql_params":
                (
                    first_target_sql[
                        "params_repr"
                    ]
                    if first_target_sql
                    else ""
                ),

            "helper_calls":
                len(
                    case_calls
                ),

            "score_helper_calls":
                len(
                    case_scores
                ),

            "anatomy_class":
                anatomy_class,

            "sql_texts_json":
                safe_json(
                    sql_texts
                ),

            "sql_params_json":
                safe_json(
                    sql_params
                ),
        }
    )


    trace_lines.extend(
        (
            "=" * 78,
            f"CASE {index:02d}",
            "=" * 78,
            f"document_id            : {target_id}",
            f"query                  : {query}",
            f"R4-R10-R4 class        : {classification}",
            "",
            f"runtime module         : {runtime_module_name}",
            f"runtime result count   : {len(result)}",
            f"target final found     : {final_rank is not None}",
            f"target final rank      : {final_rank}",
            f"target chunk           : {final_chunk}",
            f"target confidence      : {final_confidence}",
            f"target scores          : {final_scores}",
            "",
            f"SQL calls              : {len(case_sql)}",
            f"target seen in SQL     : {sql_target_present}",
            f"helper calls           : {len(case_calls)}",
            f"score helper calls     : {len(case_scores)}",
            "",
            f"ANATOMY CLASS          : {anatomy_class}",
            "",
            "SQL EVENTS",
        )
    )


    for event in case_sql:

        trace_lines.append(
            "  "
            + safe_json(
                event
            )
        )


    trace_lines.extend(
        (
            "",
            "HELPER EVENTS",
        )
    )


    for event in case_calls:

        trace_lines.append(
            "  "
            + safe_json(
                event
            )
        )


    trace_lines.extend(
        (
            "",
            "SCORE / QUERY HELPER EVENTS",
        )
    )


    for event in case_scores:

        trace_lines.append(
            "  "
            + safe_json(
                event
            )
        )


    trace_lines.append(
        ""
    )


# ============================================================
# RESTORE ALL IN-MEMORY PATCHES
# ============================================================

for name, fn in helper_originals.items():

    setattr(
        runtime_module,
        name,
        fn,
    )


if original_module_sqlite is not None:

    runtime_module.sqlite3 = (
        original_module_sqlite
    )


if original_module_connect is not None:

    runtime_module.connect = (
        original_module_connect
    )


# ============================================================
# TWO-MISSING-CASE DIRECT DB ANATOMY
# ============================================================
#
# Uses separate mode=ro connection after instrumentation is
# fully restored.
# ============================================================

missing_rows = []


ro = sqlite3.connect(
    f"file:{DB}?mode=ro",
    uri=True,
)

ro.row_factory = sqlite3.Row

ro.execute(
    "PRAGMA query_only=ON"
)


tables = [
    row["name"]
    for row in ro.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    )
]


for row in targets:

    target_id = row[
        "document_id"
    ]

    if target_id not in MISSING_IDS:
        continue

    query = row[
        "query"
    ]


    document_hits = []

    chunk_hits = []


    for table in tables:

        try:
            info = ro.execute(
                f'PRAGMA table_info("{table}")'
            ).fetchall()
        except sqlite3.DatabaseError:
            continue

        columns = [
            str(
                item["name"]
            )
            for item in info
        ]

        lowered = {
            name.casefold():
                name
            for name in columns
        }


        for candidate_col in (
            "document_id",
            "runtime_document_id",
            "doc_id",
            "id",
        ):

            actual = lowered.get(
                candidate_col
            )

            if actual is None:
                continue

            try:
                found = ro.execute(
                    f'''
                    SELECT rowid AS "__rowid__", *
                    FROM "{table}"
                    WHERE CAST("{actual}" AS TEXT)=?
                    LIMIT 100
                    ''',
                    (
                        target_id,
                    ),
                ).fetchall()
            except sqlite3.DatabaseError:
                continue

            for item in found:

                mapped = dict(
                    item
                )

                if candidate_col in (
                    "document_id",
                    "runtime_document_id",
                    "doc_id",
                ):
                    chunk_hits.append(
                        (
                            table,
                            actual,
                            mapped,
                        )
                    )

                if candidate_col == "id":

                    title = first_present(
                        mapped,
                        "title",
                        "subject",
                        "name",
                    )

                    path = first_present(
                        mapped,
                        "source_path",
                        "path",
                        "file_path",
                    )

                    if title or path:

                        document_hits.append(
                            (
                                table,
                                actual,
                                mapped,
                            )
                        )


    document_preview = []

    for table, column, mapped in document_hits[:10]:

        document_preview.append(
            {
                "table":
                    table,

                "column":
                    column,

                "title":
                    first_present(
                        mapped,
                        "title",
                        "name",
                    ),

                "subject":
                    first_present(
                        mapped,
                        "subject",
                    ),

                "path":
                    first_present(
                        mapped,
                        "source_path",
                        "path",
                        "file_path",
                    ),
            }
        )


    chunk_preview = []

    for table, column, mapped in chunk_hits[:25]:

        chunk_preview.append(
            {
                "table":
                    table,

                "column":
                    column,

                "chunk_id":
                    first_present(
                        mapped,
                        "chunk_id",
                        "id",
                        "source_id",
                    ),

                "title":
                    first_present(
                        mapped,
                        "title",
                    ),

                "subject":
                    first_present(
                        mapped,
                        "subject",
                    ),

                "text_preview":
                    first_present(
                        mapped,
                        "text",
                        "content",
                        "excerpt",
                        "body",
                        "chunk_text",
                    )[:300],
            }
        )


    missing_rows.append(
        {
            "document_id":
                target_id,

            "query":
                query,

            "document_hit_count":
                len(
                    document_hits
                ),

            "chunk_or_document_fk_hits":
                len(
                    chunk_hits
                ),

            "document_preview_json":
                safe_json(
                    document_preview
                ),

            "chunk_preview_json":
                safe_json(
                    chunk_preview
                ),
        }
    )


ro.close()


# ============================================================
# SOURCE MAP
# ============================================================

source_lines = [
    "=" * 78,
    " GENESIS RECALL R4-R10-R5",
    " search_runtime_knowledge IMPLEMENTATION",
    "=" * 78,
    "",
    f"module    : {runtime_module_name}",
    f"file      : {runtime_file_path}",
    f"signature : {inspect.signature(runtime_fn)}",
    f"lines     : {runtime_node.lineno}-"
    f"{getattr(runtime_node, 'end_lineno', runtime_node.lineno)}",
    "",
    "DIRECT CALLS",
]


for lineno, name in sorted(
    runtime_direct_calls
):

    source_lines.append(
        f"{lineno:05d}: {name}"
    )


source_lines.extend(
    (
        "",
        "MODULE-LOCAL HELPERS INSTRUMENTED",
    )
)


for name in helper_names:

    obj = helper_originals[
        name
    ]

    try:
        signature = inspect.signature(
            obj
        )
    except Exception:
        signature = (
            "<signature unavailable>"
        )

    source_lines.append(
        f"{name} {signature}"
    )


source_lines.extend(
    (
        "",
        "SQL-LIKE STRING LITERALS",
    )
)


for lineno, literal in sql_like_literals:

    source_lines.append(
        f"{lineno:05d}: {literal}"
    )


source_lines.extend(
    (
        "",
        "=" * 78,
        "search_runtime_knowledge SOURCE",
        "=" * 78,
        inspect.getsource(
            runtime_fn
        ),
    )
)


for name in helper_names:

    source_lines.extend(
        (
            "",
            "=" * 78,
            f"HELPER {name}",
            "=" * 78,
        )
    )

    try:

        source_lines.append(
            inspect.getsource(
                helper_originals[
                    name
                ]
            )
        )

    except Exception as exc:

        source_lines.append(
            f"SOURCE ERROR: {type(exc).__name__}: {exc}"
        )


SOURCE_MAP.write_text(
    "\n".join(
        source_lines
    )
    + "\n",
    encoding="utf-8",
)


# ============================================================
# WRITE ARTIFACTS
# ============================================================

write_tsv(
    DETAIL,
    detail_rows,
)

write_tsv(
    SQL_TRACE,
    sql_events,
)

write_tsv(
    CALL_TRACE,
    call_events,
)

write_tsv(
    SCORE_TRACE,
    score_events,
)

write_tsv(
    MISSING_TRACE,
    missing_rows,
)


TRACE.write_text(
    "\n".join(
        (
            "=" * 78,
            " GENESIS RECALL R4-R10-R5",
            " RUNTIME SEARCH ANATOMY",
            "=" * 78,
            "",
            *trace_lines,
        )
    ),
    encoding="utf-8",
)


# ============================================================
# ANATOMY CENSUS
# ============================================================

anatomy_counter = Counter(
    row[
        "anatomy_class"
    ]
    for row in detail_rows
)


rank_cases = [
    row
    for row in detail_rows
    if row[
        "r4_r10_r4_class"
    ]
    == "SEARCH_RANK_HORIZON_FAILURE"
]


missing_cases = [
    row
    for row in detail_rows
    if row[
        "r4_r10_r4_class"
    ]
    == "CANDIDATE_NOT_GENERATED"
]


rank_reproduced = all(
    row[
        "target_final_found"
    ]
    in (
        True,
        "True",
    )
    for row in rank_cases
)


missing_reproduced = all(
    row[
        "target_final_found"
    ]
    in (
        False,
        "False",
    )
    for row in missing_cases
)


all_nine_classified = (
    len(
        detail_rows
    )
    == EXPECTED
    and
    all(
        row[
            "anatomy_class"
        ]
        not in (
            "",
            "UNEXPECTED_INPUT_CLASS",
        )
        for row in detail_rows
    )
)


runtime_source_captured = bool(
    runtime_source.strip()
)


query_or_sql_evidence_captured = (
    bool(
        sql_events
    )
    or
    bool(
        sql_like_literals
    )
)


diagnostic_certified = all(
    (
        len(
            targets
        )
        == EXPECTED,

        len(
            rank_cases
        )
        == 7,

        len(
            missing_cases
        )
        == 2,

        rank_reproduced,

        missing_reproduced,

        all_nine_classified,

        runtime_source_captured,

        query_or_sql_evidence_captured,
    )
)


elapsed = (
    time.time()
    - started
)


report = {
    "phase":
        "Genesis Recall R4-R10-R5",

    "implementation": {
        "module":
            runtime_module_name,

        "file":
            str(
                runtime_file_path
            ),

        "signature":
            str(
                inspect.signature(
                    runtime_fn
                )
            ),

        "direct_calls":
            len(
                runtime_direct_calls
            ),

        "instrumented_helpers":
            helper_names,

        "sqlite_proxy_installed":
            sqlite_proxy_installed,

        "sql_like_literals":
            len(
                sql_like_literals
            ),
    },

    "population": {
        "total":
            len(
                targets
            ),

        "rank_horizon":
            len(
                rank_cases
            ),

        "candidate_not_generated":
            len(
                missing_cases
            ),
    },

    "trace": {
        "sql_events":
            len(
                sql_events
            ),

        "helper_events":
            len(
                call_events
            ),

        "score_events":
            len(
                score_events
            ),
    },

    "anatomy_census":
        dict(
            anatomy_counter
        ),

    "contracts": {
        "rank_horizon_reproduced":
            rank_reproduced,

        "candidate_not_generated_reproduced":
            missing_reproduced,

        "all_nine_classified":
            all_nine_classified,

        "runtime_source_captured":
            runtime_source_captured,

        "query_or_sql_evidence_captured":
            query_or_sql_evidence_captured,
    },

    "diagnostic_certified":
        diagnostic_certified,

    "elapsed_seconds":
        round(
            elapsed,
            3,
        ),
}


REPORT.write_text(
    json.dumps(
        report,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )
    + "\n",
    encoding="utf-8",
)


# ============================================================
# CONSOLE RESULT
# ============================================================

print("=" * 78)
print(" GENESIS RECALL R4-R10-R5 RESULT")
print("=" * 78)

print()
print("IMPLEMENTATION")

print(
    "  module                     :",
    runtime_module_name,
)

print(
    "  file                       :",
    runtime_file_path,
)

print(
    "  signature                  :",
    inspect.signature(
        runtime_fn
    ),
)

print(
    "  direct calls               :",
    len(
        runtime_direct_calls
    ),
)

print(
    "  instrumented helpers       :",
    helper_names,
)

print(
    "  SQLite proxy installed     :",
    sqlite_proxy_installed,
)


print()
print("TRACE COUNTS")

print(
    "  SQL events                 :",
    len(
        sql_events
    ),
)

print(
    "  helper events              :",
    len(
        call_events
    ),
)

print(
    "  score/query helper events  :",
    len(
        score_events
    ),
)


print()
print("ANATOMY CENSUS")

for name, count in sorted(
    anatomy_counter.items(),
    key=lambda item:
        (
            -item[1],
            item[0],
        ),
):

    print(
        f"  {name:<52} {count}"
    )


print()
print("CERTIFICATION")

print(
    "  rank-horizon reproduced    :",
    rank_reproduced,
)

print(
    "  missing cases reproduced   :",
    missing_reproduced,
)

print(
    "  all nine classified        :",
    all_nine_classified,
)

print(
    "  runtime source captured    :",
    runtime_source_captured,
)

print(
    "  query/SQL evidence captured:",
    query_or_sql_evidence_captured,
)


print()
print(
    "R4-R10-R5 DIAGNOSTIC CERTIFIED :",
    diagnostic_certified,
)


print()
print("Artifacts:")
print(" ", REPORT)
print(" ", DETAIL)
print(" ", SQL_TRACE)
print(" ", CALL_TRACE)
print(" ", SCORE_TRACE)
print(" ", MISSING_TRACE)
print(" ", SOURCE_MAP)
print(" ", TRACE)

print()
print(
    "elapsed seconds:",
    round(
        elapsed,
        2,
    ),
)

print("=" * 78)


raise SystemExit(
    0
    if diagnostic_certified
    else 1
)
