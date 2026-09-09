from __future__ import annotations

import argparse
import json
import sqlite3
import time

from pathlib import Path


DEFAULT_RUNTIME_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/"
    "knowledge/catalog.sqlite"
)

DEFAULT_AS1_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/"
    "knowledge/as1_identity.sqlite"
)

KNOWLEDGE_ROOT = Path(
    "/media/abdullah/JARVISDATA/Knowledge"
)

FM_CANARY = (
    KNOWLEDGE_ROOT
    / "military"
    / "doctrine"
    / "US_Army_FM_3-06.11_Urban_Terrain.pdf"
)


EXCLUDED_ACTIONS = (
    "ignore",
    "exclude",
    "reject",
    "skip",
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


def table_exists(
    conn: sqlite3.Connection,
    table: str,
) -> bool:
    return (
        conn.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type IN ('table','view')
              AND name=?
            LIMIT 1
            """,
            (table,),
        ).fetchone()
        is not None
    )


def count(
    conn: sqlite3.Connection,
    table: str,
) -> int | None:
    if not table_exists(conn, table):
        return None

    row = conn.execute(
        f'SELECT COUNT(*) FROM "{table}"'
    ).fetchone()

    return int(row[0])


def scalar(
    conn: sqlite3.Connection,
    sql: str,
    params=(),
) -> int:
    row = conn.execute(
        sql,
        params,
    ).fetchone()

    if row is None:
        return 0

    return int(row[0] or 0)


def action_distribution(
    conn: sqlite3.Connection,
) -> list[dict]:
    rows = conn.execute(
        """
        SELECT
            COALESCE(NULLIF(TRIM(action), ''), '<blank>')
                AS action_value,
            COUNT(*) AS n
        FROM knowledge_classifications
        GROUP BY
            COALESCE(NULLIF(TRIM(action), ''), '<blank>')
        ORDER BY n DESC, action_value
        """
    ).fetchall()

    return [
        {
            "action": str(row["action_value"]),
            "count": int(row["n"]),
        }
        for row in rows
    ]


def type_distribution(
    conn: sqlite3.Connection,
) -> list[dict]:
    rows = conn.execute(
        """
        SELECT
            COALESCE(
                NULLIF(TRIM(knowledge_type), ''),
                '<blank>'
            ) AS knowledge_type_value,
            COUNT(*) AS n
        FROM knowledge_classifications
        GROUP BY
            COALESCE(
                NULLIF(TRIM(knowledge_type), ''),
                '<blank>'
            )
        ORDER BY n DESC, knowledge_type_value
        """
    ).fetchall()

    return [
        {
            "knowledge_type":
                str(row["knowledge_type_value"]),
            "count":
                int(row["n"]),
        }
        for row in rows
    ]


def coverage_query() -> str:
    """
    All expensive work remains in SQLite.

    We aggregate runtime_chunks and FTS by document_id once,
    then join the much smaller coverage sets to the catalog
    population.

    Python receives only grouped summary rows.
    """

    return """
    WITH
    chunk_coverage AS (
        SELECT
            document_id,
            COUNT(*) AS chunk_count
        FROM runtime_chunks
        GROUP BY document_id
    ),

    fts_coverage AS (
        SELECT
            CAST(document_id AS INTEGER)
                AS document_id,
            COUNT(*) AS fts_count
        FROM runtime_chunks_fts
        GROUP BY
            CAST(document_id AS INTEGER)
    ),

    joined AS (
        SELECT
            kc.file_path,
            kc.action,
            kc.knowledge_type,
            rd.id AS runtime_document_id,

            COALESCE(
                cc.chunk_count,
                0
            ) AS chunk_count,

            COALESCE(
                fc.fts_count,
                0
            ) AS fts_count

        FROM knowledge_classifications kc

        LEFT JOIN runtime_documents rd
          ON rd.file_path = kc.file_path

        LEFT JOIN chunk_coverage cc
          ON cc.document_id = rd.id

        LEFT JOIN fts_coverage fc
          ON fc.document_id = rd.id
    ),

    classified AS (
        SELECT
            *,

            CASE
                WHEN lower(
                    COALESCE(
                        TRIM(action),
                        ''
                    )
                ) IN (
                    'ignore',
                    'exclude',
                    'reject',
                    'skip'
                )
                THEN 'UNSUPPORTED_OR_EXCLUDED'

                WHEN runtime_document_id IS NULL
                THEN 'CATALOG_ONLY'

                WHEN chunk_count = 0
                THEN 'RUNTIME_WITHOUT_CHUNKS'

                WHEN fts_count = 0
                THEN 'CHUNKS_WITHOUT_FTS'

                ELSE 'FULLY_RECALLABLE'
            END AS recall_status

        FROM joined
    )

    SELECT
        recall_status,
        COUNT(*) AS objects
    FROM classified
    GROUP BY recall_status
    ORDER BY
        CASE recall_status
            WHEN 'FULLY_RECALLABLE' THEN 1
            WHEN 'CATALOG_ONLY' THEN 2
            WHEN 'RUNTIME_WITHOUT_CHUNKS' THEN 3
            WHEN 'CHUNKS_WITHOUT_FTS' THEN 4
            WHEN 'UNSUPPORTED_OR_EXCLUDED' THEN 5
            ELSE 99
        END
    """


def coverage_detail_query() -> str:
    return """
    WITH
    chunk_coverage AS (
        SELECT
            document_id,
            COUNT(*) AS chunk_count
        FROM runtime_chunks
        GROUP BY document_id
    ),

    fts_coverage AS (
        SELECT
            CAST(document_id AS INTEGER)
                AS document_id,
            COUNT(*) AS fts_count
        FROM runtime_chunks_fts
        GROUP BY
            CAST(document_id AS INTEGER)
    )

    SELECT
        kc.file_path,
        kc.action,
        kc.knowledge_type,
        kc.domain,
        kc.subject,

        rd.id AS runtime_document_id,
        rd.title AS runtime_title,

        COALESCE(
            cc.chunk_count,
            0
        ) AS chunk_count,

        COALESCE(
            fc.fts_count,
            0
        ) AS fts_count,

        CASE
            WHEN lower(
                COALESCE(
                    TRIM(kc.action),
                    ''
                )
            ) IN (
                'ignore',
                'exclude',
                'reject',
                'skip'
            )
            THEN 'UNSUPPORTED_OR_EXCLUDED'

            WHEN rd.id IS NULL
            THEN 'CATALOG_ONLY'

            WHEN COALESCE(
                cc.chunk_count,
                0
            ) = 0
            THEN 'RUNTIME_WITHOUT_CHUNKS'

            WHEN COALESCE(
                fc.fts_count,
                0
            ) = 0
            THEN 'CHUNKS_WITHOUT_FTS'

            ELSE 'FULLY_RECALLABLE'
        END AS recall_status

    FROM knowledge_classifications kc

    LEFT JOIN runtime_documents rd
      ON rd.file_path = kc.file_path

    LEFT JOIN chunk_coverage cc
      ON cc.document_id = rd.id

    LEFT JOIN fts_coverage fc
      ON fc.document_id = rd.id
    """


def coverage_summary(
    conn: sqlite3.Connection,
) -> dict[str, int]:
    rows = conn.execute(
        coverage_query()
    ).fetchall()

    return {
        str(row["recall_status"]):
            int(row["objects"])
        for row in rows
    }


def gap_examples(
    conn: sqlite3.Connection,
    *,
    status: str,
    limit: int = 25,
) -> list[dict]:

    sql = (
        "WITH coverage AS ("
        + coverage_detail_query()
        + """
        )
        SELECT *
        FROM coverage
        WHERE recall_status=?
        ORDER BY file_path
        LIMIT ?
        """
    )

    rows = conn.execute(
        sql,
        (
            status,
            limit,
        ),
    ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def fm_canary(
    conn: sqlite3.Connection,
) -> dict:

    sql = (
        "WITH coverage AS ("
        + coverage_detail_query()
        + """
        )
        SELECT *
        FROM coverage
        WHERE file_path=?
        LIMIT 1
        """
    )

    row = conn.execute(
        sql,
        (str(FM_CANARY),),
    ).fetchone()

    if row is None:
        return {
            "file_path":
                str(FM_CANARY),

            "physical":
                FM_CANARY.is_file(),

            "classification":
                None,

            "recall_status":
                "NOT_IN_KNOWLEDGE_CLASSIFICATIONS",
        }

    result = dict(row)

    result["physical"] = (
        FM_CANARY.is_file()
    )

    return result


def reverse_runtime_coverage(
    conn: sqlite3.Connection,
) -> dict:
    """
    Runtime documents that do not have a matching canonical
    knowledge_classifications path.

    These can be recallable content that JARVIS lacks structured
    catalog awareness for.
    """

    runtime_without_classification = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM runtime_documents rd
        LEFT JOIN knowledge_classifications kc
          ON kc.file_path = rd.file_path
        WHERE kc.file_path IS NULL
        """
    )

    classification_without_runtime = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM knowledge_classifications kc
        LEFT JOIN runtime_documents rd
          ON rd.file_path = kc.file_path
        WHERE rd.id IS NULL
        """
    )

    return {
        "runtime_without_classification":
            runtime_without_classification,

        "classification_without_runtime":
            classification_without_runtime,
    }


def exact_runtime_recall_coverage(
    conn: sqlite3.Connection,
) -> dict:
    """
    Inspect runtime itself independently of catalog mapping.

    This answers:
      Of runtime_documents, how many have chunks and FTS?
    """

    row = conn.execute(
        """
        WITH
        chunk_docs AS (
            SELECT DISTINCT document_id
            FROM runtime_chunks
        ),

        fts_docs AS (
            SELECT DISTINCT
                CAST(document_id AS INTEGER)
                    AS document_id
            FROM runtime_chunks_fts
        )

        SELECT
            COUNT(*) AS runtime_documents,

            SUM(
                CASE
                    WHEN cd.document_id IS NOT NULL
                    THEN 1 ELSE 0
                END
            ) AS with_chunks,

            SUM(
                CASE
                    WHEN fd.document_id IS NOT NULL
                    THEN 1 ELSE 0
                END
            ) AS with_fts,

            SUM(
                CASE
                    WHEN cd.document_id IS NOT NULL
                     AND fd.document_id IS NOT NULL
                    THEN 1 ELSE 0
                END
            ) AS fully_recallable,

            SUM(
                CASE
                    WHEN cd.document_id IS NULL
                    THEN 1 ELSE 0
                END
            ) AS without_chunks,

            SUM(
                CASE
                    WHEN cd.document_id IS NOT NULL
                     AND fd.document_id IS NULL
                    THEN 1 ELSE 0
                END
            ) AS chunks_without_fts

        FROM runtime_documents rd

        LEFT JOIN chunk_docs cd
          ON cd.document_id = rd.id

        LEFT JOIN fts_docs fd
          ON fd.document_id = rd.id
        """
    ).fetchone()

    return {
        key: int(row[key] or 0)
        for key in row.keys()
    }


def awareness_layers(
    conn: sqlite3.Connection,
) -> dict:

    result = {}

    for table in (
        "discovered_files",
        "knowledge_classifications",
        "knowledge_objects",
        "knowledge_registry",
        "librarian_catalog",
        "catalog_enrichment",
        "catalog_documents",
        "document_assimilation",
        "document_subjects",
        "runtime_documents",
        "runtime_chunks",
        "runtime_chunks_fts",
    ):
        result[table] = count(
            conn,
            table,
        )

    return result


def as1_summary(
    conn: sqlite3.Connection,
) -> dict:

    result = {}

    if table_exists(
        conn,
        "as1_identity_fingerprints",
    ):
        result[
            "runtime_fingerprints"
        ] = scalar(
            conn,
            """
            SELECT COUNT(*)
            FROM as1_identity_fingerprints
            WHERE source_kind='runtime'
              AND fingerprint_version='as1-fingerprint-v1'
            """
        )

    if table_exists(
        conn,
        "as1_identity_groups",
    ):
        result[
            "identity_groups"
        ] = count(
            conn,
            "as1_identity_groups",
        )

    if table_exists(
        conn,
        "as1_identity_members",
    ):
        result[
            "identity_members"
        ] = count(
            conn,
            "as1_identity_members",
        )

    return result


def percent(
    numerator: int,
    denominator: int,
) -> float:

    if denominator <= 0:
        return 0.0

    return (
        numerator
        * 100.0
        / denominator
    )


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Genesis Recall R1A global catalog-to-runtime "
            "coverage census."
        )
    )

    parser.add_argument(
        "--runtime-db",
        type=Path,
        default=DEFAULT_RUNTIME_DB,
    )

    parser.add_argument(
        "--as1-db",
        type=Path,
        default=DEFAULT_AS1_DB,
    )

    parser.add_argument(
        "--json",
        type=Path,
        default=None,
    )

    args = parser.parse_args()

    if not args.runtime_db.is_file():
        print(
            "FAIL: runtime DB missing:",
            args.runtime_db,
            flush=True,
        )
        return 2

    if not args.as1_db.is_file():
        print(
            "FAIL: AS1 DB missing:",
            args.as1_db,
            flush=True,
        )
        return 2

    started = time.monotonic()

    runtime = ro(
        args.runtime_db
    )

    as1 = ro(
        args.as1_db
    )

    try:
        print(
            "============================================================",
            flush=True,
        )

        print(
            " GENESIS RECALL R1A — GLOBAL COVERAGE CENSUS",
            flush=True,
        )

        print(
            "============================================================",
            flush=True,
        )

        # ----------------------------------------------------
        # 1. Awareness layers
        # ----------------------------------------------------

        print()
        print(
            "=== 1. KNOWLEDGE AWARENESS LAYERS ===",
            flush=True,
        )

        awareness = awareness_layers(
            runtime
        )

        for table, n in awareness.items():
            print(
                f"{table:28} : "
                + (
                    f"{n:,}"
                    if n is not None
                    else "MISSING"
                ),
                flush=True,
            )

        # ----------------------------------------------------
        # 2. Classification policy
        # ----------------------------------------------------

        print()
        print(
            "=== 2. CLASSIFICATION ACTION DISTRIBUTION ===",
            flush=True,
        )

        actions = action_distribution(
            runtime
        )

        for item in actions:
            print(
                f"{item['action']:28} : "
                f"{item['count']:,}",
                flush=True,
            )

        print()
        print(
            "=== 3. KNOWLEDGE TYPE DISTRIBUTION ===",
            flush=True,
        )

        types = type_distribution(
            runtime
        )

        for item in types:
            print(
                f"{item['knowledge_type']:28} : "
                f"{item['count']:,}",
                flush=True,
            )

        # ----------------------------------------------------
        # 3. Runtime intrinsic recall
        # ----------------------------------------------------

        print()
        print(
            "=== 4. RUNTIME DOCUMENT RECALL COVERAGE ===",
            flush=True,
        )

        runtime_coverage = (
            exact_runtime_recall_coverage(
                runtime
            )
        )

        for key, value in (
            runtime_coverage.items()
        ):
            print(
                f"{key:28} : "
                f"{value:,}",
                flush=True,
            )

        runtime_pct = percent(
            runtime_coverage[
                "fully_recallable"
            ],
            runtime_coverage[
                "runtime_documents"
            ],
        )

        print(
            f"{'runtime recall coverage':28} : "
            f"{runtime_pct:.3f}%",
            flush=True,
        )

        # ----------------------------------------------------
        # 4. Catalog -> runtime mapping
        # ----------------------------------------------------

        print()
        print(
            "=== 5. GLOBAL CATALOG -> RUNTIME STATUS ===",
            flush=True,
        )

        coverage = coverage_summary(
            runtime
        )

        status_order = (
            "FULLY_RECALLABLE",
            "CATALOG_ONLY",
            "RUNTIME_WITHOUT_CHUNKS",
            "CHUNKS_WITHOUT_FTS",
            "UNSUPPORTED_OR_EXCLUDED",
        )

        for status in status_order:
            print(
                f"{status:28} : "
                f"{coverage.get(status, 0):,}",
                flush=True,
            )

        known = (
            awareness.get(
                "knowledge_classifications"
            )
            or 0
        )

        excluded = coverage.get(
            "UNSUPPORTED_OR_EXCLUDED",
            0,
        )

        eligible = max(
            0,
            known - excluded,
        )

        fully = coverage.get(
            "FULLY_RECALLABLE",
            0,
        )

        effective_pct = percent(
            fully,
            eligible,
        )

        print()
        print(
            f"{'classified objects':28} : "
            f"{known:,}",
            flush=True,
        )

        print(
            f"{'recall-eligible objects':28} : "
            f"{eligible:,}",
            flush=True,
        )

        print(
            f"{'effective recall coverage':28} : "
            f"{effective_pct:.3f}%",
            flush=True,
        )

        # ----------------------------------------------------
        # 5. Reverse mapping
        # ----------------------------------------------------

        print()
        print(
            "=== 6. CATALOG / RUNTIME PATH RECONCILIATION ===",
            flush=True,
        )

        reverse = reverse_runtime_coverage(
            runtime
        )

        print(
            "classification without runtime :",
            f"{reverse['classification_without_runtime']:,}",
            flush=True,
        )

        print(
            "runtime without classification :",
            f"{reverse['runtime_without_classification']:,}",
            flush=True,
        )

        # ----------------------------------------------------
        # 6. Gap examples
        # ----------------------------------------------------

        examples = {}

        for status in (
            "CATALOG_ONLY",
            "RUNTIME_WITHOUT_CHUNKS",
            "CHUNKS_WITHOUT_FTS",
        ):
            print()
            print(
                f"=== 7. SAMPLE {status} ===",
                flush=True,
            )

            rows = gap_examples(
                runtime,
                status=status,
                limit=20,
            )

            examples[status] = rows

            if not rows:
                print(
                    "(none)",
                    flush=True,
                )

            for row in rows:
                print(
                    f"{row['file_path']}",
                    flush=True,
                )

                print(
                    "  action/type :",
                    row["action"],
                    "/",
                    row["knowledge_type"],
                    flush=True,
                )

                print(
                    "  runtime id  :",
                    row["runtime_document_id"],
                    flush=True,
                )

                print(
                    "  chunks/fts  :",
                    row["chunk_count"],
                    "/",
                    row["fts_count"],
                    flush=True,
                )

        # ----------------------------------------------------
        # 7. FM canary
        # ----------------------------------------------------

        print()
        print(
            "=== 8. FM 3-06.11 CANARY ===",
            flush=True,
        )

        canary = fm_canary(
            runtime
        )

        print(
            "physical                :",
            canary.get(
                "physical"
            ),
            flush=True,
        )

        print(
            "file path               :",
            canary.get(
                "file_path"
            ),
            flush=True,
        )

        print(
            "action                  :",
            canary.get(
                "action"
            ),
            flush=True,
        )

        print(
            "knowledge type          :",
            canary.get(
                "knowledge_type"
            ),
            flush=True,
        )

        print(
            "runtime document id     :",
            canary.get(
                "runtime_document_id"
            ),
            flush=True,
        )

        print(
            "runtime title           :",
            canary.get(
                "runtime_title"
            ),
            flush=True,
        )

        print(
            "chunks                  :",
            canary.get(
                "chunk_count",
                0,
            ),
            flush=True,
        )

        print(
            "FTS rows                :",
            canary.get(
                "fts_count",
                0,
            ),
            flush=True,
        )

        print(
            "recall status           :",
            canary.get(
                "recall_status"
            ),
            flush=True,
        )

        # ----------------------------------------------------
        # 8. AS1 state
        # ----------------------------------------------------

        print()
        print(
            "=== 9. AS1 COVERAGE ===",
            flush=True,
        )

        as1_state = as1_summary(
            as1
        )

        for key, value in (
            as1_state.items()
        ):
            print(
                f"{key:28} : "
                f"{value:,}",
                flush=True,
            )

        # ----------------------------------------------------
        # 9. Critical gap total
        # ----------------------------------------------------

        critical_gaps = (
            coverage.get(
                "CATALOG_ONLY",
                0,
            )
            + coverage.get(
                "RUNTIME_WITHOUT_CHUNKS",
                0,
            )
            + coverage.get(
                "CHUNKS_WITHOUT_FTS",
                0,
            )
        )

        elapsed = (
            time.monotonic()
            - started
        )

        print()
        print(
            "============================================================",
            flush=True,
        )

        print(
            " JARVIS KNOWLEDGE RECALL COVERAGE",
            flush=True,
        )

        print(
            "============================================================",
            flush=True,
        )

        print(
            f"Known classified objects      : {known:,}",
            flush=True,
        )

        print(
            f"Recall-eligible objects        : {eligible:,}",
            flush=True,
        )

        print(
            f"Fully recallable               : {fully:,}",
            flush=True,
        )

        print(
            f"Catalog only                   : "
            f"{coverage.get('CATALOG_ONLY', 0):,}",
            flush=True,
        )

        print(
            f"Runtime without chunks         : "
            f"{coverage.get('RUNTIME_WITHOUT_CHUNKS', 0):,}",
            flush=True,
        )

        print(
            f"Chunks without FTS             : "
            f"{coverage.get('CHUNKS_WITHOUT_FTS', 0):,}",
            flush=True,
        )

        print(
            f"Unsupported / excluded         : "
            f"{excluded:,}",
            flush=True,
        )

        print(
            f"Critical recall gaps           : "
            f"{critical_gaps:,}",
            flush=True,
        )

        print(
            f"Effective recall coverage      : "
            f"{effective_pct:.3f}%",
            flush=True,
        )

        print()
        print(
            "FM 3-06.11:",
            flush=True,
        )

        print(
            "  physical                     :",
            (
                "YES"
                if canary.get(
                    "physical"
                )
                else "NO"
            ),
            flush=True,
        )

        print(
            "  runtime document             :",
            (
                "YES"
                if canary.get(
                    "runtime_document_id"
                )
                is not None
                else "NO"
            ),
            flush=True,
        )

        print(
            "  chunks                       :",
            canary.get(
                "chunk_count",
                0,
            ),
            flush=True,
        )

        print(
            "  FTS rows                     :",
            canary.get(
                "fts_count",
                0,
            ),
            flush=True,
        )

        print(
            "  status                       :",
            canary.get(
                "recall_status"
            ),
            flush=True,
        )

        print()
        print(
            f"Elapsed seconds                : {elapsed:.2f}",
            flush=True,
        )

        print(
            "Production DB writes           : 0",
            flush=True,
        )

        print(
            "============================================================",
            flush=True,
        )

        report = {
            "schema":
                "genesis-recall-r1a-v1",

            "read_only":
                True,

            "awareness_layers":
                awareness,

            "classification_actions":
                actions,

            "knowledge_types":
                types,

            "runtime_recall":
                runtime_coverage,

            "runtime_recall_coverage_pct":
                runtime_pct,

            "catalog_runtime_status":
                coverage,

            "known_classified":
                known,

            "recall_eligible":
                eligible,

            "fully_recallable":
                fully,

            "effective_recall_coverage_pct":
                effective_pct,

            "critical_recall_gaps":
                critical_gaps,

            "path_reconciliation":
                reverse,

            "gap_examples":
                examples,

            "fm_canary":
                canary,

            "as1":
                as1_state,

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

            print(
                "JSON report:",
                args.json,
                flush=True,
            )

        return 0

    finally:
        runtime.close()
        as1.close()


if __name__ == "__main__":
    raise SystemExit(main())
