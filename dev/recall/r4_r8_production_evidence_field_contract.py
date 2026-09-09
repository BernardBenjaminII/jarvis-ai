from __future__ import annotations

import ast
import csv
import inspect
import json
import math
import sys
import time
from collections import Counter
from dataclasses import asdict, fields, is_dataclass
from pathlib import Path
from typing import Any


PROJECT = Path("/media/abdullah/JARVISDATA/Projects/jarvis-ai")
OUTDIR = PROJECT / "artifacts/genesis_recall"

R4R2 = OUTDIR / "r4_r2_qualification_drop_detail.tsv"

REPORT = OUTDIR / "r4_r8_production_evidence_field_contract.json"
DETAIL = OUTDIR / "r4_r8_production_evidence_field_contract.tsv"
SCHEMA = OUTDIR / "r4_r8_r4r2_column_semantics.tsv"
TRACE = OUTDIR / "r4_r8_evidence_field_trace.txt"
SOURCE_MAP = OUTDIR / "r4_r8_candidate_construction_source_map.txt"

QUALIFIED_FILE = PROJECT / "core/knowledge_catalog/qualified_search.py"
EVALUATOR_FILE = PROJECT / "core/retrieval/qualification/evaluator.py"
CONTRACTS_FILE = PROJECT / "core/retrieval/qualification/contracts.py"

sys.path.insert(0, str(PROJECT))

from core.knowledge_catalog import qualified_search as qs
from core.retrieval.qualification import evaluator as evaluator_module
from core.retrieval.qualification.contracts import EvidenceCandidate
from core.retrieval.qualification.evaluator import QualificationEvaluator


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def text(v: Any) -> str:
    if v is None:
        return ""
    return str(v)


def clean(v: Any) -> str:
    return text(v).strip()


def lower(v: Any) -> str:
    return clean(v).casefold()


