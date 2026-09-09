from __future__ import annotations

import csv
import inspect
import json
import math
import re
import sqlite3
import sys
import time

from collections import Counter, defaultdict
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

OUTDIR = PROJECT / "artifacts" / "genesis_recall"

R3_REPORT = OUTDIR / "r3_production_recall_census.json"
R3_TSV = OUTDIR / "r3_production_recall_census.tsv"
R3_FAILURES = OUTDIR / "r3_recall_failures.tsv"

REPORT = OUTDIR / "r4_qualification_drop_anatomy.json"
TSV = OUTDIR / "r4_qualification_drop_anatomy.tsv"
RESCUE_TSV = OUTDIR / "r4_rescue_class_census.tsv"

QUALIFIED_SOURCE = (
    PROJECT / "core" / "knowledge_catalog" / "qualified_search.py"
)


# ============================================================
# IMPORT PRODUCTION COMPONENTS
# ============================================================

from core.knowledge_catalog.search import search_catalog

import core.knowledge_catalog.qualified_search as qualified_mod

from core.knowledge_catalog.qualified_search import (
    search_qualified_catalog,
    _gate_repair_should_rescue,
)

try:
    from core.knowledge_catalog.qualified_search import (
        _r2_identity_should_rescue,
    )
except ImportError:
    _r2_identity_should_rescue = None

from core.retrieval.qualification.evaluator import (
    QualificationEngine,
)


# ============================================================
# CONSTANTS
# ============================================================

RAW_LIMIT = 100
QUALIFIED_LIMIT = 100

EXPECTED_R3_SAMPLE = 250
EXPECTED_R3_DROPS = 228

TARGET_STATUS = "QUALIFICATION_DROP"


# ============================================================
# HELPERS
# ============================================================

