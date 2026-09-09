from __future__ import annotations

import csv
import json
import math
import re
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping


PROJECT = Path("/media/abdullah/JARVISDATA/Projects/jarvis-ai")
DB = Path("/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite")

REPORT = PROJECT / "artifacts/genesis_recall/r3_production_recall_census.json"
TSV = PROJECT / "artifacts/genesis_recall/r3_production_recall_census.tsv"
FAILURES = PROJECT / "artifacts/genesis_recall/r3_recall_failures.tsv"

SAMPLE_SIZE = 250
RAW_LIMIT = 100
QUALIFIED_LIMIT = 100

sys.path.insert(0, str(PROJECT))

from core.knowledge_catalog.search import search_catalog
from core.knowledge_catalog.qualified_search import search_qualified_catalog


# ----------------------------------------------------------------
# Generic row helpers
# ----------------------------------------------------------------

def value(row: Any, *names: str) -> Any:
    if row is None:
        return None

    if isinstance(row, Mapping):
        for name in names:
            if name in row:
                return row.get(name)

    for name in names:
        try:
            v = getattr(row, name)
        except Exception:
            continue
        if v is not None:
            return v

    return None


def intish(v: Any) -> int | None:
    if v is None:
        return None

    try:
        return int(v)
    except Exception:
        pass

    try:
        s = str(v).strip()
        if s.isdigit():
            return int(s)
    except Exception:
        pass

    return None


def row_document_id(row: Any) -> int | None:
    direct = intish(
        value(
            row,
            "document_id",
            "runtime_document_id",
        )
    )
    if direct is not None:
        return direct

    metadata = value(row, "metadata")

    if isinstance(metadata, Mapping):
        raw_row = metadata.get("raw_row")

        if isinstance(raw_row, Mapping):
            doc_id = intish(raw_row.get("document_id"))
            if doc_id is not None:
                return doc_id

        doc_id = intish(metadata.get("document_id"))
        if doc_id is not None:
            return doc_id

    raw_row = value(row, "raw_row")

    if isinstance(raw_row, Mapping):
        doc_id = intish(raw_row.get("document_id"))
        if doc_id is not None:
            return doc_id

    return None


def row_title(row: Any) -> str:
    for name in (
        "title",
        "subject",
        "name",
        "filename",
        "file_name",
    ):
        v = value(row, name)
        if v:
            return str(v)

    metadata = value(row, "metadata")
    if isinstance(metadata, Mapping):
        raw = metadata.get("raw_row")
        if isinstance(raw, Mapping):
            for name in (
                "title",
                "subject",
                "name",
                "filename",
                "file_name",
            ):
                v = raw.get(name)
                if v:
                    return str(v)

    return ""


# ----------------------------------------------------------------
# Query synthesis
# ----------------------------------------------------------------

EXTENSIONS = re.compile(
    r"""
    \.
    (
        pdf|txt|html?|htm|epub|mobi|azw3|
        docx?|rtf|odt|pptx?|xlsx?|csv|
        md|markdown
        re.IGNORECASE | re.VERBOSE,
    )
    $
    """
)

NOISE = re.compile(r"[_\-\.\(\)\[\]\{\}/\\]+")
SPACE = re.compile(r"\s+")


def normalize_title(title: str) -> str:
    text = str(title or "").strip()

    text = EXTENSIONS.sub("", text)
    text = NOISE.sub(" ", text)
    text = SPACE.sub(" ", text).strip()

    return text


def query_from_title(title: str) -> str:
    """
    Preserve identity-bearing title terms.

    We intentionally do NOT aggressively shorten titles here because
    R3 measures whether production can recall known catalog identity.
    """
    q = normalize_title(title)

    if len(q) > 220:
        q = q[:220].rsplit(" ", 1)[0].strip()

    return q


def query_is_eligible(query: str) -> bool:
    if not query:
        return False

    tokens = re.findall(r"[A-Za-z0-9]+", query)

    if len(tokens) < 2:
        return False

    if len(query) < 5:
        return False

    return True


# ----------------------------------------------------------------
# Read-only database discovery
# ----------------------------------------------------------------

def ro_connect() -> sqlite3.Connection:
    uri = f"file:{DB}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    return conn


def table_columns(
    conn: sqlite3.Connection,
    table: str,
) -> list[str]:
    safe = table.replace('"', '""')
    rows = conn.execute(
        f'PRAGMA table_info("{safe}")'
    ).fetchall()

    return [str(row["name"]) for row in rows]


