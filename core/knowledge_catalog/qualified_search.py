from __future__ import annotations

from contextvars import ContextVar
from pathlib import Path
from typing import Any, Iterable, Mapping

from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.knowledge_catalog.search import search_catalog
from core.retrieval.qualification import (
    EvidenceCandidate,
    QualificationDiagnostic,
    QualificationEngine,
    QualificationResult,
)


_LAST_TRACE: ContextVar[dict[str, Any] | None] = ContextVar(
    "jarvis_last_qualification_trace",
    default=None,
)

_LAST_RESULT: ContextVar[QualificationResult | None] = ContextVar(
    "jarvis_last_qualification_result",
    default=None,
)


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)

    try:
        return dict(value)
    except Exception:
        return {}


def candidate_from_row(
    row: Mapping[str, Any] | Any,
    *,
    ordinal: int,
) -> EvidenceCandidate:
    data = _mapping(row)

    source_path = str(
        data.get("file_path")
        or data.get("source_path")
        or data.get("path")
        or ""
    )
    source_id = str(
        data.get("source_id")
        or data.get("chunk_id")
        or data.get("document_id")
        or source_path
        or f"candidate-{ordinal}"
    )
    title = str(
        data.get("title")
        or data.get("document_title")
        or Path(source_path).name
        or source_id
    )
    subject = str(
        data.get("subject")
        or data.get("topic")
        or data.get("domain")
        or ""
    )
    excerpt = str(
        data.get("excerpt")
        or data.get("chunk_text")
        or data.get("text")
        or data.get("content")
        or data.get("summary")
        or ""
    )
    backend = str(
        data.get("backend")
        or data.get("retrieval_backend")
        or data.get("assigned_by")
        or "runtime_fts"
    )

    # GENESIS_RECALL_R4_R11_A5_R9_R9_R1
    # Prefer certified modern retrieval scores when explicitly supplied.
    # Existing retrieval/confidence/score fallback remains unchanged.
    raw_score = data.get("hybrid_score")
    if raw_score is None:
        raw_score = data.get("semantic_score")
    if raw_score is None:
        raw_score = data.get("retrieval_score")

    if raw_score is None:
        raw_score = data.get("confidence")

    if raw_score is None:
        raw_score = data.get("score", 0.0)

    try:
        retrieval_score = float(raw_score or 0.0)
    except (TypeError, ValueError):
        retrieval_score = 0.0

    return EvidenceCandidate(
        source_id=source_id,
        source_path=source_path,
        title=title,
        subject=subject,
        excerpt=excerpt,
        backend=backend,
        retrieval_score=retrieval_score,
        metadata={
            "raw_row": data,
            "ordinal": ordinal,
        },
    )


def qualified_row(evidence: Any) -> dict[str, Any]:
    raw = dict(
        evidence.candidate.metadata.get("raw_row")
        or {}
    )

    raw.update(
        {
            "qualification_decision": evidence.decision.value,
            "qualification_score": evidence.score.final,
            "qualification_explanation": evidence.explanation,
            "qualification_components": evidence.score.to_dict(),
        }
    )

    raw.setdefault(
        "file_path",
        evidence.candidate.source_path,
    )
    raw.setdefault(
        "source_path",
        evidence.candidate.source_path,
    )
    raw.setdefault(
        "title",
        evidence.candidate.title,
    )
    raw.setdefault(
        "subject",
        evidence.candidate.subject,
    )
    raw.setdefault(
        "excerpt",
        evidence.candidate.excerpt,
    )
    raw.setdefault(
        "confidence",
        evidence.score.final,
    )
    raw.setdefault(
        "assigned_by",
        "qualification_engine",
    )

    return raw


