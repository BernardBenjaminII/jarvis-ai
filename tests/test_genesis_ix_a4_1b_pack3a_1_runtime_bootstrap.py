from __future__ import annotations

import os
import tempfile
from pathlib import Path
import unittest

from core.certification.runtime.discovery import (
    discover_repository_root,
    is_repository_root,
)
from core.certification.runtime.imports import resolve_modules


class GenesisIXA41BPack3A1Tests(unittest.TestCase):
    def test_repository_markers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            for name in ("core", "dev", "docs"):
                (root / name).mkdir()

            self.assertTrue(is_repository_root(root))

    def test_discovery_walks_upward(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            for name in ("core", "dev", "docs"):
                (root / name).mkdir()

            nested = root / "dev/certification"
            nested.mkdir(parents=True)

            self.assertEqual(discover_repository_root(nested), root)

    def test_environment_override(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            for name in ("core", "dev", "docs"):
                (root / name).mkdir()

            previous = os.environ.get("JARVIS_PROJECT_ROOT")
            os.environ["JARVIS_PROJECT_ROOT"] = str(root)

            try:
                self.assertEqual(discover_repository_root(), root)
            finally:
                if previous is None:
                    os.environ.pop("JARVIS_PROJECT_ROOT", None)
                else:
                    os.environ["JARVIS_PROJECT_ROOT"] = previous

    def test_failed_module_resolution(self) -> None:
        result = resolve_modules(("no_such_jarvis_module",))
        self.assertFalse(result[0].imported)
        self.assertIsNotNone(result[0].error)


if __name__ == "__main__":
    unittest.main()
