from __future__ import annotations

import csv
import inspect
import json
import math
import re
import sys
import time

from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Mapping


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

OUTDIR = (
    PROJECT
    / "artifacts"
    / "genesis_recall"
)

R4R9_DETAIL = (
    OUTDIR
    / "r4_r9_subject_lexical_differential.tsv"
)

R3_TSV = (
    OUTDIR
    / "r3_production_recall_census.tsv"
)

REPORT = (
    OUTDIR
    / "r4_r10_subject_boundary_shadow.json"
)

RECOVERY_TSV = (
    OUTDIR
    / "r4_r10_subject_recovery.tsv"
)

R3_SHADOW_TSV = (
    OUTDIR
    / "r4_r10_r3_shadow_regression.tsv"
)

ADVERSARIAL_TSV = (
    OUTDIR
    / "r4_r10_adversarial_shadow.tsv"
)

TOKEN_TSV = (
    OUTDIR
    / "r4_r10_technical_token_preservation.tsv"
)

CANARY_TSV = (
    OUTDIR
    / "r4_r10_recall_canaries.tsv"
)

TRACE = (
    OUTDIR
    / "r4_r10_shadow_trace.txt"
)

SOURCE_MAP = (
    OUTDIR
    / "r4_r10_shadow_source_map.txt"
)


sys.path.insert(
    0,
    str(PROJECT),
)


from core.knowledge_catalog.search import (
    search_catalog,
)

from core.knowledge_catalog.qualified_search import (
    candidate_from_row,
)

from core.retrieval.qualification.contracts import (
    EvidenceCandidate,
)

import core.retrieval.qualification.evaluator as evaluator_module

from core.retrieval.qualification.evaluator import (
    QualificationEngine,
)

from core.retrieval.qualification.lexical import (
    analyze_lexical,
    tokenize,
)

from core.retrieval.qualification.subject import (
    SubjectAnalysis,
    analyze_subject as production_analyze_subject,
)


EXPECTED_FAILURES = 221
EXPECTED_R3 = 250


# ============================================================
# SHADOW REPAIR
# ============================================================
#
# Deliberately conservative.
#
# Existing text is preserved verbatim.
# Additional aliases are appended ONLY for dotted tokens.
#
# Example:
#
#   AFG20060328n224.html
#
# becomes shadow subject text:
#
#   AFG20060328n224.html AFG20060328n224 html
#
# This does NOT alter production tokenize().
#
# It does NOT split:
#
#   c++
#   c#
#   foo-bar
#   foo_bar
#   namespace:value
#
# ============================================================

DOTTED_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9])"
    r"([A-Za-z0-9][A-Za-z0-9_+#:-]*"
    r"(?:\.[A-Za-z0-9][A-Za-z0-9_+#:-]*)+)"
    r"(?![A-Za-z0-9])"
)


def dotted_aliases(
    value: str,
) -> tuple[str, ...]:

    aliases = []

    seen = set()

    for match in DOTTED_TOKEN_RE.finditer(
        str(
            value
            or ""
        )
    ):

        token = match.group(
            1
        )

        parts = [
            piece
            for piece in token.split(
                "."
            )
            if piece
        ]

        if len(
            parts
        ) < 2:

            continue

        for piece in parts:

            key = piece.casefold()

            if key in seen:
                continue

            seen.add(
                key
            )

            aliases.append(
                piece
            )

    return tuple(
        aliases
    )


def expand_subject_text(
    candidate_subject: str,
    candidate_title: str,
) -> tuple[str, tuple[str, ...]]:

    original = " ".join(
        part
        for part in (
            str(
                candidate_subject
                or ""
            ),
            str(
                candidate_title
                or ""
            ),
        )
        if part
    )

    aliases = []

    seen = set()

    for source in (
        candidate_subject,
        candidate_title,
    ):

        for alias in dotted_aliases(
            str(
                source
                or ""
            )
        ):

            key = alias.casefold()

            if key in seen:
                continue

            seen.add(
                key
            )

            aliases.append(
                alias
            )

    expanded = " ".join(
        (
            original,
            *aliases,
        )
    ).strip()

    return (
        expanded,
        tuple(
            aliases
        ),
    )