def scalar(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, dict):
        return {
            str(k): scalar(v)
            for k, v in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [scalar(v) for v in value]

    if is_dataclass(value):
        try:
            return scalar(asdict(value))
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        try:
            return {
                str(k): scalar(v)
                for k, v in vars(value).items()
                if not str(k).startswith("_")
            }
        except Exception:
            pass

    return repr(value)


def first_present(obj: Any, names: Iterable[str]) -> Any:
    if obj is None:
        return None

    for name in names:
        if isinstance(obj, dict):
            if name in obj:
                return obj[name]
        else:
            if hasattr(obj, name):
                try:
                    return getattr(obj, name)
                except Exception:
                    pass

    return None


def to_float(value: Any) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except Exception:
        return None


def normalize_id(value: Any) -> int | str | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return int(value)

    try:
        return int(value)
    except Exception:
        return str(value)


def row_id(row: Any) -> int | str | None:
    value = first_present(
        row,
        (
            "id",
            "document_id",
            "runtime_document_id",
            "source_id",
            "catalog_id",
            "doc_id",
        ),
    )

    if value is not None:
        return normalize_id(value)

    metadata = first_present(
        row,
        ("metadata", "meta", "source_metadata"),
    )

    value = first_present(
        metadata,
        (
            "id",
            "document_id",
            "runtime_document_id",
            "source_id",
            "catalog_id",
            "doc_id",
        ),
    )

    return normalize_id(value)


def row_title(row: Any) -> str:
    value = first_present(
        row,
        (
            "title",
            "name",
            "document_title",
            "source_title",
        ),
    )

    if value is None:
        metadata = first_present(
            row,
            ("metadata", "meta", "source_metadata"),
        )

        value = first_present(
            metadata,
            (
                "title",
                "name",
                "document_title",
                "source_title",
            ),
        )

    return str(value or "")


def find_rank(rows: list[Any], target_id: Any) -> int | None:
    wanted = normalize_id(target_id)

    for index, row in enumerate(rows, 1):
        if row_id(row) == wanted:
            return index

    return None


def call_search(func, query: str, limit: int) -> list[Any]:
    attempts = (
        lambda: func(query, limit=limit),
        lambda: func(query=query, limit=limit),
        lambda: func(query, top_k=limit),
        lambda: func(query=query, top_k=limit),
        lambda: func(query, max_results=limit),
        lambda: func(query=query, max_results=limit),
        lambda: func(query),
        lambda: func(query=query),
    )

    last_error = None

    for attempt in attempts:
        try:
            value = attempt()

            if value is None:
                return []

            if isinstance(value, list):
                return value[:limit]

            if isinstance(value, tuple):
                return list(value)[:limit]

            for attr in (
                "rows",
                "results",
                "candidates",
                "items",
            ):
                if hasattr(value, attr):
                    inner = getattr(value, attr)
                    if inner is not None:
                        return list(inner)[:limit]

            try:
                return list(value)[:limit]
            except Exception:
                return [value]

        except TypeError as exc:
            last_error = exc
            continue

    if last_error:
        raise last_error

    return []


def load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def discover_field(row: dict[str, str], names: Iterable[str]) -> str | None:
    lowered = {
        key.lower().strip(): key
        for key in row.keys()
    }

    for name in names:
        key = lowered.get(name.lower())
        if key:
            return key

    return None


def choose_r3_source() -> tuple[Path, list[dict[str, str]]]:
    candidates = (
        R3_FAILURES,
        R3_TSV,
    )

    for path in candidates:
        if not path.exists():
            continue

        rows = load_tsv(path)

        if not rows:
            continue

        status_key = discover_field(
            rows[0],
            (
                "status",
                "outcome",
                "classification",
                "result",
            ),
        )

        if status_key is None:
            continue

        drops = [
            row
            for row in rows
            if row.get(status_key) == TARGET_STATUS
        ]

        if drops:
            return path, drops

    raise RuntimeError(
        "Could not locate QUALIFICATION_DROP rows "
        "in R3 TSV artifacts"
    )


def read_document_identity(
    conn: sqlite3.Connection,
    target_id: int,
) -> dict[str, Any]:
    columns = {
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(runtime_documents)"
        ).fetchall()
    }

    selected = ["id"]

    for candidate in (
        "title",
        "path",
        "source_path",
        "filename",
        "name",
        "document_type",
        "domain",
    ):
        if candidate in columns:
            selected.append(candidate)

    sql = (
        "SELECT "
        + ", ".join('"' + col + '"' for col in selected)
        + " FROM runtime_documents WHERE id = ?"
    )

    row = conn.execute(sql, (target_id,)).fetchone()

    if row is None:
        return {
            "id": target_id,
            "missing": True,
        }

    return {
        selected[i]: row[i]
        for i in range(len(selected))
    }


def make_query(
    r3_row: dict[str, str],
    identity: dict[str, Any],
) -> str:
    query_key = discover_field(
        r3_row,
        (
            "query",
            "search_query",
            "generated_query",
            "normalized_query",
        ),
    )

    if query_key:
        value = (r3_row.get(query_key) or "").strip()
        if value:
            return value

    for field in (
        "title",
        "name",
        "filename",
    ):
        value = identity.get(field)
        if value:
            return str(value).strip()

    raise RuntimeError(
        f"No query/title available for ID {identity.get('id')}"
    )


# ============================================================
# QUALIFICATION INTROSPECTION
# ============================================================

ENGINE = QualificationEngine()


def find_engine_method():
    preferred = (
        "evaluate",
        "qualify",
        "evaluate_candidate",
        "qualify_candidate",
        "score",
    )

    for name in preferred:
        method = getattr(ENGINE, name, None)
        if callable(method):
            return name, method

    methods = []

    for name in dir(ENGINE):
        if name.startswith("_"):
            continue

        value = getattr(ENGINE, name)

        if callable(value):
            methods.append(name)

    raise RuntimeError(
        "Unable to identify QualificationEngine evaluation method. "
        f"Public methods={methods}"
    )


