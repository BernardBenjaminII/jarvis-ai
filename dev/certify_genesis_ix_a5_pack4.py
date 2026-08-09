from __future__ import annotations

from pathlib import Path

from dev.subject_trace import (
    SubjectProbe,
    SubjectQualificationTrace,
)


class CertificationProvider:
    def raw_search(
        self,
        query,
        *,
        database_path,
        limit,
    ):
        return [
            {
                "source_id": "1",
                "title": query,
                "subject": "computer_science",
            }
        ]

    def qualified_search(
        self,
        query,
        *,
        database_path,
        limit,
    ):
        return []

    def last_trace(self):
        return {
            "threshold": 0.35,
            "diagnostics": [
                {
                    "source_id": "1",
                    "title": "computer architecture",
                    "subject": "computer_science",
                    "decision": "rejected_subject_mismatch",
                    "qualification_components": {
                        "subject": 0.0,
                        "final": 0.60,
                    },
                }
            ],
        }

    def last_result(self):
        return {}


def main() -> int:
    report = SubjectQualificationTrace(
        database_path=Path("/tmp/cert.sqlite"),
        provider=CertificationProvider(),
        probes=(
            SubjectProbe(
                "CERT",
                "computer architecture",
                ("computer_architecture",),
                "known",
            ),
        ),
    ).execute()

    candidate = report.probes[0].candidates[0]

    checks = {
        "probe": len(report.probes) == 1,
        "alias_trace": bool(
            candidate.alias_matches
            or candidate.exact_matches
        ),
        "score_defect": (
            candidate.diagnosis
            == "SUBJECT_SCORING_DEFECT"
        ),
        "serialization": (
            report.to_dict()["probes"][0]["probe_id"]
            == "CERT"
        ),
    }

    failed = [
        name
        for name, passed in checks.items()
        if not passed
    ]

    print("=" * 76)
    print("GENESIS IX-A5 PACK 4 — SUBJECT QUALIFICATION TRACE")
    print("=" * 76)
    print("Checks executed :", len(checks))
    print("Checks passed   :", len(checks) - len(failed))
    print("Checks failed   :", len(failed))
    print("Overall status  :", "EXCELLENT" if not failed else "FAILED")
    print("=" * 76)

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