def serialize(v: Any) -> Any:
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    if is_dataclass(v):
        try:
            return asdict(v)
        except Exception:
            pass
    if isinstance(v, dict):
        return {str(k): serialize(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [serialize(x) for x in v]
    if hasattr(v, "__dict__"):
        try:
            return {
                str(k): serialize(x)
                for k, x in vars(v).items()
                if not str(k).startswith("__")
            }
        except Exception:
            pass
    return repr(v)


def value_state(v: Any) -> str:
    if v is None:
        return "NONE"
    if isinstance(v, str):
        if v == "":
            return "EMPTY_STRING"
        if not v.strip():
            return "WHITESPACE_STRING"
        return "POPULATED_STRING"
    if isinstance(v, bool):
        return "BOOL"
    if isinstance(v, int):
        return "INT"
    if isinstance(v, float):
        if math.isnan(v):
            return "FLOAT_NAN"
        return "FLOAT"
    return type(v).__name__


def safe_attr(obj: Any, name: str) -> Any:
    try:
        return getattr(obj, name)
    except Exception:
        return None


def first_present(row: dict[str, str], names: list[str]) -> tuple[str, str]:
    lowered = {str(k).casefold(): k for k in row}
    for wanted in names:
        key = lowered.get(wanted.casefold())
        if key is not None:
            return key, row.get(key, "")
    return "", ""


def source_id_from_candidate(candidate: Any) -> str:
    for name in (
        "document_id",
        "runtime_document_id",
        "source_document_id",
        "catalog_document_id",
        "source_id",
        "id",
    ):
        value = safe_attr(candidate, name)
        if value not in (None, ""):
            return text(value)
    return ""


def candidate_snapshot(candidate: Any) -> dict[str, Any]:
    names = [
        "source_id",
        "document_id",
        "runtime_document_id",
        "source_document_id",
        "catalog_document_id",
        "id",
        "title",
        "subject",
        "excerpt",
        "source_path",
        "path",
        "confidence",
        "retrieval_score",
        "score",
    ]

    result: dict[str, Any] = {
        "__type__": type(candidate).__name__,
    }

    for name in names:
        if hasattr(candidate, name):
            result[name] = safe_attr(candidate, name)

    if hasattr(candidate, "__dict__"):
        for k, v in vars(candidate).items():
            if k not in result:
                result[k] = v

    return result


def evidence_candidate_from_qualified_module(row: Any) -> EvidenceCandidate:
    """
    Use production candidate construction only.

    No filename fallback.
    No subject reconstruction.
    No title reconstruction.
    No diagnostic substitutions.
    """
    candidates = []

    for name in (
        "_row_to_evidence_candidate",
        "_to_evidence_candidate",
        "_candidate_from_row",
        "_make_evidence_candidate",
        "_build_evidence_candidate",
        "_qualification_candidate_from_row",
    ):
        fn = getattr(qs, name, None)
        if callable(fn):
            candidates.append((name, fn))

    errors = []

    for name, fn in candidates:
        try:
            result = fn(row)
            if isinstance(result, EvidenceCandidate):
                return result
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")

    raise RuntimeError(
        "Unable to locate callable production row -> EvidenceCandidate "
        "constructor. Tried: "
        + ", ".join(name for name, _ in candidates)
        + (" | errors: " + " ; ".join(errors) if errors else "")
    )


def find_qualify_rows():
    fn = getattr(qs, "qualify_rows", None)
    if callable(fn):
        return fn

    for name, obj in vars(qs).items():
        if callable(obj) and name.casefold() == "qualify_rows":
            return obj

    raise RuntimeError("production qualify_rows() not found")


def read_r4r2():
    with R4R2.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        rows = list(reader)
        return reader.fieldnames or [], rows


# ------------------------------------------------------------------
# R4-R2 schema semantics
# ------------------------------------------------------------------

fieldnames, all_r4r2_rows = read_r4r2()

subject_rows = []

for row in all_r4r2_rows:
    failure_key, failure_value = first_present(
        row,
        [
            "failure_class",
            "failure",
            "class",
            "rejection_class",
            "decision_class",
        ],
    )

    decision_key, decision_value = first_present(
        row,
        [
            "decision",
            "qualification_decision",
            "result_decision",
        ],
    )

    blob = " ".join(
        [clean(failure_value), clean(decision_value)]
    ).upper()

    if "SUBJECT" in blob:
        subject_rows.append(row)

if len(subject_rows) != 221:
    raise RuntimeError(
        f"Expected exactly 221 R4-R2 SUBJECT failures, got {len(subject_rows)}"
    )


# infer column semantics from name + values
schema_rows = []

for column in fieldnames:
    values = [row.get(column, "") for row in subject_rows]
    nonempty = [v for v in values if clean(v)]

    numeric = 0
    for v in nonempty:
        try:
            float(v)
            numeric += 1
        except Exception:
            pass

    numeric_fraction = (
        numeric / len(nonempty)
        if nonempty
        else 0.0
    )

    lc = column.casefold()

    if "subject" in lc and "score" in lc:
        semantic = "SUBJECT_SCORE"
    elif lc in {"subject", "candidate_subject", "raw_subject"}:
        semantic = "SUBJECT_METADATA_OR_AMBIGUOUS"
    elif "title" in lc:
        semantic = "TITLE_METADATA"
    elif "score" in lc:
        semantic = "SCORE"
    elif "query" in lc:
        semantic = "QUERY"
    elif "document" in lc and "id" in lc:
        semantic = "DOCUMENT_ID"
    elif lc in {"source_id", "id"}:
        semantic = "IDENTITY"
    elif "decision" in lc:
        semantic = "QUALIFICATION_DECISION"
    elif "failure" in lc or "class" in lc:
        semantic = "DIAGNOSTIC_CLASS"
    else:
        semantic = "OTHER"

    schema_rows.append(
        {
            "column": column,
            "semantic_class": semantic,
            "nonempty_count": len(nonempty),
            "numeric_count": numeric,
            "numeric_fraction": numeric_fraction,
            "sample_1": nonempty[0] if len(nonempty) > 0 else "",
            "sample_2": nonempty[1] if len(nonempty) > 1 else "",
            "sample_3": nonempty[2] if len(nonempty) > 2 else "",
        }
    )


# ------------------------------------------------------------------
# Capture production invocation
# ------------------------------------------------------------------

qualify_rows = find_qualify_rows()

original_eval_candidate = QualificationEvaluator.evaluate_candidate

captures: list[dict[str, Any]] = []


def wrapped_eval_candidate(self, query, candidate):
    before = candidate_snapshot(candidate)

    result = original_eval_candidate(self, query, candidate)

    after = candidate_snapshot(candidate)

    captures.append(
        {
            "query": query,
            "candidate_before": before,
            "candidate_after": after,
            "candidate_type": type(candidate).__name__,
            "candidate_source_identity": source_id_from_candidate(candidate),
            "qualification_evidence": serialize(result),
        }
    )

    return result


QualificationEvaluator.evaluate_candidate = wrapped_eval_candidate


# ------------------------------------------------------------------
# Reproduce each R4-R2 SUBJECT case through production search/qualification
# ------------------------------------------------------------------

def query_from_r4r2(row: dict[str, str]) -> str:
    key, value = first_present(
        row,
        [
            "query",
            "qualification_query",
            "search_query",
            "input_query",
        ],
    )
    if not clean(value):
        raise RuntimeError(
            "R4-R2 row has no usable query column. "
            f"Available columns: {fieldnames}"
        )
    return value


def document_id_from_r4r2(row: dict[str, str]) -> str:
    key, value = first_present(
        row,
        [
            "document_id",
            "runtime_document_id",
            "target_document_id",
            "source_document_id",
            "catalog_document_id",
        ],
    )
    return clean(value)


# Production search entry point.
search_catalog = getattr(qs, "search_catalog", None)

if not callable(search_catalog):
    from core.knowledge_catalog.search import search_catalog


details = []
classification_counter = Counter()
candidate_subject_state = Counter()
candidate_title_state = Counter()
r4r2_subject_semantics = Counter()

trace_lines = []

start = time.time()

for index, r4row in enumerate(subject_rows, 1):
    query = query_from_r4r2(r4row)
    target_id = document_id_from_r4r2(r4row)

    r4_subject_key, r4_subject_value = first_present(
        r4row,
        ["subject", "candidate_subject", "raw_subject"],
    )

    r4_subject_score_key, r4_subject_score_value = first_present(
        r4row,
        ["subject_score", "score_subject"],
    )

    r4_title_key, r4_title_value = first_present(
        r4row,
        ["title", "candidate_title", "raw_title"],
    )

    if r4_subject_key:
        try:
            float(r4_subject_value)
            if r4_subject_value.strip() in {
                "0",
                "0.0",
                "0.00",
                "0.000",
            }:
                r4r2_subject_semantics["NUMERIC_ZERO"] += 1
            else:
                r4r2_subject_semantics["NUMERIC_OR_TEXT"] += 1
        except Exception:
            r4r2_subject_semantics["TEXT"] += 1
    else:
        r4r2_subject_semantics["NO_SUBJECT_COLUMN"] += 1

    # Use production raw search.
    raw_rows = search_catalog(query, limit=20)

    if not isinstance(raw_rows, (list, tuple)):
        raw_rows = list(raw_rows)

    # Clear only our in-memory capture buffer.
    captures.clear()

    # Invoke production qualification flow exactly.
    try:
        qualification_result = qualify_rows(query, raw_rows)
    except TypeError:
        # Some production versions may require keyword form.
        qualification_result = qualify_rows(
            query=query,
            rows=raw_rows,
        )

    # Locate the target candidate capture.
    target_capture = None

    if target_id:
        for cap in captures:
            cid = clean(cap.get("candidate_source_identity"))
            if cid == target_id:
                target_capture = cap
                break

    # If identity isn't directly represented in the candidate,
    # use the exact R4-R2 target position only as a matching aid.
    # Do NOT reconstruct fields.
    if target_capture is None and len(captures) == 1:
        target_capture = captures[0]

    if target_capture is None:
        # Search all serialized candidate fields for exact target id.
        if target_id:
            for cap in captures:
                blob = json.dumps(
                    serialize(cap.get("candidate_before")),
                    ensure_ascii=False,
                    sort_keys=True,
                )
                if f'"{target_id}"' in blob or f": {target_id}" in blob:
                    target_capture = cap
                    break

    if target_capture is None:
        classification = "TARGET_CAPTURE_NOT_RESOLVED"

        details.append(
            {
                "case": index,
                "document_id": target_id,
                "query": query,
                "classification": classification,
                "r4r2_subject_column": r4_subject_key,
                "r4r2_subject_value": r4_subject_value,
                "r4r2_subject_score_column": r4_subject_score_key,
                "r4r2_subject_score_value": r4_subject_score_value,
                "r4r2_title_column": r4_title_key,
                "r4r2_title_value": r4_title_value,
                "candidate_subject_type": "",
                "candidate_subject_repr": "",
                "candidate_subject_state": "",
                "candidate_title_type": "",
                "candidate_title_repr": "",
                "candidate_title_state": "",
                "capture_count": len(captures),
            }
        )

        classification_counter[classification] += 1
        continue

    candidate = target_capture["candidate_before"]

    actual_subject = candidate.get("subject")
    actual_title = candidate.get("title")

    subj_state = value_state(actual_subject)
    title_state = value_state(actual_title)

    candidate_subject_state[subj_state] += 1
    candidate_title_state[title_state] += 1

    # ----------------------------------------------------------
    # A/B/C/D classification
    # ----------------------------------------------------------

    r4_subject_is_zero = clean(r4_subject_value) in {
        "0",
        "0.0",
        "0.00",
        "0.000",
    }

    actual_subject_is_zero = (
        isinstance(actual_subject, (int, float))
        and not isinstance(actual_subject, bool)
        and float(actual_subject) == 0.0
    ) or (
        isinstance(actual_subject, str)
        and actual_subject.strip() in {"0", "0.0", "0.00", "0.000"}
    )

    actual_subject_absent = (
        actual_subject is None
        or (isinstance(actual_subject, str) and not actual_subject.strip())
    )

    actual_title_absent = (
        actual_title is None
        or (isinstance(actual_title, str) and not actual_title.strip())
    )

    if r4_subject_is_zero and actual_subject_is_zero:
        classification = "A_ACTUAL_CANDIDATE_SUBJECT_ZERO"

    elif (
        r4_subject_is_zero
        and actual_subject_absent
        and clean(r4_subject_score_value) in {
            "0",
            "0.0",
            "0.00",
            "0.000",
        }
    ):
        classification = "B_R4R2_SCORE_COLUMN_INTERPRETED_AS_SUBJECT"

    elif actual_subject_absent and actual_title_absent:
        # We know candidate metadata is absent. Whether it existed
        # upstream requires raw-row comparison below.
        classification = "D_CANDIDATE_METADATA_ABSENT"

    else:
        classification = "C_OR_OTHER_METADATA_PROPAGATION"

    # Inspect exact raw row corresponding to target if possible.
    raw_subject = None
    raw_title = None
    raw_match = None

    for raw in raw_rows:
        rid = None

        if isinstance(raw, dict):
            for key in (
                "document_id",
                "runtime_document_id",
                "source_document_id",
                "catalog_document_id",
                "id",
                "source_id",
            ):
                if key in raw and raw[key] not in (None, ""):
                    rid = clean(raw[key])
                    break

            if target_id and rid == target_id:
                raw_match = raw
                raw_subject = raw.get("subject")
                raw_title = raw.get("title")
                break

        else:
            for key in (
                "document_id",
                "runtime_document_id",
                "source_document_id",
                "catalog_document_id",
                "id",
                "source_id",
            ):
                if hasattr(raw, key):
                    value = getattr(raw, key)
                    if value not in (None, ""):
                        rid = clean(value)
                        break

            if target_id and rid == target_id:
                raw_match = raw
                raw_subject = safe_attr(raw, "subject")
                raw_title = safe_attr(raw, "title")
                break

    raw_subject_present = (
        raw_subject is not None
        and (not isinstance(raw_subject, str) or bool(raw_subject.strip()))
    )

    raw_title_present = (
        raw_title is not None
        and (not isinstance(raw_title, str) or bool(raw_title.strip()))
    )

    if (
        classification == "D_CANDIDATE_METADATA_ABSENT"
        and (raw_subject_present or raw_title_present)
    ):
        classification = "C_METADATA_LOST_DURING_CANDIDATE_CONSTRUCTION"

    elif (
        classification == "D_CANDIDATE_METADATA_ABSENT"
        and raw_match is not None
        and not raw_subject_present
        and not raw_title_present
    ):
        classification = "D_UPSTREAM_METADATA_GENUINELY_ABSENT"

    classification_counter[classification] += 1

    detail = {
        "case": index,
        "document_id": target_id,
        "query": query,
        "classification": classification,

        "r4r2_subject_column": r4_subject_key,
        "r4r2_subject_value": r4_subject_value,
        "r4r2_subject_score_column": r4_subject_score_key,
        "r4r2_subject_score_value": r4_subject_score_value,
        "r4r2_title_column": r4_title_key,
        "r4r2_title_value": r4_title_value,

        "candidate_type": target_capture["candidate_type"],
        "candidate_identity": target_capture["candidate_source_identity"],

        "candidate_subject_type": type(actual_subject).__name__,
        "candidate_subject_repr": repr(actual_subject),
        "candidate_subject_state": subj_state,

        "candidate_title_type": type(actual_title).__name__,
        "candidate_title_repr": repr(actual_title),
        "candidate_title_state": title_state,

        "raw_row_matched": raw_match is not None,
        "raw_subject_type": type(raw_subject).__name__ if raw_match is not None else "",
        "raw_subject_repr": repr(raw_subject) if raw_match is not None else "",
        "raw_title_type": type(raw_title).__name__ if raw_match is not None else "",
        "raw_title_repr": repr(raw_title) if raw_match is not None else "",

        "capture_count": len(captures),
    }

    details.append(detail)

    if index <= 24:
        trace_lines.extend(
            [
                "-" * 78,
                f"CASE {index:03d}",
                "-" * 78,
                f"document_id            : {target_id}",
                f"query                  : {query}",
                "",
                "R4-R2 RECORDED FIELDS",
                f"  subject column       : {r4_subject_key!r}",
                f"  subject value        : {r4_subject_value!r}",
                f"  subject-score column : {r4_subject_score_key!r}",
                f"  subject-score value  : {r4_subject_score_value!r}",
                f"  title column         : {r4_title_key!r}",
                f"  title value          : {r4_title_value!r}",
                "",
                "PRODUCTION EVIDENCECANDIDATE",
                f"  type                  : {target_capture['candidate_type']}",
                f"  identity              : {target_capture['candidate_source_identity']!r}",
                f"  subject type          : {type(actual_subject).__name__}",
                f"  subject repr          : {actual_subject!r}",
                f"  subject state         : {subj_state}",
                f"  title type            : {type(actual_title).__name__}",
                f"  title repr            : {actual_title!r}",
                f"  title state           : {title_state}",
                "",
                "UPSTREAM RAW ROW",
                f"  matched               : {raw_match is not None}",
                f"  subject type          : {type(raw_subject).__name__ if raw_match is not None else ''}",
                f"  subject repr          : {raw_subject!r}",
                f"  title type            : {type(raw_title).__name__ if raw_match is not None else ''}",
                f"  title repr            : {raw_title!r}",
                "",
                f"CLASSIFICATION          : {classification}",
                "",
            ]
        )


QualificationEvaluator.evaluate_candidate = original_eval_candidate

elapsed = time.time() - start


# ------------------------------------------------------------------
# Source contract
# ------------------------------------------------------------------

source_lines = []

for path in (QUALIFIED_FILE, EVALUATOR_FILE, CONTRACTS_FILE):
    source_lines.append("=" * 78)
    source_lines.append(f"FILE: {path}")
    source_lines.append("=" * 78)

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    lines = source.splitlines()

    for node in ast.walk(tree):
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):
            name = getattr(node, "name", "")
            lname = name.casefold()

            if (
                "candidate" in lname
                or "qualif" in lname
                or "row" in lname
                or name in {"EvidenceCandidate", "QualificationEvaluator"}
            ):
                start_line = max(1, node.lineno - 2)
                end_line = min(
                    len(lines),
                    getattr(node, "end_lineno", node.lineno) + 2,
                )

                source_lines.append(
                    f"\n{name} lines {node.lineno}-"
                    f"{getattr(node, 'end_lineno', node.lineno)}"
                )

                for n in range(start_line, end_line + 1):
                    source_lines.append(
                        f"{n:05d}: {lines[n - 1]}"
                    )


# ------------------------------------------------------------------
# Determine certified interpretation
# ------------------------------------------------------------------

resolved = sum(
    count
    for key, count in classification_counter.items()
    if key != "TARGET_CAPTURE_NOT_RESOLVED"
)

unresolved = classification_counter.get(
    "TARGET_CAPTURE_NOT_RESOLVED",
    0,
)

if unresolved:
    conclusion = "INCOMPLETE_TARGET_CAPTURE"

elif classification_counter.get(
    "B_R4R2_SCORE_COLUMN_INTERPRETED_AS_SUBJECT",
    0,
) == 221:
    conclusion = "B_R4R2_COLUMN_SEMANTICS_DEFECT"

elif classification_counter.get(
    "A_ACTUAL_CANDIDATE_SUBJECT_ZERO",
    0,
) == 221:
    conclusion = "A_PRODUCTION_CANDIDATE_SUBJECT_IS_ZERO"

elif classification_counter.get(
    "C_METADATA_LOST_DURING_CANDIDATE_CONSTRUCTION",
    0,
) > 0:
    conclusion = "C_METADATA_PROPAGATION_DEFECT"

elif classification_counter.get(
    "D_UPSTREAM_METADATA_GENUINELY_ABSENT",
    0,
) == 221:
    conclusion = "D_UPSTREAM_METADATA_ABSENT"

else:
    conclusion = "MIXED_FIELD_CONTRACT"


certification = {
    "exact_subject_population": len(subject_rows) == 221,
    "all_cases_processed": len(details) == 221,
    "all_targets_resolved": unresolved == 0,
    "production_candidate_contract_captured": resolved == 221,
    "r4r2_column_semantics_captured": bool(schema_rows),
}

certified = all(certification.values())


report = {
    "phase": "Genesis Recall R4-R8",
    "purpose": (
        "Production Evidence Field Contract & "
        "R4-R2 Column-Semantics Certification"
    ),
    "population": {
        "r4r2_total_rows": len(all_r4r2_rows),
        "subject_failures": len(subject_rows),
        "processed": len(details),
        "resolved": resolved,
        "unresolved": unresolved,
    },
    "r4r2_columns": fieldnames,
    "r4r2_subject_semantics": dict(r4r2_subject_semantics),
    "candidate_subject_states": dict(candidate_subject_state),
    "candidate_title_states": dict(candidate_title_state),
    "classification": dict(classification_counter),
    "conclusion": conclusion,
    "certification": certification,
    "diagnostic_certified": certified,
    "elapsed_seconds": round(elapsed, 3),
}


REPORT.write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8",
)