ENGINE_METHOD_NAME, ENGINE_METHOD = find_engine_method()


def extract_score(obj: Any, names: Iterable[str]) -> float | None:
    value = first_present(obj, names)

    if value is None:
        scores = first_present(
            obj,
            (
                "scores",
                "score",
                "metrics",
                "components",
            ),
        )

        value = first_present(scores, names)

    return to_float(value)


def extract_reason(obj: Any) -> str | None:
    value = first_present(
        obj,
        (
            "reason",
            "rejection_reason",
            "decision_reason",
            "failure_reason",
            "gate_reason",
            "status_reason",
        ),
    )

    if value is None:
        return None

    return str(value)


def extract_decision(obj: Any) -> str | None:
    value = first_present(
        obj,
        (
            "decision",
            "status",
            "outcome",
            "qualification",
        ),
    )

    if value is None:
        return None

    return str(value)


def invoke_engine(
    query: str,
    candidate: Any,
) -> Any:
    attempts = (
        lambda: ENGINE_METHOD(query, candidate),
        lambda: ENGINE_METHOD(candidate, query),
        lambda: ENGINE_METHOD(
            query=query,
            candidate=candidate,
        ),
        lambda: ENGINE_METHOD(
            candidate=candidate,
            query=query,
        ),
    )

    last_type_error = None

    for attempt in attempts:
        try:
            return attempt()
        except TypeError as exc:
            last_type_error = exc
            continue

    if last_type_error:
        raise last_type_error

    raise RuntimeError("Qualification invocation failed")


def classify_primary(
    decision: str | None,
    reason: str | None,
    lexical: float | None,
    entity: float | None,
    subject: float | None,
    final: float | None,
    provenance: float | None,
    phrase: float | None,
) -> str:
    text = " ".join(
        part
        for part in (
            decision,
            reason,
        )
        if part
    ).lower()

    if "provenance" in text:
        return "PROVENANCE"

    if "phrase" in text:
        return "PHRASE"

    if "subject" in text:
        return "SUBJECT"

    if "lexical" in text:
        return "LEXICAL"

    if "confidence" in text:
        return "LOW_CONFIDENCE"

    if lexical is not None and lexical < float(
        ENGINE.thresholds.minimum_lexical
    ):
        return "LEXICAL"

    if subject is not None and subject < float(
        ENGINE.thresholds.minimum_subject
    ):
        return "SUBJECT"

    minimum_phrase = getattr(
        ENGINE.thresholds,
        "minimum_phrase",
        None,
    )

    if (
        minimum_phrase is not None
        and phrase is not None
        and phrase < float(minimum_phrase)
    ):
        return "PHRASE"

    if (
        final is not None
        and final < float(ENGINE.thresholds.accept)
    ):
        return "LOW_CONFIDENCE"

    if provenance is not None and provenance <= 0:
        return "PROVENANCE"

    return "OTHER"


def call_r1f(
    query: str,
    evidence: Any,
    threshold: float,
) -> tuple[bool, str | None]:
    try:
        result = _gate_repair_should_rescue(
            query,
            evidence,
            threshold=threshold,
        )
    except Exception as exc:
        return False, f"ERROR:{type(exc).__name__}"

    if isinstance(result, tuple):
        if len(result) >= 2:
            return bool(result[0]), str(result[1])
        if len(result) == 1:
            return bool(result[0]), None

    return bool(result), None


