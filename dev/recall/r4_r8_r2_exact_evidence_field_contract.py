from __future__ import annotations

import csv
import inspect
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


PROJECT = Path(sys.argv[1])
R4R2 = Path(sys.argv[2])
REPORT = Path(sys.argv[3])
TRACE = Path(sys.argv[4])
SEMANTICS = Path(sys.argv[5])
SOURCEMAP = Path(sys.argv[6])

sys.path.insert(0, str(PROJECT))


from core.knowledge_catalog.search import search_catalog
from core.knowledge_catalog.qualified_search import (
    candidate_from_row,
    qualify_rows,
)
from core.retrieval.qualification.evaluator import (
    QualificationEngine,
)
from core.retrieval.qualification.contracts import (
    EvidenceCandidate,
)


def sval(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def row_value(row: Any, name: str, default: Any = "") -> Any:
    if isinstance(row, Mapping):
        return row.get(name, default)
    return getattr(row, name, default)


def first_present(row: Mapping[str, Any], names: tuple[str, ...]) -> str:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return str(value)
    return ""


def load_r4r2() -> list[dict[str, str]]:
    with R4R2.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


r4_rows = load_r4r2()

subject_failures = [
    row
    for row in r4_rows
    if (
        row.get("failure_class", "").strip().upper() == "SUBJECT"
        or "SUBJECT" in row.get("decision", "").upper()
        or "SUBJECT" in row.get("qualification_decision", "").upper()
    )
]

if len(subject_failures) != 221:
    print(
        "FAIL: expected 221 SUBJECT failures, got",
        len(subject_failures),
    )
    raise SystemExit(2)


# ------------------------------------------------------------
# Discover useful R4-R2 identity columns.
# ------------------------------------------------------------

headers = tuple(r4_rows[0].keys()) if r4_rows else ()

id_columns = tuple(
    name
    for name in headers
    if any(
        token in name.casefold()
        for token in (
            "document_id",
            "runtime_id",
            "source_id",
            "target_id",
            "doc_id",
        )
    )
)

query_columns = tuple(
    name
    for name in headers
    if "query" in name.casefold()
)

print("R4-R2 headers:")
for name in headers:
    print(" ", name)

print()
print("identity columns:", id_columns)
print("query columns   :", query_columns)


# ------------------------------------------------------------
# Exact target matching.
#
# We are not rebuilding title/subject from filenames.
# We use R4-R2 only to recover:
#   1. query
#   2. target identity
#
# Then search_catalog() provides the production raw row.
# ------------------------------------------------------------

detail: list[dict[str, Any]] = []
semantic_rows: list[dict[str, Any]] = []

counts = Counter()

engine = QualificationEngine()


def extract_query(r4: Mapping[str, str]) -> str:
    preferred = (
        "query",
        "search_query",
        "qualification_query",
        "input_query",
    )

    q = first_present(r4, preferred)
    if q:
        return q

    for name in query_columns:
        value = r4.get(name, "")
        if value:
            return value

    return ""


def extract_target_ids(r4: Mapping[str, str]) -> set[str]:
    result: set[str] = set()

    preferred = (
        "document_id",
        "runtime_document_id",
        "runtime_id",
        "target_id",
        "doc_id",
        "source_id",
    )

    for name in preferred:
        value = r4.get(name)
        if value not in (None, ""):
            result.add(str(value).strip())

    for name in id_columns:
        value = r4.get(name)
        if value not in (None, ""):
            result.add(str(value).strip())

    return {
        value
        for value in result
        if value
    }


def raw_identity_values(raw: Mapping[str, Any]) -> set[str]:
    values = set()

    for name in (
        "id",
        "document_id",
        "runtime_document_id",
        "runtime_id",
        "source_id",
        "doc_id",
    ):
        value = raw.get(name)
        if value not in (None, ""):
            values.add(str(value).strip())

    return values


for index, r4 in enumerate(subject_failures, start=1):

    query = extract_query(r4)
    target_ids = extract_target_ids(r4)

    if not query:
        counts["missing_query"] += 1
        detail.append(
            {
                "case": index,
                "status": "MISSING_QUERY",
            }
        )
        continue

    if not target_ids:
        counts["missing_target_identity"] += 1
        detail.append(
            {
                "case": index,
                "query": query,
                "status": "MISSING_TARGET_IDENTITY",
            }
        )
        continue

    # Production raw retrieval.
    raw_rows = list(
        search_catalog(
            query,
            limit=100,
        )
    )

    matches = []

    for ordinal, raw in enumerate(raw_rows, start=1):

        if isinstance(raw, Mapping):
            raw_map = dict(raw)
        elif hasattr(raw, "keys"):
            raw_map = {
                key: raw[key]
                for key in raw.keys()
            }
        elif hasattr(raw, "_asdict"):
            raw_map = dict(raw._asdict())
        else:
            try:
                raw_map = dict(vars(raw))
            except Exception:
                continue

        identities = raw_identity_values(raw_map)

        if target_ids.intersection(identities):
            matches.append(
                (
                    ordinal,
                    raw,
                    raw_map,
                )
            )

    if not matches:
        counts["target_raw_not_found"] += 1

        detail.append(
            {
                "case": index,
                "query": query,
                "target_ids": "|".join(sorted(target_ids)),
                "raw_count": len(raw_rows),
                "status": "TARGET_RAW_NOT_FOUND",
            }
        )
        continue

    if len(matches) > 1:
        counts["multiple_raw_matches"] += 1

    ordinal, raw, raw_map = matches[0]

    # --------------------------------------------------------
    # EXACT PRODUCTION CANDIDATE CONSTRUCTION
    # --------------------------------------------------------

    candidate = candidate_from_row(
        raw,
        ordinal=ordinal,
    )

    if not isinstance(candidate, EvidenceCandidate):
        counts["candidate_contract_failure"] += 1
        continue

    # --------------------------------------------------------
    # EXACT ENGINE EVALUATION
    # --------------------------------------------------------

    result = engine.evaluate(
        query,
        (candidate,),
    )

    evidence_all = (
        *result.accepted,
        *result.rejected,
    )

    if len(evidence_all) != 1:
        counts["evidence_cardinality_error"] += 1
        continue

    evidence = evidence_all[0]

    c = evidence.candidate
    s = evidence.score

    raw_title = sval(
        raw_map.get("title", "")
    )

    raw_subject = sval(
        raw_map.get("subject", "")
    )

    candidate_title = sval(c.title)
    candidate_subject = sval(c.subject)

    title_preserved = raw_title == candidate_title
    subject_preserved = raw_subject == candidate_subject

    # Detect score/metadata semantic confusion explicitly.
    score_subject = getattr(s, "subject", None)

    r4_subject_value = r4.get("subject", "")
    r4_title_value = r4.get("title", "")

    r4_subject_score_value = first_present(
        r4,
        (
            "subject_score",
            "score_subject",
            "qualification_subject_score",
        ),
    )

    r4_title_matches_candidate = (
        r4_title_value == candidate_title
        if "title" in r4
        else None
    )

    r4_subject_matches_candidate = (
        r4_subject_value == candidate_subject
        if "subject" in r4
        else None
    )

    r4_subject_matches_score = False

    if r4_subject_value not in ("", None):
        try:
            r4_subject_matches_score = (
                abs(
                    float(r4_subject_value)
                    - float(score_subject)
                )
                < 1e-12
            )
        except Exception:
            pass

    if candidate_title:
        counts["candidate_title_populated"] += 1
    else:
        counts["candidate_title_empty"] += 1

    if candidate_subject:
        counts["candidate_subject_populated"] += 1
    else:
        counts["candidate_subject_empty"] += 1

    if raw_title:
        counts["raw_title_populated"] += 1
    else:
        counts["raw_title_empty"] += 1

    if raw_subject:
        counts["raw_subject_populated"] += 1
    else:
        counts["raw_subject_empty"] += 1

    if title_preserved:
        counts["title_preserved"] += 1
    else:
        counts["title_transformed"] += 1

    if subject_preserved:
        counts["subject_preserved"] += 1
    else:
        counts["subject_transformed"] += 1

    if float(score_subject) == 0.0:
        counts["subject_score_zero"] += 1
    else:
        counts["subject_score_positive"] += 1

    if r4_subject_matches_candidate:
        counts["r4_subject_is_candidate_subject"] += 1

    if r4_subject_matches_score:
        counts["r4_subject_is_subject_score"] += 1

    detail.append(
        {
            "case": index,
            "status": "OK",
            "query": query,
            "target_ids": "|".join(sorted(target_ids)),
            "raw_rank": ordinal,

            "raw_identities": "|".join(
                sorted(raw_identity_values(raw_map))
            ),

            "raw_title": raw_title,
            "raw_subject": raw_subject,

            "candidate_source_id": c.source_id,
            "candidate_source_path": c.source_path,
            "candidate_title": candidate_title,
            "candidate_subject": candidate_subject,
            "candidate_excerpt": c.excerpt,
            "candidate_backend": c.backend,
            "candidate_retrieval_score": c.retrieval_score,

            "candidate_metadata_json": json.dumps(
                dict(c.metadata),
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            ),

            "score_lexical": getattr(s, "lexical", None),
            "score_phrase": getattr(s, "phrase", None),
            "score_entity": getattr(s, "entity", None),
            "score_subject": score_subject,
            "score_provenance": getattr(s, "provenance", None),
            "score_final": getattr(s, "final", None),

            "decision": str(evidence.decision),
            "explanation": evidence.explanation,

            "raw_title_equals_candidate_title": title_preserved,
            "raw_subject_equals_candidate_subject": subject_preserved,

            "r4_title_column": r4_title_value,
            "r4_subject_column": r4_subject_value,
            "r4_subject_score_column": r4_subject_score_value,

            "r4_title_equals_candidate_title":
                r4_title_matches_candidate,

            "r4_subject_equals_candidate_subject":
                r4_subject_matches_candidate,

            "r4_subject_equals_score_subject":
                r4_subject_matches_score,
        }
    )

    semantic_rows.append(
        {
            "case": index,
            "query": query,

            "candidate_title_state":
                "POPULATED"
                if candidate_title
                else "EMPTY",

            "candidate_subject_state":
                "POPULATED"
                if candidate_subject
                else "EMPTY",

            "score_subject":
                score_subject,

            "r4_title_column":
                r4_title_value,

            "r4_subject_column":
                r4_subject_value,

            "r4_subject_column_matches_candidate_subject":
                r4_subject_matches_candidate,

            "r4_subject_column_matches_score_subject":
                r4_subject_matches_score,
        }
    )


# ------------------------------------------------------------
# Write detail TSV
# ------------------------------------------------------------

detail_fields = sorted(
    {
        key
        for row in detail
        for key in row.keys()
    }
)

with TRACE.open(
    "w",
    encoding="utf-8",
    newline="",
) as fh:
    writer = csv.DictWriter(
        fh,
        fieldnames=detail_fields,
        delimiter="\t",
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(detail)


semantic_fields = sorted(
    {
        key
        for row in semantic_rows
        for key in row.keys()
    }
)

with SEMANTICS.open(
    "w",
    encoding="utf-8",
    newline="",
) as fh:
    writer = csv.DictWriter(
        fh,
        fieldnames=semantic_fields,
        delimiter="\t",
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(semantic_rows)


# ------------------------------------------------------------
# Candidate construction source map
# ------------------------------------------------------------

source_lines = []

for obj_name, obj in (
    ("candidate_from_row", candidate_from_row),
    ("qualify_rows", qualify_rows),
    ("QualificationEngine.evaluate", QualificationEngine.evaluate),
    (
        "QualificationEngine.evaluate_candidate",
        QualificationEngine.evaluate_candidate,
    ),
):
    source_lines.append("=" * 78)
    source_lines.append(obj_name)
    source_lines.append("=" * 78)

    try:
        source_lines.append(inspect.getsource(obj))
    except Exception as exc:
        source_lines.append(
            f"SOURCE ERROR: {type(exc).__name__}: {exc}"
        )

SOURCEMAP.write_text(
    "\n".join(source_lines) + "\n",
    encoding="utf-8",
)


# ------------------------------------------------------------
# Classification
# ------------------------------------------------------------

ok_cases = sum(
    1
    for row in detail
    if row.get("status") == "OK"
)

all_candidate_subject_populated = (
    ok_cases == 221
    and counts["candidate_subject_populated"] == 221
)

all_candidate_title_populated = (
    ok_cases == 221
    and counts["candidate_title_populated"] == 221
)

all_subject_scores_zero = (
    ok_cases == 221
    and counts["subject_score_zero"] == 221
)

if (
    all_candidate_subject_populated
    and all_candidate_title_populated
    and all_subject_scores_zero
):
    field_contract_class = (
        "METADATA_PRESENT_SCORE_ZERO"
    )

elif (
    counts["candidate_subject_empty"] > 0
    or counts["candidate_title_empty"] > 0
):
    field_contract_class = (
        "CANDIDATE_METADATA_ABSENT_OR_PARTIAL"
    )

else:
    field_contract_class = "MIXED"


if (
    counts["r4_subject_is_subject_score"]
    > counts["r4_subject_is_candidate_subject"]
):
    r4_column_semantics = (
        "R4R2_SUBJECT_COLUMN_IS_SCORE_OR_SCORE_DERIVED"
    )

elif (
    counts["r4_subject_is_candidate_subject"]
    > counts["r4_subject_is_subject_score"]
):
    r4_column_semantics = (
        "R4R2_SUBJECT_COLUMN_IS_CANDIDATE_METADATA"
    )

else:
    r4_column_semantics = (
        "R4R2_SUBJECT_COLUMN_SEMANTICS_MIXED_OR_UNRESOLVED"
    )


certified = (
    len(subject_failures) == 221
    and ok_cases == 221
    and counts["target_raw_not_found"] == 0
    and counts["missing_query"] == 0
    and counts["missing_target_identity"] == 0
)


report = {
    "input": {
        "r4r2_rows": len(r4_rows),
        "subject_failures": len(subject_failures),
    },
    "trace": {
        "ok_cases": ok_cases,
        "counts": dict(counts),
    },
    "field_contract": {
        "classification": field_contract_class,
        "all_candidate_subject_populated":
            all_candidate_subject_populated,
        "all_candidate_title_populated":
            all_candidate_title_populated,
        "all_subject_scores_zero":
            all_subject_scores_zero,
    },
    "r4r2_column_semantics": {
        "classification": r4_column_semantics,
        "r4_subject_matches_candidate_subject":
            counts["r4_subject_is_candidate_subject"],
        "r4_subject_matches_score_subject":
            counts["r4_subject_is_subject_score"],
    },
    "certification": {
        "exact_population": len(subject_failures) == 221,
        "all_cases_traced": ok_cases == 221,
        "certified": certified,
    },
}

REPORT.write_text(
    json.dumps(
        report,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)


print()
print("=" * 78)
print(" GENESIS RECALL R4-R8-R2 RESULT")
print("=" * 78)

print()
print("INPUT")
print(
    f"  R4-R2 SUBJECT failures       : "
    f"{len(subject_failures)}"
)

print()
print("EXACT PRODUCTION TRACE")
print(f"  successfully traced          : {ok_cases}/221")
print(
    f"  target raw rows missing      : "
    f"{counts['target_raw_not_found']}"
)
print(
    f"  missing query                : "
    f"{counts['missing_query']}"
)
print(
    f"  missing target identity      : "
    f"{counts['missing_target_identity']}"
)

print()
print("RAW RETRIEVAL METADATA")
print(
    f"  raw title populated          : "
    f"{counts['raw_title_populated']}"
)
print(
    f"  raw subject populated        : "
    f"{counts['raw_subject_populated']}"
)

print()
print("EVIDENCECANDIDATE METADATA")
print(
    f"  candidate title populated    : "
    f"{counts['candidate_title_populated']}"
)
print(
    f"  candidate subject populated  : "
    f"{counts['candidate_subject_populated']}"
)
print(
    f"  title preserved raw->candidate: "
    f"{counts['title_preserved']}"
)
print(
    f"  subject preserved raw->candidate: "
    f"{counts['subject_preserved']}"
)

print()
print("QUALIFICATION SCORE")
print(
    f"  subject score = 0            : "
    f"{counts['subject_score_zero']}"
)
print(
    f"  subject score > 0            : "
    f"{counts['subject_score_positive']}"
)

print()
print("R4-R2 COLUMN SEMANTICS")
print(
    f"  'subject' matches metadata   : "
    f"{counts['r4_subject_is_candidate_subject']}"
)
print(
    f"  'subject' matches score      : "
    f"{counts['r4_subject_is_subject_score']}"
)

print()
print("CLASSIFICATION")
print(
    f"  production field contract    : "
    f"{field_contract_class}"
)
print(
    f"  R4-R2 column semantics       : "
    f"{r4_column_semantics}"
)

print()
print("CERTIFICATION")
print(
    f"  exact 221 population         : "
    f"{len(subject_failures) == 221}"
)
print(
    f"  all 221 production traced    : "
    f"{ok_cases == 221}"
)
print(
    f"  R4-R8-R2 CERTIFIED           : "
    f"{certified}"
)

print()
print(f"JSON report : {REPORT}")
print(f"trace TSV   : {TRACE}")
print(f"semantic TSV: {SEMANTICS}")
print(f"source map  : {SOURCEMAP}")

print("=" * 78)

raise SystemExit(0 if certified else 1)
