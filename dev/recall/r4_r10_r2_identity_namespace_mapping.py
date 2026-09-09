from __future__ import annotations

import csv
import inspect
import json
import re
import sqlite3
import sys
import time

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

OUTDIR = PROJECT / "artifacts/genesis_recall"

R3_TSV = OUTDIR / "r3_production_recall_census.tsv"

REPORT = OUTDIR / "r4_r10_r2_identity_namespace_mapping.json"
R3_MAP = OUTDIR / "r4_r10_r2_r3_identity_map.tsv"
RAW_MAP = OUTDIR / "r4_r10_r2_raw_candidate_identity_map.tsv"
DB_MAP = OUTDIR / "r4_r10_r2_database_identity_map.tsv"
CANARY_MAP = OUTDIR / "r4_r10_r2_canary_namespace_map.tsv"
UNRESOLVED = OUTDIR / "r4_r10_r2_unresolved_targets.tsv"
TRACE = OUTDIR / "r4_r10_r2_identity_trace.txt"
SCHEMA = OUTDIR / "r4_r10_r2_identity_schema_map.txt"


sys.path.insert(
    0,
    str(PROJECT),
)


from core.knowledge_catalog.search import (
    search_catalog,
)

from core.knowledge_catalog.qualified_search import (
    candidate_from_row,
)

from core.retrieval.qualification.contracts import (
    EvidenceCandidate,
)


EXPECTED_R3 = 250


CANARIES = (
    (
        "cpp",
        "C++ Programming",
        "4",
    ),
    (
        "effective_c",
        "Effective C",
        "14",
    ),
    (
        "ai_assisted_python",
        "AI assisted Python",
        "11",
    ),
    (
        "lane_lexicon",
        "Lane lexicon",
        "86876",
    ),
)


# ============================================================
# GENERIC HELPERS
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


def first_present(
    row: Mapping[str, Any],
    names: Iterable[str],
) -> str:

    lowered = {
        str(key).casefold(): key
        for key in row.keys()
    }

    for name in names:
        key = lowered.get(
            str(name).casefold()
        )

        if key is None:
            continue

        value = row.get(key)

        if value not in (
            None,
            "",
        ):
            return str(value).strip()

    return ""


def raw_map(
    raw: Any,
) -> dict[str, Any]:

    if isinstance(raw, Mapping):
        return dict(raw)

    if hasattr(raw, "keys"):
        try:
            return {
                key: raw[key]
                for key in raw.keys()
            }
        except Exception:
            pass

    if hasattr(raw, "_asdict"):
        try:
            return dict(
                raw._asdict()
            )
        except Exception:
            pass

    try:
        return dict(
            vars(raw)
        )
    except Exception:
        return {}


def scalar_identity(
    value: Any,
) -> str:

    if value in (
        None,
        "",
    ):
        return ""

    return str(value).strip()


def identity_equal(
    left: Any,
    right: Any,
) -> bool:

    a = scalar_identity(left)
    b = scalar_identity(right)

    if not a or not b:
        return False

    if a.casefold() == b.casefold():
        return True

    try:
        return int(a) == int(b)
    except Exception:
        return False


IDENTITY_HINTS = (
    "id",
    "document",
    "runtime",
    "source",
    "chunk",
    "catalog",
    "object",
    "parent",
    "record",
    "row",
)


def looks_like_identity_column(
    name: str,
) -> bool:

    low = name.casefold()

    if low == "id":
        return True

    if low.endswith("_id"):
        return True

    return (
        "id" in low
        and any(
            hint in low
            for hint in IDENTITY_HINTS
        )
    )


def identity_fields(
    row: Mapping[str, Any],
) -> dict[str, str]:

    result = {}

    for key, value in row.items():

        if not looks_like_identity_column(
            str(key)
        ):
            continue

        v = scalar_identity(value)

        if v:
            result[str(key)] = v

    return result