def qualify_rows(
    query: str,
    rows: Iterable[Mapping[str, Any] | Any],
    *,
    engine: QualificationEngine | None = None,
) -> tuple[list[dict[str, Any]], QualificationResult]:
    active_engine = engine or QualificationEngine()
    row_list = list(rows)

    candidates = tuple(
        candidate_from_row(
            row,
            ordinal=index,
        )
        for index, row in enumerate(
            row_list,
            start=1,
        )
    )

    result = active_engine.evaluate(
        query,
        candidates,
    )

    accepted_rows = [
        qualified_row(item)
        for item in result.accepted
    ]

    diagnostics = [
        QualificationDiagnostic.from_evidence(
            query,
            item,
        ).to_dict()
        for item in (
            *result.accepted,
            *result.rejected,
        )
    ]

    _LAST_RESULT.set(result)

    _LAST_TRACE.set(
        {
            "query": query,
            "candidate_count": result.total_candidates,
            "accepted_count": len(result.accepted),
            "rejected_count": len(result.rejected),
            "threshold": result.threshold,
            "runtime_statistics": dict(
                result.runtime_statistics
            ),
            "diagnostics": diagnostics,
        }
    )

    return accepted_rows, result


# GENESIS_QUALIFICATION_GATE_REPAIR_R1
#
# R1 principle:
# subject alignment and raw retrieval confidence remain useful signals,
# but neither may veto a candidate that contains strong deterministic
# query evidence and already clears the normal final qualification score.
#
# This avoids globally weakening QualificationEngine.

_GATE_REPAIR_STOPWORDS = frozenset({
    "a", "an", "and", "any", "are", "about", "can", "could",
    "do", "does", "for", "from", "have", "i", "in", "information",
    "is", "it", "me", "my", "of", "on", "please", "say", "show",
    "tell", "the", "there", "to", "what", "whatever", "which",
    "with", "you", "your",
})


def _gate_repair_tokens(value: str) -> tuple[str, ...]:
    import re

    normalized = re.sub(
        r"[^a-z0-9+#.-]+",
        " ",
        str(value or "").lower(),
    )

    tokens = tuple(
        token.strip(" .")
        for token in normalized.split()
        if token.strip(" .")
    )

    meaningful = tuple(
        token
        for token in tokens
        if token not in _GATE_REPAIR_STOPWORDS
        and len(token) > 1
    )

    return meaningful or tokens


def _gate_repair_normalized_text(value: str) -> str:
    import re

    return " ".join(
        re.sub(
            r"[^a-z0-9+#.-]+",
            " ",
            str(value or "").lower(),
        ).split()
    )


def _gate_repair_candidate_text(candidate: Any) -> str:
    return _gate_repair_normalized_text(
        " ".join(
            (
                str(getattr(candidate, "title", "") or ""),
                str(getattr(candidate, "subject", "") or ""),
                str(getattr(candidate, "excerpt", "") or ""),
            )
        )
    )




def _r9_r14_r3_modern_semantic_signal(
    evidence: Any,
) -> tuple[bool, str, float]:

    # GENESIS_RECALL_R4_R11_A5_R9_R14_R3_MODERN_SEMANTIC_RESCUE

    candidate = evidence.candidate

    metadata = getattr(
        candidate,
        "metadata",
        None,
    )

    if not isinstance(
        metadata,
        Mapping,
    ):
        return (
            False,
            "modern_metadata_missing",
            0.0,
        )

    raw_row = metadata.get(
        "raw_row"
    )

    if not isinstance(
        raw_row,
        Mapping,
    ):
        return (
            False,
            "modern_raw_row_missing",
            0.0,
        )

    if raw_row.get(
        "hybrid_score"
    ) is not None:

        score_name = (
            "hybrid_score"
        )

        raw_score = raw_row.get(
            "hybrid_score"
        )

    elif raw_row.get(
        "semantic_score"
    ) is not None:

        score_name = (
            "semantic_score"
        )

        raw_score = raw_row.get(
            "semantic_score"
        )

    else:

        return (
            False,
            "modern_score_absent",
            0.0,
        )

    try:

        modern_score = float(
            raw_score
        )

    except (
        TypeError,
        ValueError,
    ):

        return (
            False,
            score_name + "_invalid",
            0.0,
        )

    if not (
        0.0
        <= modern_score
        <= 1.0
    ):

        return (
            False,
            score_name + "_out_of_range",
            modern_score,
        )

    return (
        True,
        score_name,
        modern_score,
    )



