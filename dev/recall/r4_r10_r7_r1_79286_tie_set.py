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

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

OUTDIR = PROJECT / "artifacts/genesis_recall"

R3 = OUTDIR / "r3_production_recall_census.tsv"

R7_R6 = (
    OUTDIR
    / "r4_r10_r7_r6_canary_ranks.tsv"
)

REPORT = (
    OUTDIR
    / "r4_r10_r7_r1_79286_tie_set.json"
)

TIESET = (
    OUTDIR
    / "r4_r10_r7_r1_79286_tie_set.tsv"
)

R6_TRACE = (
    OUTDIR
    / "r4_r10_r7_r1_r6_canaries.tsv"
)

R3_TRACE = (
    OUTDIR
    / "r4_r10_r7_r1_r3_250_recall.tsv"
)

CANARY_TRACE = (
    OUTDIR
    / "r4_r10_r7_r1_identity_canaries.tsv"
)

SEMANTIC_TRACE = (
    OUTDIR
    / "r4_r10_r7_r1_semantic_controls.tsv"
)

ADVERSARIAL_TRACE = (
    OUTDIR
    / "r4_r10_r7_r1_adversarial.tsv"
)

FEATURE_TRACE = (
    OUTDIR
    / "r4_r10_r7_r1_title_identity_features.tsv"
)

TRACE = (
    OUTDIR
    / "r4_r10_r7_r1_trace.txt"
)

SOURCE_MAP = (
    OUTDIR
    / "r4_r10_r7_r1_source_contract.txt"
)


POOL_LIMIT = 12000
TOP_K = 20

TARGET_79286 = 79286
TARGET_QUERY = "2008 11 1 html"


sys.path.insert(
    0,
    str(PROJECT),
)


from core.knowledge_catalog.materialization.search import (
    _fts_query,
    search_runtime_knowledge,
)


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

            if key in seen:
                continue

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
        str(k).casefold():
            k
        for k in row.keys()
    }

    for name in names:

        actual = lowered.get(
            name.casefold()
        )

        if actual is None:
            continue

        value = row.get(
            actual
        )

        if value not in (
            None,
            "",
        ):
            return text(
                value
            )

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


def r3_target(
    row: Mapping[str, Any],
) -> int | None:

    raw = first_present(
        row,
        "document_id",
        "runtime_document_id",
        "target_document_id",
        "target_id",
        "doc_id",
        "id",
    )

    if not raw:
        return None

    try:
        return int(raw)
    except Exception:
        return None


# ============================================================
# R7 TOKEN CONTRACT — FROZEN
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

        seen.add(
            token
        )

        result.append(
            token
        )


    if not result:

        for token in raw:

            if token in seen:
                continue

            seen.add(
                token
            )

            result.append(
                token
            )


    return tuple(
        result
    )


# ============================================================
# R7-R1 TITLE IDENTITY TOKENIZATION
# ============================================================
#
# CRITICAL:
#   This differs from normal boundary_tokens() ONLY by allowing
#   single-character NUMERIC tokens.
#
#   Alphabetic one-character tokens remain excluded.
#
#   Examples:
#
#     2008_11_1.html
#       -> ("2008", "11", "1", "html")
#
#     C++
#       -> no new one-char alphabetic token behavior
#
# This signal is used ONLY after the original R7 score/features.
# ============================================================

def title_identity_tokens(
    value: str,
) -> tuple[str, ...]:

    raw = re.findall(
        r"[A-Za-z0-9]+",
        str(value or "").casefold(),
    )

    result = []
    seen = set()


    for token in raw:

        if token in FILE_NOISE:
            continue


        if len(token) >= 2:

            keep = True

        elif (
            len(token) == 1
            and
            token.isdigit()
        ):

            keep = True

        else:

            keep = False


        if not keep:
            continue

        if token in seen:
            continue

        seen.add(
            token
        )

        result.append(
            token
        )


    return tuple(
        result
    )