def candidate_fields(
    candidate: EvidenceCandidate,
) -> dict[str, str]:

    result = {
        "candidate.source_id":
            scalar_identity(
                candidate.source_id
            )
    }

    try:
        metadata = dict(
            candidate.metadata
        )
    except Exception:
        metadata = {}

    for key, value in metadata.items():

        if looks_like_identity_column(
            str(key)
        ):
            v = scalar_identity(value)

            if v:
                result[
                    f"metadata.{key}"
                ] = v

    return result


def matching_fields(
    target: str,
    fields: Mapping[str, str],
) -> list[str]:

    return [
        name
        for name, value in fields.items()
        if identity_equal(
            target,
            value,
        )
    ]


def row_query(
    row: Mapping[str, Any],
) -> str:

    return first_present(
        row,
        (
            "query",
            "search_query",
            "qualification_query",
            "input_query",
            "derived_query",
        ),
    )


def r3_target(
    row: Mapping[str, Any],
) -> str:

    return first_present(
        row,
        (
            "document_id",
            "runtime_document_id",
            "target_document_id",
            "target_id",
            "doc_id",
            "source_id",
            "id",
            "runtime_id",
        ),
    )


# ============================================================
# READ-ONLY DATABASE CONTRACT
# ============================================================

conn = sqlite3.connect(
    f"file:{DB}?mode=ro",
    uri=True,
)

conn.row_factory = sqlite3.Row

conn.execute(
    "PRAGMA query_only=ON"
)


integrity = conn.execute(
    "PRAGMA integrity_check"
).fetchone()[0]


if integrity != "ok":
    raise RuntimeError(
        f"database integrity failure: {integrity}"
    )


# ============================================================
# DATABASE SCHEMA DISCOVERY
# ============================================================

tables = [
    row["name"]
    for row in conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    )
]


table_columns: dict[str, list[str]] = {}

identity_columns: list[tuple[str, str, str]] = []


for table in tables:

    pragma = conn.execute(
        f'PRAGMA table_info("{table}")'
    ).fetchall()

    cols = [
        str(row["name"])
        for row in pragma
    ]

    table_columns[table] = cols

    for row in pragma:

        name = str(
            row["name"]
        )

        declared_type = str(
            row["type"]
            or ""
        )

        if looks_like_identity_column(
            name
        ):
            identity_columns.append(
                (
                    table,
                    name,
                    declared_type,
                )
            )


schema_lines = [
    "=" * 78,
    " GENESIS RECALL R4-R10-R2",
    " DATABASE IDENTITY SCHEMA",
    "=" * 78,
    "",
]


for table in tables:

    schema_lines.append(
        f"TABLE {table}"
    )

    for col in table_columns[
        table
    ]:

        marker = (
            " [IDENTITY]"
            if looks_like_identity_column(col)
            else ""
        )

        schema_lines.append(
            f"  {col}{marker}"
        )

    schema_lines.append("")


# ============================================================
# EXACT DB ID SEARCH
# ============================================================

def db_identity_hits(
    target: str,
) -> list[dict[str, Any]]:

    hits = []

    for table, column, declared_type in identity_columns:

        sql = (
            f'SELECT rowid AS "__rowid__", * '
            f'FROM "{table}" '
            f'WHERE CAST("{column}" AS TEXT) = ? '
            f'LIMIT 25'
        )

        try:
            rows = conn.execute(
                sql,
                (
                    str(target),
                ),
            ).fetchall()

        except sqlite3.DatabaseError:
            continue

        for row in rows:

            mapped = dict(row)

            hit = {
                "target_id":
                    str(target),

                "table":
                    table,

                "column":
                    column,

                "declared_type":
                    declared_type,

                "rowid":
                    mapped.get(
                        "__rowid__"
                    ),

                "title":
                    first_present(
                        mapped,
                        (
                            "title",
                            "name",
                            "document_title",
                            "subject",
                        ),
                    ),

                "subject":
                    first_present(
                        mapped,
                        (
                            "subject",
                            "document_subject",
                        ),
                    ),

                "source_path":
                    first_present(
                        mapped,
                        (
                            "source_path",
                            "path",
                            "filepath",
                            "file_path",
                        ),
                    ),

                "identity_fields":
                    identity_fields(
                        mapped
                    ),

                "raw_row":
                    mapped,
            }

            hits.append(
                hit
            )

    return hits


