from __future__ import annotations

import csv
import hashlib
import inspect
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT = Path("/media/abdullah/JARVISDATA/Projects/jarvis-ai")
OUTDIR = PROJECT / "artifacts/genesis_recall"

R4R2 = OUTDIR / "r4_r2_qualification_drop_detail.tsv"
R4R6_SAMPLE = OUTDIR / "r4_r6_token_divergence_sample.tsv"
R4R6_POP = OUTDIR / "r4_r6_token_divergence_population.tsv"

REPORT = OUTDIR / "r4_r6_r1_input_reconstruction_parity.json"
DETAIL = OUTDIR / "r4_r6_r1_input_reconstruction_parity.tsv"
RECON = OUTDIR / "r4_r6_r1_divergence_reconciliation.tsv"
SOURCE = OUTDIR / "r4_r6_r1_pipeline_contract.txt"

sys.path.insert(0, str(PROJECT))

from core.retrieval.qualification.lexical import (
    analyze_lexical,
    canonicalize_token,
    normalize_text,
    tokenize,
)

try:
    from core.retrieval.qualification.lexical import TOKEN_RE
except Exception:
    TOKEN_RE = None

try:
    from core.retrieval.qualification.lexical import STOP_WORDS
except Exception:
    STOP_WORDS = None

from core.retrieval.qualification.subject import analyze_subject


EXPECTED_SUBJECT_FAILURES = 221


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fields: list[str] = []
    seen: set[str] = set()

    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)

    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=fields,
            delimiter="\t",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def norm_key(value: Any) -> str:
    return str(value or "").strip().casefold()


def first(row: dict[str, str], *names: str) -> str:
    lowered = {str(k).casefold(): v for k, v in row.items()}

    for name in names:
        value = lowered.get(name.casefold())
        if value not in (None, ""):
            return str(value)

    return ""


