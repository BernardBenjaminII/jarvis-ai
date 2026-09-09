from __future__ import annotations

import json
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Mapping

from core.knowledge_catalog.qualified_search import (
    qualify_rows,
    _gate_repair_should_rescue,
)

from core.retrieval.qualification.evaluator import (
    QualificationEngine,
)


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

REPORT = PROJECT / (
    "artifacts/genesis_recall/"
    "r2_r2a_r3_rejected_evidence_trace.txt"
)

JSON_REPORT = PROJECT / (
    "artifacts/genesis_recall/"
    "r2_r2a_r3_identity_rescue_decision.json"
)


LANE_ID = 86876

LANE_QUERY = (
    "Edward William Lane Arabic English Lexicon Vol 6"
)


NEGATIVE_QUERIES = (
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


STOPWORDS = {
    "a",
    "an",
    "and",
    "the",
    "of",
    "for",
    "to",
    "in",
    "on",
    "by",
    "with",
    "from",
}


def out(*args: Any) -> None:
    print(*args)


def section(title: str) -> None:
    out()
    out("=" * 76)
    out(title)
    out("=" * 76)


def normalize(value: Any) -> str:
    text = str(value or "").casefold()

    # Treat punctuation and filename separators as token boundaries.
    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    return " ".join(text.split())


def tokens(value: Any) -> tuple[str, ...]:
    result = []

    for token in normalize(value).split():
        if token in STOPWORDS:
            continue

        if len(token) < 2:
            continue

        result.append(token)

    return tuple(result)


def get_value(
    obj: Any,
    name: str,
    default: Any = None,
) -> Any:
    if obj is None:
        return default

    if isinstance(obj, Mapping):
        return obj.get(name, default)

    return getattr(obj, name, default)


def decision_value(value: Any) -> str:
    if value is None:
        return ""

    raw = getattr(value, "value", value)

    return str(raw)


def candidate_identity_text(candidate: Any) -> str:
    parts = (
        get_value(candidate, "title", ""),
        get_value(candidate, "subject", ""),
        get_value(candidate, "source_path", ""),
    )

    return normalize(
        " ".join(
            str(part)
            for part in parts
            if part
        )
    )


def identity_evidence(
    query: str,
    candidate: Any,
) -> dict[str, Any]:

    q_tokens = tokens(query)

    identity_text = candidate_identity_text(
        candidate
    )

    matched = tuple(
        token
        for token in q_tokens
        if token in identity_text.split()
    )

    missing = tuple(
        token
        for token in q_tokens
        if token not in identity_text.split()
    )

    coverage = (
        len(matched) / len(q_tokens)
        if q_tokens
        else 0.0
    )

    ordered_query = " ".join(q_tokens)

    exact_normalized_phrase = bool(
        ordered_query
        and ordered_query in identity_text
    )

    title = normalize(
        get_value(candidate, "title", "")
    )

    subject = normalize(
        get_value(candidate, "subject", "")
    )

    source_path = normalize(
        get_value(candidate, "source_path", "")
    )

    title_token_set = set(title.split())
    subject_token_set = set(subject.split())
    path_token_set = set(source_path.split())

    title_coverage = (
        sum(
            1
            for token in q_tokens
            if token in title_token_set
        ) / len(q_tokens)
        if q_tokens
        else 0.0
    )

    subject_coverage = (
        sum(
            1
            for token in q_tokens
            if token in subject_token_set
        ) / len(q_tokens)
        if q_tokens
        else 0.0
    )

    path_coverage = (
        sum(
            1
            for token in q_tokens
            if token in path_token_set
        ) / len(q_tokens)
        if q_tokens
        else 0.0
    )

    return {
        "query_tokens": q_tokens,
        "matched_tokens": matched,
        "missing_tokens": missing,
        "coverage": coverage,
        "exact_normalized_phrase": exact_normalized_phrase,
        "title_coverage": title_coverage,
        "subject_coverage": subject_coverage,
        "path_coverage": path_coverage,
        "identity_text": identity_text,
    }


def shadow_identity_rescue(
    query: str,
    evidence: Any,
    *,
    threshold: float,
) -> tuple[bool, str, dict[str, Any]]:
    """
    Shadow-only deterministic identity rescue.

    This does NOT replace normal qualification.

    Intended semantics:
      - candidate was rejected by ordinary qualification;
      - provenance must be complete;
      - query must contain enough meaningful identity terms;
      - normalized title/subject/path must deterministically cover
        essentially the complete document identity;
      - arbitrary semantic/topic matches must not qualify;
      - no production threshold is changed.
    """

    candidate = get_value(
        evidence,
        "candidate",
    )

    score = get_value(
        evidence,
        "score",
    )

    identity = identity_evidence(
        query,
        candidate,
    )

    q_tokens = identity["query_tokens"]

    try:
        provenance = float(
            get_value(
                score,
                "provenance",
                0.0,
            )
        )
    except Exception:
        provenance = 0.0

    try:
        final = float(
            get_value(
                score,
                "final",
                0.0,
            )
        )
    except Exception:
        final = 0.0

    # Identity rescue is deliberately NOT a global relevance
    # threshold bypass.  It is only available for sufficiently
    # descriptive document-identity queries.
    if len(q_tokens) < 4:
        return (
            False,
            "identity_query_too_short",
            identity,
        )

    if provenance < 1.0:
        return (
            False,
            "identity_provenance_incomplete",
            identity,
        )

    coverage = float(
        identity["coverage"]
    )

    title_coverage = float(
        identity["title_coverage"]
    )

    subject_coverage = float(
        identity["subject_coverage"]
    )

    path_coverage = float(
        identity["path_coverage"]
    )

    # Exact normalized identity phrase is strongest.
    if (
        identity["exact_normalized_phrase"]
        and coverage == 1.0
        and (
            title_coverage == 1.0
            or subject_coverage == 1.0
            or path_coverage == 1.0
        )
    ):
        return (
            True,
            "exact_normalized_catalog_identity",
            identity,
        )

    # Filename punctuation and volume notation commonly prevent
    # phrase analyzers from recognizing what is nevertheless an
    # unambiguous catalog identity.
    #
    # Require complete meaningful-token coverage and strong
    # coverage in at least one explicit identity field.
    if (
        coverage == 1.0
        and max(
            title_coverage,
            subject_coverage,
            path_coverage,
        ) >= 0.90
    ):
        return (
            True,
            "complete_catalog_identity_token_coverage",
            identity,
        )

    # Do not use final score as an independent identity rescue
    # mechanism.  It is reported for anatomy only.
    _ = threshold
    _ = final

    return (
        False,
        "insufficient_catalog_identity_evidence",
        identity,
    )


def fetch_runtime_document(
    conn: sqlite3.Connection,
    runtime_id: int,
) -> dict[str, Any] | None:

    row = conn.execute(
        """
        SELECT *
        FROM runtime_documents
        WHERE id = ?
        LIMIT 1
        """,
        (runtime_id,),
    ).fetchone()

    if row is None:
        return None

    return dict(row)


def fetch_identity_candidates(
    conn: sqlite3.Connection,
    query: str,
    *,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """
    Read-only deterministic catalog identity scan used ONLY
    for the shadow negative-control decision.

    This intentionally avoids depending on the rolled-back R2
    production helper.
    """

    q_tokens = tokens(query)

    if len(q_tokens) < 2:
        return []

    rows = conn.execute(
        """
        SELECT
            id,
            title,
            file_path,
            sha256,
            media_type,
            content_text,
            materialized_at,
            updated_at
        FROM runtime_documents
        WHERE title IS NOT NULL
          AND TRIM(title) <> ''
        """
    ).fetchall()

    scored: list[
        tuple[
            float,
            int,
            dict[str, Any],
        ]
    ] = []

    for raw in rows:
        row = dict(raw)

        identity_text = normalize(
            " ".join(
                (
                    str(
                        row.get(
                            "title",
                            "",
                        )
                        or ""
                    ),
                    str(
                        row.get(
                            "file_path",
                            "",
                        )
                        or ""
                    ),
                )
            )
        )

        identity_tokens = set(
            identity_text.split()
        )

        matched = sum(
            1
            for token in q_tokens
            if token in identity_tokens
        )

        coverage = (
            matched / len(q_tokens)
            if q_tokens
            else 0.0
        )

        # Candidate horizon deliberately requires substantial
        # identity overlap.  It is not a content search.
        if coverage < 0.50:
            continue

        scored.append(
            (
                coverage,
                int(row["id"]),
                row,
            )
        )

    scored.sort(
        key=lambda item: (
            -item[0],
            item[1],
        )
    )

    return [
        row
        for _, _, row in scored[:limit]
    ]


def prepare_candidate_row(
    row: Mapping[str, Any],
) -> dict[str, Any]:

    prepared = dict(row)

    runtime_id = prepared.get("id")

    prepared.setdefault(
        "runtime_document_id",
        runtime_id,
    )

    prepared.setdefault(
        "document_id",
        runtime_id,
    )

    title = str(
        prepared.get(
            "title",
            "",
        )
        or ""
    )

    path = str(
        prepared.get(
            "file_path",
            "",
        )
        or ""
    )

    prepared.setdefault(
        "subject",
        title,
    )

    prepared.setdefault(
        "source_path",
        path,
    )

    prepared.setdefault(
        "path",
        path,
    )

    # Identity candidates have no FTS retrieval confidence.
    # Preserve that fact instead of fabricating confidence.
    prepared["retrieval_score"] = 0.0

    return prepared


def evidence_record(
    query: str,
    evidence: Any,
    *,
    threshold: float,
) -> dict[str, Any]:

    candidate = get_value(
        evidence,
        "candidate",
    )

    score = get_value(
        evidence,
        "score",
    )

    decision = decision_value(
        get_value(
            evidence,
            "decision",
            "",
        )
    )

    explanation = str(
        get_value(
            evidence,
            "explanation",
            "",
        )
        or ""
    )

    score_fields = {}

    for field in (
        "lexical",
        "semantic",
        "phrase",
        "entity",
        "subject",
        "provenance",
        "final",
    ):
        value = get_value(
            score,
            field,
            None,
        )

        try:
            value = (
                float(value)
                if value is not None
                else None
            )
        except Exception:
            pass

        score_fields[field] = value

    current_rescue = False
    current_rescue_reason = ""

    try:
        (
            current_rescue,
            current_rescue_reason,
        ) = _gate_repair_should_rescue(
            query,
            evidence,
            threshold=threshold,
        )
    except Exception as exc:
        current_rescue_reason = (
            "current_rescue_exception:"
            + type(exc).__name__
            + ":"
            + str(exc)
        )

    (
        identity_rescue,
        identity_reason,
        identity,
    ) = shadow_identity_rescue(
        query,
        evidence,
        threshold=threshold,
    )

    return {
        "query": query,
        "source_id": str(
            get_value(
                candidate,
                "source_id",
                "",
            )
        ),
        "title": str(
            get_value(
                candidate,
                "title",
                "",
            )
            or ""
        ),
        "subject": str(
            get_value(
                candidate,
                "subject",
                "",
            )
            or ""
        ),
        "source_path": str(
            get_value(
                candidate,
                "source_path",
                "",
            )
            or ""
        ),
        "backend": str(
            get_value(
                candidate,
                "backend",
                "",
            )
            or ""
        ),
        "retrieval_score": get_value(
            candidate,
            "retrieval_score",
            None,
        ),
        "decision": decision,
        "explanation": explanation,
        "scores": score_fields,
        "normal_threshold": threshold,
        "current_content_rescue": {
            "rescue": bool(
                current_rescue
            ),
            "reason": str(
                current_rescue_reason
            ),
        },
        "shadow_identity_rescue": {
            "rescue": bool(
                identity_rescue
            ),
            "reason": str(
                identity_reason
            ),
            "identity": {
                key: (
                    list(value)
                    if isinstance(
                        value,
                        tuple,
                    )
                    else value
                )
                for key, value
                in identity.items()
                if key != "identity_text"
            },
        },
    }


def print_record(
    label: str,
    record: Mapping[str, Any],
) -> None:

    section(label)

    out(
        "query              :",
        record["query"],
    )

    out(
        "source id          :",
        record["source_id"],
    )

    out(
        "title              :",
        record["title"],
    )

    out(
        "backend            :",
        record["backend"],
    )

    out(
        "retrieval score    :",
        record["retrieval_score"],
    )

    out()
    out("QUALIFICATION")

    out(
        "decision           :",
        record["decision"],
    )

    out(
        "explanation        :",
        record["explanation"],
    )

    scores = record["scores"]

    for key in (
        "lexical",
        "semantic",
        "phrase",
        "entity",
        "subject",
        "provenance",
        "final",
    ):
        out(
            f"{key:<19}:",
            scores.get(key),
        )

    out(
        "normal threshold   :",
        record["normal_threshold"],
    )

    out()
    out("CURRENT R1F CONTENT RESCUE")

    current = record[
        "current_content_rescue"
    ]

    out(
        "rescue             :",
        current["rescue"],
    )

    out(
        "reason             :",
        current["reason"],
    )

    out()
    out("SHADOW IDENTITY RESCUE")

    shadow = record[
        "shadow_identity_rescue"
    ]

    out(
        "rescue             :",
        shadow["rescue"],
    )

    out(
        "reason             :",
        shadow["reason"],
    )

    identity = shadow["identity"]

    out(
        "query tokens       :",
        identity["query_tokens"],
    )

    out(
        "matched tokens     :",
        identity["matched_tokens"],
    )

    out(
        "missing tokens     :",
        identity["missing_tokens"],
    )

    out(
        "identity coverage  :",
        identity["coverage"],
    )

    out(
        "title coverage     :",
        identity["title_coverage"],
    )

    out(
        "subject coverage   :",
        identity["subject_coverage"],
    )

    out(
        "path coverage      :",
        identity["path_coverage"],
    )

    out(
        "normalized phrase  :",
        identity[
            "exact_normalized_phrase"
        ],
    )


def main() -> int:

    started = time.time()

    REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    original_stdout = sys.stdout

    with REPORT.open(
        "w",
        encoding="utf-8",
    ) as report_handle:

        class Tee:
            def write(
                self,
                value: str,
            ) -> int:
                original_stdout.write(
                    value
                )
                return report_handle.write(
                    value
                )

            def flush(self) -> None:
                original_stdout.flush()
                report_handle.flush()

        sys.stdout = Tee()

        try:
            section(
                "GENESIS RECALL R2-R2A-R3 — "
                "REJECTED EVIDENCE SCORE TRACE "
                "+ IDENTITY RESCUE DECISION"
            )

            conn = sqlite3.connect(
                f"file:{DB}?mode=ro",
                uri=True,
            )

            conn.row_factory = sqlite3.Row

            conn.execute(
                "PRAGMA query_only = ON"
            )

            query_only = conn.execute(
                "PRAGMA query_only"
            ).fetchone()[0]

            integrity = conn.execute(
                "PRAGMA integrity_check"
            ).fetchone()[0]

            section(
                "1. READ-ONLY DATABASE CONTRACT"
            )

            out(
                "query_only :",
                query_only,
            )

            out(
                "integrity  :",
                integrity,
            )

            if query_only != 1:
                out(
                    "FAIL: query_only not active"
                )
                return 10

            if integrity != "ok":
                out(
                    "FAIL: database integrity"
                )
                return 11

            engine = QualificationEngine()

            threshold = float(
                engine.thresholds.accept
            )

            section(
                "2. PRODUCTION THRESHOLDS"
            )

            out(
                "accept             :",
                engine.thresholds.accept,
            )

            out(
                "minimum_confidence :",
                engine.thresholds.minimum_confidence,
            )

            out(
                "minimum_lexical    :",
                engine.thresholds.minimum_lexical,
            )

            out(
                "minimum_subject    :",
                engine.thresholds.minimum_subject,
            )

            out(
                "minimum_phrase     :",
                engine.thresholds.minimum_phrase,
            )

            lane_row = fetch_runtime_document(
                conn,
                LANE_ID,
            )

            if lane_row is None:
                section(
                    "3. LANE CANARY"
                )
                out(
                    "FAIL: runtime document",
                    LANE_ID,
                    "not found",
                )
                return 20

            lane_candidate = (
                prepare_candidate_row(
                    lane_row
                )
            )

            accepted_rows, qualification = (
                qualify_rows(
                    LANE_QUERY,
                    [lane_candidate],
                    engine=engine,
                )
            )

            section(
                "3. EXACT QUALIFICATION RETURN"
            )

            out(
                "accepted rows      :",
                len(accepted_rows),
            )

            out(
                "accepted evidence  :",
                len(
                    qualification.accepted
                ),
            )

            out(
                "rejected evidence  :",
                len(
                    qualification.rejected
                ),
            )

            if (
                len(
                    qualification.rejected
                )
                != 1
            ):
                out(
                    "FAIL: expected exactly "
                    "one rejected Lane evidence"
                )
                return 21

            rejected = (
                qualification.rejected[0]
            )

            lane_record = evidence_record(
                LANE_QUERY,
                rejected,
                threshold=threshold,
            )

            print_record(
                "4. LANE REJECTED EVIDENCE "
                "SCORE TRACE",
                lane_record,
            )

            # ---------------------------------------------
            # Explain the actual ordinary qualification
            # failure from the engine's returned evidence.
            # ---------------------------------------------

            section(
                "5. ORDINARY QUALIFICATION "
                "FAILURE DECISION"
            )

            explanation = (
                lane_record[
                    "explanation"
                ]
            )

            scores = lane_record["scores"]

            out(
                "decision    :",
                lane_record[
                    "decision"
                ],
            )

            out(
                "explanation :",
                explanation,
            )

            out()
            out(
                "lexical     :",
                scores["lexical"],
                "required >=",
                engine.thresholds.minimum_lexical,
            )

            out(
                "subject     :",
                scores["subject"],
                "required >=",
                engine.thresholds.minimum_subject,
            )

            out(
                "final       :",
                scores["final"],
                "required >=",
                engine.thresholds.accept,
            )

            ordinary_failure_confirmed = (
                not qualification.accepted
                and bool(
                    qualification.rejected
                )
            )

            out()
            out(
                "ordinary rejection confirmed :",
                ordinary_failure_confirmed,
            )

            # ---------------------------------------------
            # Negative identity controls.
            # ---------------------------------------------

            section(
                "6. ADVERSARIAL IDENTITY "
                "RESCUE CONTROLS"
            )

            negative_records = []

            suspicious_negative = 0

            for query in NEGATIVE_QUERIES:

                candidates = (
                    fetch_identity_candidates(
                        conn,
                        query,
                        limit=25,
                    )
                )

                rescued = []

                evaluated = []

                for raw_row in candidates:

                    prepared = (
                        prepare_candidate_row(
                            raw_row
                        )
                    )

                    (
                        _accepted,
                        result,
                    ) = qualify_rows(
                        query,
                        [prepared],
                        engine=engine,
                    )

                    evidence_pool = (
                        tuple(
                            result.accepted
                        )
                        + tuple(
                            result.rejected
                        )
                    )

                    for evidence in (
                        evidence_pool
                    ):

                        record = (
                            evidence_record(
                                query,
                                evidence,
                                threshold=threshold,
                            )
                        )

                        evaluated.append(
                            record
                        )

                        if (
                            record[
                                "shadow_identity_rescue"
                            ][
                                "rescue"
                            ]
                        ):
                            rescued.append(
                                record
                            )

                if rescued:
                    suspicious_negative += (
                        len(rescued)
                    )

                negative_records.append(
                    {
                        "query": query,
                        "identity_candidates": len(
                            candidates
                        ),
                        "evaluated": len(
                            evaluated
                        ),
                        "shadow_rescues": len(
                            rescued
                        ),
                        "rescued_source_ids": [
                            item[
                                "source_id"
                            ]
                            for item in rescued
                        ],
                    }
                )

                out()
                out(
                    "query               :",
                    query,
                )

                out(
                    "identity candidates :",
                    len(candidates),
                )

                out(
                    "shadow rescues      :",
                    len(rescued),
                )

            # ---------------------------------------------
            # Decision.
            # ---------------------------------------------

            section(
                "7. IDENTITY RESCUE DECISION"
            )

            lane_shadow = lane_record[
                "shadow_identity_rescue"
            ]

            lane_rescued = bool(
                lane_shadow["rescue"]
            )

            current_content_rescue = bool(
                lane_record[
                    "current_content_rescue"
                ][
                    "rescue"
                ]
            )

            identity = lane_shadow[
                "identity"
            ]

            complete_identity = (
                float(
                    identity[
                        "coverage"
                    ]
                )
                == 1.0
            )

            provenance_complete = (
                float(
                    scores[
                        "provenance"
                    ]
                    or 0.0
                )
                == 1.0
            )

            shadow_certified = (
                ordinary_failure_confirmed
                and lane_rescued
                and complete_identity
                and provenance_complete
                and suspicious_negative == 0
            )

            out(
                "ordinary Lane rejection :",
                ordinary_failure_confirmed,
            )

            out(
                "current R1F rescue       :",
                current_content_rescue,
            )

            out(
                "shadow identity rescue   :",
                lane_rescued,
            )

            out(
                "identity coverage        :",
                identity[
                    "coverage"
                ],
            )

            out(
                "provenance               :",
                scores[
                    "provenance"
                ],
            )

            out(
                "negative false rescues   :",
                suspicious_negative,
            )

            out()
            out(
                "SHADOW CERTIFIED         :",
                shadow_certified,
            )

            payload = {
                "phase": (
                    "Genesis Recall "
                    "R2-R2A-R3"
                ),
                "mode": "read_only_shadow",
                "lane": lane_record,
                "ordinary_failure_confirmed": (
                    ordinary_failure_confirmed
                ),
                "negative_controls": (
                    negative_records
                ),
                "negative_false_rescues": (
                    suspicious_negative
                ),
                "shadow_certified": (
                    shadow_certified
                ),
                "production_source_changes": 0,
                "production_db_writes": 0,
                "elapsed_seconds": round(
                    time.time()
                    - started,
                    3,
                ),
            }

            JSON_REPORT.write_text(
                json.dumps(
                    payload,
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            section(
                "8. R2-R2A-R3 RESULT"
            )

            out(
                "Lane evidence traced     :",
                True,
            )

            out(
                "ordinary rejection found :",
                ordinary_failure_confirmed,
            )

            out(
                "identity rescue candidate:",
                lane_rescued,
            )

            out(
                "adversarial precision    :",
                suspicious_negative == 0,
            )

            out(
                "R2-R2A-R3 CERTIFIED      :",
                shadow_certified,
            )

            out(
                "production source changes:",
                0,
            )

            out(
                "production DB writes     :",
                0,
            )

            out()
            out(
                "JSON report:",
                JSON_REPORT,
            )

            conn.close()

            return (
                0
                if shadow_certified
                else 1
            )

        finally:
            sys.stdout = original_stdout


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
