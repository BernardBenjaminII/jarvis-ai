from __future__ import annotations

import csv
import inspect
import json
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

OUTDIR = PROJECT / "artifacts/genesis_recall"

R3_TSV = OUTDIR / "r3_production_recall_census.tsv"
R4R9_DETAIL = OUTDIR / "r4_r9_subject_lexical_differential.tsv"

REPORT = OUTDIR / "r4_r10_r1_identity_reconstruction.json"
R3_TRACE = OUTDIR / "r4_r10_r1_r3_identity_trace.tsv"
CANARY_TRACE = OUTDIR / "r4_r10_r1_canary_identity_trace.tsv"
RECOVERY_TSV = OUTDIR / "r4_r10_r1_subject_recovery.tsv"
ADVERSARIAL_TSV = OUTDIR / "r4_r10_r1_adversarial.tsv"
TOKEN_TSV = OUTDIR / "r4_r10_r1_token_preservation.tsv"
TRACE = OUTDIR / "r4_r10_r1_trace.txt"
SOURCE_MAP = OUTDIR / "r4_r10_r1_source_map.txt"

sys.path.insert(
    0,
    str(PROJECT),
)

from core.knowledge_catalog.search import search_catalog

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


EXPECTED_R3 = 250
EXPECTED_FAILURES = 221


# ============================================================
# FROZEN R4-R10 SHADOW REPAIR
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
        str(value or "")
    ):
        token = match.group(1)

        parts = [
            part
            for part in token.split(".")
            if part
        ]

        if len(parts) < 2:
            continue

        for part in parts:
            key = part.casefold()

            if key in seen:
                continue

            seen.add(key)
            aliases.append(part)

    return tuple(aliases)


def expand_subject_text(
    subject: str,
    title: str,
) -> tuple[str, tuple[str, ...]]:

    original = " ".join(
        part
        for part in (
            str(subject or ""),
            str(title or ""),
        )
        if part
    )

    aliases = []
    seen = set()

    for source in (
        subject,
        title,
    ):
        for alias in dotted_aliases(
            str(source or "")
        ):
            key = alias.casefold()

            if key in seen:
                continue

            seen.add(key)
            aliases.append(alias)

    expanded = " ".join(
        (
            original,
            *aliases,
        )
    ).strip()

    return expanded, tuple(aliases)