def call_r2(
    query: str,
    candidate: Any,
    evidence: Any,
) -> tuple[bool, str | None]:
    if _r2_identity_should_rescue is None:
        return False, "UNAVAILABLE"

    attempts = (
        lambda: _r2_identity_should_rescue(
            query,
            candidate,
            evidence,
        ),
        lambda: _r2_identity_should_rescue(
            query=query,
            candidate=candidate,
            evidence=evidence,
        ),
        lambda: _r2_identity_should_rescue(
            query,
            evidence,
        ),
        lambda: _r2_identity_should_rescue(
            query=query,
            evidence=evidence,
        ),
    )

    last_type_error = None

    for attempt in attempts:
        try:
            result = attempt()

            if isinstance(result, tuple):
                if len(result) >= 2:
                    return bool(result[0]), str(result[1])
                if len(result) == 1:
                    return bool(result[0]), None

            return bool(result), None

        except TypeError as exc:
            last_type_error = exc
            continue

        except Exception as exc:
            return False, f"ERROR:{type(exc).__name__}"

    return False, (
        "SIGNATURE_MISMATCH:"
        + type(last_type_error).__name__
        if last_type_error
        else "SIGNATURE_MISMATCH"
    )


# ============================================================
# START
# ============================================================

started = time.time()

print("=" * 78)
print(" GENESIS RECALL R4")
print(" QUALIFICATION DROP ANATOMY + RESCUE-CLASS CENSUS")
print("=" * 78)

print()
print("=== A. R3 INPUT CONTRACT ===")

with R3_REPORT.open(
    "r",
    encoding="utf-8",
) as handle:
    r3_report = json.load(handle)

source_tsv, drops = choose_r3_source()

print("R3 source TSV       :", source_tsv)
print("qualification drops :", len(drops))
print("expected             :", EXPECTED_R3_DROPS)

if len(drops) != EXPECTED_R3_DROPS:
    raise RuntimeError(
        "R3 qualification-drop count changed: "
        f"expected {EXPECTED_R3_DROPS}, got {len(drops)}"
    )

print("PASS: exact R3 drop population loaded")


print()
print("=== B. QUALIFICATION ENGINE CONTRACT ===")

print("engine method       :", ENGINE_METHOD_NAME)
print("accept              :", ENGINE.thresholds.accept)
print("minimum confidence  :", ENGINE.thresholds.minimum_confidence)
print("minimum lexical     :", ENGINE.thresholds.minimum_lexical)
print("minimum subject     :", ENGINE.thresholds.minimum_subject)
print(
    "minimum phrase      :",
    getattr(ENGINE.thresholds, "minimum_phrase", None),
)

print("PASS: qualification engine available")


# ============================================================
# DATABASE READ-ONLY
# ============================================================

uri = "file:" + str(DB) + "?mode=ro"
conn = sqlite3.connect(uri, uri=True)
conn.execute("PRAGMA query_only = ON")


# ============================================================
# CENSUS
# ============================================================

print()
print("=== C. 228-DOCUMENT QUALIFICATION DROP CENSUS ===")

records: list[dict[str, Any]] = []

primary_counter = Counter()
decision_counter = Counter()
reason_counter = Counter()
rescue_counter = Counter()

r1f_count = 0
r2_count = 0
both_count = 0
neither_count = 0

target_id_key = discover_field(
    drops[0],
    (
        "id",
        "document_id",
        "target_id",
        "runtime_document_id",
    ),
)

if target_id_key is None:
    raise RuntimeError(
        "Unable to locate target document ID column in R3 TSV"
    )