# ============================================================
# RAW SEARCH MAPPING
# ============================================================

def search_identity_observations(
    query: str,
    target: str,
    *,
    limit: int = 500,
) -> list[dict[str, Any]]:

    rows = list(
        search_catalog(
            query,
            limit=limit,
        )
    )

    observations = []

    for ordinal, raw in enumerate(
        rows,
        start=1,
    ):

        mapped = raw_map(
            raw
        )

        raw_ids = identity_fields(
            mapped
        )

        matched_raw_fields = matching_fields(
            target,
            raw_ids,
        )

        candidate = candidate_from_row(
            raw,
            ordinal=ordinal,
        )

        cand_ids = candidate_fields(
            candidate
        )

        matched_candidate_fields = matching_fields(
            target,
            cand_ids,
        )

        observations.append(
            {
                "rank":
                    ordinal,

                "raw":
                    mapped,

                "raw_ids":
                    raw_ids,

                "raw_target_fields":
                    matched_raw_fields,

                "candidate":
                    candidate,

                "candidate_ids":
                    cand_ids,

                "candidate_target_fields":
                    matched_candidate_fields,
            }
        )

    return observations


# ============================================================
# NAMESPACE CLASSIFICATION
# ============================================================

def namespace_name(
    field_name: str,
) -> str:

    low = field_name.casefold()

    if "chunk" in low:
        return "CHUNK_ID"

    if (
        "runtime_document" in low
        or "runtime_doc" in low
    ):
        return "RUNTIME_DOCUMENT_ID"

    if "document" in low or "doc_id" in low:
        return "DOCUMENT_ID"

    if "catalog" in low:
        return "CATALOG_ID"

    if "source" in low:
        return "SOURCE_ID"

    if "object" in low:
        return "OBJECT_ID"

    if low == "id" or low.endswith(".id"):
        return "GENERIC_ID"

    return "UNKNOWN_ID"


# ============================================================
# R3 POPULATION
# ============================================================

started = time.time()

r3_rows = read_tsv(
    R3_TSV
)


if len(r3_rows) != EXPECTED_R3:
    raise RuntimeError(
        f"expected 250 R3 rows; got {len(r3_rows)}"
    )


r3_map_rows = []

raw_map_rows = []

db_map_rows = []

unresolved_rows = []


r3_namespace_counter = Counter()

candidate_namespace_counter = Counter()

raw_target_field_counter = Counter()

candidate_target_field_counter = Counter()

transformation_counter = Counter()

resolution_counter = Counter()


exact_r3_resolved = 0

namespace_known = 0

candidate_namespace_known = 0

raw_to_candidate_mapped = 0