def query_identity_tokens(
    query: str,
) -> tuple[str, ...]:

    raw = re.findall(
        r"[A-Za-z0-9]+",
        str(query or "").casefold(),
    )

    result = []
    seen = set()


    for token in raw:

        if token in FILE_NOISE:
            continue

        if token in GENERIC_QUERY_NOISE:
            continue


        if len(token) >= 2:

            keep = True

        elif (
            len(token) == 1
            and
            token.isdigit()
        ):

            keep = True

        else:

            keep = False


        if not keep:
            continue

        if token in seen:
            continue

        seen.add(
            token
        )

        result.append(
            token
        )


    return tuple(
        result
    )


def title_identity_coverage(
    query: str,
    title: str,
) -> tuple[
    float,
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
]:

    qtokens = query_identity_tokens(
        query
    )

    ttokens = title_identity_tokens(
        title
    )

    tset = set(
        ttokens
    )


    matched = tuple(
        token
        for token in qtokens
        if token in tset
    )


    if not qtokens:

        coverage = 0.0

    else:

        coverage = (
            len(
                matched
            )
            /
            len(
                qtokens
            )
        )


    return (
        coverage,
        qtokens,
        ttokens,
        matched,
    )


# ============================================================
# R7 SHADOW CANDIDATE — ORIGINAL FEATURES
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

    # R7-R1 additions:
    full_title_identity: float

    full_identity_query_tokens: tuple[str, ...]

    full_identity_title_tokens: tuple[str, ...]

    full_identity_matched_tokens: tuple[str, ...]


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


# ============================================================
# FROZEN R7 SCORE + NEW TIE BREAK
# ============================================================

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


        if len(
            rows
        ) <= 1:

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
                    len(
                        rows
                    )
                    - 1
                )
            )


        # ----------------------------------------------------
        # EXACT ORIGINAL R7 SCORE
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


        title = text(
            row.get(
                "title"
            )
        )


        (
            full_title_identity,
            full_query_tokens,
            full_title_tokens,
            full_matched_tokens,
        ) = title_identity_coverage(
            query,
            title,
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

                rarity_coverage=
                    rarity_coverage,

                title_coverage=
                    title_coverage,

                numeric_identity=
                    numeric_identity,

                bm25_position=
                    bm25_position,

                shadow_score=
                    shadow_score,

                full_title_identity=
                    full_title_identity,

                full_identity_query_tokens=
                    full_query_tokens,

                full_identity_title_tokens=
                    full_title_tokens,

                full_identity_matched_tokens=
                    full_matched_tokens,
            )
        )


    # ========================================================
    # R7-R1 CHANGE:
    #
    # Original R7 score and feature precedence remain intact.
    #
    # full_title_identity is inserted ONLY after the complete
    # original R7 feature set and BEFORE production rank.
    #
    # Therefore it can only resolve candidates that are already
    # effectively tied under the certified R7 feature model.
    # ========================================================

    ranked.sort(
        key=lambda item: (
            -item.shadow_score,
            -item.coverage,
            -item.rarity_coverage,
            -item.title_coverage,
            -item.numeric_identity,

            # NEW NARROW TIE BREAK
            -item.full_title_identity,

            # ORIGINAL FALLBACKS
            item.production_rank,
            item.document_id,
            item.chunk_id,
        )
    )


    return ranked


# ============================================================
# DOCUMENT COLLAPSE
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


def document_rank(
    ranked: list[ShadowCandidate],
    target_document_id: int,
) -> int | None:

    for ordinal, item in enumerate(
        document_ranked(
            ranked
        ),
        start=1,
    ):

        if (
            item.document_id
            == target_document_id
        ):

            return ordinal

    return None


def production_document_rank(
    rows: list[Mapping[str, Any]],
    target_document_id: int,
) -> int | None:

    seen = set()
    ordinal = 0


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

        ordinal += 1


        if (
            document_id
            == target_document_id
        ):

            return ordinal


    return None


def best_target(
    ranked: list[ShadowCandidate],
    target_id: int,
) -> ShadowCandidate | None:

    for item in ranked:

        if item.document_id == target_id:
            return item

    return None