for index, r3_row in enumerate(drops, 1):
    target_id = int(r3_row[target_id_key])

    identity = read_document_identity(
        conn,
        target_id,
    )

    query = make_query(
        r3_row,
        identity,
    )

    raw_rows = call_search(
        search_catalog,
        query,
        RAW_LIMIT,
    )

    raw_rank = find_rank(
        raw_rows,
        target_id,
    )

    candidate = None

    if raw_rank is not None:
        candidate = raw_rows[raw_rank - 1]

    qualified_rows = call_search(
        search_qualified_catalog,
        query,
        QUALIFIED_LIMIT,
    )

    qualified_rank = find_rank(
        qualified_rows,
        target_id,
    )

    if candidate is None:
        evidence = None
        decision = None
        reason = "TARGET_NOT_IN_CURRENT_RAW_HORIZON"

        lexical = None
        entity = None
        subject = None
        final = None
        provenance = None
        phrase = None

        primary = "RAW_REPRODUCTION_MISS"

        r1f_rescue = False
        r1f_reason = None

        r2_rescue = False
        r2_reason = None

    else:
        try:
            evidence = invoke_engine(
                query,
                candidate,
            )
        except Exception as exc:
            evidence = None
            decision = "ENGINE_TRACE_ERROR"
            reason = (
                f"{type(exc).__name__}: {exc}"
            )

            lexical = None
            entity = None
            subject = None
            final = None
            provenance = None
            phrase = None

            primary = "TRACE_ERROR"

            r1f_rescue = False
            r1f_reason = None

            r2_rescue = False
            r2_reason = None

        else:
            decision = extract_decision(evidence)
            reason = extract_reason(evidence)

            lexical = extract_score(
                evidence,
                (
                    "lexical",
                    "lexical_score",
                    "lexical_similarity",
                ),
            )

            entity = extract_score(
                evidence,
                (
                    "entity",
                    "entity_score",
                    "entity_similarity",
                ),
            )

            subject = extract_score(
                evidence,
                (
                    "subject",
                    "subject_score",
                    "subject_similarity",
                ),
            )

            final = extract_score(
                evidence,
                (
                    "final",
                    "final_score",
                    "confidence",
                    "score",
                ),
            )

            provenance = extract_score(
                evidence,
                (
                    "provenance",
                    "provenance_score",
                ),
            )

            phrase = extract_score(
                evidence,
                (
                    "phrase",
                    "phrase_score",
                    "phrase_similarity",
                ),
            )

            primary = classify_primary(
                decision,
                reason,
                lexical,
                entity,
                subject,
                final,
                provenance,
                phrase,
            )

            threshold = first_present(
                evidence,
                ("threshold",),
            )

            threshold = to_float(threshold)

            if threshold is None:
                threshold = float(
                    ENGINE.thresholds.accept
                )

            r1f_rescue, r1f_reason = call_r1f(
                query,
                evidence,
                threshold,
            )

            r2_rescue, r2_reason = call_r2(
                query,
                candidate,
                evidence,
            )

    if r1f_rescue and r2_rescue:
        rescue_class = "R1F_AND_R2"
        both_count += 1

    elif r1f_rescue:
        rescue_class = "R1F_CONTENT_RESCUE"
        r1f_count += 1

    elif r2_rescue:
        rescue_class = "R2_IDENTITY_RESCUE"
        r2_count += 1

    else:
        rescue_class = "NO_EXISTING_RESCUE"
        neither_count += 1

    primary_counter[primary] += 1
    decision_counter[str(decision)] += 1
    reason_counter[str(reason)] += 1
    rescue_counter[rescue_class] += 1

    record = {
        "sample_index": index,
        "document_id": target_id,
        "query": query,
        "title": identity.get("title"),
        "raw_rank": raw_rank,
        "qualified_rank": qualified_rank,
        "decision": decision,
        "reason": reason,
        "lexical": lexical,
        "entity": entity,
        "subject": subject,
        "final": final,
        "provenance": provenance,
        "phrase": phrase,
        "primary_failure_class": primary,
        "r1f_rescue": r1f_rescue,
        "r1f_reason": r1f_reason,
        "r2_rescue": r2_rescue,
        "r2_reason": r2_reason,
        "rescue_class": rescue_class,
    }

    records.append(record)

    print(
        f"[{index:03d}/{len(drops):03d}] "
        f"id={target_id:<7} "
        f"raw={str(raw_rank):<5} "
        f"qualified={str(qualified_rank):<5} "
        f"{primary:<24} "
        f"{rescue_class}"
    )


conn.close()


# ============================================================
# WRITE DETAIL TSV
# ============================================================

print()
print("=== D. FAILURE-CLASS ANATOMY ===")

for key, count in primary_counter.most_common():
    pct = 100.0 * count / len(records)

    print(
        f"{key:<28} "
        f"{count:>4} "
        f"({pct:6.2f}%)"
    )