for index, row in enumerate(
    r3_rows,
    start=1,
):

    query = row_query(
        row
    )

    target = r3_target(
        row
    )


    if not query or not target:

        unresolved_rows.append(
            {
                "row":
                    index,

                "query":
                    query,

                "target_id":
                    target,

                "reason":
                    "MISSING_R3_QUERY_OR_TARGET",
            }
        )

        r3_map_rows.append(
            {
                "row":
                    index,

                "query":
                    query,

                "target_id":
                    target,

                "status":
                    "UNRESOLVED",
            }
        )

        continue


    # --------------------------------------------------------
    # A. Locate target in DB identity namespaces.
    # --------------------------------------------------------

    db_hits = db_identity_hits(
        target
    )


    db_namespaces = set()

    for hit in db_hits:

        ns = namespace_name(
            hit[
                "column"
            ]
        )

        db_namespaces.add(
            ns
        )

        db_map_rows.append(
            {
                "r3_row":
                    index,

                "query":
                    query,

                "target_id":
                    target,

                "table":
                    hit[
                        "table"
                    ],

                "column":
                    hit[
                        "column"
                    ],

                "namespace":
                    ns,

                "rowid":
                    hit[
                        "rowid"
                    ],

                "title":
                    hit[
                        "title"
                    ],

                "subject":
                    hit[
                        "subject"
                    ],

                "source_path":
                    hit[
                        "source_path"
                    ],

                "identity_fields_json":
                    json.dumps(
                        hit[
                            "identity_fields"
                        ],
                        sort_keys=True,
                        ensure_ascii=False,
                    ),
            }
        )


    if len(
        db_namespaces
    ) == 1:

        r3_namespace = next(
            iter(
                db_namespaces
            )
        )

    elif len(
        db_namespaces
    ) > 1:

        r3_namespace = (
            "MULTIPLE:"
            + ",".join(
                sorted(
                    db_namespaces
                )
            )
        )

    else:

        r3_namespace = "DB_ID_NOT_FOUND"


    r3_namespace_counter[
        r3_namespace
    ] += 1


    if r3_namespace != "DB_ID_NOT_FOUND":

        namespace_known += 1


    # --------------------------------------------------------
    # B. Search original R3 query.
    # --------------------------------------------------------

    observations = search_identity_observations(
        query,
        target,
        limit=500,
    )


    direct_raw = [
        obs
        for obs in observations
        if obs[
            "raw_target_fields"
        ]
    ]


    direct_candidate = [
        obs
        for obs in observations
        if obs[
            "candidate_target_fields"
        ]
    ]


    chosen = None

    resolution_method = ""


    if len(
        direct_raw
    ) == 1:

        chosen = direct_raw[
            0
        ]

        resolution_method = (
            "RAW_TARGET_IDENTITY"
        )


    elif len(
        direct_raw
    ) > 1:

        # Prefer the earliest ranked exact raw identity.
        chosen = sorted(
            direct_raw,
            key=lambda item:
                item[
                    "rank"
                ],
        )[0]

        resolution_method = (
            "RAW_TARGET_IDENTITY_MULTIPLE"
        )


    # --------------------------------------------------------
    # C. If target is outside search horizon, use DB metadata
    #    only to formulate alternate retrieval queries.
    #
    #    No raw row is synthesized.
    # --------------------------------------------------------

    alternate_queries = []

    if chosen is None:

        for hit in db_hits:

            for text in (
                hit[
                    "title"
                ],
                hit[
                    "subject"
                ],
            ):

                text = str(
                    text
                    or ""
                ).strip()

                if (
                    text
                    and
                    text.casefold()
                    != query.casefold()
                    and
                    text.casefold()
                    not in {
                        q.casefold()
                        for q in alternate_queries
                    }
                ):

                    alternate_queries.append(
                        text
                    )


        for alt_query in alternate_queries[:8]:

            alt_obs = (
                search_identity_observations(
                    alt_query,
                    target,
                    limit=500,
                )
            )

            alt_direct = [
                obs
                for obs in alt_obs
                if obs[
                    "raw_target_fields"
                ]
            ]


            if alt_direct:

                chosen = sorted(
                    alt_direct,
                    key=lambda item:
                        item[
                            "rank"
                        ],
                )[0]

                resolution_method = (
                    "DB_METADATA_QUERY_TO_RAW_IDENTITY"
                )

                chosen[
                    "alternate_query"
                ] = alt_query

                break


    # --------------------------------------------------------
    # D. Record exact mapping.
    # --------------------------------------------------------

    if chosen is not None:

        exact_r3_resolved += 1

        resolution_counter[
            resolution_method
        ] += 1


        raw_target_fields = chosen[
            "raw_target_fields"
        ]

        candidate_target_fields = chosen[
            "candidate_target_fields"
        ]


        for field in raw_target_fields:

            raw_target_field_counter[
                field
            ] += 1


        for field in candidate_target_fields:

            candidate_target_field_counter[
                field
            ] += 1


        raw_ids = chosen[
            "raw_ids"
        ]

        candidate_ids = chosen[
            "candidate_ids"
        ]


        candidate_source = candidate_ids.get(
            "candidate.source_id",
            "",
        )


        # Determine which raw identity equals candidate.source_id.
        source_origin_fields = [
            name
            for name, value in raw_ids.items()
            if identity_equal(
                value,
                candidate_source,
            )
        ]


        if source_origin_fields:

            raw_to_candidate_mapped += 1

            source_origin = ",".join(
                source_origin_fields
            )

            source_namespaces = {
                namespace_name(
                    field
                )
                for field in source_origin_fields
            }

            candidate_namespace = (
                ",".join(
                    sorted(
                        source_namespaces
                    )
                )
            )

        else:

            source_origin = (
                "NO_RAW_IDENTITY_FIELD_MATCH"
            )

            candidate_namespace = (
                "UNKNOWN_ID"
            )


        candidate_namespace_counter[
            candidate_namespace
        ] += 1


        if candidate_namespace != "UNKNOWN_ID":

            candidate_namespace_known += 1


        transformation = (
            f"{r3_namespace}"
            f" -> "
            f"{candidate_namespace}"
        )


        transformation_counter[
            transformation
        ] += 1


        candidate = chosen[
            "candidate"
        ]


        r3_map_rows.append(
            {
                "row":
                    index,

                "query":
                    query,

                "target_id":
                    target,

                "r3_namespace":
                    r3_namespace,

                "raw_rank":
                    chosen[
                        "rank"
                    ],

                "resolution_method":
                    resolution_method,

                "alternate_query":
                    chosen.get(
                        "alternate_query",
                        "",
                    ),

                "raw_target_fields":
                    ",".join(
                        raw_target_fields
                    ),

                "candidate_target_fields":
                    ",".join(
                        candidate_target_fields
                    ),

                "candidate_source_id":
                    candidate.source_id,

                "candidate_source_origin_fields":
                    source_origin,

                "candidate_namespace":
                    candidate_namespace,

                "identity_transformation":
                    transformation,

                "candidate_title":
                    candidate.title,

                "candidate_subject":
                    candidate.subject,

                "candidate_source_path":
                    candidate.source_path,

                "status":
                    "RESOLVED",
            }
        )


        raw_map_rows.append(
            {
                "r3_row":
                    index,

                "query":
                    query,

                "target_id":
                    target,

                "raw_rank":
                    chosen[
                        "rank"
                    ],

                "raw_identity_fields_json":
                    json.dumps(
                        raw_ids,
                        sort_keys=True,
                        ensure_ascii=False,
                    ),

                "raw_target_fields":
                    ",".join(
                        raw_target_fields
                    ),

                "candidate_identity_fields_json":
                    json.dumps(
                        candidate_ids,
                        sort_keys=True,
                        ensure_ascii=False,
                    ),

                "candidate_source_id":
                    candidate.source_id,

                "candidate_source_origin_fields":
                    source_origin,

                "r3_namespace":
                    r3_namespace,

                "candidate_namespace":
                    candidate_namespace,
            }
        )


    else:

        resolution_counter[
            "UNRESOLVED"
        ] += 1


        unresolved_rows.append(
            {
                "row":
                    index,

                "query":
                    query,

                "target_id":
                    target,

                "r3_namespace":
                    r3_namespace,

                "db_hit_count":
                    len(
                        db_hits
                    ),

                "alternate_queries":
                    " | ".join(
                        alternate_queries[:8]
                    ),

                "original_search_candidates":
                    len(
                        observations
                    ),

                "reason":
                    "TARGET_NOT_EXPOSED_BY_RAW_SEARCH",
            }
        )


        r3_map_rows.append(
            {
                "row":
                    index,

                "query":
                    query,

                "target_id":
                    target,

                "r3_namespace":
                    r3_namespace,

                "status":
                    "UNRESOLVED",
            }
        )


