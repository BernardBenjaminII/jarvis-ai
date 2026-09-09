from __future__ import annotations

import csv
import inspect
import json
import re
import sqlite3
import sys
import time

from dataclasses import asdict, fields, is_dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

REPORT = PROJECT / (
    "artifacts/genesis_recall/"
    "r2_r2a_r1_exact_qualification_trace.json"
)

TSV = PROJECT / (
    "artifacts/genesis_recall/"
    "r2_r2a_r1_exact_qualification_trace.tsv"
)


# ============================================================
# IMPORT PRODUCTION PATHS
# ============================================================

from core.knowledge_catalog.search import (
    search_catalog,
)

from core.knowledge_catalog.qualified_search import (
    qualify_rows,
    search_qualified_catalog,
)

from core.retrieval.qualification.evaluator import (
    QualificationEngine,
)


# ============================================================
# SERIALIZATION
# ============================================================

def jsonable(value: Any) -> Any:
    """
    Conservative serializer.

    Deliberately avoids dataclasses.asdict() because qualification
    objects may contain MappingProxyType members that cannot be
    deepcopy/pickled.
    """

    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, MappingProxyType):
        return {
            str(k): jsonable(v)
            for k, v in dict(value).items()
        }

    if isinstance(value, Mapping):
        return {
            str(k): jsonable(v)
            for k, v in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]

    if is_dataclass(value):
        out = {}

        for f in fields(value):
            try:
                out[f.name] = jsonable(
                    getattr(value, f.name)
                )
            except Exception as exc:
                out[f.name] = (
                    f"<unavailable:{type(exc).__name__}>"
                )

        return out

    if hasattr(value, "__dict__"):
        out = {}

        for k, v in vars(value).items():
            if str(k).startswith("_"):
                continue

            try:
                out[str(k)] = jsonable(v)
            except Exception as exc:
                out[str(k)] = (
                    f"<unavailable:{type(exc).__name__}>"
                )

        return out

    return repr(value)


# ============================================================
# GENERIC FIELD ACCESS
# ============================================================