def _gate_repair_should_rescue(
    query: str,
    evidence: Any,
    *,
    threshold: float,
) -> tuple[bool, str]:
    """
    Rescue a candidate only when the candidate itself contains strong,
    deterministic support for the meaningful query terms.

    This is intentionally stricter than merely lowering subject or
    confidence thresholds.
    """

    candidate = evidence.candidate
    score = evidence.score

    tokens = _gate_repair_tokens(query)

    # Avoid rescue based on vague single-token queries.
    if len(tokens) < 2:
        return False, "core_query_too_short"

    haystack = _gate_repair_candidate_text(candidate)

    if not haystack:
        return False, "empty_candidate_text"

    # All meaningful terms must actually occur in the candidate.
    missing = tuple(
        token
        for token in tokens
        if token not in haystack
    )

    # A semantic score is a ranking signal, not proof of topical identity.
    # Never allow it to bypass the deterministic query-term gate.  The old
    # bypass admitted high-scoring but unrelated passages (for example,
    # shelter instructions for a gardening query).
    if missing:
        return False, "missing_core_terms:" + ",".join(missing)

    phrase = " ".join(tokens)
    phrase_match = phrase in haystack

    try:
        final_score = float(score.final)
    except Exception:
        final_score = 0.0

    try:
        lexical = float(score.lexical)
    except Exception:
        lexical = 0.0

    try:
        entity = float(score.entity)
    except Exception:
        entity = 0.0

    try:
        provenance = float(score.provenance)
    except Exception:
        provenance = 0.0

    # Existing global score remains mandatory.
    if final_score < float(threshold):
        return False, "final_below_threshold"

    # GENESIS RECALL R1F-R3
    #
    # Shadow-certified fallback for low-confidence evidence that
    # contains every meaningful query term and independently
    # demonstrates strong relevance.
    #
    # This does not lower the normal QualificationEngine thresholds
    # and does not alter the existing strict rescue path.
    if lexical < 0.80:
        try:
            subject = float(score.subject)
        except Exception:
            subject = 0.0

        if (
            len(tokens) >= 3
            and lexical >= 0.70
            and entity >= 0.70
            and subject >= 0.20
            and provenance >= 0.50
        ):
            return (
                True,
                "complete_core_term_coverage_strong_subject",
            )

        return False, "lexical_below_rescue_floor"

    # Entity overlap gives another independent deterministic signal.
    if entity < 0.75:
        return False, "entity_below_rescue_floor"

    # Do not rescue evidence with weak provenance.
    if provenance < 0.50:
        return False, "provenance_below_rescue_floor"

    # Exact core phrase is the preferred rescue condition.
    if phrase_match:
        return True, "exact_core_phrase"

    # For 3+ meaningful terms, complete token coverage can substitute
    # for adjacency because OCR and PDF extraction frequently split
    # words/phrases irregularly.
    if len(tokens) >= 3:
        return True, "complete_core_term_coverage"

    return False, "two_term_query_requires_phrase"



# ============================================================
# GENESIS_RECALL_R2_R2A_R4_R8_IDENTITY_HELPER
#
# Exact document-identity rescue.
#
# EvidenceCandidate.source_id is a CHUNK identity.
#
# Durable document identity is preserved at:
#
#   candidate.metadata["raw_row"]["document_id"]
#
# Rescue is permitted only when the query uniquely identifies
# exactly ONE document_id across the current QualificationResult.
#
# Ordinary qualification and R1F remain authoritative first.
# ============================================================

_R2_IDENTITY_STOPWORDS = frozenset(
    {
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
    }
)


