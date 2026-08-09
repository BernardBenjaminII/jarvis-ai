from __future__ import annotations

import unittest
from pathlib import Path

from dev.subject_trace import (
    SubjectProbe,
    SubjectQualificationTrace,
)
from dev.subject_trace.taxonomy import (
    compare_subjects,
)


class FakeProvider:
    def __init__(self):
        self.query = ""

    def raw_search(
        self,
        query,
        *,
        database_path,
        limit,
    ):
        self.query = query
        return [
            {
                "source_id": "raw-1",
                "title": query,
                "subject": "",
            }
        ]

    def qualified_search(
        self,
        query,
        *,
        database_path,
        limit,
    ):
        self.query = query
        return []

    def last_trace(self):
        return {
            "threshold": 0.35,
            "diagnostics": [
                {
                    "source_id": "candidate-1",
                    "title": self.query,
                    "decision": "rejected_subject_mismatch",
                    "subject": "",
                    "qualification_components": {
                        "subject": 0.0,
                        "final": 0.60,
                    },
                }
            ],
        }

    def last_result(self):
        return {}


class GenesisIXA5Pack4Tests(unittest.TestCase):
    def test_alias_match(self):
        match = compare_subjects(
            ("computer_architecture",),
            ("computer_science",),
        )

        self.assertTrue(
            match.alias_matches
            or match.exact_matches
        )

    def test_missing_metadata_diagnosis(self):
        report = SubjectQualificationTrace(
            database_path=Path("/tmp/fake.sqlite"),
            provider=FakeProvider(),
            probes=(
                SubjectProbe(
                    "TEST",
                    "computer architecture",
                    ("computer_architecture",),
                    "known",
                ),
            ),
        ).execute()

        candidate = report.probes[0].candidates[0]

        self.assertTrue(candidate.missing_metadata)
        self.assertEqual(
            candidate.diagnosis,
            "MISSING_SUBJECT_METADATA",
        )

    def test_report_summary(self):
        report = SubjectQualificationTrace(
            database_path=Path("/tmp/fake.sqlite"),
            provider=FakeProvider(),
            probes=(
                SubjectProbe(
                    "TEST",
                    "Executive Director",
                    ("executive",),
                    "known",
                ),
            ),
        ).execute()

        self.assertEqual(
            report.summary["candidate_count"],
            1,
        )
        self.assertEqual(
            report.summary["missing_subject_metadata"],
            1,
        )

    def test_serialization(self):
        report = SubjectQualificationTrace(
            database_path=Path("/tmp/fake.sqlite"),
            provider=FakeProvider(),
            probes=(
                SubjectProbe(
                    "TEST",
                    "SHA-256",
                    ("cybersecurity",),
                    "known",
                ),
            ),
        ).execute()

        payload = report.to_dict()

        self.assertEqual(
            payload["probes"][0]["probe_id"],
            "TEST",
        )


if __name__ == "__main__":
    unittest.main()
