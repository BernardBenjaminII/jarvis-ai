from __future__ import annotations

from dev.qualification_forensics.extract import (
    candidate_record,
    infer_rejection_reason,
)


def main() -> int:
    checks = []

    def check(code, passed, detail):
        checks.append(
            {
                "code": code,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
            }
        )

    reason = infer_rejection_reason(
        decision="REJECTED",
        explanation="lexical 0.000 below 0.200",
        lexical=0.0,
        phrase=0.5,
        subject=0.5,
        confidence=0.5,
        final=0.1,
        threshold=0.2,
    )
    check("LEXICAL-CLASSIFICATION", reason == "LEXICAL", str(reason))

    record = candidate_record(
        {
            "source_id": "candidate",
            "title": "Candidate",
            "qualification_decision": "REJECTED",
            "qualification_score": 0.49,
            "qualification_explanation": "below threshold",
            "qualification_components": {
                "lexical": 0.6,
                "phrase": 0.5,
                "subject": 0.5,
                "confidence": 0.5,
                "final": 0.49,
            },
        },
        raw_rank=1,
        threshold=0.6,
    )
    check(
        "MARGIN",
        abs((record.score_margin or 0.0) + 0.11) < 1e-9,
        str(record.score_margin),
    )
    check(
        "SERIALIZATION",
        record.to_dict()["candidate_id"] == "candidate",
        record.candidate_id,
    )

    failed = [x for x in checks if x["status"] != "PASS"]

    print("=" * 76)
    print("GENESIS IX-A5 PACK 3 — QUALIFICATION RECALL FORENSICS")
    print("=" * 76)
    print("Checks executed :", len(checks))
    print("Checks passed   :", len(checks) - len(failed))
    print("Checks failed   :", len(failed))
    print("Overall status  :", "EXCELLENT" if not failed else "FAILED")
    print("=" * 76)

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