def _r2_identity_tokens(
    value: Any,
) -> tuple[str, ...]:
    import re

    normalized = re.sub(
        r"[^a-z0-9]+",
        " ",
        str(value or "").lower(),
    )

    output: list[str] = []

    for token in normalized.split():

        if token in _R2_IDENTITY_STOPWORDS:
            continue

        if (
            len(token) <= 1
            and not token.isdigit()
        ):
            continue

        if token not in output:
            output.append(token)

    return tuple(output)


def _r2_evidence_document_id(
    evidence: Any,
) -> int | None:
    """
    Return durable DOCUMENT identity.

    Do not use candidate.source_id here:
    source_id is the chunk identity in the current retrieval stack.
    """

    try:
        candidate = evidence.candidate
    except Exception:
        return None

    try:
        metadata = candidate.metadata
    except Exception:
        metadata = None

    if metadata is None:
        return None

    try:
        raw_row = metadata.get("raw_row")
    except Exception:
        return None

    if raw_row is None:
        return None

    try:
        value = raw_row.get("document_id")
    except Exception:
        return None

    if value is None:
        return None

    try:
        return int(value)
    except Exception:
        return None


def _r2_evidence_chunk_id(
    evidence: Any,
) -> int | None:
    """
    Diagnostic only. Chunk identity must never be substituted
    for durable document identity.
    """

    try:
        candidate = evidence.candidate
    except Exception:
        return None

    try:
        value = candidate.source_id
    except Exception:
        return None

    try:
        return int(value)
    except Exception:
        return None


def _r2_candidate_identity_fields(
    evidence: Any,
) -> tuple[str, ...]:
    import re

    try:
        candidate = evidence.candidate
    except Exception:
        return ()

    values: list[str] = []

    # Require complete query coverage inside one explicit identity
    # field. Do not combine fragments from unrelated fields.
    for name in (
        "title",
        "subject",
        "source_path",
    ):

        try:
            value = getattr(
                candidate,
                name,
                None,
            )
        except Exception:
            value = None

        if not value:
            continue

        normalized = " ".join(
            re.sub(
                r"[^a-z0-9]+",
                " ",
                str(value).lower(),
            ).split()
        )

        if normalized:
            values.append(normalized)

    return tuple(values)


def _r2_identity_evidence_matches_query(
    query: str,
    evidence: Any,
) -> bool:
    """
    Conservative deterministic identity test.

    A candidate qualifies as an identity match only when:
      - durable document_id is present;
      - query has >= 4 meaningful tokens;
      - every meaningful query token is present in ONE
        candidate identity field;
      - provenance is complete.
    """

    document_id = _r2_evidence_document_id(
        evidence
    )

    if document_id is None:
        return False

    tokens = _r2_identity_tokens(
        query
    )

    # Avoid rescuing generic short queries such as:
    # "Lane Lexicon" or "Arabic dictionary".
    if len(tokens) < 4:
        return False

    fields = _r2_candidate_identity_fields(
        evidence
    )

    if not fields:
        return False

    complete_field_match = False

    for field in fields:

        field_tokens = set(
            field.split()
        )

        if all(
            token in field_tokens
            for token in tokens
        ):
            complete_field_match = True
            break

    if not complete_field_match:
        return False

    try:
        provenance = float(
            evidence.score.provenance
        )
    except Exception:
        provenance = 0.0

    if provenance < 1.0:
        return False

    return True


def _r2_exact_identity_targets(
    query: str,
    result: Any,
) -> frozenset[int]:
    """
    Determine document identity independently across the complete
    QualificationResult evidence universe.

    Many chunks may map to the same document. They collapse into
    one durable document_id.

    A rescue is allowed only when the resulting document-id set
    contains exactly one member.
    """

    document_ids: set[int] = set()

    evidence_pool = (
        tuple(
            getattr(
                result,
                "accepted",
                (),
            )
            or ()
        )
        +
        tuple(
            getattr(
                result,
                "rejected",
                (),
            )
            or ()
        )
    )

    for evidence in evidence_pool:

        if not _r2_identity_evidence_matches_query(
            query,
            evidence,
        ):
            continue

        document_id = _r2_evidence_document_id(
            evidence
        )

        if document_id is not None:
            document_ids.add(
                document_id
            )

    return frozenset(
        document_ids
    )


