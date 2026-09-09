from __future__ import annotations

import csv
import inspect
import json
import math
import re
import sqlite3
import statistics
import sys
import time

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

OUTDIR = PROJECT / "artifacts/genesis_recall"

R3 = OUTDIR / "r3_production_recall_census.tsv"

R6_DETAIL = (
    OUTDIR
    / "r4_r10_r6_exact_fts_match_truth.tsv"
)

REPORT = (
    OUTDIR
    / "r4_r10_r7_shadow_ranker.json"
)

R3_TRACE = (
    OUTDIR
    / "r4_r10_r7_r3_250_recall.tsv"
)

R6_TRACE = (
    OUTDIR
    / "r4_r10_r7_r6_canary_ranks.tsv"
)

CANARY_TRACE = (
    OUTDIR
    / "r4_r10_r7_identity_canaries.tsv"
)

SEMANTIC_TRACE = (
    OUTDIR
    / "r4_r10_r7_semantic_regression.tsv"
)

ADVERSARIAL_TRACE = (
    OUTDIR
    / "r4_r10_r7_adversarial_precision.tsv"
)

FEATURE_TRACE = (
    OUTDIR
    / "r4_r10_r7_feature_trace.tsv"
)

TRACE = (
    OUTDIR
    / "r4_r10_r7_shadow_trace.txt"
)

SOURCE_MAP = (
    OUTDIR
    / "r4_r10_r7_shadow_ranker_source.txt"
)


POOL_LIMIT = 12000
TOP_K = 20

EXPECTED_R3 = 250
EXPECTED_R6 = 9


sys.path.insert(
    0,
    str(PROJECT),
)


from core.knowledge_catalog.materialization.search import (
    _fts_query,
    search_runtime_knowledge,
)


# ============================================================
# CONSTANTS
# ============================================================

FILE_NOISE = {
    "html",
    "htm",
    "pdf",
    "txt",
    "doc",
    "docx",
    "xml",
    "json",
    "csv",
}

GENERIC_QUERY_NOISE = {
    "file",
    "document",
    "page",
    "chapter",
}


IDENTITY_CANARIES = (
    (
        "cpp",
        "C++ Programming",
        4,
    ),
    (
        "effective_c",
        "Effective C",
        14,
    ),
    (
        "ai_assisted_python",
        "AI assisted Python",
        11,
    ),
    (
        "lane",
        "Lane lexicon",
        86876,
    ),
)