def shadow_analyze_subject(
    query: str,
    candidate_subject: str,
    candidate_title: str = "",
) -> SubjectAnalysis:

    expanded, _aliases = expand_subject_text(
        candidate_subject,
        candidate_title,
    )

    result = analyze_lexical(
        query,
        expanded,
    )

    return SubjectAnalysis(
        result.score,
        query,
        expanded,
    )


# ============================================================
# TEMPORARY IN-MEMORY SHADOW HOOK
# ============================================================

@contextmanager
def shadow_subject_hook():

    original = (
        evaluator_module
        .analyze_subject
    )

    evaluator_module.analyze_subject = (
        shadow_analyze_subject
    )

    try:

        yield

    finally:

        evaluator_module.analyze_subject = (
            original
        )


# ============================================================
# GENERIC HELPERS
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

        for key in row.keys():

            if key not in seen:

                seen.add(
                    key
                )

                fields.append(
                    key
                )

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

        writer.writerows(
            rows
        )


def sval(
    value: Any,
) -> str:

    if value is None:
        return ""

    return str(
        value
    )


def first_present(
    row: Mapping[str, Any],
    names: Iterable[str],
) -> str:

    lower_map = {
        str(
            key
        ).casefold():
            key
        for key in row.keys()
    }

    for name in names:

        actual = lower_map.get(
            str(
                name
            ).casefold()
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

            return str(
                value
            )

    return ""


def raw_map(
    raw: Any,
) -> dict[str, Any]:

    if isinstance(
        raw,
        Mapping,
    ):

        return dict(
            raw
        )

    if hasattr(
        raw,
        "keys",
    ):

        try:

            return {
                key:
                    raw[
                        key
                    ]
                for key
                in raw.keys()
            }

        except Exception:
            pass

    if hasattr(
        raw,
        "_asdict",
    ):

        try:
            return dict(
                raw._asdict()
            )
        except Exception:
            pass

    try:

        return dict(
            vars(
                raw
            )
        )

    except Exception:

        return {}


def raw_ids(
    row: Mapping[str, Any],
) -> set[str]:

    result = set()

    for name in (
        "id",
        "document_id",
        "runtime_document_id",
        "runtime_id",
        "source_id",
        "doc_id",
    ):

        value = row.get(
            name
        )

        if value not in (
            None,
            "",
        ):

            result.add(
                str(
                    value
                ).strip()
            )

    return result


def candidate_ids(
    candidate: EvidenceCandidate,
) -> set[str]:

    result = {
        str(
            candidate.source_id
        ).strip()
    }

    try:

        metadata = dict(
            candidate.metadata
        )

    except Exception:

        metadata = {}

    result.update(
        raw_ids(
            metadata
        )
    )

    return {
        item
        for item in result
        if item
    }


def target_candidate(
    query: str,
    target_ids: set[str],
    *,
    limit: int = 100,
) -> tuple[
    EvidenceCandidate | None,
    int | None,
    int,
]:

    rows = list(
        search_catalog(
            query,
            limit=limit,
        )
    )

    matches = []

    for ordinal, raw in enumerate(
        rows,
        start=1,
    ):

        mapped = raw_map(
            raw
        )

        if target_ids.intersection(
            raw_ids(
                mapped
            )
        ):

            candidate = candidate_from_row(
                raw,
                ordinal=ordinal,
            )

            matches.append(
                (
                    candidate,
                    ordinal,
                )
            )

    if not matches:

        return (
            None,
            None,
            0,
        )

    candidate, ordinal = matches[
        0
    ]

    return (
        candidate,
        ordinal,
        len(
            matches
        ),
    )


def one_evidence(
    engine: QualificationEngine,
    query: str,
    candidate: EvidenceCandidate,
    *,
    shadow: bool,
):

    if shadow:

        with shadow_subject_hook():

            result = engine.evaluate(
                query,
                (
                    candidate,
                ),
            )

    else:

        result = engine.evaluate(
            query,
            (
                candidate,
            ),
        )

    evidence = (
        *result.accepted,
        *result.rejected,
    )

    if len(
        evidence
    ) != 1:

        raise RuntimeError(
            "unexpected evidence cardinality "
            f"{len(evidence)}"
        )

    return evidence[
        0
    ]


def is_accepted(
    evidence: Any,
) -> bool:

    text = str(
        evidence.decision
    ).upper()

    return (
        "ACCEPT" in text
        and
        "REJECT" not in text
    )


# ============================================================
# LOAD R4-R9 EXACT FAILURE POPULATION
# ============================================================

r4r9_rows = read_tsv(
    R4R9_DETAIL
)

r4r9_rows = [
    row
    for row in r4r9_rows
    if row.get(
        "status",
        "",
    )
    == "OK"
]


if len(
    r4r9_rows
) != EXPECTED_FAILURES:

    raise RuntimeError(
        "Expected 221 exact R4-R9 cases, "
        f"found {len(r4r9_rows)}"
    )


# ============================================================
# A. 221-CASE SHADOW RECOVERY
# ============================================================

engine = QualificationEngine()

started = time.time()

recovery_rows = []

trace_lines = []

recovered = 0

still_rejected = 0

production_unexpected_accept = 0

subject_score_increase = 0

subject_score_not_increased = 0

alias_empty = 0

target_missing = 0

multiple_target = 0


for index, row in enumerate(
    r4r9_rows,
    start=1,
):

    query = row[
        "query"
    ]

    target_id = str(
        row.get(
            "document_id",
            "",
        )
    ).strip()

    if not target_id:

        raise RuntimeError(
            f"R4-R9 case {index}: missing document_id"
        )


    candidate, rank, match_count = (
        target_candidate(
            query,
            {
                target_id,
            },
            limit=100,
        )
    )


    if candidate is None:

        target_missing += 1

        recovery_rows.append(
            {
                "case":
                    index,

                "document_id":
                    target_id,

                "query":
                    query,

                "status":
                    "TARGET_NOT_FOUND",
            }
        )

        continue


    if match_count > 1:

        multiple_target += 1


    production = one_evidence(
        engine,
        query,
        candidate,
        shadow=False,
    )

    shadow = one_evidence(
        engine,
        query,
        candidate,
        shadow=True,
    )


    expanded, aliases = (
        expand_subject_text(
            candidate.subject,
            candidate.title,
        )
    )


    prod_subject = float(
        production.score.subject
    )

    shadow_subject = float(
        shadow.score.subject
    )


    prod_accept = is_accepted(
        production
    )

    shadow_accept = is_accepted(
        shadow
    )


    if prod_accept:

        production_unexpected_accept += 1


    if (
        not prod_accept
        and
        shadow_accept
    ):

        recovered += 1


    elif not shadow_accept:

        still_rejected += 1


    if shadow_subject > prod_subject:

        subject_score_increase += 1

    else:

        subject_score_not_increased += 1


    if not aliases:

        alias_empty += 1


    recovery_rows.append(
        {
            "case":
                index,

            "document_id":
                target_id,

            "query":
                query,

            "raw_rank":
                rank,

            "candidate_title":
                candidate.title,

            "candidate_subject":
                candidate.subject,

            "aliases":
                ",".join(
                    aliases
                ),

            "shadow_subject_text":
                expanded,

            "production_subject_score":
                prod_subject,

            "shadow_subject_score":
                shadow_subject,

            "production_final_score":
                float(
                    production.score.final
                ),

            "shadow_final_score":
                float(
                    shadow.score.final
                ),

            "production_decision":
                str(
                    production.decision
                ),

            "shadow_decision":
                str(
                    shadow.decision
                ),

            "production_accepted":
                prod_accept,

            "shadow_accepted":
                shadow_accept,

            "recovered":
                (
                    not prod_accept
                    and shadow_accept
                ),

            "production_explanation":
                production.explanation,

            "shadow_explanation":
                shadow.explanation,

            "status":
                "OK",
        }
    )


    if index <= 16:

        trace_lines.extend(
            (
                "=" * 78,
                f"RECOVERY CASE {index:03d}",
                "=" * 78,
                f"document_id     : {target_id}",
                f"query           : {query}",
                f"title           : {candidate.title}",
                f"subject         : {candidate.subject}",
                f"aliases         : {aliases}",
                "",
                f"production subj : {prod_subject}",
                f"shadow subj     : {shadow_subject}",
                f"production final: {production.score.final}",
                f"shadow final    : {shadow.score.final}",
                f"production dec  : {production.decision}",
                f"shadow dec      : {shadow.decision}",
                f"recovered       : {not prod_accept and shadow_accept}",
                "",
                f"production tokens:"
                f" {tokenize(candidate.subject + ' ' + candidate.title)}",
                f"shadow tokens    : {tokenize(expanded)}",
                "",
            )
        )


# ============================================================
# B. R3 DETERMINISTIC 250-DOCUMENT REGRESSION
# ============================================================

r3_rows = read_tsv(
    R3_TSV
)


if len(
    r3_rows
) != EXPECTED_R3:

    raise RuntimeError(
        "Expected exact R3 250-row census TSV, "
        f"found {len(r3_rows)}"
    )


r3_shadow_rows = []

r3_resolved = 0

r3_unresolved = 0

accepted_controls = 0

accepted_controls_preserved = 0

accepted_controls_flipped = 0

r3_current_rejected = 0

r3_shadow_recovered = 0

r3_shadow_still_rejected = 0


QUERY_NAMES = (
    "query",
    "search_query",
    "qualification_query",
    "input_query",
)

ID_NAMES = (
    "document_id",
    "runtime_document_id",
    "target_document_id",
    "target_id",
    "doc_id",
    "source_id",
    "id",
)


for index, row in enumerate(
    r3_rows,
    start=1,
):

    query = first_present(
        row,
        QUERY_NAMES,
    )

    target_id = first_present(
        row,
        ID_NAMES,
    )


    if not query or not target_id:

        r3_unresolved += 1

        r3_shadow_rows.append(
            {
                "row":
                    index,

                "query":
                    query,

                "document_id":
                    target_id,

                "status":
                    "INPUT_IDENTITY_UNRESOLVED",
            }
        )

        continue


    candidate, rank, match_count = (
        target_candidate(
            query,
            {
                target_id,
            },
            limit=100,
        )
    )


    if candidate is None:

        r3_unresolved += 1

        r3_shadow_rows.append(
            {
                "row":
                    index,

                "query":
                    query,

                "document_id":
                    target_id,

                "status":
                    "TARGET_NOT_FOUND",
            }
        )

        continue


    r3_resolved += 1


    prod = one_evidence(
        engine,
        query,
        candidate,
        shadow=False,
    )

    shadow = one_evidence(
        engine,
        query,
        candidate,
        shadow=True,
    )


    prod_accept = is_accepted(
        prod
    )

    shadow_accept = is_accepted(
        shadow
    )


    if prod_accept:

        accepted_controls += 1

        if shadow_accept:

            accepted_controls_preserved += 1

        else:

            accepted_controls_flipped += 1


    else:

        r3_current_rejected += 1

        if shadow_accept:

            r3_shadow_recovered += 1

        else:

            r3_shadow_still_rejected += 1


    aliases = expand_subject_text(
        candidate.subject,
        candidate.title,
    )[1]


    r3_shadow_rows.append(
        {
            "row":
                index,

            "query":
                query,

            "document_id":
                target_id,

            "raw_rank":
                rank,

            "aliases":
                ",".join(
                    aliases
                ),

            "production_subject_score":
                float(
                    prod.score.subject
                ),

            "shadow_subject_score":
                float(
                    shadow.score.subject
                ),

            "production_final_score":
                float(
                    prod.score.final
                ),

            "shadow_final_score":
                float(
                    shadow.score.final
                ),

            "production_decision":
                str(
                    prod.decision
                ),

            "shadow_decision":
                str(
                    shadow.decision
                ),

            "production_accepted":
                prod_accept,

            "shadow_accepted":
                shadow_accept,

            "decision_changed":
                (
                    prod_accept
                    != shadow_accept
                ),

            "status":
                "OK",
        }
    )


# ============================================================
# C. ADVERSARIAL PRECISION
# ============================================================

ADVERSARIAL_QUERIES = (
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


adversarial_rows = []

adversarial_shadow_increase = 0

adversarial_shadow_accept_total = 0


for query in ADVERSARIAL_QUERIES:

    raw_rows = list(
        search_catalog(
            query,
            limit=20,
        )
    )


    candidates = tuple(
        candidate_from_row(
            raw,
            ordinal=index,
        )
        for index, raw
        in enumerate(
            raw_rows,
            start=1,
        )
    )


    production_result = engine.evaluate(
        query,
        candidates,
    )


    with shadow_subject_hook():

        shadow_result = engine.evaluate(
            query,
            candidates,
        )


    prod_count = len(
        production_result.accepted
    )

    shadow_count = len(
        shadow_result.accepted
    )


    adversarial_shadow_accept_total += (
        shadow_count
    )


    if shadow_count > prod_count:

        adversarial_shadow_increase += 1


    adversarial_rows.append(
        {
            "query":
                query,

            "raw_candidates":
                len(
                    candidates
                ),

            "production_accepted":
                prod_count,

            "shadow_accepted":
                shadow_count,

            "increased":
                shadow_count
                > prod_count,
        }
    )


# ============================================================
# D. TECHNICAL TOKEN PRESERVATION
# ============================================================

TOKEN_CONTROLS = (
    (
        "C++",
        "Modern C++ programming",
    ),
    (
        "C#",
        "C# language reference",
    ),
    (
        "foo-bar",
        "foo-bar maintenance procedure",
    ),
    (
        "foo_bar",
        "foo_bar identifier",
    ),
    (
        "namespace:value",
        "namespace:value syntax",
    ),
    (
        "RFC9110",
        "RFC9110 HTTP semantics",
    ),
    (
        "v1.2.3",
        "v1.2.3 release notes",
    ),
    (
        "example.com",
        "example.com",
    ),
    (
        "std::vector",
        "std::vector C++ container",
    ),
    (
        "systemd-networkd",
        "systemd-networkd configuration",
    ),
)


token_control_rows = []

technical_original_token_loss = 0


for query, candidate_text in TOKEN_CONTROLS:

    before = tokenize(
        candidate_text
    )

    expanded, aliases = (
        expand_subject_text(
            candidate_text,
            "",
        )
    )

    after = tokenize(
        expanded
    )


    lost = [
        token
        for token in before
        if token not in after
    ]


    if lost:

        technical_original_token_loss += 1


    prod = analyze_lexical(
        query,
        candidate_text,
    )

    shadow = analyze_lexical(
        query,
        expanded,
    )


    token_control_rows.append(
        {
            "query":
                query,

            "candidate_text":
                candidate_text,

            "production_tokens":
                ",".join(
                    before
                ),

            "shadow_tokens":
                ",".join(
                    after
                ),

            "aliases":
                ",".join(
                    aliases
                ),

            "lost_original_tokens":
                ",".join(
                    lost
                ),

            "production_score":
                float(
                    prod.score
                ),

            "shadow_score":
                float(
                    shadow.score
                ),

            "original_tokens_preserved":
                not bool(
                    lost
                ),
        }
    )


# ============================================================
# E. KNOWN RECALL CANARY QUERIES
# ============================================================
#
# These are regression observations, not strict identity
# assertions unless the target ID is supplied.
# ============================================================

CANARIES = (
    (
        "cpp",
        "C++ Programming",
        "4",
    ),
    (
        "effective_c",
        "Effective C",
        "14",
    ),
    (
        "ai_assisted_python",
        "AI assisted Python",
        "11",
    ),
    (
        "lane_lexicon",
        "Lane lexicon",
        "86876",
    ),
    (
        "civil_defense",
        "civil defense manual",
        "",
    ),
    (
        "army_survival",
        "US Army survival manual",
        "",
    ),
    (
        "electronics",
        "practical electronics handbook",
        "",
    ),
    (
        "marx",
        "Marx mathematical manuscripts",
        "",
    ),
)


canary_rows = []

canary_regressions = 0

identity_canaries_resolved = 0


for name, query, target_id in CANARIES:

    raw_rows = list(
        search_catalog(
            query,
            limit=20,
        )
    )


    candidates = tuple(
        candidate_from_row(
            raw,
            ordinal=index,
        )
        for index, raw
        in enumerate(
            raw_rows,
            start=1,
        )
    )


    prod_result = engine.evaluate(
        query,
        candidates,
    )


    with shadow_subject_hook():

        shadow_result = engine.evaluate(
            query,
            candidates,
        )


    prod_ids = set()

    shadow_ids = set()


    for item in prod_result.accepted:

        prod_ids.update(
            candidate_ids(
                item.candidate
            )
        )


    for item in shadow_result.accepted:

        shadow_ids.update(
            candidate_ids(
                item.candidate
            )
        )


    target_found = (
        target_id
        and
        (
            target_id in prod_ids
            or
            target_id in shadow_ids
        )
    )


    if target_id and target_found:

        identity_canaries_resolved += 1


    regression = False


    if target_id and target_id in prod_ids:

        if target_id not in shadow_ids:

            regression = True


    if regression:

        canary_regressions += 1


    canary_rows.append(
        {
            "name":
                name,

            "query":
                query,

            "target_id":
                target_id,

            "raw_candidates":
                len(
                    candidates
                ),

            "production_accepted":
                len(
                    prod_result.accepted
                ),

            "shadow_accepted":
                len(
                    shadow_result.accepted
                ),

            "production_target_present":
                (
                    target_id in prod_ids
                    if target_id
                    else ""
                ),

            "shadow_target_present":
                (
                    target_id in shadow_ids
                    if target_id
                    else ""
                ),

            "target_observed":
                bool(
                    target_found
                ),

            "regression":
                regression,
        }
    )


# ============================================================
# WRITE ARTIFACTS
# ============================================================

write_tsv(
    RECOVERY_TSV,
    recovery_rows,
)

write_tsv(
    R3_SHADOW_TSV,
    r3_shadow_rows,
)

write_tsv(
    ADVERSARIAL_TSV,
    adversarial_rows,
)

write_tsv(
    TOKEN_TSV,
    token_control_rows,
)

write_tsv(
    CANARY_TSV,
    canary_rows,
)


TRACE.write_text(
    "\n".join(
        (
            "=" * 78,
            " GENESIS RECALL R4-R10",
            " SUBJECT BOUNDARY NORMALIZATION SHADOW TRACE",
            "=" * 78,
            "",
            *trace_lines,
        )
    ),
    encoding="utf-8",
)


SOURCE_MAP.write_text(
    "\n".join(
        (
            "=" * 78,
            "SHADOW REPAIR",
            "=" * 78,
            inspect.getsource(
                dotted_aliases
            ),
            "",
            inspect.getsource(
                expand_subject_text
            ),
            "",
            inspect.getsource(
                shadow_analyze_subject
            ),
            "",
            "=" * 78,
            "PRODUCTION analyze_subject",
            "=" * 78,
            inspect.getsource(
                production_analyze_subject
            ),
            "",
            "=" * 78,
            "PRODUCTION QualificationEngine.evaluate_candidate",
            "=" * 78,
            inspect.getsource(
                QualificationEngine
                .evaluate_candidate
            ),
        )
    ),
    encoding="utf-8",
)


# ============================================================
# CERTIFICATION CALCULATIONS
# ============================================================

recovery_pct = (
    100.0
    * recovered
    / EXPECTED_FAILURES
)


r3_exact = (
    len(
        r3_rows
    )
    == EXPECTED_R3
)


r3_full_trace = (
    r3_resolved
    == EXPECTED_R3
    and
    r3_unresolved
    == 0
)


accepted_preservation = (
    accepted_controls
    > 0
    and
    accepted_controls_preserved
    == accepted_controls
    and
    accepted_controls_flipped
    == 0
)


adversarial_precision = (
    adversarial_shadow_increase
    == 0
    and
    adversarial_shadow_accept_total
    == 0
)


technical_preservation = (
    technical_original_token_loss
    == 0
)


known_canary_preservation = (
    canary_regressions
    == 0
)


# Strong recovery requirement.
#
# R4-R9 proved this is one universal 221-case class.
# A proposed exact repair should therefore recover nearly all
# of it. 95% leaves room for isolated data anomalies while
# refusing a weak partial workaround.
recovery_pass = (
    recovered
    >= 210
    and
    recovery_pct
    >= 95.0
)


no_unexpected_production_accepts = (
    production_unexpected_accept
    == 0
)


shadow_certified = all(
    (
        recovery_pass,
        target_missing == 0,
        no_unexpected_production_accepts,
        r3_exact,
        r3_full_trace,
        accepted_preservation,
        adversarial_precision,
        technical_preservation,
        known_canary_preservation,
    )
)


elapsed = (
    time.time()
    - started
)


report = {
    "phase":
        "Genesis Recall R4-R10",

    "repair":
        {
            "type":
                "SUBJECT_ONLY_DOTTED_TOKEN_ALIAS_EXPANSION",

            "production_tokenizer_changed":
                False,

            "production_subject_analyzer_changed":
                False,

            "global_tokenizer_replacement":
                False,

            "splits_dot":
                True,

            "splits_plus":
                False,

            "splits_hash":
                False,

            "splits_hyphen":
                False,

            "splits_underscore":
                False,

            "splits_colon":
                False,
        },

    "r4_r9_recovery":
        {
            "population":
                EXPECTED_FAILURES,

            "recovered":
                recovered,

            "recovery_percent":
                recovery_pct,

            "still_rejected":
                still_rejected,

            "subject_score_increased":
                subject_score_increase,

            "subject_score_not_increased":
                subject_score_not_increased,

            "alias_empty":
                alias_empty,

            "target_missing":
                target_missing,

            "multiple_target":
                multiple_target,

            "unexpected_production_accept":
                production_unexpected_accept,

            "pass":
                recovery_pass,
        },

    "r3_regression":
        {
            "expected_population":
                EXPECTED_R3,

            "actual_rows":
                len(
                    r3_rows
                ),

            "resolved":
                r3_resolved,

            "unresolved":
                r3_unresolved,

            "production_accepted_controls":
                accepted_controls,

            "accepted_controls_preserved":
                accepted_controls_preserved,

            "accepted_controls_flipped":
                accepted_controls_flipped,

            "production_rejected":
                r3_current_rejected,

            "shadow_recovered":
                r3_shadow_recovered,

            "shadow_still_rejected":
                r3_shadow_still_rejected,

            "accepted_preservation_pass":
                accepted_preservation,
        },

    "adversarial":
        {
            "queries":
                len(
                    ADVERSARIAL_QUERIES
                ),

            "queries_with_accept_increase":
                adversarial_shadow_increase,

            "shadow_accepted_total":
                adversarial_shadow_accept_total,

            "pass":
                adversarial_precision,
        },

    "technical_tokens":
        {
            "controls":
                len(
                    TOKEN_CONTROLS
                ),

            "controls_losing_original_token":
                technical_original_token_loss,

            "pass":
                technical_preservation,
        },

    "known_canaries":
        {
            "controls":
                len(
                    CANARIES
                ),

            "identity_canaries_observed":
                identity_canaries_resolved,

            "regressions":
                canary_regressions,

            "pass":
                known_canary_preservation,
        },

    "certification":
        {
            "recovery_pass":
                recovery_pass,

            "all_r4_r9_targets_resolved":
                target_missing
                == 0,

            "no_unexpected_production_accept":
                no_unexpected_production_accepts,

            "r3_exact_250":
                r3_exact,

            "r3_full_trace":
                r3_full_trace,

            "accepted_controls_preserved":
                accepted_preservation,

            "adversarial_precision":
                adversarial_precision,

            "technical_tokens_preserved":
                technical_preservation,

            "known_canaries_preserved":
                known_canary_preservation,
        },

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


# ============================================================
# CONSOLE RESULT
# ============================================================

print("=" * 78)
print(" GENESIS RECALL R4-R10 RESULT")
print("=" * 78)


print()
print("SHADOW REPAIR")

print(
    "  type                       :",
    report[
        "repair"
    ][
        "type"
    ],
)

print(
    "  production tokenizer change:",
    False,
)

print(
    "  boundary expanded          : DOT ONLY"
)


print()
print("R4-R9 SUBJECT FAILURE RECOVERY")

print(
    "  population                 :",
    EXPECTED_FAILURES,
)

print(
    "  recovered                  :",
    recovered,
)

print(
    "  recovery percent           :",
    round(
        recovery_pct,
        2,
    ),
)

print(
    "  still rejected             :",
    still_rejected,
)

print(
    "  subject score increased    :",
    subject_score_increase,
)

print(
    "  aliases empty              :",
    alias_empty,
)

print(
    "  target missing             :",
    target_missing,
)


print()
print("R3 DETERMINISTIC CORPUS REGRESSION")

print(
    "  census rows                :",
    len(
        r3_rows
    ),
)

print(
    "  resolved                   :",
    r3_resolved,
)

print(
    "  unresolved                 :",
    r3_unresolved,
)

print(
    "  production accepted        :",
    accepted_controls,
)

print(
    "  accepted preserved         :",
    accepted_controls_preserved,
)

print(
    "  accepted flipped to reject :",
    accepted_controls_flipped,
)

print(
    "  production rejected        :",
    r3_current_rejected,
)

print(
    "  shadow recovered           :",
    r3_shadow_recovered,
)

print(
    "  shadow still rejected      :",
    r3_shadow_still_rejected,
)


print()
print("ADVERSARIAL PRECISION")

print(
    "  queries                    :",
    len(
        ADVERSARIAL_QUERIES
    ),
)

print(
    "  accept-count increases     :",
    adversarial_shadow_increase,
)

print(
    "  shadow accepted total      :",
    adversarial_shadow_accept_total,
)


print()
print("TECHNICAL TOKEN PRESERVATION")

print(
    "  controls                   :",
    len(
        TOKEN_CONTROLS
    ),
)

print(
    "  original-token losses      :",
    technical_original_token_loss,
)


print()
print("KNOWN RECALL CANARIES")

print(
    "  controls                   :",
    len(
        CANARIES
    ),
)

print(
    "  identity canaries observed :",
    identity_canaries_resolved,
)

print(
    "  regressions                :",
    canary_regressions,
)


print()
print("CERTIFICATION")

for key, value in report[
    "certification"
].items():

    print(
        f"  {key:<38}: {value}"
    )


print()
print(
    "R4-R10 SHADOW CERTIFIED :",
    shadow_certified,
)


print()
print(
    "JSON report :",
    REPORT,
)

print(
    "recovery TSV:",
    RECOVERY_TSV,
)

print(
    "R3 shadow   :",
    R3_SHADOW_TSV,
)

print(
    "adversarial :",
    ADVERSARIAL_TSV,
)

print(
    "token TSV   :",
    TOKEN_TSV,
)

print(
    "canary TSV  :",
    CANARY_TSV,
)

print(
    "trace       :",
    TRACE,
)

print(
    "source map  :",
    SOURCE_MAP,
)

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