def _r2_exact_document_identity_should_rescue(
    query: str,
    evidence: Any,
    *,
    target_document_ids: frozenset[int],
) -> tuple[bool, str]:
    """
    Rescue only an exact, uniquely identified durable document.

    This is NOT a lower relevance threshold.
    """

    if len(target_document_ids) == 0:
        return (
            False,
            "identity_target_not_found",
        )

    if len(target_document_ids) != 1:
        return (
            False,
            "identity_target_ambiguous",
        )

    document_id = _r2_evidence_document_id(
        evidence
    )

    if document_id is None:
        return (
            False,
            "document_identity_unavailable",
        )

    target_document_id = next(
        iter(target_document_ids)
    )

    if document_id != target_document_id:
        return (
            False,
            "document_identity_mismatch",
        )

    if not _r2_identity_evidence_matches_query(
        query,
        evidence,
    ):
        return (
            False,
            "document_identity_query_mismatch",
        )

    return (
        True,
        "exact_unique_document_identity",
    )



def _gate_repair_qualified_row(
    evidence: Any,
    *,
    reason: str,
) -> dict[str, Any]:
    row = qualified_row(evidence)

    row["qualification_decision_original"] = row.get(
        "qualification_decision"
    )

    row["qualification_decision"] = "accepted_content_rescue"
    row["qualification_rescue"] = True
    row["qualification_rescue_reason"] = reason

    row["assigned_by"] = "qualification_gate_repair_r1"

    return row


# GENESIS_CONVERSATIONAL_QUERY_NORMALIZATION_R1_1
#
# R1.1 principle:
#
# The Executive may receive natural conversational questions while the
# catalog retrieval layer performs best on compact topical queries.
#
# R1.1 therefore:
#
#   1. preserves the original operator query;
#   2. derives a conservative normalized retrieval variant;
#   3. searches BOTH forms when they differ;
#   4. merges and deduplicates the candidate pools;
#   5. qualifies against the normalized topical query;
#   6. preserves R1's conservative content rescue;
#   7. records the transformation in the qualification trace.
#
# It does NOT perform global stopword deletion and does NOT rewrite
# arbitrary queries.

_CONVERSATIONAL_QUERY_PATTERNS = (
    # "What qualified documents do you have about ..."
    #
    # Document-discovery wording describes the requested response shape; it
    # is not part of the topic.  Leaving these terms in the query causes the
    # strict qualification gate to demand that source passages discuss
    # "qualified documents" as well as the actual subject.
    r"^\s*what\s+(?:qualified\s+)?(?:documents?|sources?|materials?)\s+"
    r"(?:do\s+you\s+have|are\s+available)\s+"
    r"(?:(?:in|from)\s+(?:the\s+)?knowledge\s+catalog\s+)?"
    r"(?:on|about)\s+",

    # "Do you have ..."
    r"^\s*do\s+you\s+have\s+(?:any\s+)?information\s+(?:on|about)\s+",
    r"^\s*do\s+you\s+have\s+(?:anything|something)\s+(?:on|about)\s+",

    # "Do I have ..."
    r"^\s*do\s+i\s+have\s+(?:any\s+)?information\s+(?:on|about)\s+",
    r"^\s*do\s+i\s+have\s+(?:anything|something)\s+(?:on|about)\s+",

    # "Tell me ..."
    r"^\s*(?:please\s+)?tell\s+me\s+(?:something\s+)?about\s+",

    # "Can you tell me how to ..."
    r"^\s*(?:can|could|would)\s+you\s+(?:please\s+)?"
    r"tell\s+me\s+(?:how\s+to|how\s+i\s+(?:can|could|should))\s+",

    # "Tell/show me how to ..."
    r"^\s*(?:please\s+)?(?:tell|show)\s+me\s+how\s+to\s+",

    # "How do/can I ..." and "How to ..."
    r"^\s*how\s+(?:do|can|could|should)\s+i\s+",
    r"^\s*how\s+to\s+",

    # "What do you know ..."
    r"^\s*what\s+do\s+you\s+know\s+(?:about|on)\s+",

    # "Can/Could you find ..."
    r"^\s*(?:can|could|would)\s+you\s+(?:please\s+)?find\s+"
    r"(?:me\s+)?(?:any\s+)?information\s+(?:on|about)\s+",

    # "Find information ..."
    r"^\s*(?:please\s+)?find\s+(?:me\s+)?(?:any\s+)?information\s+"
    r"(?:on|about)\s+",

    # "Show me ..."
    r"^\s*(?:please\s+)?show\s+me\s+(?:any\s+)?information\s+"
    r"(?:on|about)\s+",

    r"^\s*(?:please\s+)?show\s+me\s+(?:anything|something)\s+"
    r"(?:on|about)\s+",
)