SEMANTIC_CONTROLS = (
    "civil defense manual",
    "US Army survival manual",
    "practical electronics handbook",
    "Marx mathematical manuscripts",
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
# IO
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


# ============================================================
# BASIC HELPERS
# ============================================================

def text(
    value: Any,
) -> str:

    if value is None:
        return ""

    return str(value).strip()


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

        value = row.get(actual)

        if value not in (
            None,
            "",
        ):
            return text(value)

    return ""


def r3_query(
    row: Mapping[str, Any],
) -> str:

    return first_present(
        row,
        "query",
        "search_query",
        "qualification_query",
        "input_query",
        "derived_query",
    )


def r3_target_id(
    row: Mapping[str, Any],
) -> int | None:

    value = first_present(
        row,
        "document_id",
        "runtime_document_id",
        "target_document_id",
        "target_id",
        "doc_id",
        "id",
    )

    if not value:
        return None

    try:
        return int(value)
    except Exception:
        return None


# ============================================================
# TOKENIZATION
# ============================================================

def boundary_tokens(
    value: str,
) -> tuple[str, ...]:

    return tuple(
        token.casefold()
        for token in re.findall(
            r"[A-Za-z0-9]{2,}",
            str(value or ""),
        )
    )


def production_terms(
    query: str,
) -> tuple[str, ...]:

    expression = _fts_query(
        query
    )

    return tuple(
        term.casefold()
        for term in re.findall(
            r'"([^"]+)"',
            expression or "",
        )
    )


def substantive_terms(
    query: str,
) -> tuple[str, ...]:

    raw = production_terms(
        query
    )

    result = []
    seen = set()

    for token in raw:

        if token in FILE_NOISE:
            continue

        if token in GENERIC_QUERY_NOISE:
            continue

        if token in seen:
            continue

        seen.add(token)
        result.append(token)

    # Never create a query with zero evidence merely because
    # every production term happened to look generic.
    if not result:

        for token in raw:

            if token not in seen:
                seen.add(token)
                result.append(token)

    return tuple(result)


# ============================================================
# CANDIDATE FEATURE MODEL
# ============================================================

@dataclass(frozen=True)
class ShadowCandidate:

    row: Mapping[str, Any]

    production_rank: int

    document_id: int

    chunk_id: int

    query_terms: tuple[str, ...]

    matched_terms: tuple[str, ...]

    coverage: float

    rarity_coverage: float

    title_coverage: float

    numeric_identity: float

    bm25_position: float

    shadow_score: float


def token_set_for_candidate(
    row: Mapping[str, Any],
) -> set[str]:

    blob = " ".join(
        (
            text(
                row.get(
                    "title"
                )
            ),
            text(
                row.get(
                    "subject"
                )
            ),
            text(
                row.get(
                    "excerpt"
                )
            ),
            text(
                row.get(
                    "chunk_text"
                )
            ),
            text(
                row.get(
                    "source_path"
                )
            ),
            text(
                row.get(
                    "file_path"
                )
            ),
        )
    )

    return set(
        boundary_tokens(
            blob
        )
    )


def title_token_set(
    row: Mapping[str, Any],
) -> set[str]:

    blob = " ".join(
        (
            text(
                row.get(
                    "title"
                )
            ),
            text(
                row.get(
                    "subject"
                )
            ),
        )
    )

    return set(
        boundary_tokens(
            blob
        )
    )


def shadow_rank(
    query: str,
    rows: list[Mapping[str, Any]],
) -> list[ShadowCandidate]:

    qterms = substantive_terms(
        query
    )

    if not qterms:
        return []


    candidate_token_sets = [
        token_set_for_candidate(
            row
        )
        for row in rows
    ]


    # --------------------------------------------------------
    # Query-local rarity.
    #
    # This deliberately avoids new global index state.
    # A term appearing in nearly every candidate receives
    # little weight; a selective term receives much more.
    # --------------------------------------------------------

    document_frequency = {
        term:
            sum(
                1
                for tokens in candidate_token_sets
                if term in tokens
            )
        for term in qterms
    }


    total_candidates = max(
        1,
        len(rows),
    )


    rarity_weights = {
        term:
            1.0
            + math.log(
                (
                    total_candidates
                    + 1.0
                )
                /
                (
                    document_frequency[
                        term
                    ]
                    + 1.0
                )
            )
        for term in qterms
    }


    rarity_denominator = sum(
        rarity_weights.values()
    ) or 1.0


    numeric_terms = tuple(
        term
        for term in qterms
        if term.isdigit()
    )


    ranked = []


    for ordinal, (
        row,
        tokens,
    ) in enumerate(
        zip(
            rows,
            candidate_token_sets,
        ),
        start=1,
    ):

        title_tokens = title_token_set(
            row
        )


        matched = tuple(
            term
            for term in qterms
            if term in tokens
        )


        coverage = (
            len(
                matched
            )
            /
            len(
                qterms
            )
        )


        rarity_coverage = (
            sum(
                rarity_weights[
                    term
                ]
                for term in matched
            )
            /
            rarity_denominator
        )


        title_matched = tuple(
            term
            for term in qterms
            if term in title_tokens
        )


        title_coverage = (
            len(
                title_matched
            )
            /
            len(
                qterms
            )
        )


        if numeric_terms:

            numeric_identity = (
                sum(
                    1
                    for term in numeric_terms
                    if term in title_tokens
                )
                /
                len(
                    numeric_terms
                )
            )

        else:

            numeric_identity = 0.0


        # Existing BM25 order contributes only weakly.
        if len(rows) <= 1:

            bm25_position = 1.0

        else:

            bm25_position = (
                1.0
                -
                (
                    ordinal
                    - 1
                )
                /
                (
                    len(rows)
                    - 1
                )
            )


        # ----------------------------------------------------
        # Deterministic shadow score.
        #
        # Coverage and rarity dominate.
        # Title identity is strong.
        # Numeric identity is useful but bounded.
        # Existing BM25 position is deliberately weak.
        # ----------------------------------------------------

        shadow_score = (
            0.40
            * coverage

            + 0.27
            * rarity_coverage

            + 0.23
            * title_coverage

            + 0.07
            * numeric_identity

            + 0.03
            * bm25_position
        )


        ranked.append(
            ShadowCandidate(
                row=row,

                production_rank=ordinal,

                document_id=int(
                    row[
                        "document_id"
                    ]
                ),

                chunk_id=int(
                    row[
                        "chunk_id"
                    ]
                ),

                query_terms=qterms,

                matched_terms=matched,

                coverage=coverage,

                rarity_coverage=rarity_coverage,

                title_coverage=title_coverage,

                numeric_identity=numeric_identity,

                bm25_position=bm25_position,

                shadow_score=shadow_score,
            )
        )


    ranked.sort(
        key=lambda item: (
            -item.shadow_score,
            -item.coverage,
            -item.rarity_coverage,
            -item.title_coverage,
            -item.numeric_identity,
            item.production_rank,
            item.document_id,
            item.chunk_id,
        )
    )


    return ranked


# ============================================================
# DOCUMENT-LEVEL COLLAPSE
# ============================================================
#
# Runtime search returns chunks. R3 certifies document recall.
# Keep the highest-ranked chunk for each document.
# ============================================================

def document_ranked(
    ranked: list[ShadowCandidate],
) -> list[ShadowCandidate]:

    seen = set()
    result = []

    for item in ranked:

        if item.document_id in seen:
            continue

        seen.add(
            item.document_id
        )

        result.append(
            item
        )

    return result


def production_document_rank(
    rows: list[Mapping[str, Any]],
    target_document_id: int,
) -> int | None:

    seen = set()
    doc_rank = 0

    for row in rows:

        document_id = int(
            row[
                "document_id"
            ]
        )

        if document_id in seen:
            continue

        seen.add(
            document_id
        )

        doc_rank += 1

        if document_id == target_document_id:
            return doc_rank

    return None


def shadow_document_rank(
    ranked: list[ShadowCandidate],
    target_document_id: int,
) -> int | None:

    for rank, item in enumerate(
        document_ranked(
            ranked
        ),
        start=1,
    ):

        if item.document_id == target_document_id:
            return rank

    return None


def target_feature(
    ranked: list[ShadowCandidate],
    target_document_id: int,
) -> ShadowCandidate | None:

    target_items = [
        item
        for item in ranked
        if item.document_id
        == target_document_id
    ]

    if not target_items:
        return None

    return min(
        target_items,
        key=lambda item:
            (
                -item.shadow_score,
                item.production_rank,
            )
    )


# ============================================================
# SHADOW ACCEPTANCE FOR ADVERSARIAL PRECISION
# ============================================================

def shadow_accepts(
    ranked: list[ShadowCandidate],
) -> bool:

    if not ranked:
        return False

    best = ranked[
        0
    ]

    return (
        best.coverage
        >= 0.50

        and
        best.shadow_score
        >= 0.55

        and
        (
            best.title_coverage
            >= 0.50

            or
            best.rarity_coverage
            >= 0.70
        )
    )


# ============================================================
# READ-ONLY DATABASE
# ============================================================

conn = sqlite3.connect(
    f"file:{DB}?mode=ro",
    uri=True,
)

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
# EXACT R3 POPULATION
# ============================================================

r3_rows = read_tsv(
    R3
)

if len(
    r3_rows
) != EXPECTED_R3:

    raise RuntimeError(
        f"expected 250 R3 rows, got {len(r3_rows)}"
    )


r3_trace = []
feature_rows = []

r3_resolved = 0
r3_unresolved = 0

production_top20 = 0
shadow_top20 = 0

production_top100 = 0
shadow_top100 = 0

shadow_top1 = 0

improved = 0
unchanged = 0
regressed = 0

production_ranks = []
shadow_ranks = []


started = time.time()


for case, source in enumerate(
    r3_rows,
    start=1,
):

    query = r3_query(
        source
    )

    target_id = r3_target_id(
        source
    )


    if not query or target_id is None:

        r3_unresolved += 1

        r3_trace.append(
            {
                "case":
                    case,

                "query":
                    query,

                "target_document_id":
                    target_id
                    if target_id
                    is not None
                    else "",

                "status":
                    "R3_INPUT_UNRESOLVED",
            }
        )

        continue


    raw_rows = list(
        search_runtime_knowledge(
            query,
            db_path=DB,
            limit=POOL_LIMIT,
        )
    )


    production_rank = production_document_rank(
        raw_rows,
        target_id,
    )


    ranked = shadow_rank(
        query,
        raw_rows,
    )


    shadow_rank_value = shadow_document_rank(
        ranked,
        target_id,
    )


    feature = target_feature(
        ranked,
        target_id,
    )


    if production_rank is None:

        r3_unresolved += 1

        status = (
            "TARGET_OUTSIDE_SHADOW_POOL"
        )

    else:

        r3_resolved += 1

        status = "OK"

        production_ranks.append(
            production_rank
        )


        if shadow_rank_value is not None:

            shadow_ranks.append(
                shadow_rank_value
            )


        if production_rank <= 20:
            production_top20 += 1

        if production_rank <= 100:
            production_top100 += 1


        if (
            shadow_rank_value
            is not None
            and
            shadow_rank_value <= 20
        ):
            shadow_top20 += 1


        if (
            shadow_rank_value
            is not None
            and
            shadow_rank_value <= 100
        ):
            shadow_top100 += 1


        if shadow_rank_value == 1:
            shadow_top1 += 1


        if shadow_rank_value is not None:

            if shadow_rank_value < production_rank:
                improved += 1

            elif shadow_rank_value == production_rank:
                unchanged += 1

            else:
                regressed += 1


    r3_trace.append(
        {
            "case":
                case,

            "query":
                query,

            "target_document_id":
                target_id,

            "candidate_chunks":
                len(
                    raw_rows
                ),

            "production_document_rank":
                production_rank
                if production_rank
                is not None
                else "",

            "shadow_document_rank":
                shadow_rank_value
                if shadow_rank_value
                is not None
                else "",

            "rank_delta":
                (
                    production_rank
                    - shadow_rank_value
                    if production_rank
                    is not None
                    and
                    shadow_rank_value
                    is not None
                    else ""
                ),

            "status":
                status,
        }
    )


    if feature is not None:

        feature_rows.append(
            {
                "population":
                    "R3",

                "case":
                    case,

                "query":
                    query,

                "document_id":
                    target_id,

                "production_chunk_rank":
                    feature.production_rank,

                "query_terms":
                    ",".join(
                        feature.query_terms
                    ),

                "matched_terms":
                    ",".join(
                        feature.matched_terms
                    ),

                "coverage":
                    feature.coverage,

                "rarity_coverage":
                    feature.rarity_coverage,

                "title_coverage":
                    feature.title_coverage,

                "numeric_identity":
                    feature.numeric_identity,

                "bm25_position":
                    feature.bm25_position,

                "shadow_score":
                    feature.shadow_score,

                "shadow_document_rank":
                    shadow_rank_value
                    if shadow_rank_value
                    is not None
                    else "",
            }
        )


# ============================================================
# R6 HARD CANARIES
# ============================================================

r6_rows = read_tsv(
    R6_DETAIL
)

if len(
    r6_rows
) != EXPECTED_R6:

    raise RuntimeError(
        f"expected 9 R6 canaries, got {len(r6_rows)}"
    )


r6_trace = []

r6_top20 = 0
r6_top10 = 0
r6_top1 = 0


for case, row in enumerate(
    r6_rows,
    start=1,
):

    query = row[
        "query"
    ]

    target_id = int(
        row[
            "document_id"
        ]
    )

    certified_production_rank = int(
        row[
            "production_target_best_rank"
        ]
    )


    raw_rows = list(
        search_runtime_knowledge(
            query,
            db_path=DB,
            limit=POOL_LIMIT,
        )
    )


    production_rank = production_document_rank(
        raw_rows,
        target_id,
    )


    ranked = shadow_rank(
        query,
        raw_rows,
    )


    shadow_rank_value = shadow_document_rank(
        ranked,
        target_id,
    )


    feature = target_feature(
        ranked,
        target_id,
    )


    if (
        shadow_rank_value
        is not None
        and
        shadow_rank_value <= 20
    ):
        r6_top20 += 1


    if (
        shadow_rank_value
        is not None
        and
        shadow_rank_value <= 10
    ):
        r6_top10 += 1


    if shadow_rank_value == 1:
        r6_top1 += 1


    r6_trace.append(
        {
            "case":
                case,

            "document_id":
                target_id,

            "query":
                query,

            "certified_r6_chunk_rank":
                certified_production_rank,

            "production_document_rank":
                production_rank
                if production_rank
                is not None
                else "",

            "shadow_document_rank":
                shadow_rank_value
                if shadow_rank_value
                is not None
                else "",

            "coverage":
                feature.coverage
                if feature
                else "",

            "rarity_coverage":
                feature.rarity_coverage
                if feature
                else "",

            "title_coverage":
                feature.title_coverage
                if feature
                else "",

            "numeric_identity":
                feature.numeric_identity
                if feature
                else "",

            "shadow_score":
                feature.shadow_score
                if feature
                else "",

            "PASS_TOP20":
                (
                    shadow_rank_value
                    is not None
                    and
                    shadow_rank_value <= 20
                ),
        }
    )


# ============================================================
# IDENTITY CANARIES
# ============================================================

canary_rows = []

canaries_resolved = 0
canaries_top20 = 0
canary_regressions = 0


for name, query, target_id in IDENTITY_CANARIES:

    raw_rows = list(
        search_runtime_knowledge(
            query,
            db_path=DB,
            limit=POOL_LIMIT,
        )
    )


    production_rank = production_document_rank(
        raw_rows,
        target_id,
    )


    ranked = shadow_rank(
        query,
        raw_rows,
    )


    shadow_rank_value = shadow_document_rank(
        ranked,
        target_id,
    )


    if production_rank is not None:

        canaries_resolved += 1


    if (
        shadow_rank_value
        is not None
        and
        shadow_rank_value <= TOP_K
    ):

        canaries_top20 += 1


    regression = (
        production_rank
        is not None
        and
        shadow_rank_value
        is not None
        and
        shadow_rank_value
        > max(
            production_rank,
            TOP_K,
        )
    )


    if regression:
        canary_regressions += 1


    canary_rows.append(
        {
            "name":
                name,

            "query":
                query,

            "target_document_id":
                target_id,

            "production_document_rank":
                production_rank
                if production_rank
                is not None
                else "",

            "shadow_document_rank":
                shadow_rank_value
                if shadow_rank_value
                is not None
                else "",

            "regression":
                regression,
        }
    )


# ============================================================
# SEMANTIC REGRESSION
# ============================================================

semantic_rows = []

semantic_controls_pass = 0


for query in SEMANTIC_CONTROLS:

    raw_rows = list(
        search_runtime_knowledge(
            query,
            db_path=DB,
            limit=POOL_LIMIT,
        )
    )


    if not raw_rows:

        semantic_rows.append(
            {
                "query":
                    query,

                "production_results":
                    0,

                "production_top_document":
                    "",

                "production_top_in_shadow_top20":
                    False,
            }
        )

        continue


    production_top_document = int(
        raw_rows[
            0
        ][
            "document_id"
        ]
    )


    ranked = document_ranked(
        shadow_rank(
            query,
            raw_rows,
        )
    )


    top20_documents = {
        item.document_id
        for item in ranked[
            :20
        ]
    }


    preserved = (
        production_top_document
        in top20_documents
    )


    if preserved:
        semantic_controls_pass += 1


    semantic_rows.append(
        {
            "query":
                query,

            "production_results":
                len(
                    raw_rows
                ),

            "production_top_document":
                production_top_document,

            "production_top_in_shadow_top20":
                preserved,
        }
    )


# ============================================================
# ADVERSARIAL PRECISION
# ============================================================

adversarial_rows = []

adversarial_accepts = 0


for query in ADVERSARIAL:

    raw_rows = list(
        search_runtime_knowledge(
            query,
            db_path=DB,
            limit=POOL_LIMIT,
        )
    )


    ranked = shadow_rank(
        query,
        raw_rows,
    )


    accepted = shadow_accepts(
        ranked
    )


    if accepted:
        adversarial_accepts += 1


    best = (
        ranked[
            0
        ]
        if ranked
        else None
    )


    adversarial_rows.append(
        {
            "query":
                query,

            "candidate_chunks":
                len(
                    raw_rows
                ),

            "shadow_accept":
                accepted,

            "best_document":
                best.document_id
                if best
                else "",

            "best_score":
                best.shadow_score
                if best
                else "",

            "best_coverage":
                best.coverage
                if best
                else "",

            "best_rarity_coverage":
                best.rarity_coverage
                if best
                else "",

            "best_title_coverage":
                best.title_coverage
                if best
                else "",
        }
    )


# ============================================================
# SUMMARY STATISTICS
# ============================================================

def safe_median(
    values: list[int],
) -> float | None:

    if not values:
        return None

    return float(
        statistics.median(
            values
        )
    )


production_median = safe_median(
    production_ranks
)

shadow_median = safe_median(
    shadow_ranks
)


# ============================================================
# CERTIFICATION GATES
# ============================================================

exact_r3_population = (
    len(
        r3_rows
    )
    == EXPECTED_R3
)


r3_pool_complete = (
    r3_resolved
    == EXPECTED_R3
    and
    r3_unresolved == 0
)


r6_hard_canaries = (
    r6_top20
    == EXPECTED_R6
)


r3_top100_complete = (
    shadow_top100
    == EXPECTED_R3
)


# Strong but not absurdly brittle:
# require at least 98% of exact R3 targets in top 20.
r3_top20_gate = (
    shadow_top20
    >= 245
)


median_improved = (
    production_median
    is not None
    and
    shadow_median
    is not None
    and
    shadow_median
    <= production_median
)


identity_canaries_pass = (
    canaries_resolved
    == len(
        IDENTITY_CANARIES
    )
    and
    canaries_top20
    == len(
        IDENTITY_CANARIES
    )
    and
    canary_regressions == 0
)


semantic_regression_pass = (
    semantic_controls_pass
    == len(
        SEMANTIC_CONTROLS
    )
)


adversarial_precision_pass = (
    adversarial_accepts
    == 0
)


certification = {
    "exact_r3_population":
        exact_r3_population,

    "r3_candidate_pool_complete":
        r3_pool_complete,

    "r6_nine_targets_top20":
        r6_hard_canaries,

    "r3_250_targets_top100":
        r3_top100_complete,

    "r3_at_least_245_top20":
        r3_top20_gate,

    "median_rank_improved_or_equal":
        median_improved,

    "identity_canaries_pass":
        identity_canaries_pass,

    "semantic_controls_pass":
        semantic_regression_pass,

    "adversarial_precision_pass":
        adversarial_precision_pass,

    "database_integrity":
        integrity == "ok",
}


shadow_certified = all(
    certification.values()
)


elapsed = (
    time.time()
    - started
)


report = {
    "phase":
        "Genesis Recall R4-R10-R7",

    "shadow_ranker": {
        "candidate_generator":
            "production search_runtime_knowledge",

        "pool_limit":
            POOL_LIMIT,

        "weights": {
            "coverage":
                0.40,

            "rarity_coverage":
                0.27,

            "title_coverage":
                0.23,

            "numeric_identity":
                0.07,

            "bm25_position":
                0.03,
        },

        "document_collapse":
            "best-ranked chunk per document",
    },

    "r3": {
        "population":
            len(
                r3_rows
            ),

        "resolved":
            r3_resolved,

        "unresolved":
            r3_unresolved,

        "production_top20":
            production_top20,

        "shadow_top20":
            shadow_top20,

        "production_top100":
            production_top100,

        "shadow_top100":
            shadow_top100,

        "shadow_top1":
            shadow_top1,

        "improved":
            improved,

        "unchanged":
            unchanged,

        "regressed":
            regressed,

        "production_median_rank":
            production_median,

        "shadow_median_rank":
            shadow_median,
    },

    "r6_canaries": {
        "population":
            EXPECTED_R6,

        "top20":
            r6_top20,

        "top10":
            r6_top10,

        "top1":
            r6_top1,
    },

    "identity_canaries": {
        "population":
            len(
                IDENTITY_CANARIES
            ),

        "resolved":
            canaries_resolved,

        "top20":
            canaries_top20,

        "regressions":
            canary_regressions,
    },

    "semantic_controls": {
        "population":
            len(
                SEMANTIC_CONTROLS
            ),

        "preserved":
            semantic_controls_pass,
    },

    "adversarial": {
        "population":
            len(
                ADVERSARIAL
            ),

        "accepted":
            adversarial_accepts,
    },

    "certification":
        certification,

    "shadow_certified":
        shadow_certified,

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
    R3_TRACE,
    r3_trace,
)

write_tsv(
    R6_TRACE,
    r6_trace,
)

write_tsv(
    CANARY_TRACE,
    canary_rows,
)

write_tsv(
    SEMANTIC_TRACE,
    semantic_rows,
)

write_tsv(
    ADVERSARIAL_TRACE,
    adversarial_rows,
)

write_tsv(
    FEATURE_TRACE,
    feature_rows,
)


# ============================================================
# HUMAN TRACE
# ============================================================

trace_lines = [
    "=" * 78,
    " GENESIS RECALL R4-R10-R7",
    " COVERAGE-AWARE SHADOW RANKER",
    "=" * 78,
    "",
    "R3",
    f"  population             : {len(r3_rows)}",
    f"  resolved               : {r3_resolved}",
    f"  unresolved             : {r3_unresolved}",
    f"  production top20       : {production_top20}",
    f"  shadow top20           : {shadow_top20}",
    f"  production top100      : {production_top100}",
    f"  shadow top100          : {shadow_top100}",
    f"  shadow top1            : {shadow_top1}",
    f"  improved               : {improved}",
    f"  unchanged              : {unchanged}",
    f"  regressed              : {regressed}",
    f"  production median rank : {production_median}",
    f"  shadow median rank     : {shadow_median}",
    "",
    "R6 HARD CANARIES",
    f"  top20                  : {r6_top20}/9",
    f"  top10                  : {r6_top10}/9",
    f"  top1                   : {r6_top1}/9",
    "",
    "IDENTITY CANARIES",
    f"  resolved               : {canaries_resolved}/4",
    f"  top20                  : {canaries_top20}/4",
    f"  regressions            : {canary_regressions}",
    "",
    "SEMANTIC CONTROLS",
    f"  preserved              : {semantic_controls_pass}/4",
    "",
    "ADVERSARIAL",
    f"  accepted               : {adversarial_accepts}/10",
    "",
    "CERTIFICATION",
]


for key, value in certification.items():

    trace_lines.append(
        f"  {key:<38}: {value}"
    )


trace_lines.extend(
    (
        "",
        f"R4-R10-R7 SHADOW CERTIFIED : {shadow_certified}",
    )
)


TRACE.write_text(
    "\n".join(
        trace_lines
    )
    + "\n",
    encoding="utf-8",
)


SOURCE_MAP.write_text(
    "\n".join(
        (
            "=" * 78,
            " GENESIS RECALL R4-R10-R7",
            " SHADOW RANKER SOURCE CONTRACT",
            "=" * 78,
            "",
            "substantive_terms",
            "-" * 78,
            inspect.getsource(
                substantive_terms
            ),
            "",
            "shadow_rank",
            "-" * 78,
            inspect.getsource(
                shadow_rank
            ),
            "",
            "document_ranked",
            "-" * 78,
            inspect.getsource(
                document_ranked
            ),
            "",
            "shadow_accepts",
            "-" * 78,
            inspect.getsource(
                shadow_accepts
            ),
        )
    )
    + "\n",
    encoding="utf-8",
)


conn.close()


# ============================================================
# CONSOLE RESULT
# ============================================================

print("=" * 78)
print(" GENESIS RECALL R4-R10-R7 RESULT")
print("=" * 78)

print()
print("EXACT R3 250-DOCUMENT CENSUS")

print(
    "  population                 :",
    len(
        r3_rows
    ),
)

print(
    "  candidate-pool resolved    :",
    r3_resolved,
)

print(
    "  candidate-pool unresolved  :",
    r3_unresolved,
)

print()
print("PRODUCTION VS SHADOW")

print(
    "  production top 20          :",
    production_top20,
)

print(
    "  shadow top 20              :",
    shadow_top20,
)

print(
    "  production top 100         :",
    production_top100,
)

print(
    "  shadow top 100             :",
    shadow_top100,
)

print(
    "  shadow rank 1              :",
    shadow_top1,
)

print(
    "  improved                   :",
    improved,
)

print(
    "  unchanged                  :",
    unchanged,
)

print(
    "  regressed                  :",
    regressed,
)

print(
    "  production median rank     :",
    production_median,
)

print(
    "  shadow median rank         :",
    shadow_median,
)

print()
print("R6 NINE HARD CANARIES")

print(
    "  top 20                     :",
    f"{r6_top20}/9",
)

print(
    "  top 10                     :",
    f"{r6_top10}/9",
)

print(
    "  rank 1                     :",
    f"{r6_top1}/9",
)

print()
print("IDENTITY CANARIES")

print(
    "  resolved                   :",
    f"{canaries_resolved}/4",
)

print(
    "  top 20                     :",
    f"{canaries_top20}/4",
)

print(
    "  regressions                :",
    canary_regressions,
)

print()
print("SEMANTIC CONTROLS")

print(
    "  preserved                  :",
    f"{semantic_controls_pass}/4",
)

print()
print("ADVERSARIAL PRECISION")

print(
    "  accepted                   :",
    f"{adversarial_accepts}/10",
)

print()
print("CERTIFICATION")

for key, value in certification.items():

    print(
        f"  {key:<38}: {value}"
    )

print()
print(
    "R4-R10-R7 SHADOW CERTIFIED :",
    shadow_certified,
)

print()
print("Artifacts:")
print(" ", REPORT)
print(" ", R3_TRACE)
print(" ", R6_TRACE)
print(" ", CANARY_TRACE)
print(" ", SEMANTIC_TRACE)
print(" ", ADVERSARIAL_TRACE)
print(" ", FEATURE_TRACE)
print(" ", TRACE)
print(" ", SOURCE_MAP)

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
    if shadow_certified
    else 1
)