detail_fields = [
    "case",
    "document_id",
    "query",
    "classification",
    "r4r2_subject_column",
    "r4r2_subject_value",
    "r4r2_subject_score_column",
    "r4r2_subject_score_value",
    "r4r2_title_column",
    "r4r2_title_value",
    "candidate_type",
    "candidate_identity",
    "candidate_subject_type",
    "candidate_subject_repr",
    "candidate_subject_state",
    "candidate_title_type",
    "candidate_title_repr",
    "candidate_title_state",
    "raw_row_matched",
    "raw_subject_type",
    "raw_subject_repr",
    "raw_title_type",
    "raw_title_repr",
    "capture_count",
]

with DETAIL.open("w", encoding="utf-8", newline="") as fh:
    writer = csv.DictWriter(
        fh,
        fieldnames=detail_fields,
        delimiter="\t",
    )
    writer.writeheader()
    writer.writerows(details)


schema_fields = [
    "column",
    "semantic_class",
    "nonempty_count",
    "numeric_count",
    "numeric_fraction",
    "sample_1",
    "sample_2",
    "sample_3",
]

with SCHEMA.open("w", encoding="utf-8", newline="") as fh:
    writer = csv.DictWriter(
        fh,
        fieldnames=schema_fields,
        delimiter="\t",
    )
    writer.writeheader()
    writer.writerows(schema_rows)