def normalize_conversational_query(query: str) -> str:
    """
    Remove only recognized conversational retrieval scaffolding.

    This intentionally does NOT apply general stopword removal.

    Examples:
        Do you have any information on urban warfare?
            -> urban warfare

        Tell me about urban warfare.
            -> urban warfare

        What do you know about HTTP?
            -> HTTP

        What does RFC 9110 define?
            -> unchanged

        The Art of War
            -> unchanged
    """
    import re

    original = str(query or "").strip()

    if not original:
        return original

    normalized = original

    for pattern in _CONVERSATIONAL_QUERY_PATTERNS:
        candidate = re.sub(
            pattern,
            "",
            normalized,
            count=1,
            flags=re.IGNORECASE,
        ).strip()

        if candidate != normalized:
            normalized = candidate
            break

    # Strip punctuation introduced by the conversational wrapper while
    # preserving useful search syntax inside the actual subject.
    normalized = normalized.strip()

    normalized = re.sub(
        r"^[\s:;,]+",
        "",
        normalized,
    )

    normalized = re.sub(
        r"[\s?!.,;:]+$",
        "",
        normalized,
    )

    # Apply only explicitly certified, high-confidence typo repairs.
    # Do not use general spell correction: technical identifiers,
    # acronyms, filenames, commands, and model numbers must survive.
    certified_typos = {
        "netwrok": "network",
    }

    for typo, correction in certified_typos.items():
        normalized = re.sub(
            rf"\b{re.escape(typo)}\b",
            correction,
            normalized,
            flags=re.IGNORECASE,
        )

    # Canonicalize only narrow, certified retrieval constructions.
    # This converts an instructional phrase into the topical form that
    # the catalog and qualification engine already retrieve reliably.
    if re.fullmatch(
        r"harden\s+(?:(?:my|the|a|an)\s+)?network",
        normalized,
        flags=re.IGNORECASE,
    ):
        normalized = "network hardening"

    # Never normalize a meaningful query into nothing.
    if not normalized:
        return original

    return normalized


def _r1_1_row_identity(row: Any) -> tuple[str, str, str]:
    """
    Stable candidate identity for merging original-query and
    normalized-query retrieval.
    """
    data = dict(row)

    path = str(
        data.get("file_path")
        or data.get("source_path")
        or ""
    )

    excerpt = str(
        data.get("excerpt")
        or data.get("chunk_text")
        or ""
    )

    source_id = str(
        data.get("source_id")
        or data.get("chunk_id")
        or data.get("id")
        or ""
    )

    return (
        path,
        source_id,
        excerpt,
    )


def _r1_1_merge_rows(
    *groups: Any,
) -> list[Any]:
    merged: list[Any] = []
    seen: set[tuple[str, str, str]] = set()

    for group in groups:
        for row in group:
            identity = _r1_1_row_identity(row)

            if identity in seen:
                continue

            seen.add(identity)
            merged.append(row)

    return merged