def shadow_analyze_subject(
    query: str,
    candidate_subject: str,
    candidate_title: str = "",
) -> SubjectAnalysis:

    expanded, _ = expand_subject_text(
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


@contextmanager
def shadow_subject_hook():

    original = evaluator_module.analyze_subject

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


def first_present(
    row: Mapping[str, Any],
    names: Iterable[str],
) -> str:

    lowered = {
        str(k).casefold(): k
        for k in row.keys()
    }

    for wanted in names:
        actual = lowered.get(
            wanted.casefold()
        )

        if actual is None:
            continue

        value = row.get(actual)

        if value not in (
            None,
            "",
        ):
            return str(value).strip()

    return ""


def raw_map(
    raw: Any,
) -> dict[str, Any]:

    if isinstance(raw, Mapping):
        return dict(raw)

    if hasattr(raw, "keys"):
        try:
            return {
                key: raw[key]
                for key in raw.keys()
            }
        except Exception:
            pass

    if hasattr(raw, "_asdict"):
        try:
            return dict(raw._asdict())
        except Exception:
            pass

    try:
        return dict(vars(raw))
    except Exception:
        return {}


def raw_identity_values(
    row: Mapping[str, Any],
) -> set[str]:

    result = set()

    for key in (
        "id",
        "document_id",
        "runtime_document_id",
        "runtime_id",
        "source_id",
        "doc_id",
        "catalog_id",
    ):
        value = row.get(key)

        if value not in (
            None,
            "",
        ):
            result.add(
                str(value).strip()
            )

    return {
        value
        for value in result
        if value
    }


def candidate_identity_values(
    candidate: EvidenceCandidate,
) -> set[str]:

    values = {
        str(candidate.source_id).strip()
    }

    try:
        metadata = dict(candidate.metadata)
    except Exception:
        metadata = {}

    values.update(
        raw_identity_values(metadata)
    )

    return {
        value
        for value in values
        if value
    }


def normalized_identity(
    value: Any,
) -> str:

    return str(
        value or ""
    ).strip().casefold()


def identity_equivalent(
    left: Any,
    right: Any,
) -> bool:

    a = normalized_identity(left)
    b = normalized_identity(right)

    if not a or not b:
        return False

    if a == b:
        return True

    try:
        return int(a) == int(b)
    except Exception:
        pass

    return False


def row_query(
    row: Mapping[str, Any],
) -> str:

    return first_present(
        row,
        (
            "query",
            "search_query",
            "qualification_query",
            "input_query",
            "derived_query",
        ),
    )


def row_target_values(
    row: Mapping[str, Any],
) -> set[str]:

    values = set()

    for key in (
        "document_id",
        "runtime_document_id",
        "target_document_id",
        "target_id",
        "doc_id",
        "source_id",
        "id",
        "runtime_id",
    ):
        value = first_present(
            row,
            (key,),
        )

        if value:
            values.add(value)

    return values


def identity_intersects(
    left: set[str],
    right: set[str],
) -> bool:

    for a in left:
        for b in right:
            if identity_equivalent(
                a,
                b,
            ):
                return True

    return False


# ============================================================
# MULTI-STRATEGY TARGET RESOLUTION
# ============================================================

def resolve_target(
    query: str,
    target_ids: set[str],
    *,
    preferred_title: str = "",
    preferred_subject: str = "",
    preferred_path: str = "",
    max_limit: int = 500,
):

    limits = (
        20,
        50,
        100,
        250,
        500,
    )

    attempts = []

    for limit in limits:

        if limit > max_limit:
            break

        rows = list(
            search_catalog(
                query,
                limit=limit,
            )
        )

        for ordinal, raw in enumerate(
            rows,
            start=1,
        ):
            mapped = raw_map(raw)

            ids = raw_identity_values(
                mapped
            )

            if target_ids and identity_intersects(
                target_ids,
                ids,
            ):
                candidate = candidate_from_row(
                    raw,
                    ordinal=ordinal,
                )

                return {
                    "candidate": candidate,
                    "raw": mapped,
                    "rank": ordinal,
                    "method": "EXACT_IDENTITY",
                    "limit": limit,
                }

        attempts.append(
            f"limit={limit}:identity_miss"
        )

    # --------------------------------------------------------
    # Fallback 1: exact title/subject/path equivalence.
    #
    # This does NOT synthesize metadata.
    # It only uses existing R3 artifact metadata to resolve
    # which raw candidate corresponds to the census target.
    # --------------------------------------------------------

    rows = list(
        search_catalog(
            query,
            limit=max_limit,
        )
    )

    field_matches = []

    for ordinal, raw in enumerate(
        rows,
        start=1,
    ):
        mapped = raw_map(raw)

        raw_title = str(
            mapped.get("title") or ""
        ).strip()

        raw_subject = str(
            mapped.get("subject") or ""
        ).strip()

        raw_path = str(
            mapped.get("source_path")
            or mapped.get("path")
            or ""
        ).strip()

        score = 0

        if (
            preferred_title
            and raw_title
            and raw_title == preferred_title
        ):
            score += 3

        if (
            preferred_subject
            and raw_subject
            and raw_subject == preferred_subject
        ):
            score += 3

        if (
            preferred_path
            and raw_path
            and raw_path == preferred_path
        ):
            score += 5

        if score > 0:
            field_matches.append(
                (
                    score,
                    ordinal,
                    raw,
                    mapped,
                )
            )

    if field_matches:
        field_matches.sort(
            key=lambda x: (
                -x[0],
                x[1],
            )
        )

        top = field_matches[0]

        if (
            len(field_matches) == 1
            or top[0] > field_matches[1][0]
        ):
            _score, ordinal, raw, mapped = top

            candidate = candidate_from_row(
                raw,
                ordinal=ordinal,
            )

            return {
                "candidate": candidate,
                "raw": mapped,
                "rank": ordinal,
                "method": "FIELD_PARITY",
                "limit": max_limit,
            }

    # --------------------------------------------------------
    # Fallback 2: exact single-candidate raw result.
    # --------------------------------------------------------

    if len(rows) == 1:
        candidate = candidate_from_row(
            rows[0],
            ordinal=1,
        )

        return {
            "candidate": candidate,
            "raw": raw_map(rows[0]),
            "rank": 1,
            "method": "SINGLE_RAW_RESULT",
            "limit": max_limit,
        }

    return {
        "candidate": None,
        "raw": None,
        "rank": None,
        "method": "UNRESOLVED",
        "limit": max_limit,
        "attempts": attempts,
    }


def evaluate_one(
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
                (candidate,),
            )
    else:
        result = engine.evaluate(
            query,
            (candidate,),
        )

    evidence = (
        *result.accepted,
        *result.rejected,
    )

    if len(evidence) != 1:
        raise RuntimeError(
            f"unexpected evidence count {len(evidence)}"
        )

    return evidence[0]


def accepted(
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
# A. EXACT R3 IDENTITY RECONSTRUCTION
# ============================================================

started = time.time()

r3_rows = read_tsv(
    R3_TSV
)

if len(r3_rows) != EXPECTED_R3:
    raise RuntimeError(
        f"expected 250 R3 rows, got {len(r3_rows)}"
    )


r3_trace_rows = []

r3_resolved = 0
r3_unresolved = 0

resolution_methods = Counter()

accepted_prod = 0
accepted_shadow_preserved = 0
accepted_shadow_flipped = 0

prod_rejected = 0
shadow_recovered = 0
shadow_still_rejected = 0


engine = QualificationEngine()


for index, row in enumerate(
    r3_rows,
    start=1,
):

    query = row_query(row)
    target_ids = row_target_values(row)

    title = first_present(
        row,
        (
            "title",
            "candidate_title",
            "raw_title",
            "document_title",
        ),
    )

    subject = first_present(
        row,
        (
            "candidate_subject",
            "raw_subject",
            "document_subject",
        ),
    )

    path = first_present(
        row,
        (
            "source_path",
            "path",
            "candidate_source_path",
            "raw_source_path",
        ),
    )


    if not query:

        r3_unresolved += 1

        r3_trace_rows.append(
            {
                "row": index,
                "status": "MISSING_QUERY",
            }
        )

        continue


    resolved = resolve_target(
        query,
        target_ids,
        preferred_title=title,
        preferred_subject=subject,
        preferred_path=path,
        max_limit=500,
    )


    candidate = resolved[
        "candidate"
    ]


    if candidate is None:

        r3_unresolved += 1

        resolution_methods[
            "UNRESOLVED"
        ] += 1

        r3_trace_rows.append(
            {
                "row": index,
                "query": query,
                "target_ids": "|".join(
                    sorted(target_ids)
                ),
                "status": "UNRESOLVED",
                "method": resolved["method"],
            }
        )

        continue


    r3_resolved += 1

    resolution_methods[
        resolved["method"]
    ] += 1


    prod = evaluate_one(
        engine,
        query,
        candidate,
        shadow=False,
    )

    shadow = evaluate_one(
        engine,
        query,
        candidate,
        shadow=True,
    )


    prod_ok = accepted(prod)
    shadow_ok = accepted(shadow)


    if prod_ok:
        accepted_prod += 1

        if shadow_ok:
            accepted_shadow_preserved += 1
        else:
            accepted_shadow_flipped += 1

    else:
        prod_rejected += 1

        if shadow_ok:
            shadow_recovered += 1
        else:
            shadow_still_rejected += 1


    aliases = expand_subject_text(
        candidate.subject,
        candidate.title,
    )[1]


    r3_trace_rows.append(
        {
            "row": index,
            "query": query,
            "target_ids": "|".join(
                sorted(target_ids)
            ),
            "candidate_ids": "|".join(
                sorted(
                    candidate_identity_values(
                        candidate
                    )
                )
            ),
            "candidate_title": candidate.title,
            "candidate_subject": candidate.subject,
            "candidate_path": candidate.source_path,
            "raw_rank": resolved["rank"],
            "resolution_method": resolved["method"],
            "aliases": ",".join(aliases),
            "production_subject_score":
                float(prod.score.subject),
            "shadow_subject_score":
                float(shadow.score.subject),
            "production_decision":
                str(prod.decision),
            "shadow_decision":
                str(shadow.decision),
            "production_accepted":
                prod_ok,
            "shadow_accepted":
                shadow_ok,
            "status": "OK",
        }
    )


# ============================================================
# B. KNOWN IDENTITY CANARIES
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
)


canary_rows = []

canaries_resolved = 0
canaries_prod_present = 0
canaries_shadow_present = 0
canary_regressions = 0


for name, query, target_id in CANARIES:

    resolved = resolve_target(
        query,
        {target_id},
        max_limit=500,
    )

    candidate = resolved[
        "candidate"
    ]


    if candidate is None:

        canary_rows.append(
            {
                "name": name,
                "query": query,
                "target_id": target_id,
                "status": "UNRESOLVED",
                "resolution_method":
                    resolved["method"],
            }
        )

        continue


    canaries_resolved += 1


    candidate_ids = candidate_identity_values(
        candidate
    )


    identity_match = identity_intersects(
        {target_id},
        candidate_ids,
    )


    prod = evaluate_one(
        engine,
        query,
        candidate,
        shadow=False,
    )

    shadow = evaluate_one(
        engine,
        query,
        candidate,
        shadow=True,
    )


    prod_ok = accepted(prod)
    shadow_ok = accepted(shadow)


    if prod_ok:
        canaries_prod_present += 1

    if shadow_ok:
        canaries_shadow_present += 1

    if prod_ok and not shadow_ok:
        canary_regressions += 1


    canary_rows.append(
        {
            "name": name,
            "query": query,
            "target_id": target_id,
            "candidate_ids": "|".join(
                sorted(candidate_ids)
            ),
            "identity_match": identity_match,
            "resolution_method":
                resolved["method"],
            "raw_rank": resolved["rank"],
            "production_accepted": prod_ok,
            "shadow_accepted": shadow_ok,
            "production_decision":
                str(prod.decision),
            "shadow_decision":
                str(shadow.decision),
            "status": "OK",
        }
    )


# ============================================================
# C. RE-RUN 221 EXACT R4-R9 RECOVERY
# ============================================================

r4r9_rows = [
    row
    for row in read_tsv(
        R4R9_DETAIL
    )
    if row.get(
        "status",
        ""
    )
    == "OK"
]


if len(r4r9_rows) != EXPECTED_FAILURES:
    raise RuntimeError(
        f"expected 221 R4-R9 rows, got {len(r4r9_rows)}"
    )


recovery_rows = []

recovered = 0
still_rejected = 0
recovery_missing = 0


for index, row in enumerate(
    r4r9_rows,
    start=1,
):

    query = row["query"]
    target_id = str(
        row["document_id"]
    ).strip()


    resolved = resolve_target(
        query,
        {target_id},
        preferred_title=row.get(
            "candidate_title",
            "",
        ),
        preferred_subject=row.get(
            "candidate_subject",
            "",
        ),
        preferred_path=row.get(
            "candidate_source_path",
            "",
        ),
        max_limit=500,
    )


    candidate = resolved[
        "candidate"
    ]


    if candidate is None:

        recovery_missing += 1

        recovery_rows.append(
            {
                "case": index,
                "query": query,
                "document_id": target_id,
                "status": "UNRESOLVED",
            }
        )

        continue


    prod = evaluate_one(
        engine,
        query,
        candidate,
        shadow=False,
    )

    shadow = evaluate_one(
        engine,
        query,
        candidate,
        shadow=True,
    )


    prod_ok = accepted(prod)
    shadow_ok = accepted(shadow)


    if not prod_ok and shadow_ok:
        recovered += 1

    if not shadow_ok:
        still_rejected += 1


    aliases = expand_subject_text(
        candidate.subject,
        candidate.title,
    )[1]


    recovery_rows.append(
        {
            "case": index,
            "query": query,
            "document_id": target_id,
            "resolution_method":
                resolved["method"],
            "aliases": ",".join(
                aliases
            ),
            "production_subject":
                float(prod.score.subject),
            "shadow_subject":
                float(shadow.score.subject),
            "production_decision":
                str(prod.decision),
            "shadow_decision":
                str(shadow.decision),
            "recovered":
                (
                    not prod_ok
                    and shadow_ok
                ),
            "status": "OK",
        }
    )


# ============================================================
# D. ADVERSARIAL REGRESSION
# ============================================================

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


adversarial_rows = []

adversarial_increase = 0
adversarial_shadow_total = 0


for query in ADVERSARIAL:

    raw_rows = list(
        search_catalog(
            query,
            limit=20,
        )
    )

    candidates = tuple(
        candidate_from_row(
            raw,
            ordinal=i,
        )
        for i, raw in enumerate(
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


    prod_count = len(
        prod_result.accepted
    )

    shadow_count = len(
        shadow_result.accepted
    )


    adversarial_shadow_total += (
        shadow_count
    )


    if shadow_count > prod_count:
        adversarial_increase += 1


    adversarial_rows.append(
        {
            "query": query,
            "raw_candidates":
                len(candidates),
            "production_accepted":
                prod_count,
            "shadow_accepted":
                shadow_count,
            "increased":
                shadow_count > prod_count,
        }
    )


# ============================================================
# E. TECHNICAL TOKEN PRESERVATION
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


token_rows = []

token_losses = 0


for query, candidate_text in TOKEN_CONTROLS:

    before = tokenize(
        candidate_text
    )

    expanded, aliases = expand_subject_text(
        candidate_text,
        "",
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
        token_losses += 1


    token_rows.append(
        {
            "query": query,
            "candidate_text":
                candidate_text,
            "production_tokens":
                ",".join(before),
            "shadow_tokens":
                ",".join(after),
            "aliases":
                ",".join(aliases),
            "lost_original_tokens":
                ",".join(lost),
            "production_score":
                float(
                    analyze_lexical(
                        query,
                        candidate_text,
                    ).score
                ),
            "shadow_score":
                float(
                    analyze_lexical(
                        query,
                        expanded,
                    ).score
                ),
            "original_tokens_preserved":
                not bool(lost),
        }
    )


# ============================================================
# F. CERTIFICATION
# ============================================================

recovery_pct = (
    100.0
    * recovered
    / EXPECTED_FAILURES
)


r3_full_trace = (
    r3_resolved == EXPECTED_R3
    and
    r3_unresolved == 0
)


accepted_preserved = (
    accepted_prod > 0
    and
    accepted_shadow_preserved
    == accepted_prod
    and
    accepted_shadow_flipped == 0
)


identity_canaries_complete = (
    canaries_resolved
    == len(CANARIES)
)


canary_preservation = (
    identity_canaries_complete
    and
    canary_regressions == 0
)


adversarial_pass = (
    adversarial_increase == 0
    and
    adversarial_shadow_total == 0
)


technical_pass = (
    token_losses == 0
)


recovery_pass = (
    recovered >= 219
    and
    recovery_pct >= 99.0
    and
    recovery_missing == 0
)


certification = {
    "exact_r3_population":
        len(r3_rows) == 250,

    "r3_full_identity_trace":
        r3_full_trace,

    "accepted_controls_preserved":
        accepted_preserved,

    "identity_canaries_resolved":
        identity_canaries_complete,

    "identity_canaries_preserved":
        canary_preservation,

    "r4_r9_recovery_pass":
        recovery_pass,

    "adversarial_precision":
        adversarial_pass,

    "technical_tokens_preserved":
        technical_pass,
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
        "Genesis Recall R4-R10-R1",

    "repair":
        {
            "type":
                "SUBJECT_ONLY_DOTTED_TOKEN_ALIAS_EXPANSION",

            "changed_from_r4_r10":
                False,

            "production_source_changed":
                False,

            "production_tokenizer_changed":
                False,
        },

    "r3_identity": {
        "population":
            len(r3_rows),

        "resolved":
            r3_resolved,

        "unresolved":
            r3_unresolved,

        "resolution_methods":
            dict(
                resolution_methods
            ),

        "production_accepted":
            accepted_prod,

        "accepted_preserved":
            accepted_shadow_preserved,

        "accepted_flipped":
            accepted_shadow_flipped,

        "production_rejected":
            prod_rejected,

        "shadow_recovered":
            shadow_recovered,

        "shadow_still_rejected":
            shadow_still_rejected,
    },

    "canaries": {
        "population":
            len(CANARIES),

        "resolved":
            canaries_resolved,

        "production_accepted":
            canaries_prod_present,

        "shadow_accepted":
            canaries_shadow_present,

        "regressions":
            canary_regressions,
    },

    "r4_r9_recovery": {
        "population":
            EXPECTED_FAILURES,

        "resolved":
            EXPECTED_FAILURES
            - recovery_missing,

        "unresolved":
            recovery_missing,

        "recovered":
            recovered,

        "recovery_percent":
            recovery_pct,

        "still_rejected":
            still_rejected,
    },

    "adversarial": {
        "queries":
            len(ADVERSARIAL),

        "accept_increases":
            adversarial_increase,

        "shadow_accepted_total":
            adversarial_shadow_total,
    },

    "technical_tokens": {
        "controls":
            len(TOKEN_CONTROLS),

        "controls_with_loss":
            token_losses,
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
    r3_trace_rows,
)

write_tsv(
    CANARY_TRACE,
    canary_rows,
)

write_tsv(
    RECOVERY_TSV,
    recovery_rows,
)

write_tsv(
    ADVERSARIAL_TSV,
    adversarial_rows,
)

write_tsv(
    TOKEN_TSV,
    token_rows,
)


TRACE.write_text(
    "\n".join(
        (
            "=" * 78,
            " GENESIS RECALL R4-R10-R1",
            " R3 IDENTITY RECONSTRUCTION TRACE",
            "=" * 78,
            "",
            f"R3 resolved   : {r3_resolved}",
            f"R3 unresolved : {r3_unresolved}",
            "",
            "RESOLUTION METHODS",
            *[
                f"  {k}: {v}"
                for k, v
                in sorted(
                    resolution_methods.items()
                )
            ],
            "",
            f"Canaries resolved: {canaries_resolved}/{len(CANARIES)}",
            f"Canary regressions: {canary_regressions}",
            "",
            f"R4-R9 recovered: {recovered}/{EXPECTED_FAILURES}",
            f"Recovery percent: {recovery_pct:.2f}",
            "",
        )
    ),
    encoding="utf-8",
)


SOURCE_MAP.write_text(
    "\n".join(
        (
            "=" * 78,
            "FROZEN R4-R10 SHADOW REPAIR",
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
            "IDENTITY RESOLUTION",
            "=" * 78,
            inspect.getsource(
                resolve_target
            ),
        )
    ),
    encoding="utf-8",
)


# ============================================================
# CONSOLE RESULT
# ============================================================

print("=" * 78)
print(" GENESIS RECALL R4-R10-R1 RESULT")
print("=" * 78)

print()
print("R3 IDENTITY RECONSTRUCTION")

print(
    "  population                 :",
    len(r3_rows),
)

print(
    "  resolved                   :",
    r3_resolved,
)

print(
    "  unresolved                 :",
    r3_unresolved,
)

print()
print("RESOLUTION METHODS")

for name, count in sorted(
    resolution_methods.items(),
    key=lambda item: (
        -item[1],
        item[0],
    ),
):
    print(
        f"  {name:<32} {count}"
    )

print()
print("R3 REGRESSION")

print(
    "  production accepted        :",
    accepted_prod,
)

print(
    "  accepted preserved         :",
    accepted_shadow_preserved,
)

print(
    "  accepted flipped           :",
    accepted_shadow_flipped,
)

print(
    "  production rejected        :",
    prod_rejected,
)

print(
    "  shadow recovered           :",
    shadow_recovered,
)

print(
    "  shadow still rejected      :",
    shadow_still_rejected,
)

print()
print("IDENTITY CANARIES")

print(
    "  population                 :",
    len(CANARIES),
)

print(
    "  resolved                   :",
    canaries_resolved,
)

print(
    "  production accepted        :",
    canaries_prod_present,
)

print(
    "  shadow accepted            :",
    canaries_shadow_present,
)

print(
    "  regressions                :",
    canary_regressions,
)

print()
print("R4-R9 SUBJECT RECOVERY")

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
    "  unresolved                 :",
    recovery_missing,
)

print()
print("ADVERSARIAL PRECISION")

print(
    "  accept increases           :",
    adversarial_increase,
)

print(
    "  shadow accepted total      :",
    adversarial_shadow_total,
)

print()
print("TECHNICAL TOKENS")

print(
    "  controls                   :",
    len(TOKEN_CONTROLS),
)

print(
    "  controls with token loss   :",
    token_losses,
)

print()
print("CERTIFICATION")

for key, value in certification.items():
    print(
        f"  {key:<38}: {value}"
    )

print()
print(
    "R4-R10-R1 SHADOW CERTIFIED :",
    shadow_certified,
)

print()
print("Artifacts:")
print(" ", REPORT)
print(" ", R3_TRACE)
print(" ", CANARY_TRACE)
print(" ", RECOVERY_TSV)
print(" ", ADVERSARIAL_TSV)
print(" ", TOKEN_TSV)
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
