from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from dev.runtime import (
    GenesisRepositoryValidationError,
    bootstrap_runtime,
    ensure_repository_layout,
    locate_project_root,
)


class GenesisIXA5Pack11Tests(unittest.TestCase):
    def test_locates_repository(self) -> None:
        root = locate_project_root(Path(__file__))

        self.assertTrue((root / "core").is_dir())
        self.assertTrue((root / "dev").is_dir())

    def test_bootstrap_inserts_root_once(self) -> None:
        first = bootstrap_runtime(Path(__file__))
        second = bootstrap_runtime(Path(__file__))

        self.assertEqual(first.project_root, second.project_root)
        self.assertEqual(
            sys.path.count(str(first.project_root)),
            1,
        )

    def test_context_serialization(self) -> None:
        runtime = bootstrap_runtime(Path(__file__))
        payload = json.loads(runtime.to_json())

        self.assertTrue(payload["repository_verified"])
        self.assertEqual(
            payload["project_root"],
            str(runtime.project_root),
        )

    def test_invalid_layout_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(
                GenesisRepositoryValidationError
            ):
                ensure_repository_layout(Path(temp))


if __name__ == "__main__":
    unittest.main()