print()
print("=== E. DECISION CENSUS ===")

for key, count in decision_counter.most_common():
    pct = 100.0 * count / len(records)

    print(
        f"{key:<40} "
        f"{count:>4} "
        f"({pct:6.2f}%)"
    )


print()
print("=== F. REJECTION-REASON CENSUS ===")

for key, count in reason_counter.most_common():
    pct = 100.0 * count / len(records)

    print(
        f"{key:<48} "
        f"{count:>4} "
        f"({pct:6.2f}%)"
    )


print()
print("=== G. EXISTING RESCUE-CLASS CENSUS ===")

for key, count in rescue_counter.most_common():
    pct = 100.0 * count / len(records)

    print(
        f"{key:<28} "
        f"{count:>4} "
        f"({pct:6.2f}%)"
    )


# ============================================================
# SCORE DISTRIBUTIONS
# ============================================================

def distribution(field: str) -> dict[str, Any]:
    values = sorted(
        float(record[field])
        for record in records
        if record.get(field) is not None
        and math.isfinite(float(record[field]))
    )

    if not values:
        return {
            "count": 0,
            "min": None,
            "p25": None,
            "median": None,
            "p75": None,
            "max": None,
        }

    def quantile(q: float) -> float:
        if len(values) == 1:
            return values[0]

        pos = q * (len(values) - 1)
        lo = int(math.floor(pos))
        hi = int(math.ceil(pos))

        if lo == hi:
            return values[lo]

        fraction = pos - lo

        return (
            values[lo] * (1.0 - fraction)
            + values[hi] * fraction
        )

    return {
        "count": len(values),
        "min": values[0],
        "p25": quantile(0.25),
        "median": quantile(0.50),
        "p75": quantile(0.75),
        "max": values[-1],
    }


score_distributions = {
    field: distribution(field)
    for field in (
        "lexical",
        "entity",
        "subject",
        "final",
        "provenance",
        "phrase",
    )
}

print()
print("=== H. SCORE DISTRIBUTIONS ===")

for field, stats in score_distributions.items():
    print()
    print(field)
    for key, value in stats.items():
        print(f"  {key:<8}: {value}")


# ============================================================
# WRITE ARTIFACTS
# ============================================================

fieldnames = [
    "sample_index",
    "document_id",
    "query",
    "title",
    "raw_rank",
    "qualified_rank",
    "decision",
    "reason",
    "lexical",
    "entity",
    "subject",
    "final",
    "provenance",
    "phrase",
    "primary_failure_class",
    "r1f_rescue",
    "r1f_reason",
    "r2_rescue",
    "r2_reason",
    "rescue_class",
]

with TSV.open(
    "w",
    encoding="utf-8",
    newline="",
) as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=fieldnames,
        delimiter="\t",
    )

    writer.writeheader()

    for record in records:
        writer.writerow(record)


rescue_rows = []

for rescue_class, count in rescue_counter.most_common():
    rescue_rows.append(
        {
            "rescue_class": rescue_class,
            "count": count,
            "pct": round(
                100.0 * count / len(records),
                4,
            ),
        }
    )

with RESCUE_TSV.open(
    "w",
    encoding="utf-8",
    newline="",
) as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=(
            "rescue_class",
            "count",
            "pct",
        ),
        delimiter="\t",
    )

    writer.writeheader()
    writer.writerows(rescue_rows)


# ============================================================
# INTERPRETATION
# ============================================================

trace_errors = primary_counter.get(
    "TRACE_ERROR",
    0,
)

raw_reproduction_misses = primary_counter.get(
    "RAW_REPRODUCTION_MISS",
    0,
)

anatomized = (
    len(records)
    - trace_errors
    - raw_reproduction_misses
)

anatomy_complete = (
    len(records) == EXPECTED_R3_DROPS
    and trace_errors == 0
)