def choose_document_table(
    conn: sqlite3.Connection,
) -> tuple[str, str, str]:
    """
    Locate a catalog/runtime document table containing:
      - an ID column
      - a usable title/identity column

    Prefer runtime_documents because R4-R8 durable identity is
    document_id.
    """

    tables = [
        str(row["name"])
        for row in conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()
    ]

    preferred = [
        "runtime_documents",
        "documents",
        "catalog_documents",
        "document",
    ]

    ordered = []

    for table in preferred:
        if table in tables and table not in ordered:
            ordered.append(table)

    for table in tables:
        if table not in ordered:
            ordered.append(table)

    id_names = (
        "document_id",
        "runtime_document_id",
        "id",
    )

    title_names = (
        "title",
        "subject",
        "name",
        "filename",
        "file_name",
    )

    for table in ordered:
        cols = table_columns(conn, table)
        lower = {c.lower(): c for c in cols}

        id_col = None
        title_col = None

        for candidate in id_names:
            if candidate in lower:
                id_col = lower[candidate]
                break

        for candidate in title_names:
            if candidate in lower:
                title_col = lower[candidate]
                break

        if id_col and title_col:
            return table, id_col, title_col

    raise RuntimeError(
        "No eligible document identity table discovered"
    )


def load_eligible_universe() -> tuple[
    list[dict[str, Any]],
    dict[str, Any],
]:
    conn = ro_connect()

    try:
        table, id_col, title_col = choose_document_table(conn)

        safe_table = table.replace('"', '""')
        safe_id = id_col.replace('"', '""')
        safe_title = title_col.replace('"', '""')

        rows = conn.execute(
            f"""
            SELECT
                "{safe_id}" AS document_id,
                "{safe_title}" AS title
            FROM "{safe_table}"
            WHERE "{safe_id}" IS NOT NULL
              AND "{safe_title}" IS NOT NULL
            ORDER BY "{safe_id}"
            """
        ).fetchall()

        eligible = []

        for row in rows:
            document_id = intish(row["document_id"])
            title = str(row["title"] or "").strip()

            if document_id is None:
                continue

            query = query_from_title(title)

            if not query_is_eligible(query):
                continue

            eligible.append(
                {
                    "document_id": document_id,
                    "title": title,
                    "query": query,
                }
            )

        meta = {
            "table": table,
            "id_column": id_col,
            "title_column": title_col,
            "rows_seen": len(rows),
            "eligible_documents": len(eligible),
        }

        return eligible, meta

    finally:
        conn.close()


# ----------------------------------------------------------------
# Deterministic quantile sampling
# ----------------------------------------------------------------