# ============================================================
# CANARY NAMESPACE MAPPING
# ============================================================

canary_rows = []

canary_resolved = 0

canary_namespace_known = 0

canary_candidate_mapping_known = 0


for name, query, target in CANARIES:

    db_hits = db_identity_hits(
        target
    )


    db_namespaces = {
        namespace_name(
            hit[
                "column"
            ]
        )
        for hit in db_hits
    }


    if len(
        db_namespaces
    ) == 1:

        target_namespace = next(
            iter(
                db_namespaces
            )
        )

    elif db_namespaces:

        target_namespace = (
            "MULTIPLE:"
            + ",".join(
                sorted(
                    db_namespaces
                )
            )
        )

    else:

        target_namespace = (
            "DB_ID_NOT_FOUND"
        )


    observations = search_identity_observations(
        query,
        target,
        limit=500,
    )


    direct = [
        obs
        for obs in observations
        if obs[
            "raw_target_fields"
        ]
    ]


    chosen = (
        sorted(
            direct,
            key=lambda item:
                item[
                    "rank"
                ],
        )[0]
        if direct
        else None
    )


    method = (
        "RAW_TARGET_IDENTITY"
        if chosen
        else ""
    )


    if chosen is None:

        alternate_queries = []

        for hit in db_hits:

            for text in (
                hit[
                    "title"
                ],
                hit[
                    "subject"
                ],
            ):

                text = str(
                    text
                    or ""
                ).strip()

                if (
                    text
                    and
                    text.casefold()
                    != query.casefold()
                ):

                    alternate_queries.append(
                        text
                    )


        for alt_query in alternate_queries[:8]:

            alt_obs = search_identity_observations(
                alt_query,
                target,
                limit=500,
            )

            alt_direct = [
                obs
                for obs in alt_obs
                if obs[
                    "raw_target_fields"
                ]
            ]


            if alt_direct:

                chosen = sorted(
                    alt_direct,
                    key=lambda item:
                        item[
                            "rank"
                        ],
                )[0]

                method = (
                    "DB_METADATA_QUERY_TO_RAW_IDENTITY"
                )

                break


    if chosen is None:

        canary_rows.append(
            {
                "name":
                    name,

                "query":
                    query,

                "target_id":
                    target,

                "target_namespace":
                    target_namespace,

                "db_hit_count":
                    len(
                        db_hits
                    ),

                "status":
                    "UNRESOLVED",
            }
        )

        continue


    canary_resolved += 1


    if target_namespace != "DB_ID_NOT_FOUND":

        canary_namespace_known += 1


    candidate = chosen[
        "candidate"
    ]

    raw_ids = chosen[
        "raw_ids"
    ]

    candidate_ids = chosen[
        "candidate_ids"
    ]


    source_origin_fields = [
        field
        for field, value in raw_ids.items()
        if identity_equal(
            value,
            candidate.source_id,
        )
    ]


    if source_origin_fields:

        canary_candidate_mapping_known += 1


    canary_rows.append(
        {
            "name":
                name,

            "query":
                query,

            "target_id":
                target,

            "target_namespace":
                target_namespace,

            "raw_rank":
                chosen[
                    "rank"
                ],

            "resolution_method":
                method,

            "raw_target_fields":
                ",".join(
                    chosen[
                        "raw_target_fields"
                    ]
                ),

            "candidate_source_id":
                candidate.source_id,

            "candidate_source_origin_fields":
                ",".join(
                    source_origin_fields
                ),

            "candidate_identity_fields_json":
                json.dumps(
                    candidate_ids,
                    sort_keys=True,
                    ensure_ascii=False,
                ),

            "candidate_title":
                candidate.title,

            "status":
                "RESOLVED",
        }
    )