def all_columns(rows: list[dict[str, str]]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for row in rows:
        for key in row:
            if key not in seen:
                result.append(key)
                seen.add(key)

    return result


def looks_subject_failure(row: dict[str, str]) -> bool:
    blob = " ".join(
        str(v or "")
        for v in row.values()
    ).casefold()

    return (
        "rejected_subject_mismatch" in blob
        or "subject 0.000 below" in blob
        or norm_key(first(
            row,
            "failure_class",
            "class",
            "failure",
        )) == "subject"
    )


def extract_query(row: dict[str, str]) -> str:
    return first(
        row,
        "query",
        "qualification_query",
        "search_query",
        "input_query",
        "derived_query",
    )


def extract_title(row: dict[str, str]) -> str:
    return first(
        row,
        "title",
        "candidate_title",
        "raw_title",
        "document_title",
    )


def extract_subject(row: dict[str, str]) -> str:
    return first(
        row,
        "subject",
        "candidate_subject",
        "raw_subject",
        "document_subject",
    )


def extract_source_path(row: dict[str, str]) -> str:
    return first(
        row,
        "source_path",
        "path",
        "candidate_source_path",
        "raw_source_path",
    )


def extract_excerpt(row: dict[str, str]) -> str:
    return first(
        row,
        "excerpt",
        "candidate_excerpt",
        "raw_excerpt",
        "text",
    )


def extract_id(row: dict[str, str]) -> str:
    return first(
        row,
        "document_id",
        "runtime_document_id",
        "target_id",
        "source_id",
        "id",
        "candidate_id",
    )


def reference_tokens(text: str) -> tuple[str, ...]:
    """
    Deliberately simple independent reference tokenizer.

    This is NOT a proposed production implementation.

    Its sole purpose is to determine whether ordinary
    alphanumeric components overlap when production exact
    token matching does not.
    """
    return tuple(
        token.casefold()
        for token in re.findall(r"[A-Za-z0-9]+", str(text or ""))
        if token
    )


def unique_overlap(a: tuple[str, ...], b: tuple[str, ...]) -> tuple[str, ...]:
    bset = set(b)
    return tuple(dict.fromkeys(x for x in a if x in bset))


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def row_signature(
    query: str,
    subject: str,
    title: str,
    source_path: str,
) -> str:
    blob = "\x1f".join(
        [
            query.strip(),
            subject.strip(),
            title.strip(),
            source_path.strip(),
        ]
    )
    return hashlib.sha256(blob.encode("utf-8", "replace")).hexdigest()


def reconcile_lookup(
    rows: list[dict[str, str]],
) -> tuple[
    dict[str, list[dict[str, str]]],
    dict[str, list[dict[str, str]]],
]:
    by_id: dict[str, list[dict[str, str]]] = {}
    by_query: dict[str, list[dict[str, str]]] = {}

    for row in rows:
        rid = norm_key(extract_id(row))
        query = norm_key(extract_query(row))

        if rid:
            by_id.setdefault(rid, []).append(row)

        if query:
            by_query.setdefault(query, []).append(row)

    return by_id, by_query


def select_comparison(
    row: dict[str, str],
    by_id: dict[str, list[dict[str, str]]],
    by_query: dict[str, list[dict[str, str]]],
) -> tuple[dict[str, str] | None, str, int]:
    rid = norm_key(extract_id(row))
    query = norm_key(extract_query(row))

    if rid and rid in by_id:
        choices = by_id[rid]
        if len(choices) == 1:
            return choices[0], "ID", 1

        if query:
            exact = [
                x for x in choices
                if norm_key(extract_query(x)) == query
            ]
            if len(exact) == 1:
                return exact[0], "ID+QUERY", 1

        return choices[0], "ID_AMBIGUOUS", len(choices)

    if query and query in by_query:
        choices = by_query[query]
        if len(choices) == 1:
            return choices[0], "QUERY", 1

        return choices[0], "QUERY_AMBIGUOUS", len(choices)

    return None, "NONE", 0


r4r2_all = read_tsv(R4R2)
r4r6_sample = read_tsv(R4R6_SAMPLE)
r4r6_population = read_tsv(R4R6_POP)

subject_rows = [
    row
    for row in r4r2_all
    if looks_subject_failure(row)
]

print("=" * 78)
print(" GENESIS RECALL R4-R6-R1")
print(" FULL-POPULATION INPUT RECONSTRUCTION PARITY")
print("=" * 78)

print()
print("INPUT ARTIFACTS")
print("  R4-R2 rows              :", len(r4r2_all))
print("  R4-R2 SUBJECT rows      :", len(subject_rows))
print("  R4-R6 sample rows       :", len(r4r6_sample))
print("  R4-R6 population rows   :", len(r4r6_population))

print()
print("R4-R2 COLUMNS")
for col in all_columns(r4r2_all):
    print(" ", col)

pop_by_id, pop_by_query = reconcile_lookup(r4r6_population)
sample_by_id, sample_by_query = reconcile_lookup(r4r6_sample)

detail_rows: list[dict[str, Any]] = []
reconciliation_rows: list[dict[str, Any]] = []

classification_counts: Counter[str] = Counter()
subject_score_zero = 0
production_overlap_positive = 0
reference_overlap_positive = 0
reference_positive_prod_zero = 0
no_reference_or_prod = 0
subject_pipeline_mismatch = 0
population_rows_matched = 0
population_rows_unmatched = 0
sample_rows_matched = 0
sample_rows_unmatched = 0
query_missing = 0
candidate_missing = 0

for index, row in enumerate(subject_rows, start=1):

    query = extract_query(row)
    title = extract_title(row)
    subject = extract_subject(row)
    source_path = extract_source_path(row)
    excerpt = extract_excerpt(row)
    rid = extract_id(row)

    if not query:
        query_missing += 1

    combined_subject = " ".join(
        x for x in (subject, title) if x
    )

    if not combined_subject:
        candidate_missing += 1

    q_prod = tokenize(query)
    subject_prod = tokenize(subject)
    title_prod = tokenize(title)
    combined_prod = tokenize(combined_subject)

    q_ref = reference_tokens(query)
    subject_ref = reference_tokens(subject)
    title_ref = reference_tokens(title)
    combined_ref = reference_tokens(combined_subject)

    prod_overlap = unique_overlap(q_prod, combined_prod)
    ref_overlap = unique_overlap(q_ref, combined_ref)

    lexical = analyze_lexical(query, combined_subject)
    subject_result = analyze_subject(
        query,
        subject,
        title,
    )

    lexical_score = float(lexical.score)
    subject_score = float(subject_result.score)

    if subject_score == 0.0:
        subject_score_zero += 1

    if prod_overlap:
        production_overlap_positive += 1

    if ref_overlap:
        reference_overlap_positive += 1

    if ref_overlap and not prod_overlap:
        reference_positive_prod_zero += 1

    if not ref_overlap and not prod_overlap:
        no_reference_or_prod += 1

    if abs(subject_score - lexical_score) > 1e-12:
        subject_pipeline_mismatch += 1

    if ref_overlap and not prod_overlap:
        divergence_class = "REFERENCE_OVERLAP_PRODUCTION_ZERO"
    elif prod_overlap:
        divergence_class = "PRODUCTION_EXACT_MATCH"
    else:
        divergence_class = "NO_REFERENCE_OR_PRODUCTION_MATCH"

    classification_counts[divergence_class] += 1

    pop_row, pop_match_method, pop_match_count = select_comparison(
        row,
        pop_by_id,
        pop_by_query,
    )

    if pop_row is None:
        population_rows_unmatched += 1
    else:
        population_rows_matched += 1

    sample_row, sample_match_method, sample_match_count = select_comparison(
        row,
        sample_by_id,
        sample_by_query,
    )

    if sample_row is None:
        sample_rows_unmatched += 1
    else:
        sample_rows_matched += 1

    existing_pop_class = ""
    existing_pop_ref = ""
    existing_pop_prod = ""

    if pop_row:
        existing_pop_class = first(
            pop_row,
            "divergence_class",
            "class",
            "root_cause_class",
        )
        existing_pop_ref = first(
            pop_row,
            "reference_matched",
            "reference_overlap",
            "ref_overlap",
            "reference_matched_tokens",
        )
        existing_pop_prod = first(
            pop_row,
            "production_matched",
            "production_overlap",
            "prod_overlap",
            "production_matched_tokens",
        )

    existing_sample_class = ""
    existing_sample_ref = ""
    existing_sample_prod = ""

    if sample_row:
        existing_sample_class = first(
            sample_row,
            "divergence_class",
            "classes",
            "class",
        )
        existing_sample_ref = first(
            sample_row,
            "reference_matched",
            "reference_overlap",
            "ref_overlap",
            "reference_matched_tokens",
        )
        existing_sample_prod = first(
            sample_row,
            "production_matched",
            "production_overlap",
            "prod_overlap",
            "production_matched_tokens",
        )

    detail_rows.append(
        {
            "ordinal": index,
            "document_id": rid,
            "query": query,
            "subject": subject,
            "title": title,
            "source_path": source_path,
            "excerpt_prefix": excerpt[:160],
            "input_signature": row_signature(
                query,
                subject,
                title,
                source_path,
            ),
            "normalized_query": normalize_text(query),
            "normalized_subject": normalize_text(subject),
            "normalized_title": normalize_text(title),
            "production_query_tokens": ",".join(q_prod),
            "production_subject_tokens": ",".join(subject_prod),
            "production_title_tokens": ",".join(title_prod),
            "production_combined_tokens": ",".join(combined_prod),
            "production_matched_tokens": ",".join(prod_overlap),
            "reference_query_tokens": ",".join(q_ref),
            "reference_subject_tokens": ",".join(subject_ref),
            "reference_title_tokens": ",".join(title_ref),
            "reference_combined_tokens": ",".join(combined_ref),
            "reference_matched_tokens": ",".join(ref_overlap),
            "lexical_score": lexical_score,
            "subject_score": subject_score,
            "subject_lexical_parity": (
                abs(subject_score - lexical_score) <= 1e-12
            ),
            "reconstructed_divergence_class": divergence_class,
            "r4r6_population_match_method": pop_match_method,
            "r4r6_population_match_count": pop_match_count,
            "r4r6_population_class": existing_pop_class,
            "r4r6_population_reference": existing_pop_ref,
            "r4r6_population_production": existing_pop_prod,
            "r4r6_sample_match_method": sample_match_method,
            "r4r6_sample_match_count": sample_match_count,
            "r4r6_sample_class": existing_sample_class,
            "r4r6_sample_reference": existing_sample_ref,
            "r4r6_sample_production": existing_sample_prod,
        }
    )

    if pop_row is not None:
        class_parity = (
            not existing_pop_class
            or norm_key(existing_pop_class) == norm_key(divergence_class)
        )

        ref_parity = (
            not existing_pop_ref
            or norm_key(existing_pop_ref)
            == norm_key(",".join(ref_overlap))
        )

        prod_parity = (
            not existing_pop_prod
            or norm_key(existing_pop_prod)
            == norm_key(",".join(prod_overlap))
        )

        reconciliation_rows.append(
            {
                "document_id": rid,
                "query": query,
                "comparison": "R4R6_POPULATION",
                "match_method": pop_match_method,
                "existing_class": existing_pop_class,
                "reconstructed_class": divergence_class,
                "existing_reference": existing_pop_ref,
                "reconstructed_reference": ",".join(ref_overlap),
                "existing_production": existing_pop_prod,
                "reconstructed_production": ",".join(prod_overlap),
                "class_parity": class_parity,
                "reference_parity": ref_parity,
                "production_parity": prod_parity,
            }
        )

    if sample_row is not None:
        reconciliation_rows.append(
            {
                "document_id": rid,
                "query": query,
                "comparison": "R4R6_SAMPLE",
                "match_method": sample_match_method,
                "existing_class": existing_sample_class,
                "reconstructed_class": divergence_class,
                "existing_reference": existing_sample_ref,
                "reconstructed_reference": ",".join(ref_overlap),
                "existing_production": existing_sample_prod,
                "reconstructed_production": ",".join(prod_overlap),
                "class_parity": (
                    not existing_sample_class
                    or norm_key(divergence_class)
                    in norm_key(existing_sample_class)
                ),
                "reference_parity": (
                    not existing_sample_ref
                    or norm_key(existing_sample_ref)
                    == norm_key(",".join(ref_overlap))
                ),
                "production_parity": (
                    not existing_sample_prod
                    or norm_key(existing_sample_prod)
                    == norm_key(",".join(prod_overlap))
                ),
            }
        )


write_tsv(DETAIL, detail_rows)
write_tsv(RECON, reconciliation_rows)


pop_recon = [
    r
    for r in reconciliation_rows
    if r["comparison"] == "R4R6_POPULATION"
]

sample_recon = [
    r
    for r in reconciliation_rows
    if r["comparison"] == "R4R6_SAMPLE"
]

pop_class_mismatch = sum(
    1 for r in pop_recon if not r["class_parity"]
)

pop_ref_mismatch = sum(
    1 for r in pop_recon if not r["reference_parity"]
)

pop_prod_mismatch = sum(
    1 for r in pop_recon if not r["production_parity"]
)

sample_ref_mismatch = sum(
    1 for r in sample_recon if not r["reference_parity"]
)

sample_prod_mismatch = sum(
    1 for r in sample_recon if not r["production_parity"]
)


if (
    reference_positive_prod_zero > 0
    and pop_ref_mismatch > 0
):
    reconciliation_result = (
        "R4R6_FULL_POPULATION_REFERENCE_RECONSTRUCTION_DEFECT"
    )
elif (
    reference_positive_prod_zero > 0
    and pop_ref_mismatch == 0
):
    reconciliation_result = (
        "TRUE_PRODUCTION_TOKEN_MATCH_DIVERGENCE"
    )
elif (
    reference_positive_prod_zero == 0
    and no_reference_or_prod == EXPECTED_SUBJECT_FAILURES
):
    reconciliation_result = (
        "NO_LEXICAL_OVERLAP_IN_RECONSTRUCTED_R4R2_INPUTS"
    )
else:
    reconciliation_result = (
        "MIXED_OR_UNRESOLVED"
    )


population_exact = (
    len(subject_rows) == EXPECTED_SUBJECT_FAILURES
)

pipeline_exact = (
    subject_pipeline_mismatch == 0
)

inputs_complete = (
    query_missing == 0
    and candidate_missing == 0
)

r4r6_population_join_complete = (
    population_rows_matched == EXPECTED_SUBJECT_FAILURES
)

reconciliation_complete = (
    population_exact
    and pipeline_exact
    and inputs_complete
    and r4r6_population_join_complete
)

diagnostic_certified = reconciliation_complete


report = {
    "stage": "Genesis Recall R4-R6-R1",
    "purpose": (
        "Full-population input reconstruction parity and "
        "R4-R6 divergence reconciliation"
    ),
    "input": {
        "r4_r2_rows": len(r4r2_all),
        "subject_failures": len(subject_rows),
        "r4_r6_sample_rows": len(r4r6_sample),
        "r4_r6_population_rows": len(r4r6_population),
    },
    "input_quality": {
        "query_missing": query_missing,
        "candidate_subject_title_missing": candidate_missing,
    },
    "production_pipeline": {
        "subject_score_zero": subject_score_zero,
        "subject_lexical_pipeline_mismatch": subject_pipeline_mismatch,
        "production_overlap_positive": production_overlap_positive,
        "reference_overlap_positive": reference_overlap_positive,
        "reference_positive_production_zero": (
            reference_positive_prod_zero
        ),
        "no_reference_or_production_match": no_reference_or_prod,
    },
    "reconstructed_classes": dict(classification_counts),
    "r4_r6_population_reconciliation": {
        "matched": population_rows_matched,
        "unmatched": population_rows_unmatched,
        "class_mismatches": pop_class_mismatch,
        "reference_mismatches": pop_ref_mismatch,
        "production_mismatches": pop_prod_mismatch,
    },
    "r4_r6_sample_reconciliation": {
        "matched": sample_rows_matched,
        "unmatched": sample_rows_unmatched,
        "reference_mismatches": sample_ref_mismatch,
        "production_mismatches": sample_prod_mismatch,
    },
    "reconciliation_result": reconciliation_result,
    "certification": {
        "exact_subject_population": population_exact,
        "production_subject_pipeline_parity": pipeline_exact,
        "input_reconstruction_complete": inputs_complete,
        "r4_r6_population_join_complete": (
            r4r6_population_join_complete
        ),
        "reconciliation_complete": reconciliation_complete,
        "diagnostic_certified": diagnostic_certified,
    },
}

REPORT.write_text(
    json.dumps(report, indent=2, sort_keys=True),
    encoding="utf-8",
)


with SOURCE.open("w", encoding="utf-8") as fh:
    fh.write("GENESIS RECALL R4-R6-R1 PIPELINE CONTRACT\n")
    fh.write("=" * 78 + "\n\n")

    fh.write("normalize_text\n")
    fh.write("-" * 78 + "\n")
    fh.write(inspect.getsource(normalize_text))
    fh.write("\n\n")

    fh.write("canonicalize_token\n")
    fh.write("-" * 78 + "\n")
    fh.write(inspect.getsource(canonicalize_token))
    fh.write("\n\n")

    fh.write("tokenize\n")
    fh.write("-" * 78 + "\n")
    fh.write(inspect.getsource(tokenize))
    fh.write("\n\n")

    fh.write("analyze_lexical\n")
    fh.write("-" * 78 + "\n")
    fh.write(inspect.getsource(analyze_lexical))
    fh.write("\n\n")

    fh.write("analyze_subject\n")
    fh.write("-" * 78 + "\n")
    fh.write(inspect.getsource(analyze_subject))
    fh.write("\n\n")

    fh.write(f"TOKEN_RE: {TOKEN_RE!r}\n")
    fh.write(
        "STOP_WORDS count: "
        f"{len(STOP_WORDS) if STOP_WORDS is not None else 'UNKNOWN'}\n"
    )


print()
print("=" * 78)
print(" GENESIS RECALL R4-R6-R1 RESULT")
print("=" * 78)

print()
print("POPULATION")
print("  R4-R2 SUBJECT failures       :", len(subject_rows))
print("  expected                     :", EXPECTED_SUBJECT_FAILURES)

print()
print("INPUT RECONSTRUCTION")
print("  missing queries              :", query_missing)
print("  missing subject/title        :", candidate_missing)

print()
print("PRODUCTION PIPELINE")
print(
    "  subject score = 0           :",
    subject_score_zero,
    f"/{len(subject_rows)}",
)
print(
    "  subject/lexical mismatches  :",
    subject_pipeline_mismatch,
)

print()
print("OVERLAP RECONSTRUCTION")
print(
    "  production overlap > 0      :",
    production_overlap_positive,
)
print(
    "  reference overlap > 0       :",
    reference_overlap_positive,
)
print(
    "  ref overlap + prod zero     :",
    reference_positive_prod_zero,
)
print(
    "  neither reference nor prod  :",
    no_reference_or_prod,
)

print()
print("RECONSTRUCTED CLASSES")
for key, value in sorted(classification_counts.items()):
    pct = (
        100.0 * value / len(subject_rows)
        if subject_rows
        else 0.0
    )
    print(f"  {key:<42} {value:>4} ({pct:6.2f}%)")

print()
print("R4-R6 POPULATION RECONCILIATION")
print("  matched                     :", population_rows_matched)
print("  unmatched                   :", population_rows_unmatched)
print("  class mismatches            :", pop_class_mismatch)
print("  reference mismatches        :", pop_ref_mismatch)
print("  production mismatches       :", pop_prod_mismatch)

print()
print("R4-R6 SAMPLE RECONCILIATION")
print("  matched                     :", sample_rows_matched)
print("  unmatched                   :", sample_rows_unmatched)
print("  reference mismatches        :", sample_ref_mismatch)
print("  production mismatches       :", sample_prod_mismatch)

print()
print("RECONCILIATION RESULT")
print(" ", reconciliation_result)

print()
print("CERTIFICATION")
print("  exact SUBJECT population    :", population_exact)
print("  production pipeline parity  :", pipeline_exact)
print("  input reconstruction        :", inputs_complete)
print(
    "  population join complete   :",
    r4r6_population_join_complete,
)
print("  reconciliation complete     :", reconciliation_complete)

print()
print(
    "R4-R6-R1 DIAGNOSTIC CERTIFIED:",
    diagnostic_certified,
)

print()
print("JSON report :", REPORT)
print("detail TSV  :", DETAIL)
print("reconcile   :", RECON)
print("source map  :", SOURCE)

print("=" * 78)

raise SystemExit(0 if diagnostic_certified else 1)