def deterministic_quantile_sample(
    universe: list[dict[str, Any]],
    n: int,
) -> list[dict[str, Any]]:
    if len(universe) < n:
        raise RuntimeError(
            f"Eligible universe {len(universe)} < required sample {n}"
        )

    if n == 1:
        return [universe[len(universe) // 2]]

    indexes = []

    for i in range(n):
        position = i * (len(universe) - 1) / (n - 1)
        idx = int(round(position))
        indexes.append(idx)

    # Rounding should already be unique when universe >= n,
    # but enforce uniqueness deterministically.
    selected_indexes = []
    used = set()

    for idx in indexes:
        candidate = idx

        while candidate in used and candidate + 1 < len(universe):
            candidate += 1

        while candidate in used and candidate - 1 >= 0:
            candidate -= 1

        if candidate in used:
            raise RuntimeError(
                "Unable to produce exact deterministic sample"
            )

        used.add(candidate)
        selected_indexes.append(candidate)

    sample = [universe[i] for i in selected_indexes]

    if len(sample) != n:
        raise RuntimeError(
            f"Sample size {len(sample)} != required {n}"
        )

    if len({x["document_id"] for x in sample}) != n:
        raise RuntimeError(
            "Deterministic sample contains duplicate document IDs"
        )

    return sample


# ----------------------------------------------------------------
# Retrieval ranking
# ----------------------------------------------------------------

def find_rank(
    rows: Iterable[Any],
    target_document_id: int,
) -> int | None:
    for rank, row in enumerate(rows, start=1):
        if row_document_id(row) == target_document_id:
            return rank

    return None


def rank_bucket(rank: int | None) -> str:
    if rank is None:
        return "MISS"
    if rank == 1:
        return "@1"
    if rank <= 5:
        return "@5"
    if rank <= 20:
        return "@20"
    return "@100"


def classify(
    raw_rank: int | None,
    qualified_rank: int | None,
) -> str:
    if raw_rank is None:
        return "RAW_MISS"

    if qualified_rank is None:
        return "QUALIFICATION_DROP"

    if qualified_rank == 1:
        return "FULL_PASS_RANK1"

    if qualified_rank <= 5:
        return "FULL_PASS_TOP5"

    if qualified_rank <= 20:
        return "FULL_PASS_TOP20"

    return "FULL_PASS_TOP100"


# ----------------------------------------------------------------
# Known production regression canaries
# ----------------------------------------------------------------

KNOWN = (
    (
        "ai_assisted_python",
        "AI assisted Python programming",
        11,
    ),
    (
        "cpp",
        "C++ programming",
        4,
    ),
    (
        "effective_c",
        "effective C programming",
        14,
    ),
    (
        "lane",
        "Edward William Lane Arabic English Lexicon Vol 6",
        86876,
    ),
)


ADVERSARIAL = (
    "quantum upholstery banana zeppelin",
    "medieval sourdough GPU firmware",
    "hydraulic pastry compiler astronomy",
    "volcanic spreadsheet penguin firmware",
    "ceramic database pineapple cavalry",
    "orbital sandwich kernel theology",
    "Victorian Kubernetes broccoli engine",
    "submarine pastry JavaScript cathedral",
    "neural gearbox cinnamon telescope",
    "Apache helicopter sourdough recursion violin",
)


# ----------------------------------------------------------------
# Main
# ----------------------------------------------------------------

def pct(num: int, den: int) -> float:
    if den <= 0:
        return 0.0
    return round((num / den) * 100.0, 2)


def main() -> int:
    started = time.time()

    print("=" * 78)
    print(" GENESIS RECALL R3")
    print(" DETERMINISTIC PRODUCTION RECALL CENSUS")
    print("=" * 78)

    universe, universe_meta = load_eligible_universe()

    print()
    print("=== A. ELIGIBLE UNIVERSE ===")
    print("table              :", universe_meta["table"])
    print("id column          :", universe_meta["id_column"])
    print("title column       :", universe_meta["title_column"])
    print("rows seen          :", universe_meta["rows_seen"])
    print("eligible documents :", universe_meta["eligible_documents"])

    sample = deterministic_quantile_sample(
        universe,
        SAMPLE_SIZE,
    )

    print()
    print("=== B. DETERMINISTIC SAMPLE ===")
    print("required :", SAMPLE_SIZE)
    print("selected :", len(sample))
    print(
        "first ID :",
        sample[0]["document_id"],
    )
    print(
        "last ID  :",
        sample[-1]["document_id"],
    )

    records: list[dict[str, Any]] = []

    print()
    print("=== C. PRODUCTION RECALL CENSUS ===")

    for index, item in enumerate(sample, start=1):
        document_id = int(item["document_id"])
        title = str(item["title"])
        query = str(item["query"])

        raw_rows = search_catalog(
            query,
            db_path=DB,
            limit=RAW_LIMIT,
        )

        qualified_rows = search_qualified_catalog(
            query,
            db_path=DB,
            limit=QUALIFIED_LIMIT,
        )

        raw_rank = find_rank(
            raw_rows,
            document_id,
        )

        qualified_rank = find_rank(
            qualified_rows,
            document_id,
        )

        status = classify(
            raw_rank,
            qualified_rank,
        )

        record = {
            "sample_index": index,
            "document_id": document_id,
            "title": title,
            "query": query,
            "raw_rank": raw_rank,
            "raw_bucket": rank_bucket(raw_rank),
            "qualified_rank": qualified_rank,
            "qualified_bucket": rank_bucket(
                qualified_rank
            ),
            "status": status,
        }

        records.append(record)

        print(
            f"[{index:03d}/{SAMPLE_SIZE:03d}] "
            f"id={document_id:<7} "
            f"raw={str(raw_rank):<5} "
            f"qualified={str(qualified_rank):<5} "
            f"{status}"
        )

    # ------------------------------------------------------------
    # D. Aggregate metrics
    # ------------------------------------------------------------

    total = len(records)

    raw_at_1 = sum(
        1
        for r in records
        if r["raw_rank"] is not None
        and r["raw_rank"] <= 1
    )

    raw_at_5 = sum(
        1
        for r in records
        if r["raw_rank"] is not None
        and r["raw_rank"] <= 5
    )

    raw_at_20 = sum(
        1
        for r in records
        if r["raw_rank"] is not None
        and r["raw_rank"] <= 20
    )

    raw_at_100 = sum(
        1
        for r in records
        if r["raw_rank"] is not None
        and r["raw_rank"] <= 100
    )

    qualified_at_1 = sum(
        1
        for r in records
        if r["qualified_rank"] is not None
        and r["qualified_rank"] <= 1
    )

    qualified_at_5 = sum(
        1
        for r in records
        if r["qualified_rank"] is not None
        and r["qualified_rank"] <= 5
    )

    qualified_at_20 = sum(
        1
        for r in records
        if r["qualified_rank"] is not None
        and r["qualified_rank"] <= 20
    )

    qualified_at_100 = sum(
        1
        for r in records
        if r["qualified_rank"] is not None
        and r["qualified_rank"] <= 100
    )

    raw_miss = sum(
        1
        for r in records
        if r["status"] == "RAW_MISS"
    )

    qualification_drop = sum(
        1
        for r in records
        if r["status"] == "QUALIFICATION_DROP"
    )

    status_counts = Counter(
        r["status"]
        for r in records
    )

    # ------------------------------------------------------------
    # E. Known regression
    # ------------------------------------------------------------

    print()
    print("=== D. KNOWN PRODUCTION REGRESSION ===")

    known_results = []

    for name, query, target_id in KNOWN:
        raw = search_catalog(
            query,
            db_path=DB,
            limit=100,
        )

        qualified = search_qualified_catalog(
            query,
            db_path=DB,
            limit=100,
        )

        raw_rank = find_rank(raw, target_id)
        qualified_rank = find_rank(
            qualified,
            target_id,
        )

        passed = (
            raw_rank is not None
            and qualified_rank is not None
        )

        known_results.append(
            {
                "name": name,
                "query": query,
                "target_document_id": target_id,
                "raw_rank": raw_rank,
                "qualified_rank": qualified_rank,
                "pass": passed,
            }
        )

        print()
        print(name)
        print("  raw rank       :", raw_rank)
        print("  qualified rank :", qualified_rank)
        print("  PASS           :", passed)

    known_pass = all(
        item["pass"]
        for item in known_results
    )

    # ------------------------------------------------------------
    # F. Adversarial precision
    # ------------------------------------------------------------

    print()
    print("=== E. ADVERSARIAL PRECISION ===")

    adversarial_results = []

    for query in ADVERSARIAL:
        rows = search_qualified_catalog(
            query,
            db_path=DB,
            limit=20,
        )

        passed = len(rows) == 0

        adversarial_results.append(
            {
                "query": query,
                "qualified_results": len(rows),
                "pass": passed,
            }
        )

        print()
        print(query)
        print("  qualified :", len(rows))
        print("  PASS      :", passed)

    adversarial_pass = all(
        item["pass"]
        for item in adversarial_results
    )

    # ------------------------------------------------------------
    # G. Corpus grade
    # ------------------------------------------------------------

    qualified_recall_20_pct = pct(
        qualified_at_20,
        total,
    )

    raw_recall_20_pct = pct(
        raw_at_20,
        total,
    )

    if qualified_recall_20_pct >= 95.0:
        corpus_grade = "EXCELLENT"
    elif qualified_recall_20_pct >= 90.0:
        corpus_grade = "GOOD"
    elif qualified_recall_20_pct >= 80.0:
        corpus_grade = "MARGINAL"
    else:
        corpus_grade = "RECALL_DEFICIENT"

    #
    # IMPORTANT:
    # R3 certification is measurement certification.
    #
    # A low corpus recall rate does NOT invalidate the benchmark.
    # It is precisely what the benchmark exists to measure.
    #
    census_complete = (
        total == SAMPLE_SIZE
        and len(
            {
                r["document_id"]
                for r in records
            }
        ) == SAMPLE_SIZE
    )

    certified = (
        census_complete
        and known_pass
        and adversarial_pass
    )

    # ------------------------------------------------------------
    # H. Reports
    # ------------------------------------------------------------

    summary = {
        "sample_size_required": SAMPLE_SIZE,
        "sample_size_actual": total,
        "eligible_universe": universe_meta,
        "sampling_method": "deterministic_quantile",
        "raw_recall": {
            "@1": {
                "count": raw_at_1,
                "pct": pct(raw_at_1, total),
            },
            "@5": {
                "count": raw_at_5,
                "pct": pct(raw_at_5, total),
            },
            "@20": {
                "count": raw_at_20,
                "pct": raw_recall_20_pct,
            },
            "@100": {
                "count": raw_at_100,
                "pct": pct(raw_at_100, total),
            },
        },
        "qualified_recall": {
            "@1": {
                "count": qualified_at_1,
                "pct": pct(
                    qualified_at_1,
                    total,
                ),
            },
            "@5": {
                "count": qualified_at_5,
                "pct": pct(
                    qualified_at_5,
                    total,
                ),
            },
            "@20": {
                "count": qualified_at_20,
                "pct": qualified_recall_20_pct,
            },
            "@100": {
                "count": qualified_at_100,
                "pct": pct(
                    qualified_at_100,
                    total,
                ),
            },
        },
        "failure_anatomy": {
            "raw_miss": raw_miss,
            "qualification_drop": qualification_drop,
            "status_counts": dict(status_counts),
        },
        "corpus_grade": corpus_grade,
        "known_regression_pass": known_pass,
        "adversarial_precision_pass": adversarial_pass,
        "census_complete": census_complete,
        "certified": certified,
        "elapsed_seconds": round(
            time.time() - started,
            2,
        ),
    }

    report = {
        "summary": summary,
        "known_regression": known_results,
        "adversarial_controls": adversarial_results,
        "sample": records,
    }

    REPORT.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    fieldnames = [
        "sample_index",
        "document_id",
        "title",
        "query",
        "raw_rank",
        "raw_bucket",
        "qualified_rank",
        "qualified_bucket",
        "status",
    ]

    with TSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=fieldnames,
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(records)

    failures = [
        r
        for r in records
        if r["status"] in (
            "RAW_MISS",
            "QUALIFICATION_DROP",
        )
    ]

    with FAILURES.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=fieldnames,
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(failures)

    # ------------------------------------------------------------
    # I. Console summary
    # ------------------------------------------------------------

    print()
    print("=" * 78)
    print(" GENESIS RECALL R3 CORPUS-LEVEL RESULT")
    print("=" * 78)

    print()
    print("ELIGIBLE UNIVERSE")
    print(
        "  eligible documents       :",
        universe_meta["eligible_documents"],
    )

    print()
    print("DETERMINISTIC SAMPLE")
    print(
        "  required                 :",
        SAMPLE_SIZE,
    )
    print(
        "  actual                   :",
        total,
    )
    print(
        "  exact sample             :",
        census_complete,
    )

    print()
    print("RAW PRODUCTION RECALL")
    print(
        f"  recall @1                : "
        f"{raw_at_1}/{total} "
        f"({pct(raw_at_1,total):.2f}%)"
    )
    print(
        f"  recall @5                : "
        f"{raw_at_5}/{total} "
        f"({pct(raw_at_5,total):.2f}%)"
    )
    print(
        f"  recall @20               : "
        f"{raw_at_20}/{total} "
        f"({pct(raw_at_20,total):.2f}%)"
    )
    print(
        f"  recall @100              : "
        f"{raw_at_100}/{total} "
        f"({pct(raw_at_100,total):.2f}%)"
    )

    print()
    print("QUALIFIED PRODUCTION RECALL")
    print(
        f"  recall @1                : "
        f"{qualified_at_1}/{total} "
        f"({pct(qualified_at_1,total):.2f}%)"
    )
    print(
        f"  recall @5                : "
        f"{qualified_at_5}/{total} "
        f"({pct(qualified_at_5,total):.2f}%)"
    )
    print(
        f"  recall @20               : "
        f"{qualified_at_20}/{total} "
        f"({pct(qualified_at_20,total):.2f}%)"
    )
    print(
        f"  recall @100              : "
        f"{qualified_at_100}/{total} "
        f"({pct(qualified_at_100,total):.2f}%)"
    )

    print()
    print("FAILURE ANATOMY")
    print(
        "  raw retrieval misses     :",
        raw_miss,
    )
    print(
        "  qualification drops      :",
        qualification_drop,
    )

    for key in sorted(status_counts):
        print(
            f"  {key:<25}: "
            f"{status_counts[key]}"
        )

    print()
    print("CORPUS ASSESSMENT")
    print(
        "  qualified recall @20     :",
        f"{qualified_recall_20_pct:.2f}%",
    )
    print(
        "  corpus grade             :",
        corpus_grade,
    )

    print()
    print("SAFETY / REGRESSION")
    print(
        "  known production canaries:",
        known_pass,
    )
    print(
        "  adversarial precision    :",
        adversarial_pass,
    )

    print()
    print("CERTIFICATION")
    print(
        "  census complete          :",
        census_complete,
    )
    print(
        "  R3 CERTIFIED             :",
        certified,
    )

    print()
    print(
        "elapsed seconds            :",
        summary["elapsed_seconds"],
    )

    print("=" * 78)

    return 0 if certified else 1


if __name__ == "__main__":
    raise SystemExit(main())