# ============================================================
# CERTIFICATION
# ============================================================

r3_exact = (
    exact_r3_resolved
    == EXPECTED_R3
)


r3_target_namespace_complete = (
    namespace_known
    == EXPECTED_R3
)


candidate_namespace_complete = (
    candidate_namespace_known
    == EXPECTED_R3
)


identity_transformation_complete = (
    raw_to_candidate_mapped
    == EXPECTED_R3
)


canary_complete = (
    canary_resolved
    == len(
        CANARIES
    )
)


canary_namespace_complete = (
    canary_namespace_known
    == len(
        CANARIES
    )
)


canary_candidate_mapping_complete = (
    canary_candidate_mapping_known
    == len(
        CANARIES
    )
)


certification = {
    "exact_r3_population":
        len(
            r3_rows
        )
        == EXPECTED_R3,

    "r3_exact_target_resolution":
        r3_exact,

    "r3_target_namespace_complete":
        r3_target_namespace_complete,

    "candidate_namespace_complete":
        candidate_namespace_complete,

    "raw_to_candidate_identity_map_complete":
        identity_transformation_complete,

    "canaries_resolved":
        canary_complete,

    "canary_target_namespace_complete":
        canary_namespace_complete,

    "canary_candidate_mapping_complete":
        canary_candidate_mapping_complete,

    "database_integrity":
        integrity
        == "ok",
}


