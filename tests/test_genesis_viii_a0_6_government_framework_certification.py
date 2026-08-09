from pathlib import Path
import tempfile
import unittest

from dev.tools.audit_government_framework import (
    Finding,
    architecture_fingerprint,
    source_fingerprint,
)


class GovernmentFrameworkCertificationTests(unittest.TestCase):
    def test_source_fingerprint_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "a.py"
            second = root / "b.py"
            first.write_text("A = 1\n", encoding="utf-8")
            second.write_text("B = 2\n", encoding="utf-8")
            self.assertEqual(
                source_fingerprint(root, (first, second)),
                source_fingerprint(root, (second, first)),
            )

    def test_source_fingerprint_changes_with_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "a.py"
            path.write_text("A = 1\n", encoding="utf-8")
            before = source_fingerprint(root, (path,))
            path.write_text("A = 2\n", encoding="utf-8")
            self.assertNotEqual(before, source_fingerprint(root, (path,)))

    def test_architecture_fingerprint_is_deterministic(self) -> None:
        findings = (
            Finding("b", "pass", "B"),
            Finding("a", "pass", "A"),
        )
        self.assertEqual(
            architecture_fingerprint(findings),
            architecture_fingerprint(tuple(reversed(findings))),
        )

    def test_failed_finding_changes_fingerprint(self) -> None:
        self.assertNotEqual(
            architecture_fingerprint((Finding("a", "pass", "A"),)),
            architecture_fingerprint((Finding("a", "fail", "A"),)),
        )


if __name__ == "__main__":
    unittest.main()