rescue_measured = (
    len(records) == EXPECTED_R3_DROPS
)

elapsed = time.time() - started

payload = {
    "genesis_recall": "R4",
    "purpose": (
        "Qualification Drop Anatomy "
        "+ Rescue-Class Census"
    ),
    "input": {
        "r3_source_tsv": str(source_tsv),
        "r3_expected_sample": EXPECTED_R3_SAMPLE,
        "r3_expected_qualification_drops": EXPECTED_R3_DROPS,
        "actual_qualification_drops": len(records),
    },
    "thresholds": {
        "accept": float(
            ENGINE.thresholds.accept
        ),
        "minimum_confidence": float(
            ENGINE.thresholds.minimum_confidence
        ),
        "minimum_lexical": float(
            ENGINE.thresholds.minimum_lexical
        ),
        "minimum_subject": float(
            ENGINE.thresholds.minimum_subject
        ),
        "minimum_phrase": (
            float(
                getattr(
                    ENGINE.thresholds,
                    "minimum_phrase",
                )
            )
            if getattr(
                ENGINE.thresholds,
                "minimum_phrase",
                None,
            ) is not None
            else None
        ),
    },
    "qualification_engine_method": ENGINE_METHOD_NAME,
    "primary_failure_classes": dict(
        primary_counter
    ),
    "decisions": dict(
        decision_counter
    ),
    "reasons": dict(
        reason_counter
    ),
    "rescue_classes": dict(
        rescue_counter
    ),
    "score_distributions": score_distributions,
    "trace_errors": trace_errors,
    "raw_reproduction_misses": raw_reproduction_misses,
    "anatomized": anatomized,
    "anatomy_complete": anatomy_complete,
    "rescue_measured": rescue_measured,
    "elapsed_seconds": round(elapsed, 3),
    "records": records,
}

with REPORT.open(
    "w",
    encoding="utf-8",
) as handle:
    json.dump(
        payload,
        handle,
        indent=2,
        ensure_ascii=False,
    )


# ============================================================
# RESULT
# ============================================================

print()
print("=" * 78)
print(" GENESIS RECALL R4 RESULT")
print("=" * 78)

print()
print("INPUT POPULATION")
print(
    "  R3 qualification drops : "
    f"{len(records)}"
)

print()
print("ANATOMY")
print(
    "  successfully anatomized : "
    f"{anatomized}/{len(records)}"
)
print(
    "  trace errors            : "
    f"{trace_errors}"
)
print(
    "  raw reproduction misses : "
    f"{raw_reproduction_misses}"
)

print()
print("EXISTING RESCUE COVERAGE")
print(
    "  R1F only                : "
    f"{rescue_counter.get('R1F_CONTENT_RESCUE', 0)}"
)
print(
    "  R2 only                 : "
    f"{rescue_counter.get('R2_IDENTITY_RESCUE', 0)}"
)
print(
    "  R1F + R2                : "
    f"{rescue_counter.get('R1F_AND_R2', 0)}"
)
print(
    "  no existing rescue      : "
    f"{rescue_counter.get('NO_EXISTING_RESCUE', 0)}"
)

print()
print("CERTIFICATION")
print(
    "  exact drop population   :",
    len(records) == EXPECTED_R3_DROPS,
)
print(
    "  anatomy complete        :",
    anatomy_complete,
)
print(
    "  rescue census complete  :",
    rescue_measured,
)

print()
print("IMPORTANT:")
print(
    "  R4 certifies the DIAGNOSTIC CENSUS only."
)
print(
    "  R4 does NOT certify any new production rescue."
)
print(
    "  No qualification thresholds were changed."
)

print()
print("Report     :", REPORT)
print("Detail TSV :", TSV)
print("Rescue TSV :", RESCUE_TSV)

print()
print("elapsed seconds :", round(elapsed, 2))
print("=" * 78)

if anatomy_complete and rescue_measured:
    raise SystemExit(0)

raise SystemExit(1)