TRACE.write_text(
    "\n".join(
        [
            "=" * 78,
            " GENESIS RECALL R4-R8",
            " PRODUCTION EVIDENCE FIELD TRACE",
            "=" * 78,
            "",
            *trace_lines,
        ]
    ),
    encoding="utf-8",
)

SOURCE_MAP.write_text(
    "\n".join(source_lines),
    encoding="utf-8",
)


print("=" * 78)
print(" GENESIS RECALL R4-R8 RESULT")
print("=" * 78)
print()
print("POPULATION")
print(f"  R4-R2 rows               : {len(all_r4r2_rows)}")
print(f"  SUBJECT failures         : {len(subject_rows)}")
print(f"  processed                : {len(details)}")
print(f"  target captures resolved : {resolved}")
print(f"  unresolved               : {unresolved}")
print()
print("R4-R2 SUBJECT COLUMN STATES")
for k, v in sorted(r4r2_subject_semantics.items()):
    print(f"  {k:36s} {v}")
print()
print("PRODUCTION CANDIDATE.SUBJECT STATES")
for k, v in sorted(candidate_subject_state.items()):
    print(f"  {k:36s} {v}")
print()
print("PRODUCTION CANDIDATE.TITLE STATES")
for k, v in sorted(candidate_title_state.items()):
    print(f"  {k:36s} {v}")
print()
print("A/B/C/D FIELD-CONTRACT CLASSIFICATION")
for k, v in classification_counter.most_common():
    print(f"  {k:48s} {v}")
print()
print("CONCLUSION")
print(f"  {conclusion}")
print()
print("CERTIFICATION")
for k, v in certification.items():
    print(f"  {k:40s}: {v}")
print()
print(f"R4-R8 DIAGNOSTIC CERTIFIED : {certified}")
print()
print(f"JSON report : {REPORT}")
print(f"detail TSV  : {DETAIL}")
print(f"schema TSV  : {SCHEMA}")
print(f"trace       : {TRACE}")
print(f"source map  : {SOURCE_MAP}")
print()
print(f"elapsed seconds: {elapsed:.2f}")
print("=" * 78)

raise SystemExit(0 if certified else 1)
