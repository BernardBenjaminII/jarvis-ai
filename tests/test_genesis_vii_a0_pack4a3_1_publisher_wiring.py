"""Isolated Genesis VII-A0 Pack 4A-3.1 route tests."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = ROOT / "core/src/main.py"


class GenesisVIIA0Pack4A31Tests(unittest.TestCase):
    def test_canonical_event_router_precedes_placeholder_router(
        self,
    ) -> None:
        text = MAIN_PATH.read_text(encoding="utf-8")
        canonical = text.index(
            "app.include_router(executive_event_runtime_router)"
        )
        compatibility = text.index(
            "app.include_router(executive_operations_router)"
        )
        self.assertLess(canonical, compatibility)

    def test_application_lifespan_uses_isolated_timeline(
        self,
    ) -> None:
        script = r"""
import json
from fastapi.testclient import TestClient
from core.src.main import app

with TestClient(app) as client:
    response = client.get(
        "/operations/executive/events",
        params={"limit": 10},
    )
    response.raise_for_status()
    print(json.dumps(response.json()))
"""
        with TemporaryDirectory() as directory:
            environment = os.environ.copy()
            environment[
                "JARVIS_EXECUTIVE_TIMELINE_ROOT"
            ] = directory

            result = subprocess.run(
                [sys.executable, "-c", script],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(
                result.returncode,
                0,
                msg=result.stderr,
            )
            envelope = json.loads(
                result.stdout.strip().splitlines()[-1]
            )
            data = envelope["data"]
            self.assertTrue(data["configured"])
            self.assertTrue(data["integrity_certified"])

            kinds = {
                event["kind"]
                for event in data["events"]
            }
            self.assertIn("executive_boot_started", kinds)
            self.assertIn("executive_boot_completed", kinds)

            timeline = (
                Path(directory)
                / "executive.timeline.jsonl"
            )
            self.assertTrue(timeline.is_file())


if __name__ == "__main__":
    unittest.main()