# ============================================================
# ADVERSARIAL ACCEPT CONTRACT — FROZEN FROM R7
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
        best.coverage >= 0.50

        and
        best.shadow_score >= 0.55

        and
        (
            best.title_coverage >= 0.50

            or
            best.rarity_coverage >= 0.70
        )
    )


# ============================================================
# READ-ONLY DB
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
# A. 79286 EXACT TIE-SET ANATOMY
# ============================================================

started = time.time()


target_rows = list(
    search_runtime_knowledge(
        TARGET_QUERY,
        db_path=DB,
        limit=POOL_LIMIT,
    )
)


target_ranked = shadow_rank(
    TARGET_QUERY,
    target_rows,
)


target_documents = document_ranked(
    target_ranked
)


target_new_rank = document_rank(
    target_ranked,
    TARGET_79286,
)


target_feature = best_target(
    target_ranked,
    TARGET_79286,
)


if target_feature is None:

    raise RuntimeError(
        "79286 absent from R7-R1 candidate pool"
    )


# ------------------------------------------------------------
# Reconstruct original R7 ordering by removing only the new
# title-identity tiebreak.
# ------------------------------------------------------------

original_order = sorted(
    target_ranked,
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


original_documents = document_ranked(
    original_order
)


target_original_rank = None

for rank, item in enumerate(
    original_documents,
    start=1,
):

    if item.document_id == TARGET_79286:

        target_original_rank = rank
        break


if target_original_rank != 27:

    raise RuntimeError(
        f"R7 parity failure for 79286: "
        f"expected 27 got {target_original_rank}"
    )


# ------------------------------------------------------------
# Capture original top-40 tie neighborhood.
# ------------------------------------------------------------

tie_rows = []


for original_rank, candidate in enumerate(
    original_documents[:40],
    start=1,
):

    new_rank = document_rank(
        target_ranked,
        candidate.document_id,
    )


    title = text(
        candidate.row.get(
            "title"
        )
    )


    tie_rows.append(
        {
            "original_r7_rank":
                original_rank,

            "r7_r1_rank":
                new_rank
                if new_rank
                is not None
                else "",

            "document_id":
                candidate.document_id,

            "chunk_id":
                candidate.chunk_id,

            "title":
                title,

            "production_chunk_rank":
                candidate.production_rank,

            "shadow_score":
                candidate.shadow_score,

            "coverage":
                candidate.coverage,

            "rarity_coverage":
                candidate.rarity_coverage,

            "title_coverage":
                candidate.title_coverage,

            "numeric_identity":
                candidate.numeric_identity,

            "bm25_position":
                candidate.bm25_position,

            "full_title_identity":
                candidate.full_title_identity,

            "full_query_tokens":
                ",".join(
                    candidate.full_identity_query_tokens
                ),

            "full_title_tokens":
                ",".join(
                    candidate.full_identity_title_tokens
                ),

            "full_matched_tokens":
                ",".join(
                    candidate.full_identity_matched_tokens
                ),

            "is_target_79286":
                (
                    candidate.document_id
                    == TARGET_79286
                ),
        }
    )


# ============================================================
# B. R6 NINE HARD CANARIES
# ============================================================

r7_r6_rows = read_tsv(
    R7_R6
)

if len(
    r7_r6_rows
) != 9:

    raise RuntimeError(
        f"expected 9 R6 canaries, got {len(r7_r6_rows)}"
    )


r6_rows = []

r6_top20 = 0
r6_top10 = 0
r6_top1 = 0


for source in r7_r6_rows:

    query = source[
        "query"
    ]

    target_id = int(
        source[
            "document_id"
        ]
    )


    raw = list(
        search_runtime_knowledge(
            query,
            db_path=DB,
            limit=POOL_LIMIT,
        )
    )


    ranked = shadow_rank(
        query,
        raw,
    )


    rank = document_rank(
        ranked,
        target_id,
    )


    feature = best_target(
        ranked,
        target_id,
    )


    if (
        rank is not None
        and
        rank <= 20
    ):
        r6_top20 += 1


    if (
        rank is not None
        and
        rank <= 10
    ):
        r6_top10 += 1


    if rank == 1:
        r6_top1 += 1


    r6_rows.append(
        {
            "document_id":
                target_id,

            "query":
                query,

            "previous_r7_rank":
                source[
                    "shadow_document_rank"
                ],

            "r7_r1_rank":
                rank
                if rank
                is not None
                else "",

            "full_title_identity":
                feature.full_title_identity
                if feature
                else "",

            "full_query_tokens":
                (
                    ",".join(
                        feature.full_identity_query_tokens
                    )
                    if feature
                    else ""
                ),

            "full_title_tokens":
                (
                    ",".join(
                        feature.full_identity_title_tokens
                    )
                    if feature
                    else ""
                ),

            "PASS_TOP20":
                (
                    rank is not None
                    and
                    rank <= 20
                ),
        }
    )


# ============================================================
# C. EXACT R3 250 POPULATION
# ============================================================

r3_population = read_tsv(
    R3
)

if len(
    r3_population
) != 250:

    raise RuntimeError(
        f"expected 250 R3 rows; got {len(r3_population)}"
    )


r3_rows = []

feature_rows = []

r3_resolved = 0

top20 = 0
top100 = 0
top1 = 0

improved = 0
unchanged = 0
regressed = 0

ranks = []


for case, source in enumerate(
    r3_population,
    start=1,
):

    query = r3_query(
        source
    )

    target_id = r3_target(
        source
    )


    if (
        not query
        or
        target_id is None
    ):

        r3_rows.append(
            {
                "case":
                    case,

                "query":
                    query,

                "target_document_id":
                    (
                        target_id
                        if target_id
                        is not None
                        else ""
                    ),

                "status":
                    "INPUT_UNRESOLVED",
            }
        )

        continue


    raw = list(
        search_runtime_knowledge(
            query,
            db_path=DB,
            limit=POOL_LIMIT,
        )
    )


    ranked = shadow_rank(
        query,
        raw,
    )


    new_rank = document_rank(
        ranked,
        target_id,
    )


    # --------------------------------------------------------
    # Exact original R7 rank reconstructed from same candidates
    # --------------------------------------------------------

    original_ranked = sorted(
        ranked,
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


    old_rank = document_rank(
        original_ranked,
        target_id,
    )


    feature = best_target(
        ranked,
        target_id,
    )


    if new_rank is not None:

        r3_resolved += 1
        ranks.append(
            new_rank
        )


        if new_rank <= 20:
            top20 += 1

        if new_rank <= 100:
            top100 += 1

        if new_rank == 1:
            top1 += 1


    if (
        old_rank is not None
        and
        new_rank is not None
    ):

        if new_rank < old_rank:
            improved += 1

        elif new_rank == old_rank:
            unchanged += 1

        else:
            regressed += 1


    r3_rows.append(
        {
            "case":
                case,

            "query":
                query,

            "target_document_id":
                target_id,

            "previous_r7_rank":
                (
                    old_rank
                    if old_rank
                    is not None
                    else ""
                ),

            "r7_r1_rank":
                (
                    new_rank
                    if new_rank
                    is not None
                    else ""
                ),

            "rank_delta":
                (
                    old_rank
                    - new_rank
                    if old_rank is not None
                    and new_rank is not None
                    else ""
                ),

            "status":
                (
                    "OK"
                    if new_rank
                    is not None
                    else "TARGET_OUTSIDE_POOL"
                ),
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

                "r7_r1_rank":
                    (
                        new_rank
                        if new_rank
                        is not None
                        else ""
                    ),

                "shadow_score":
                    feature.shadow_score,

                "coverage":
                    feature.coverage,

                "rarity_coverage":
                    feature.rarity_coverage,

                "title_coverage":
                    feature.title_coverage,

                "numeric_identity":
                    feature.numeric_identity,

                "full_title_identity":
                    feature.full_title_identity,

                "full_query_tokens":
                    ",".join(
                        feature.full_identity_query_tokens
                    ),

                "full_title_tokens":
                    ",".join(
                        feature.full_identity_title_tokens
                    ),

                "full_matched_tokens":
                    ",".join(
                        feature.full_identity_matched_tokens
                    ),
            }
        )


# ============================================================
# D. IDENTITY CANARIES
# ============================================================

identity_rows = []

identity_pass = 0
identity_regressions = 0


for name, query, target_id in IDENTITY_CANARIES:

    raw = list(
        search_runtime_knowledge(
            query,
            db_path=DB,
            limit=POOL_LIMIT,
        )
    )


    ranked = shadow_rank(
        query,
        raw,
    )


    new_rank = document_rank(
        ranked,
        target_id,
    )


    old_ranked = sorted(
        ranked,
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


    old_rank = document_rank(
        old_ranked,
        target_id,
    )


    regression = (
        old_rank is not None
        and
        new_rank is not None
        and
        new_rank > old_rank
    )


    if (
        new_rank is not None
        and
        new_rank <= 20
    ):

        identity_pass += 1


    if regression:
        identity_regressions += 1


    identity_rows.append(
        {
            "name":
                name,

            "query":
                query,

            "target_document_id":
                target_id,

            "previous_r7_rank":
                (
                    old_rank
                    if old_rank
                    is not None
                    else ""
                ),

            "r7_r1_rank":
                (
                    new_rank
                    if new_rank
                    is not None
                    else ""
                ),

            "regression":
                regression,
        }
    )


# ============================================================
# E. SEMANTIC CONTROLS
# ============================================================

semantic_rows = []

semantic_pass = 0


for query in SEMANTIC_CONTROLS:

    raw = list(
        search_runtime_knowledge(
            query,
            db_path=DB,
            limit=POOL_LIMIT,
        )
    )


    if not raw:

        semantic_rows.append(
            {
                "query":
                    query,

                "production_top_document":
                    "",

                "preserved_top20":
                    False,
            }
        )

        continue


    production_top_document = int(
        raw[
            0
        ][
            "document_id"
        ]
    )


    ranked = document_ranked(
        shadow_rank(
            query,
            raw,
        )
    )


    semantic_top20_documents = {
        item.document_id
        for item in ranked[
            :20
        ]
    }


    preserved = (
        production_top_document
        in semantic_top20_documents
    )


    if preserved:
        semantic_pass += 1


    semantic_rows.append(
        {
            "query":
                query,

            "production_top_document":
                production_top_document,

            "preserved_top20":
                preserved,
        }
    )


# ============================================================
# F. ADVERSARIAL CONTROLS
# ============================================================

adversarial_rows = []

adversarial_accepts = 0


for query in ADVERSARIAL:

    raw = list(
        search_runtime_knowledge(
            query,
            db_path=DB,
            limit=POOL_LIMIT,
        )
    )


    ranked = shadow_rank(
        query,
        raw,
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
                    raw
                ),

            "shadow_accept":
                accepted,

            "best_document":
                (
                    best.document_id
                    if best
                    else ""
                ),

            "best_score":
                (
                    best.shadow_score
                    if best
                    else ""
                ),

            "best_full_title_identity":
                (
                    best.full_title_identity
                    if best
                    else ""
                ),
        }
    )


# ============================================================
# CERTIFICATION
# ============================================================

r3_median = (
    float(
        statistics.median(
            ranks
        )
    )
    if ranks
    else None
)


certification = {
    "79286_original_r7_rank_is_27":
        target_original_rank == 27,

    "79286_r7_r1_top20":
        (
            target_new_rank
            is not None
            and
            target_new_rank <= 20
        ),

    "79286_single_digit_identity_present":
        (
            "1"
            in
            target_feature.full_identity_query_tokens

            and
            "1"
            in
            target_feature.full_identity_title_tokens

            and
            "1"
            in
            target_feature.full_identity_matched_tokens
        ),

    "r6_nine_targets_top20":
        r6_top20 == 9,

    "r3_exact_250_resolved":
        r3_resolved == 250,

    "r3_all_250_top100":
        top100 == 250,

    "r3_at_least_245_top20":
        top20 >= 245,

    "r3_zero_regressions_vs_r7":
        regressed == 0,

    "identity_canaries_4_of_4_top20":
        identity_pass == 4,

    "identity_canaries_zero_regressions":
        identity_regressions == 0,

    "semantic_controls_4_of_4":
        semantic_pass == 4,

    "adversarial_accepts_zero":
        adversarial_accepts == 0,

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
        "Genesis Recall R4-R10-R7-R1",

    "change": {
        "base_ranker":
            "R7 frozen",

        "primary_score_changed":
            False,

        "new_signal":
            "full_title_identity",

        "new_signal_role":
            "tie-break only",

        "single_digit_policy":
            (
                "numeric one-character tokens preserved "
                "only for query/title identity comparison"
            ),
    },

    "target_79286": {
        "query":
            TARGET_QUERY,

        "original_r7_rank":
            target_original_rank,

        "r7_r1_rank":
            target_new_rank,

        "shadow_score":
            target_feature.shadow_score,

        "coverage":
            target_feature.coverage,

        "rarity_coverage":
            target_feature.rarity_coverage,

        "title_coverage":
            target_feature.title_coverage,

        "numeric_identity":
            target_feature.numeric_identity,

        "full_title_identity":
            target_feature.full_title_identity,

        "full_query_tokens":
            list(
                target_feature.full_identity_query_tokens
            ),

        "full_title_tokens":
            list(
                target_feature.full_identity_title_tokens
            ),

        "full_matched_tokens":
            list(
                target_feature.full_identity_matched_tokens
            ),
    },

    "r6": {
        "population":
            9,

        "top20":
            r6_top20,

        "top10":
            r6_top10,

        "top1":
            r6_top1,
    },

    "r3": {
        "population":
            250,

        "resolved":
            r3_resolved,

        "top20":
            top20,

        "top100":
            top100,

        "top1":
            top1,

        "improved_vs_r7":
            improved,

        "unchanged_vs_r7":
            unchanged,

        "regressed_vs_r7":
            regressed,

        "median_rank":
            r3_median,
    },

    "identity_canaries": {
        "top20":
            identity_pass,

        "regressions":
            identity_regressions,
    },

    "semantic_controls": {
        "preserved":
            semantic_pass,
    },

    "adversarial": {
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
    TIESET,
    tie_rows,
)

write_tsv(
    R6_TRACE,
    r6_rows,
)

write_tsv(
    R3_TRACE,
    r3_rows,
)

write_tsv(
    CANARY_TRACE,
    identity_rows,
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
# TRACE
# ============================================================

trace_lines = [
    "=" * 78,
    " GENESIS RECALL R4-R10-R7-R1",
    " 79286 TIE-SET + TITLE IDENTITY TRACE",
    "=" * 78,
    "",
    "79286",
    f"  query                  : {TARGET_QUERY}",
    f"  original R7 rank       : {target_original_rank}",
    f"  R7-R1 rank             : {target_new_rank}",
    f"  shadow score           : {target_feature.shadow_score}",
    f"  coverage               : {target_feature.coverage}",
    f"  rarity coverage        : {target_feature.rarity_coverage}",
    f"  title coverage         : {target_feature.title_coverage}",
    f"  numeric identity       : {target_feature.numeric_identity}",
    f"  full title identity    : {target_feature.full_title_identity}",
    (
        "  full query tokens     : "
        + repr(
            target_feature.full_identity_query_tokens
        )
    ),
    (
        "  full title tokens     : "
        + repr(
            target_feature.full_identity_title_tokens
        )
    ),
    (
        "  full matched tokens   : "
        + repr(
            target_feature.full_identity_matched_tokens
        )
    ),
    "",
    "R6",
    f"  top20                  : {r6_top20}/9",
    f"  top10                  : {r6_top10}/9",
    f"  top1                   : {r6_top1}/9",
    "",
    "R3",
    f"  resolved               : {r3_resolved}/250",
    f"  top20                  : {top20}/250",
    f"  top100                 : {top100}/250",
    f"  top1                   : {top1}/250",
    f"  improved vs R7         : {improved}",
    f"  unchanged vs R7        : {unchanged}",
    f"  regressed vs R7        : {regressed}",
    f"  median rank            : {r3_median}",
    "",
    "PRECISION",
    f"  identity top20         : {identity_pass}/4",
    f"  identity regressions   : {identity_regressions}",
    f"  semantic preserved     : {semantic_pass}/4",
    f"  adversarial accepted   : {adversarial_accepts}/10",
    "",
    "CERTIFICATION",
]


for key, value in certification.items():

    trace_lines.append(
        f"  {key:<45}: {value}"
    )


trace_lines.extend(
    (
        "",
        f"R7-R1 SHADOW CERTIFIED : {shadow_certified}",
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
            " GENESIS RECALL R4-R10-R7-R1",
            " SOURCE CONTRACT",
            "=" * 78,
            "",
            "title_identity_tokens",
            "-" * 78,
            inspect.getsource(
                title_identity_tokens
            ),
            "",
            "query_identity_tokens",
            "-" * 78,
            inspect.getsource(
                query_identity_tokens
            ),
            "",
            "title_identity_coverage",
            "-" * 78,
            inspect.getsource(
                title_identity_coverage
            ),
            "",
            "shadow_rank",
            "-" * 78,
            inspect.getsource(
                shadow_rank
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
print(" GENESIS RECALL R4-R10-R7-R1 RESULT")
print("=" * 78)

print()
print("79286")

print(
    "  query                       :",
    TARGET_QUERY,
)

print(
    "  original R7 rank            :",
    target_original_rank,
)

print(
    "  R7-R1 rank                  :",
    target_new_rank,
)

print(
    "  original shadow score       :",
    target_feature.shadow_score,
)

print(
    "  original coverage           :",
    target_feature.coverage,
)

print(
    "  original rarity coverage    :",
    target_feature.rarity_coverage,
)

print(
    "  original title coverage     :",
    target_feature.title_coverage,
)

print(
    "  original numeric identity   :",
    target_feature.numeric_identity,
)

print(
    "  full title identity         :",
    target_feature.full_title_identity,
)

print(
    "  full query tokens           :",
    target_feature.full_identity_query_tokens,
)

print(
    "  full title tokens           :",
    target_feature.full_identity_title_tokens,
)

print(
    "  full matched tokens         :",
    target_feature.full_identity_matched_tokens,
)


print()
print("R6 HARD CANARIES")

print(
    "  top20                       :",
    f"{r6_top20}/9",
)

print(
    "  top10                       :",
    f"{r6_top10}/9",
)

print(
    "  rank1                       :",
    f"{r6_top1}/9",
)


print()
print("R3 EXACT 250")

print(
    "  resolved                    :",
    f"{r3_resolved}/250",
)

print(
    "  top20                       :",
    f"{top20}/250",
)

print(
    "  top100                      :",
    f"{top100}/250",
)

print(
    "  rank1                       :",
    f"{top1}/250",
)

print(
    "  improved vs R7              :",
    improved,
)

print(
    "  unchanged vs R7             :",
    unchanged,
)

print(
    "  regressed vs R7             :",
    regressed,
)

print(
    "  median rank                 :",
    r3_median,
)


print()
print("PRECISION")

print(
    "  identity canaries top20     :",
    f"{identity_pass}/4",
)

print(
    "  identity regressions        :",
    identity_regressions,
)

print(
    "  semantic controls preserved :",
    f"{semantic_pass}/4",
)

print(
    "  adversarial accepted        :",
    f"{adversarial_accepts}/10",
)


print()
print("CERTIFICATION")

for key, value in certification.items():

    print(
        f"  {key:<45}: {value}"
    )


print()
print(
    "R4-R10-R7-R1 SHADOW CERTIFIED :",
    shadow_certified,
)


print()
print("Artifacts:")
print(" ", REPORT)
print(" ", TIESET)
print(" ", R6_TRACE)
print(" ", R3_TRACE)
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
