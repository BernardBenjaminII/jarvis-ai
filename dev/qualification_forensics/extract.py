from __future__ import annotations

from typing import Any, Mapping

from .contracts import CandidateForensicRecord


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return dict(value.to_dict())
    try:
        return dict(value)
    except Exception:
        return {}


def _float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _component(data: dict[str, Any], *names: str) -> float | None:
    components = _mapping(
        data.get("qualification_components")
        or data.get("score")
        or data.get("components")
        or {}
    )

    for name in names:
        if name in components:
            value = components[name]
            if isinstance(value, Mapping):
                for key in ("value", "score", "final"):
                    if key in value:
                        return _float(value[key])
            return _float(value)

    for name in names:
        if name in data:
            return _float(data[name])

    return None


def infer_rejection_reason(
    *,
    decision: str,
    explanation: str,
    lexical: float | None,
    phrase: float | None,
    subject: float | None,
    confidence: float | None,
    final: float | None,
    threshold: float | None,
) -> str | None:
    if decision.casefold().startswith("accept"):
        return None

    text = explanation.casefold()

    if "lexical" in text:
        return "LEXICAL"
    if "phrase" in text:
        return "PHRASE"
    if "subject" in text or "topic" in text:
        return "SUBJECT"
    if "confidence" in text:
        return "CONFIDENCE"
    if "threshold" in text or "below" in text:
        return "FINAL_THRESHOLD"

    scored = {
        "LEXICAL": lexical,
        "PHRASE": phrase,
        "SUBJECT": subject,
        "CONFIDENCE": confidence,
    }
    available = {
        key: value
        for key, value in scored.items()
        if value is not None
    }

    if available:
        return min(available, key=available.get)

    if (
        final is not None
        and threshold is not None
        and final < threshold
    ):
        return "FINAL_THRESHOLD"

    return "UNKNOWN"


def candidate_record(
    row: Any,
    *,
    raw_rank: int,
    threshold: float | None = None,
) -> CandidateForensicRecord:
    data = _mapping(row)
    raw = _mapping(data.get("raw_row") or data.get("metadata") or {})
    merged = {**raw, **data}

    candidate = _mapping(
        data.get("candidate")
        or merged.get("candidate")
        or {}
    )

    score_data = _mapping(
        data.get("score")
        or merged.get("qualification_components")
        or {}
    )

    candidate_id = str(
        merged.get("source_id")
        or merged.get("chunk_id")
        or candidate.get("source_id")
        or candidate.get("chunk_id")
        or f"candidate-{raw_rank}"
    )
    title = str(
        merged.get("title")
        or candidate.get("title")
        or candidate_id
    )
    source_path = str(
        merged.get("source_path")
        or merged.get("file_path")
        or candidate.get("source_path")
        or ""
    )
    decision = str(
        merged.get("qualification_decision")
        or merged.get("decision")
        or "UNKNOWN"
    )
    explanation = str(
        merged.get("qualification_explanation")
        or merged.get("explanation")
        or ""
    )

    lexical = _component(merged, "lexical", "lexical_score")
    phrase = _component(merged, "phrase", "phrase_score")
    subject = _component(merged, "subject", "subject_score")
    confidence = _component(merged, "confidence", "confidence_score")
    final = _component(merged, "final", "final_score", "qualification_score")
    active_threshold = (
        threshold
        if threshold is not None
        else _float(merged.get("threshold"))
    )

    reason = infer_rejection_reason(
        decision=decision,
        explanation=explanation,
        lexical=lexical,
        phrase=phrase,
        subject=subject,
        confidence=confidence,
        final=final,
        threshold=active_threshold,
    )

    margin = (
        None
        if final is None or active_threshold is None
        else final - active_threshold
    )

    return CandidateForensicRecord(
        candidate_id=candidate_id,
        title=title,
        source_path=source_path,
        raw_rank=raw_rank,
        retrieval_score=float(
            merged.get("retrieval_score")
            or merged.get("score_raw")
            or merged.get("confidence")
            or 0.0
        ),
        lexical_score=lexical,
        phrase_score=phrase,
        subject_score=subject,
        confidence_score=confidence,
        final_score=final,
        threshold=active_threshold,
        decision=decision,
        rejection_reason=reason,
        score_margin=margin,
        explanation=explanation,
        metadata={
            "score_data": score_data,
        },
    )
