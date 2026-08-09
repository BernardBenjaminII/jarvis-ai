from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


PATH_EQUIVALENTS = {
    "path",
    "file_path",
    "document_path",
    "source_path",
    "local_path",
    "relative_path",
}

ID_EQUIVALENTS = {
    "id",
    "document_id",
    "source_id",
    "chunk_id",
}

CATEGORY_EQUIVALENTS = {
    "category",
    "domain",
    "subject",
    "topic",
    "classification",
}


def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def normalize_name(name: str) -> str:
    text = name.casefold()

    if text in PATH_EQUIVALENTS:
        return "path"
    if text in ID_EQUIVALENTS:
        return "id"
    if text in CATEGORY_EQUIVALENTS:
        return "category"

    return text


def open_ro(path: Path):
    return sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )


def candidate_pairs(
    table_profiles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    pairs = []

    for left_index, left in enumerate(table_profiles):
        for right in table_profiles[left_index + 1 :]:
            for left_column in left["profiled_columns"]:
                if not left_column["key_like"]:
                    continue

                for right_column in right["profiled_columns"]:
                    if not right_column["key_like"]:
                        continue

                    left_norm = normalize_name(left_column["name"])
                    right_norm = normalize_name(right_column["name"])

                    if left_norm != right_norm:
                        continue

                    pairs.append(
                        {
                            "left_database": left["database"],
                            "left_database_path": left["database_path"],
                            "left_table": left["table"],
                            "left_column": left_column["name"],
                            "left_rows": left["row_count"],
                            "left_coverage": left_column["coverage"],
                            "left_uniqueness": left_column["uniqueness"],
                            "right_database": right["database"],
                            "right_database_path": right["database_path"],
                            "right_table": right["table"],
                            "right_column": right_column["name"],
                            "right_rows": right["row_count"],
                            "right_coverage": right_column["coverage"],
                            "right_uniqueness": right_column["uniqueness"],
                            "normalized_key": left_norm,
                        }
                    )

    return pairs


def evaluate_same_database_join(
    pair: dict[str, Any],
    *,
    sample_limit: int = 5000,
) -> dict[str, Any]:
    if (
        pair["left_database_path"]
        != pair["right_database_path"]
    ):
        return {
            **pair,
            "join_scope": "cross_database",
            "matched_left_rows": None,
            "matched_right_rows": None,
            "left_match_rate": None,
            "right_match_rate": None,
            "ambiguous_values": None,
            "score": 0.0,
            "recommendation": "inspect_cross_database",
        }

    path = Path(pair["left_database_path"])
    connection = open_ro(path)

    try:
        left_table = qident(pair["left_table"])
        right_table = qident(pair["right_table"])
        left_column = qident(pair["left_column"])
        right_column = qident(pair["right_column"])

        left_nonempty = int(
            connection.execute(
                f"""
                SELECT COUNT(*)
                FROM {left_table}
                WHERE {left_column} IS NOT NULL
                  AND TRIM(CAST({left_column} AS TEXT)) <> ''
                """
            ).fetchone()[0]
        )
        right_nonempty = int(
            connection.execute(
                f"""
                SELECT COUNT(*)
                FROM {right_table}
                WHERE {right_column} IS NOT NULL
                  AND TRIM(CAST({right_column} AS TEXT)) <> ''
                """
            ).fetchone()[0]
        )

        matched_left = int(
            connection.execute(
                f"""
                SELECT COUNT(*)
                FROM (
                    SELECT DISTINCT l.rowid
                    FROM {left_table} AS l
                    JOIN {right_table} AS r
                      ON CAST(l.{left_column} AS TEXT)
                       = CAST(r.{right_column} AS TEXT)
                    WHERE l.{left_column} IS NOT NULL
                      AND TRIM(CAST(l.{left_column} AS TEXT)) <> ''
                    LIMIT ?
                )
                """,
                (sample_limit,),
            ).fetchone()[0]
        )
        matched_right = int(
            connection.execute(
                f"""
                SELECT COUNT(*)
                FROM (
                    SELECT DISTINCT r.rowid
                    FROM {left_table} AS l
                    JOIN {right_table} AS r
                      ON CAST(l.{left_column} AS TEXT)
                       = CAST(r.{right_column} AS TEXT)
                    WHERE r.{right_column} IS NOT NULL
                      AND TRIM(CAST(r.{right_column} AS TEXT)) <> ''
                    LIMIT ?
                )
                """,
                (sample_limit,),
            ).fetchone()[0]
        )
        ambiguous = int(
            connection.execute(
                f"""
                SELECT COUNT(*)
                FROM (
                    SELECT CAST({left_column} AS TEXT) AS value
                    FROM {left_table}
                    WHERE {left_column} IS NOT NULL
                      AND TRIM(CAST({left_column} AS TEXT)) <> ''
                    GROUP BY CAST({left_column} AS TEXT)
                    HAVING COUNT(*) > 1
                )
                """
            ).fetchone()[0]
        )

        left_rate = (
            0.0
            if left_nonempty == 0
            else min(1.0, matched_left / left_nonempty)
        )
        right_rate = (
            0.0
            if right_nonempty == 0
            else min(1.0, matched_right / right_nonempty)
        )

        uniqueness = min(
            float(pair["left_uniqueness"]),
            float(pair["right_uniqueness"]),
        )
        score = (
            0.45 * left_rate
            + 0.35 * right_rate
            + 0.20 * uniqueness
        )

        if score >= 0.85:
            recommendation = "preferred_join"
        elif score >= 0.60:
            recommendation = "usable_with_validation"
        elif score >= 0.30:
            recommendation = "weak_join"
        else:
            recommendation = "reject_join"

        return {
            **pair,
            "join_scope": "same_database",
            "matched_left_rows": matched_left,
            "matched_right_rows": matched_right,
            "left_match_rate": left_rate,
            "right_match_rate": right_rate,
            "ambiguous_values": ambiguous,
            "score": score,
            "recommendation": recommendation,
        }
    except Exception as exc:
        return {
            **pair,
            "join_scope": "same_database",
            "matched_left_rows": None,
            "matched_right_rows": None,
            "left_match_rate": None,
            "right_match_rate": None,
            "ambiguous_values": None,
            "score": 0.0,
            "recommendation": "join_error",
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        connection.close()


def lineage_paths(
    joins: list[dict[str, Any]],
    table_profiles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    category_tables = {
        (
            profile["database"],
            profile["table"],
        ): [
            column["name"]
            for column in profile["profiled_columns"]
            if column["category_like"]
            and column["coverage"] > 0
        ]
        for profile in table_profiles
    }

    paths = []

    for join in joins:
        left_category = category_tables.get(
            (
                join["left_database"],
                join["left_table"],
            ),
            [],
        )
        right_category = category_tables.get(
            (
                join["right_database"],
                join["right_table"],
            ),
            [],
        )

        if not left_category and not right_category:
            continue

        paths.append(
            {
                "source": (
                    f"{join['left_database']}."
                    f"{join['left_table']}."
                    f"{join['left_column']}"
                ),
                "target": (
                    f"{join['right_database']}."
                    f"{join['right_table']}."
                    f"{join['right_column']}"
                ),
                "normalized_key": join["normalized_key"],
                "score": join["score"],
                "recommendation": join["recommendation"],
                "left_category_fields": left_category,
                "right_category_fields": right_category,
                "metadata_propagation_possible": bool(
                    left_category or right_category
                )
                and join["recommendation"]
                in {
                    "preferred_join",
                    "usable_with_validation",
                },
            }
        )

    return paths