diagnostic_certified = all(
    certification.values()
)


elapsed = (
    time.time()
    - started
)


report = {
    "phase":
        "Genesis Recall R4-R10-R2",

    "purpose":
        (
            "Raw-Row -> EvidenceCandidate Identity Namespace "
            "Mapping & Exact R3 Target Resolution"
        ),

    "r3": {
        "population":
            len(
                r3_rows
            ),

        "resolved":
            exact_r3_resolved,

        "unresolved":
            EXPECTED_R3
            - exact_r3_resolved,

        "target_namespace_known":
            namespace_known,

        "candidate_namespace_known":
            candidate_namespace_known,

        "raw_to_candidate_identity_mapped":
            raw_to_candidate_mapped,

        "resolution_methods":
            dict(
                resolution_counter
            ),

        "target_namespace_census":
            dict(
                r3_namespace_counter
            ),

        "candidate_namespace_census":
            dict(
                candidate_namespace_counter
            ),

        "raw_target_field_census":
            dict(
                raw_target_field_counter
            ),

        "candidate_target_field_census":
            dict(
                candidate_target_field_counter
            ),

        "identity_transformation_census":
            dict(
                transformation_counter
            ),
    },

    "canaries": {
        "population":
            len(
                CANARIES
            ),

        "resolved":
            canary_resolved,

        "target_namespace_known":
            canary_namespace_known,

        "candidate_mapping_known":
            canary_candidate_mapping_known,
    },

    "database": {
        "tables":
            len(
                tables
            ),

        "identity_columns":
            len(
                identity_columns
            ),

        "integrity":
            integrity,
    },

    "certification":
        certification,

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


write_tsv(
    R3_MAP,
    r3_map_rows,
)

write_tsv(
    RAW_MAP,
    raw_map_rows,
)

write_tsv(
    DB_MAP,
    db_map_rows,
)

write_tsv(
    CANARY_MAP,
    canary_rows,
)

write_tsv(
    UNRESOLVED,
    unresolved_rows,
)


SCHEMA.write_text(
    "\n".join(
        schema_lines
    )
    + "\n",
    encoding="utf-8",
)


trace_lines = [
    "=" * 78,
    " GENESIS RECALL R4-R10-R2",
    " IDENTITY NAMESPACE TRACE",
    "=" * 78,
    "",
    f"R3 population                : {len(r3_rows)}",
    f"R3 resolved                  : {exact_r3_resolved}",
    f"R3 unresolved                : {EXPECTED_R3 - exact_r3_resolved}",
    f"R3 target namespace known    : {namespace_known}",
    f"candidate namespace known    : {candidate_namespace_known}",
    f"raw->candidate mapped        : {raw_to_candidate_mapped}",
    "",
    "R3 TARGET NAMESPACE CENSUS",
]


for key, value in sorted(
    r3_namespace_counter.items(),
    key=lambda item:
        (
            -item[1],
            item[0],
        ),
):

    trace_lines.append(
        f"  {key:<48} {value}"
    )


trace_lines.extend(
    (
        "",
        "CANDIDATE NAMESPACE CENSUS",
    )
)


for key, value in sorted(
    candidate_namespace_counter.items(),
    key=lambda item:
        (
            -item[1],
            item[0],
        ),
):

    trace_lines.append(
        f"  {key:<48} {value}"
    )


trace_lines.extend(
    (
        "",
        "RAW TARGET FIELD CENSUS",
    )
)


for key, value in sorted(
    raw_target_field_counter.items(),
    key=lambda item:
        (
            -item[1],
            item[0],
        ),
):

    trace_lines.append(
        f"  {key:<48} {value}"
    )


trace_lines.extend(
    (
        "",
        "IDENTITY TRANSFORMATION CENSUS",
    )
)


for key, value in sorted(
    transformation_counter.items(),
    key=lambda item:
        (
            -item[1],
            item[0],
        ),
):

    trace_lines.append(
        f"  {key:<64} {value}"
    )


TRACE.write_text(
    "\n".join(
        trace_lines
    )
    + "\n",
    encoding="utf-8",
)


conn.close()


# ============================================================
# CONSOLE RESULT
# ============================================================

print("=" * 78)
print(" GENESIS RECALL R4-R10-R2 RESULT")
print("=" * 78)

print()
print("R3 EXACT TARGET RESOLUTION")

print(
    "  population                    :",
    len(
        r3_rows
    ),
)

print(
    "  resolved                      :",
    exact_r3_resolved,
)

print(
    "  unresolved                    :",
    EXPECTED_R3
    - exact_r3_resolved,
)

print(
    "  target namespace known        :",
    namespace_known,
)

print(
    "  candidate namespace known     :",
    candidate_namespace_known,
)

print(
    "  raw -> candidate mapping known:",
    raw_to_candidate_mapped,
)


print()
print("RESOLUTION METHODS")

for key, value in sorted(
    resolution_counter.items(),
    key=lambda item:
        (
            -item[1],
            item[0],
        ),
):

    print(
        f"  {key:<42} {value}"
    )


print()
print("R3 TARGET NAMESPACE CENSUS")

for key, value in sorted(
    r3_namespace_counter.items(),
    key=lambda item:
        (
            -item[1],
            item[0],
        ),
):

    print(
        f"  {key:<42} {value}"
    )


print()
print("CANDIDATE NAMESPACE CENSUS")

for key, value in sorted(
    candidate_namespace_counter.items(),
    key=lambda item:
        (
            -item[1],
            item[0],
        ),
):

    print(
        f"  {key:<42} {value}"
    )


print()
print("RAW TARGET FIELD CENSUS")

for key, value in sorted(
    raw_target_field_counter.items(),
    key=lambda item:
        (
            -item[1],
            item[0],
        ),
):

    print(
        f"  {key:<42} {value}"
    )


print()
print("IDENTITY TRANSFORMATION CENSUS")

for key, value in sorted(
    transformation_counter.items(),
    key=lambda item:
        (
            -item[1],
            item[0],
        ),
):

    print(
        f"  {key:<58} {value}"
    )


print()
print("CANARIES")

print(
    "  population                    :",
    len(
        CANARIES
    ),
)

print(
    "  resolved                      :",
    canary_resolved,
)

print(
    "  target namespace known        :",
    canary_namespace_known,
)

print(
    "  candidate mapping known       :",
    canary_candidate_mapping_known,
)


print()
print("CERTIFICATION")

for key, value in certification.items():

    print(
        f"  {key:<42}: {value}"
    )


print()
print(
    "R4-R10-R2 DIAGNOSTIC CERTIFIED :",
    diagnostic_certified,
)


print()
print("Artifacts:")
print(" ", REPORT)
print(" ", R3_MAP)
print(" ", RAW_MAP)
print(" ", DB_MAP)
print(" ", CANARY_MAP)
print(" ", UNRESOLVED)
print(" ", TRACE)
print(" ", SCHEMA)

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