def getv(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default

    if isinstance(obj, Mapping):
        return obj.get(name, default)

    return getattr(obj, name, default)


def first_value(
    obj: Any,
    names: Iterable[str],
    default: Any = None,
) -> Any:
    for name in names:
        value = getv(obj, name, None)

        if value is not None:
            return value

    return default


def numeric(
    obj: Any,
    names: Iterable[str],
) -> float | None:
    value = first_value(obj, names, None)

    if value is None:
        return None

    try:
        return float(value)
    except Exception:
        return None


# ============================================================
# NORMALIZATION
# ============================================================

TOKEN_RE = re.compile(r"[a-z0-9]+")

STOP = {
    "a",
    "an",
    "and",
    "by",
    "for",
    "from",
    "in",
    "of",
    "on",
    "the",
    "to",
    "with",
    "pdf",
    "txt",
    "htm",
    "html",
    "doc",
    "docx",
    "epub",
}


def normalize(text: Any) -> str:
    text = "" if text is None else str(text)

    text = text.lower()

    # Common filename / punctuation separators.
    text = re.sub(
        r"[\._/\\()\[\]{}:;,+\-–—]+",
        " ",
        text,
    )

    text = re.sub(r"\s+", " ", text).strip()

    return text


def meaningful_tokens(text: Any) -> list[str]:
    tokens = TOKEN_RE.findall(normalize(text))

    return [
        token
        for token in tokens
        if token not in STOP
    ]


def ordered_subsequence(
    needle: list[str],
    haystack: list[str],
) -> bool:
    if not needle:
        return False

    pos = 0

    for token in haystack:
        if token == needle[pos]:
            pos += 1

            if pos == len(needle):
                return True

    return False


def identity_analysis(
    query: str,
    title: str,
    source_path: str,
) -> dict[str, Any]:
    q_tokens = meaningful_tokens(query)

    identity_text = " ".join(
        part
        for part in (
            normalize(title),
            normalize(source_path),
        )
        if part
    )

    identity_tokens = meaningful_tokens(identity_text)

    identity_set = set(identity_tokens)

    missing = [
        token
        for token in q_tokens
        if token not in identity_set
    ]

    if q_tokens:
        coverage = (
            len(q_tokens) - len(missing)
        ) / len(q_tokens)
    else:
        coverage = 0.0

    ordered = ordered_subsequence(
        q_tokens,
        identity_tokens,
    )

    alias = bool(
        len(q_tokens) >= 2
        and coverage == 1.0
        and ordered
    )

    return {
        "query_normalized": normalize(query),
        "title_normalized": normalize(title),
        "query_tokens": q_tokens,
        "identity_tokens": identity_tokens,
        "missing_tokens": missing,
        "coverage": coverage,
        "ordered_subsequence": ordered,
        "identity_alias": alias,
    }


# ============================================================
# DATABASE DISCOVERY
# ============================================================

def connect_ro() -> sqlite3.Connection:
    con = sqlite3.connect(
        f"file:{DB}?mode=ro",
        uri=True,
    )

    con.row_factory = sqlite3.Row

    con.execute("PRAGMA query_only=ON")

    return con


def table_columns(
    con: sqlite3.Connection,
    table: str,
) -> list[str]:
    return [
        str(row["name"])
        for row in con.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    ]


def first_existing(
    columns: list[str],
    candidates: Iterable[str],
) -> str | None:
    lowered = {
        col.lower(): col
        for col in columns
    }

    for candidate in candidates:
        found = lowered.get(candidate.lower())

        if found:
            return found

    return None


def runtime_schema(
    con: sqlite3.Connection,
) -> dict[str, str | None]:
    tables = {
        str(row["name"])
        for row in con.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            """
        ).fetchall()
    }

    if "runtime_documents" not in tables:
        raise RuntimeError(
            "runtime_documents table not found"
        )

    cols = table_columns(
        con,
        "runtime_documents",
    )

    return {
        "id": first_existing(
            cols,
            (
                "runtime_document_id",
                "document_id",
                "id",
            ),
        ),
        "title": first_existing(
            cols,
            (
                "title",
                "document_title",
                "name",
                "filename",
                "file_name",
            ),
        ),
        "path": first_existing(
            cols,
            (
                "source_path",
                "file_path",
                "path",
                "document_path",
                "uri",
            ),
        ),
        "text": first_existing(
            cols,
            (
                "text",
                "content",
                "document_text",
                "body",
                "extracted_text",
            ),
        ),
        "source_type": first_existing(
            cols,
            (
                "source_type",
                "document_type",
                "kind",
                "type",
            ),
        ),
    }


def select_expr(
    column: str | None,
    alias: str,
) -> str:
    if column:
        return f'"{column}" AS "{alias}"'

    return f'NULL AS "{alias}"'


def load_runtime_by_id(
    con: sqlite3.Connection,
    schema: dict[str, str | None],
    runtime_id: int,
) -> dict[str, Any] | None:
    id_col = schema["id"]

    if not id_col:
        raise RuntimeError(
            "runtime_documents ID column not found"
        )

    sql = f"""
        SELECT
            {select_expr(schema["id"], "runtime_id")},
            {select_expr(schema["title"], "title")},
            {select_expr(schema["path"], "source_path")},
            {select_expr(schema["text"], "text")},
            {select_expr(schema["source_type"], "source_type")}
        FROM runtime_documents
        WHERE "{id_col}" = ?
        LIMIT 1
    """

    row = con.execute(
        sql,
        (runtime_id,),
    ).fetchone()

    return dict(row) if row else None


def find_runtime_identity(
    con: sqlite3.Connection,
    schema: dict[str, str | None],
    query: str,
    expected_id: int | None = None,
) -> tuple[dict[str, Any] | None, str]:
    """
    Test acquisition only.

    Prefer a known runtime ID.

    If unknown, scan runtime identity metadata and choose only a
    deterministic complete ordered identity alias.
    """

    if expected_id is not None:
        row = load_runtime_by_id(
            con,
            schema,
            expected_id,
        )

        if row is not None:
            return row, "known_runtime_id"

    id_col = schema["id"]
    title_col = schema["title"]
    path_col = schema["path"]

    if not id_col:
        raise RuntimeError(
            "runtime ID column unavailable"
        )

    sql = f"""
        SELECT
            {select_expr(schema["id"], "runtime_id")},
            {select_expr(schema["title"], "title")},
            {select_expr(schema["path"], "source_path")},
            {select_expr(schema["source_type"], "source_type")}
        FROM runtime_documents
        ORDER BY "{id_col}"
    """

    matches: list[
        tuple[
            float,
            int,
            dict[str, Any],
        ]
    ] = []

    for raw in con.execute(sql):
        row = dict(raw)

        analysis = identity_analysis(
            query,
            str(row.get("title") or ""),
            str(row.get("source_path") or ""),
        )

        if not analysis["identity_alias"]:
            continue

        rid = int(row["runtime_id"])

        matches.append(
            (
                float(analysis["coverage"]),
                rid,
                row,
            )
        )

    if not matches:
        return None, "identity_scan_no_match"

    matches.sort(
        key=lambda item: (
            -item[0],
            item[1],
        )
    )

    chosen = matches[0][2]

    # Reload complete row so text is available if stored directly.
    full = load_runtime_by_id(
        con,
        schema,
        int(chosen["runtime_id"]),
    )

    return full, "deterministic_identity_scan"


# ============================================================
# CANDIDATE CONSTRUCTION
# ============================================================

def candidate_from_runtime(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Build a conservative search-result-like mapping.

    We intentionally preserve catalog identity fields instead of
    replacing them with query text.
    """

    runtime_id = row.get("runtime_id")
    title = row.get("title")
    source_path = row.get("source_path")
    text = row.get("text")
    source_type = row.get("source_type")

    candidate = {
        "runtime_document_id": runtime_id,
        "document_id": runtime_id,
        "id": runtime_id,
        "title": title,
        "subject": title,
        "source_path": source_path,
        "file_path": source_path,
        "source_type": source_type,
        "text": text,
        "content": text,

        # Identity lane candidates have deterministic catalog
        # provenance. Do not manufacture semantic similarity.
        "catalog_identity": True,
        "identity_source": "runtime_documents",
    }

    return candidate


# ============================================================
# QUALIFICATION RESULT EXTRACTION
# ============================================================

def evidence_items(result: Any) -> list[Any]:
    """
    Locate evidence objects without assuming one historical
    QualificationResult layout.
    """

    for name in (
        "evidence",
        "evaluations",
        "results",
        "items",
        "candidates",
    ):
        value = getv(result, name, None)

        if value is None:
            continue

        if isinstance(value, Mapping):
            return list(value.values())

        if isinstance(value, (list, tuple)):
            return list(value)

    # Some implementations may expose a single evidence object.
    if (
        getv(result, "candidate", None) is not None
        or getv(result, "score", None) is not None
        or getv(result, "decision", None) is not None
    ):
        return [result]

    return []


def candidate_runtime_id(candidate: Any) -> int | None:
    if candidate is None:
        return None

    for name in (
        "runtime_document_id",
        "document_id",
        "id",
    ):
        value = getv(candidate, name, None)

        if value is None:
            continue

        try:
            return int(value)
        except Exception:
            pass

    metadata = getv(candidate, "metadata", None)

    if metadata is not None:
        for name in (
            "runtime_document_id",
            "document_id",
            "id",
        ):
            value = getv(metadata, name, None)

            if value is None:
                continue

            try:
                return int(value)
            except Exception:
                pass

    return None


def find_evidence_for_runtime(
    result: Any,
    runtime_id: int,
) -> Any | None:
    items = evidence_items(result)

    for item in items:
        candidate = getv(item, "candidate", None)

        if candidate_runtime_id(candidate) == runtime_id:
            return item

        if candidate_runtime_id(item) == runtime_id:
            return item

    # One-candidate qualification call: if exactly one evidence
    # object exists, it is deterministically the candidate.
    if len(items) == 1:
        return items[0]

    return None


def decision_text(evidence: Any) -> str | None:
    value = first_value(
        evidence,
        (
            "decision",
            "status",
            "outcome",
        ),
        None,
    )

    if value is None:
        return None

    if hasattr(value, "value"):
        value = value.value

    return str(value)


def explanation_text(evidence: Any) -> str | None:
    value = first_value(
        evidence,
        (
            "explanation",
            "reason",
            "message",
        ),
        None,
    )

    return None if value is None else str(value)


def score_object(evidence: Any) -> Any:
    score = getv(evidence, "score", None)

    if score is not None:
        return score

    return evidence


def trace_evidence(
    evidence: Any,
) -> dict[str, Any]:
    score = score_object(evidence)

    return {
        "decision": decision_text(evidence),
        "explanation": explanation_text(evidence),
        "lexical": numeric(
            score,
            ("lexical", "lexical_score"),
        ),
        "phrase": numeric(
            score,
            ("phrase", "phrase_score"),
        ),
        "subject": numeric(
            score,
            ("subject", "subject_score"),
        ),
        "entity": numeric(
            score,
            ("entity", "entity_score"),
        ),
        "provenance": numeric(
            score,
            ("provenance", "provenance_score"),
        ),
        "confidence": numeric(
            score,
            (
                "confidence",
                "retrieval_confidence",
            ),
        ),
        "final": numeric(
            score,
            (
                "final",
                "final_score",
                "score",
            ),
        ),
        "candidate": jsonable(
            getv(evidence, "candidate", None)
        ),
        "raw_evidence": jsonable(evidence),
    }


# ============================================================
# SHADOW REPAIR
# ============================================================

def is_subject_rejection(trace: Mapping[str, Any]) -> bool:
    decision = str(
        trace.get("decision") or ""
    ).lower()

    explanation = str(
        trace.get("explanation") or ""
    ).lower()

    subject_markers = (
        "subject",
        "topic",
    )

    rejection_markers = (
        "reject",
        "mismatch",
        "below",
        "fail",
    )

    if (
        any(marker in decision for marker in subject_markers)
        and any(marker in decision for marker in rejection_markers)
    ):
        return True

    if (
        any(marker in explanation for marker in subject_markers)
        and any(marker in explanation for marker in rejection_markers)
    ):
        return True

    return False


def is_already_accepted(trace: Mapping[str, Any]) -> bool:
    decision = str(
        trace.get("decision") or ""
    ).lower()

    return (
        "accept" in decision
        and "reject" not in decision
    )


def shadow_identity_subject_repair(
    identity: Mapping[str, Any],
    trace: Mapping[str, Any],
) -> tuple[bool, str]:
    """
    Critical safety boundary:

    This shadow repair does NOT lower thresholds and does NOT
    rescue arbitrary low-confidence evidence.

    It only asks whether a deterministic identity alias should
    prevent a subject-semantic veto.
    """

    if not identity.get("identity_alias"):
        return False, "not_deterministic_identity_alias"

    if float(identity.get("coverage") or 0.0) != 1.0:
        return False, "identity_coverage_incomplete"

    if not identity.get("ordered_subsequence"):
        return False, "identity_order_not_preserved"

    if is_already_accepted(trace):
        return True, "already_accepted"

    if is_subject_rejection(trace):
        return True, "deterministic_identity_overrides_subject_veto"

    return False, "not_subject_mismatch"


# ============================================================
# RESULT ID EXTRACTION
# ============================================================

def result_runtime_id(row: Any) -> int | None:
    return candidate_runtime_id(row)


def rank_for_runtime(
    rows: Iterable[Any],
    runtime_id: int,
) -> int | None:
    for rank, row in enumerate(rows, 1):
        if result_runtime_id(row) == runtime_id:
            return rank

    return None


# ============================================================
# CANARIES
# ============================================================

CATALOG_CANARIES = (
    {
        "name": "list_sora",
        "query": "List Sora names",
        "runtime_id": None,
    },
    {
        "name": "riyadh_saliheem",
        "query": "Riyadh us Saliheem",
        "runtime_id": 84923,
    },
    {
        "name": "la_ta7zan",
        "query": "la ta7zan",
        "runtime_id": None,
    },
    {
        "name": "kameez_pattern",
        "query": "kameez pattern",
        "runtime_id": None,
    },
    {
        "name": "guerilla_warfare",
        "query": "Guevara Che Guerilla Warfare",
        "runtime_id": None,
    },
    {
        "name": "lane_lexicon",
        "query": "Edward William Lane Arabic English Lexicon Vol 6",
        "runtime_id": 86876,
    },
)


SEMANTIC_CANARIES = (
    {
        "name": "ai_assisted_python",
        "query": "AI assisted Python programming",
        "runtime_id": 11,
    },
    {
        "name": "cpp",
        "query": "C++ programming",
        "runtime_id": 4,
    },
    {
        "name": "effective_c",
        "query": "effective C programming",
        "runtime_id": 14,
    },
    {
        "name": "civil_defense",
        "query": "civil defense manual",
        "runtime_id": 18,
    },
    {
        "name": "army_survival",
        "query": "US Army survival manual",
        "runtime_id": 32,
    },
    {
        "name": "electronics",
        "query": "practical electronics handbook",
        "runtime_id": 42,
    },
    {
        "name": "marx",
        "query": "Marx mathematical manuscripts",
        "runtime_id": None,
    },
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


# ============================================================
# MAIN
# ============================================================

def main() -> int:
    started = time.monotonic()

    print("=" * 76)
    print(" GENESIS RECALL R2-R2A-R1")
    print(" DETERMINISTIC IDENTITY CANDIDATE")
    print(" + EXACT QUALIFICATION EVIDENCE TRACE")
    print("=" * 76)

    engine = QualificationEngine()

    thresholds = getattr(
        engine,
        "thresholds",
        None,
    )

    print()
    print("=== ACTIVE QUALIFICATION THRESHOLDS ===")

    for name in (
        "accept",
        "minimum_confidence",
        "minimum_lexical",
        "minimum_subject",
        "minimum_phrase",
        "strong_phrase_override",
    ):
        value = getv(
            thresholds,
            name,
            None,
        )

        if value is not None:
            print(f"{name:24}: {value}")

    con = connect_ro()

    query_only = con.execute(
        "PRAGMA query_only"
    ).fetchone()[0]

    integrity = con.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]

    print()
    print("=== READ-ONLY DATABASE CONTRACT ===")
    print("query_only :", query_only)
    print("integrity  :", integrity)

    schema = runtime_schema(con)

    print()
    print("=== runtime_documents SCHEMA MAP ===")

    for key, value in schema.items():
        print(f"{key:12}: {value}")

    if not schema["id"]:
        raise RuntimeError(
            "cannot identify runtime_documents ID column"
        )

    catalog_results: list[dict[str, Any]] = []

    print()
    print("=== A. DETERMINISTIC CATALOG CANARY ACQUISITION ===")

    for canary in CATALOG_CANARIES:
        print()
        print("-" * 76)
        print(canary["name"])
        print("query :", canary["query"])

        row, acquisition = find_runtime_identity(
            con,
            schema,
            canary["query"],
            canary["runtime_id"],
        )

        if row is None:
            print("TARGET: NOT FOUND")

            catalog_results.append(
                {
                    **canary,
                    "found": False,
                    "acquisition": acquisition,
                    "pass": False,
                }
            )

            continue

        runtime_id = int(row["runtime_id"])

        title = str(
            row.get("title") or ""
        )

        source_path = str(
            row.get("source_path") or ""
        )

        identity = identity_analysis(
            canary["query"],
            title,
            source_path,
        )

        print("runtime id        :", runtime_id)
        print("acquisition       :", acquisition)
        print("title             :", title)
        print("token coverage    :", identity["coverage"])
        print("ordered subseq    :", identity["ordered_subsequence"])
        print("identity alias    :", identity["identity_alias"])

        catalog_results.append(
            {
                **canary,
                "runtime_id_actual": runtime_id,
                "found": True,
                "acquisition": acquisition,
                "title": title,
                "source_path": source_path,
                "identity": identity,
            }
        )

    print()
    print("=== B. EXACT QUALIFICATION EVIDENCE TRACE ===")

    for result in catalog_results:
        if not result.get("found"):
            continue

        print()
        print("-" * 76)
        print(result["name"])

        runtime_id = int(
            result["runtime_id_actual"]
        )

        row = load_runtime_by_id(
            con,
            schema,
            runtime_id,
        )

        if row is None:
            result["qualification_trace"] = None
            result["shadow_accepted"] = False
            result["shadow_reason"] = (
                "runtime_row_disappeared"
            )
            result["pass"] = False

            print("FAIL: runtime row unavailable")

            continue

        candidate = candidate_from_runtime(row)

        try:
            accepted_rows, qualification = qualify_rows(
                result["query"],
                [candidate],
                engine=engine,
            )
        except Exception as exc:
            result["qualification_exception"] = (
                f"{type(exc).__name__}: {exc}"
            )
            result["qualification_trace"] = None
            result["shadow_accepted"] = False
            result["shadow_reason"] = (
                "qualification_exception"
            )
            result["pass"] = False

            print(
                "QUALIFICATION EXCEPTION:",
                result["qualification_exception"],
            )

            continue

        evidence = find_evidence_for_runtime(
            qualification,
            runtime_id,
        )

        if evidence is None:
            result["qualification_result_raw"] = (
                jsonable(qualification)
            )
            result["qualification_trace"] = None
            result["shadow_accepted"] = False
            result["shadow_reason"] = (
                "evidence_not_located"
            )
            result["pass"] = False

            print("FAIL: exact evidence object not located")

            continue

        trace = trace_evidence(evidence)

        shadow_accepted, shadow_reason = (
            shadow_identity_subject_repair(
                result["identity"],
                trace,
            )
        )

        result["qualification_trace"] = trace
        result["qualification_result_raw"] = (
            jsonable(qualification)
        )
        result["accepted_rows"] = (
            jsonable(accepted_rows)
        )
        result["shadow_accepted"] = shadow_accepted
        result["shadow_reason"] = shadow_reason

        # This stage is diagnostic. A deterministic identity alias
        # is the prerequisite. If qualification already accepts it,
        # that is also a pass. If qualification subject-vetoes it,
        # the shadow repair must accept it.
        result["pass"] = bool(
            result["identity"]["identity_alias"]
            and shadow_accepted
        )

        print("decision           :", trace["decision"])
        print("explanation        :", trace["explanation"])
        print("lexical            :", trace["lexical"])
        print("phrase             :", trace["phrase"])
        print("subject            :", trace["subject"])
        print("entity             :", trace["entity"])
        print("provenance         :", trace["provenance"])
        print("confidence         :", trace["confidence"])
        print("final              :", trace["final"])
        print("shadow accepted    :", shadow_accepted)
        print("shadow reason      :", shadow_reason)
        print("PASS               :", result["pass"])

    print()
    print("=== C. LANE EXACT EVIDENCE ANATOMY ===")

    lane = next(
        (
            row
            for row in catalog_results
            if row["name"] == "lane_lexicon"
        ),
        None,
    )

    lane_trace_pass = bool(
        lane
        and lane.get("found")
        and lane.get("qualification_trace")
        is not None
    )

    lane_identity_pass = bool(
        lane
        and lane.get("identity", {}).get(
            "identity_alias"
        )
    )

    lane_shadow_pass = bool(
        lane
        and lane.get("shadow_accepted")
    )

    print("evidence located :", lane_trace_pass)
    print("identity alias   :", lane_identity_pass)
    print("shadow accepted  :", lane_shadow_pass)

    if lane and lane.get("identity"):
        print()
        print("Lane query tokens:")

        identity_tokens = set(
            lane["identity"]["identity_tokens"]
        )

        for token in lane["identity"]["query_tokens"]:
            status = (
                "MATCH"
                if token in identity_tokens
                else "MISS"
            )

            print(
                f"{token:24} -> {status}"
            )

    print()
    print("=== D. REAL PRODUCTION SEMANTIC REGRESSION ===")

    semantic_results: list[dict[str, Any]] = []

    for canary in SEMANTIC_CANARIES:
        query = canary["query"]
        expected_id = canary["runtime_id"]

        try:
            raw = search_catalog(
                query,
                db_path=DB,
                limit=20,
            )

            qualified = search_qualified_catalog(
                query,
                db_path=DB,
                limit=20,
            )
        except Exception as exc:
            entry = {
                **canary,
                "exception": (
                    f"{type(exc).__name__}: {exc}"
                ),
                "pass": False,
            }

            semantic_results.append(entry)

            print(
                f"{canary['name']:24} "
                f"EXCEPTION={entry['exception']}"
            )

            continue

        if expected_id is not None:
            raw_rank = rank_for_runtime(
                raw,
                expected_id,
            )

            qualified_rank = rank_for_runtime(
                qualified,
                expected_id,
            )

            passed = qualified_rank is not None

        else:
            # For a canary whose historical runtime ID was not
            # preserved in the test specification, retain the
            # production behavior test: a qualified result must
            # exist and the top result must deterministically
            # identify the query.
            raw_rank = 1 if raw else None
            qualified_rank = (
                1 if qualified else None
            )

            if qualified:
                top = qualified[0]

                top_title = str(
                    first_value(
                        top,
                        (
                            "title",
                            "subject",
                            "name",
                        ),
                        "",
                    )
                )

                top_path = str(
                    first_value(
                        top,
                        (
                            "source_path",
                            "file_path",
                            "path",
                        ),
                        "",
                    )
                )

                top_identity = identity_analysis(
                    query,
                    top_title,
                    top_path,
                )

                passed = bool(
                    top_identity["identity_alias"]
                )
            else:
                top_identity = None
                passed = False

        entry = {
            **canary,
            "raw_rank": raw_rank,
            "qualified_rank": qualified_rank,
            "raw_count": len(raw),
            "qualified_count": len(qualified),
            "pass": passed,
        }

        if expected_id is None:
            entry["top_identity"] = top_identity

        semantic_results.append(entry)

        print(
            f"{canary['name']:24} "
            f"raw={str(raw_rank):4} "
            f"qualified={str(qualified_rank):4} "
            f"PASS={passed}"
        )

    semantic_pass = all(
        row["pass"]
        for row in semantic_results
    )

    print()
    print("=== E. ADVERSARIAL IDENTITY ALIAS CONTROLS ===")

    adversarial_results: list[dict[str, Any]] = []

    for query in ADVERSARIAL:
        alias_matches = 0

        id_col = schema["id"]

        sql = f"""
            SELECT
                {select_expr(schema["id"], "runtime_id")},
                {select_expr(schema["title"], "title")},
                {select_expr(schema["path"], "source_path")}
            FROM runtime_documents
            ORDER BY "{id_col}"
        """

        for raw in con.execute(sql):
            row = dict(raw)

            analysis = identity_analysis(
                query,
                str(row.get("title") or ""),
                str(row.get("source_path") or ""),
            )

            if analysis["identity_alias"]:
                alias_matches += 1

        passed = alias_matches == 0

        adversarial_results.append(
            {
                "query": query,
                "alias_matches": alias_matches,
                "pass": passed,
            }
        )

        print()
        print("query         :", query)
        print("alias matches :", alias_matches)
        print("PASS          :", passed)

    adversarial_pass = all(
        row["pass"]
        for row in adversarial_results
    )

    catalog_acquisition_pass = all(
        row.get("found", False)
        for row in catalog_results
    )

    catalog_identity_pass = all(
        row.get(
            "identity",
            {},
        ).get(
            "identity_alias",
            False,
        )
        for row in catalog_results
        if row.get("found")
    ) and catalog_acquisition_pass

    evidence_trace_pass = all(
        row.get("qualification_trace")
        is not None
        for row in catalog_results
        if row.get("found")
    ) and catalog_acquisition_pass

    shadow_pass = all(
        row.get("shadow_accepted", False)
        for row in catalog_results
        if row.get("found")
    ) and catalog_acquisition_pass

    certified = bool(
        catalog_acquisition_pass
        and catalog_identity_pass
        and evidence_trace_pass
        and shadow_pass
        and lane_trace_pass
        and lane_identity_pass
        and lane_shadow_pass
        and semantic_pass
        and adversarial_pass
    )

    elapsed = time.monotonic() - started

    payload = {
        "stage": "Genesis Recall R2-R2A-R1",
        "mode": "shadow_only",
        "production_source_changes": 0,
        "production_db_writes": 0,
        "llm_calls": 0,
        "database": str(DB),
        "query_only": query_only,
        "integrity": integrity,
        "runtime_schema": schema,
        "thresholds": jsonable(thresholds),
        "catalog_canaries": catalog_results,
        "semantic_regression": semantic_results,
        "adversarial": adversarial_results,
        "summary": {
            "catalog_acquisition_pass": (
                catalog_acquisition_pass
            ),
            "catalog_identity_pass": (
                catalog_identity_pass
            ),
            "evidence_trace_pass": (
                evidence_trace_pass
            ),
            "lane_trace_pass": lane_trace_pass,
            "lane_identity_pass": lane_identity_pass,
            "lane_shadow_pass": lane_shadow_pass,
            "shadow_pass": shadow_pass,
            "semantic_regression_pass": semantic_pass,
            "adversarial_alias_pass": adversarial_pass,
            "certified": certified,
            "elapsed_seconds": elapsed,
        },
    }

    REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    with TSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as fh:
        writer = csv.writer(
            fh,
            delimiter="\t",
        )

        writer.writerow(
            (
                "name",
                "runtime_id",
                "acquisition",
                "identity_alias",
                "coverage",
                "ordered_subsequence",
                "decision",
                "explanation",
                "lexical",
                "subject",
                "provenance",
                "confidence",
                "final",
                "shadow_accepted",
                "shadow_reason",
                "pass",
            )
        )

        for row in catalog_results:
            trace = (
                row.get("qualification_trace")
                or {}
            )

            identity = (
                row.get("identity")
                or {}
            )

            writer.writerow(
                (
                    row["name"],
                    row.get("runtime_id_actual"),
                    row.get("acquisition"),
                    identity.get("identity_alias"),
                    identity.get("coverage"),
                    identity.get(
                        "ordered_subsequence"
                    ),
                    trace.get("decision"),
                    trace.get("explanation"),
                    trace.get("lexical"),
                    trace.get("subject"),
                    trace.get("provenance"),
                    trace.get("confidence"),
                    trace.get("final"),
                    row.get("shadow_accepted"),
                    row.get("shadow_reason"),
                    row.get("pass"),
                )
            )

    print()
    print("=" * 76)
    print(" R2-R2A-R1 RESULT")
    print("=" * 76)
    print(
        "catalog acquisition    :",
        "PASS" if catalog_acquisition_pass else "FAIL",
    )
    print(
        "deterministic identity :",
        "PASS" if catalog_identity_pass else "FAIL",
    )
    print(
        "exact evidence trace   :",
        "PASS" if evidence_trace_pass else "FAIL",
    )
    print(
        "Lane evidence trace    :",
        "PASS" if lane_trace_pass else "FAIL",
    )
    print(
        "Lane identity alias    :",
        "PASS" if lane_identity_pass else "FAIL",
    )
    print(
        "Lane shadow repair     :",
        "PASS" if lane_shadow_pass else "FAIL",
    )
    print(
        "all catalog shadows    :",
        "PASS" if shadow_pass else "FAIL",
    )
    print(
        "semantic regression    :",
        "PASS" if semantic_pass else "FAIL",
    )
    print(
        "adversarial aliases    :",
        "PASS" if adversarial_pass else "FAIL",
    )
    print()
    print("R2-R2A-R1 CERTIFIED    :", certified)
    print(
        "elapsed seconds        :",
        round(elapsed, 3),
    )
    print("production source edits: 0")
    print("production DB writes   : 0")
    print("=" * 76)

    print()
    print("JSON:", REPORT)
    print("TSV :", TSV)

    con.close()

    return 0 if certified else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            f"R2-R2A-R1 FATAL: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )

        raise
