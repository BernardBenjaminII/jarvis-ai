"""Governance regression tests for Genesis IV-B3."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from core.observation.audit import (
    AUDIT_SCHEMA_VERSION,
    CANONICAL_OBSERVATION_PATH,
    ObservationDefinitionStatus,
    audit_observation_definitions,
    format_observation_convergence_report,
    render_observation_convergence_markdown,
    require_observation_convergence,
    write_observation_convergence_reports,
)
from core.observation.errors import ObservationConvergenceError


class ObservationConvergenceGovernanceTests(unittest.TestCase):
    def _write(
        self,
        root: Path,
        relative: str,
        content: str,
    ) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_classifies_all_governance_states(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write(
                root,
                CANONICAL_OBSERVATION_PATH,
                "class Observation:\n    pass\n",
            )
            self._write(
                root,
                "core/cognition/contracts.py",
                "class Observation:\n    pass\n",
            )
            self._write(
                root,
                "core/example/contracts.py",
                "class Observation:\n    pass\n",
            )

            report = audit_observation_definitions(root)

            statuses = {
                item.path: item.status
                for item in report.definitions
            }
            self.assertEqual(
                statuses[CANONICAL_OBSERVATION_PATH],
                ObservationDefinitionStatus.CANONICAL,
            )
            self.assertEqual(
                statuses["core/cognition/contracts.py"],
                ObservationDefinitionStatus.APPROVED_LEGACY,
            )
            self.assertEqual(
                statuses["core/example/contracts.py"],
                ObservationDefinitionStatus.FORBIDDEN,
            )
            self.assertFalse(report.converged)

    def test_convergence_requires_canonical_owner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ObservationConvergenceError):
                require_observation_convergence(Path(directory))

    def test_approved_legacy_does_not_fail_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write(
                root,
                CANONICAL_OBSERVATION_PATH,
                "class Observation:\n    pass\n",
            )
            self._write(
                root,
                "core/cognition/contracts.py",
                "class Observation:\n    pass\n",
            )

            report = require_observation_convergence(root)

            self.assertTrue(report.converged)
            self.assertEqual(
                report.approved_legacy_definitions,
                ("core/cognition/contracts.py",),
            )

    def test_forbidden_definition_fails_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write(
                root,
                CANONICAL_OBSERVATION_PATH,
                "class Observation:\n    pass\n",
            )
            self._write(
                root,
                "core/rogue.py",
                "class Observation:\n    pass\n",
            )

            with self.assertRaisesRegex(
                ObservationConvergenceError,
                "core/rogue.py",
            ):
                require_observation_convergence(root)

    def test_fingerprint_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write(
                root,
                CANONICAL_OBSERVATION_PATH,
                "class Observation:\n    pass\n",
            )

            first = audit_observation_definitions(root)
            second = audit_observation_definitions(root)

            self.assertEqual(first.fingerprint, second.fingerprint)

    def test_text_inventory_is_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write(
                root,
                CANONICAL_OBSERVATION_PATH,
                "class Observation:\n    pass\n",
            )

            text = format_observation_convergence_report(
                audit_observation_definitions(root)
            )

            self.assertIn("Canonical", text)
            self.assertIn("Approved Legacy", text)
            self.assertIn("Deprecated", text)
            self.assertIn("Forbidden", text)
            self.assertIn("Fingerprint", text)

    def test_report_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "reports"
            self._write(
                root,
                CANONICAL_OBSERVATION_PATH,
                "class Observation:\n    pass\n",
            )
            report = audit_observation_definitions(root)

            json_path, markdown_path = (
                write_observation_convergence_reports(
                    report,
                    output,
                )
            )

            payload = json.loads(
                json_path.read_text(encoding="utf-8")
            )
            markdown = markdown_path.read_text(
                encoding="utf-8"
            )

            self.assertEqual(
                payload["schema_version"],
                AUDIT_SCHEMA_VERSION,
            )
            self.assertEqual(
                payload["fingerprint"],
                report.fingerprint,
            )
            self.assertEqual(
                markdown,
                render_observation_convergence_markdown(
                    report
                ),
            )


if __name__ == "__main__":
    unittest.main()
