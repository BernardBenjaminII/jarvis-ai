from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from core.executive.director_dispatch import (
    DirectorDispatchError,
    invoke_director,
    resolve_director_dispatch,
)


class SubmitDirector:
    def submit(self, value):
        return f"submitted:{value}"


class ExecuteOnlyDirector:
    def execute(self, value):
        return f"executed:{value}"


class NoDirectorMethods:
    value = 1


class GenesisIXA44Tests(unittest.TestCase):
    def test_submit_is_preferred(self) -> None:
        resolved = resolve_director_dispatch(
            SubmitDirector(),
            preferred="submit",
        )
        self.assertEqual(resolved.method_name, "submit")

    def test_invoke_director(self) -> None:
        result = invoke_director(
            SubmitDirector(),
            "mission",
            preferred="submit",
        )
        self.assertEqual(result, "submitted:mission")

    def test_execute_is_only_fallback(self) -> None:
        resolved = resolve_director_dispatch(
            ExecuteOnlyDirector()
        )
        self.assertEqual(resolved.method_name, "execute")

    def test_missing_dispatch_raises(self) -> None:
        with self.assertRaises(DirectorDispatchError):
            resolve_director_dispatch(NoDirectorMethods())

    def test_reconstruction_fixture_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = (
                root
                / "docs/audits/genesis_ix_a4_3c/"
                "runtime_call_graph.json"
            )
            path.parent.mkdir(parents=True)
            path.write_text(
                json.dumps(
                    {
                        "director_hook": {
                            "method": "submit",
                        }
                    }
                ),
                encoding="utf-8",
            )

            from dev.certification.repair_genesis_ix_a4_4_runtime_integration import (
                read_resolved_hook,
            )

            self.assertEqual(read_resolved_hook(root), "submit")


if __name__ == "__main__":
    unittest.main()