def search_qualified_catalog(
    query: str,
    *,
    db_path: Path = DEFAULT_CATALOG_DB,
    limit: int = 25,
    engine: QualificationEngine | None = None,
) -> list[dict[str, Any]]:
    requested_limit = max(1, int(limit))

    raw_limit = max(
        requested_limit * 4,
        100,
    )

    original_query = str(query or "").strip()

    normalized_query = normalize_conversational_query(
        original_query
    )

    normalization_applied = (
        bool(normalized_query)
        and normalized_query != original_query
    )

    # --------------------------------------------------------------
    # Search original query.
    #
    # We preserve this because the complete wording can occasionally
    # contain useful identifiers or specificity.
    # --------------------------------------------------------------

    original_rows = list(
        search_catalog(
            original_query,
            db_path=db_path,
            limit=raw_limit,
        )
    )

    # --------------------------------------------------------------
    # Search normalized topical query when applicable.
    # --------------------------------------------------------------

    if normalization_applied:
        normalized_rows = list(
            search_catalog(
                normalized_query,
                db_path=db_path,
                limit=raw_limit,
            )
        )
    else:
        normalized_rows = []

    raw_rows = _r1_1_merge_rows(
        normalized_rows,
        original_rows,
    )

    # --------------------------------------------------------------
    # Qualification query
    #
    # Qualification should judge candidate relevance against the
    # actual topical request, not conversational scaffolding.
    # --------------------------------------------------------------

    qualification_query = (
        normalized_query
        if normalization_applied
        else original_query
    )

    accepted_rows, result = qualify_rows(
        qualification_query,
        raw_rows,
        engine=engine,
    )

    output = list(accepted_rows)

    seen: set[tuple[str, str]] = set()

    for row in output:
        path_value = str(
            row.get("file_path")
            or row.get("source_path")
            or ""
        )

        excerpt_value = str(
            row.get("excerpt")
            or row.get("chunk_text")
            or ""
        )

        seen.add(
            (
                path_value,
                excerpt_value,
            )
        )

    rescue_diagnostics: list[dict[str, Any]] = []
    rescued_evidence: list[tuple[Any, str]] = []

    # --------------------------------------------------------------
    # Preserve Qualification Gate Repair R1.
    # --------------------------------------------------------------

    if len(output) < requested_limit:

        for rejected in result.rejected:

            rescue, reason = _gate_repair_should_rescue(
                qualification_query,
                rejected,
                threshold=float(result.threshold),
            )

            # GENESIS_RECALL_R2_R2A_R4_R8_IDENTITY_FLOW
            #
            # Existing R1F content rescue remains first.
            #
            # When R1F declines, independently derive the unique
            # durable document identity from the full qualification
            # evidence pool, then require exact document-id equality.
            if not rescue:

                identity_target_ids = (
                    _r2_exact_identity_targets(
                        qualification_query,
                        result,
                    )
                )

                (
                    identity_rescue,
                    identity_reason,
                ) = (
                    _r2_exact_document_identity_should_rescue(
                        qualification_query,
                        rejected,
                        target_document_ids=identity_target_ids,
                    )
                )

                if identity_rescue:
                    rescue = True
                    reason = identity_reason

            rescue_diagnostics.append(
                {
                    "source_id":
                        rejected.candidate.source_id,

                    "source_path":
                        rejected.candidate.source_path,

                    "rescue":
                        rescue,

                    "reason":
                        reason,

                    "score":
                        rejected.score.to_dict(),

                    "original_decision":
                        rejected.decision.value,
                }
            )

            if not rescue:
                continue

            row = _gate_repair_qualified_row(
                rejected,
                reason=reason,
            )

            path_value = str(
                row.get("file_path")
                or row.get("source_path")
                or ""
            )

            excerpt_value = str(
                row.get("excerpt")
                or row.get("chunk_text")
                or ""
            )

            identity = (
                path_value,
                excerpt_value,
            )

            if identity in seen:
                continue

            seen.add(identity)

            row["query_original"] = original_query
            row["query_normalized"] = normalized_query
            row["query_normalization_applied"] = (
                normalization_applied
            )

            output.append(row)
            rescued_evidence.append((rejected, reason))

            if len(output) >= requested_limit:
                break

    # GENESIS_UI_CONVERSATION_R3_R2_RESCUE_RECONCILIATION
    #
    # Gate repair changes the externally returned decision from rejected to
    # accepted. Reconcile the canonical QualificationResult accordingly so
    # grounded-answer planning consumes the same evidence that callers receive.
    if rescued_evidence:
        from core.retrieval.qualification.contracts import (
            QualifiedEvidence,
            QualificationResult,
        )
        from core.retrieval.qualification.enums import QualificationDecision

        rescued_ids = {id(item) for item, _ in rescued_evidence}
        promoted = tuple(
            QualifiedEvidence(
                candidate=item.candidate,
                score=item.score,
                decision=QualificationDecision.ACCEPTED,
                explanation=(
                    f"{item.explanation}; qualification rescue: {reason}"
                    if item.explanation
                    else f"qualification rescue: {reason}"
                ),
            )
            for item, reason in rescued_evidence
        )

        statistics = dict(result.runtime_statistics)
        statistics["qualification_rescued_count"] = len(promoted)

        result = QualificationResult(
            accepted=(*result.accepted, *promoted),
            rejected=tuple(
                item
                for item in result.rejected
                if id(item) not in rescued_ids
            ),
            threshold=result.threshold,
            runtime_statistics=statistics,
        )
        _LAST_RESULT.set(result)

    # --------------------------------------------------------------
    # Add normalization provenance to normally accepted rows too.
    # --------------------------------------------------------------

    for row in output:
        row.setdefault(
            "query_original",
            original_query,
        )

        row.setdefault(
            "query_normalized",
            normalized_query,
        )

        row.setdefault(
            "query_normalization_applied",
            normalization_applied,
        )

    # --------------------------------------------------------------
    # Preserve and augment trace.
    # --------------------------------------------------------------

    trace = get_last_qualification_trace()

    if trace is not None:
        trace["gate_repair_revision"] = "R1"
        trace["query_normalization_revision"] = "R1.1"

        trace["query_original"] = original_query
        trace["query_normalized"] = normalized_query

        trace["query_normalization_applied"] = (
            normalization_applied
        )

        trace["qualification_query"] = (
            qualification_query
        )

        trace["raw_candidate_limit"] = raw_limit

        trace["raw_original_count"] = len(
            original_rows
        )

        trace["raw_normalized_count"] = len(
            normalized_rows
        )

        trace["raw_merged_count"] = len(
            raw_rows
        )

        trace["requested_limit"] = requested_limit

        trace["rescued_count"] = sum(
            1
            for item in output
            if item.get("qualification_rescue")
        )

        trace["returned_count"] = len(output)

        # Report the reconciled final decision state, not the pre-rescue state.
        trace["accepted_count"] = len(result.accepted)
        trace["rejected_count"] = len(result.rejected)
        trace["runtime_statistics"] = dict(result.runtime_statistics)
        trace["diagnostics"] = [
            QualificationDiagnostic.from_evidence(
                qualification_query,
                item,
            ).to_dict()
            for item in (*result.accepted, *result.rejected)
        ]

        trace["rescue_diagnostics"] = (
            rescue_diagnostics
        )

        _LAST_TRACE.set(trace)

    return output[:requested_limit]
def get_last_qualification_result() -> QualificationResult | None:
    return _LAST_RESULT.get()


def get_last_qualification_trace() -> dict[str, Any] | None:
    value = _LAST_TRACE.get()

    return None if value is None else dict(value)


def clear_last_qualification_state() -> None:
    _LAST_RESULT.set(None)
    _LAST_TRACE.set(None)
