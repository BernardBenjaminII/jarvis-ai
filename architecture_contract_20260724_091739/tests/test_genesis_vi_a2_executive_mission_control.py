from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from core.src.routes import operations

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "core/src/static/mission_control"


class GenesisVIA2ExecutiveMissionControlTests(unittest.TestCase):
    def test_executive_route_projects_service_snapshot(self):
        class Snapshot:
            def to_dict(self):
                return {"state": "reasoning", "readiness": 0.96}

        class Service:
            def executive(self):
                return Snapshot()

        with patch.object(operations, "get_operations_service", return_value=Service()):
            self.assertEqual(
                operations.operations_executive(),
                {"state": "reasoning", "readiness": 0.96},
            )

    def test_mission_control_consumes_only_operations_boundary(self):
        javascript = (STATIC / "app.js").read_text(encoding="utf-8")
        self.assertIn('executive: "/operations/executive"', javascript)
        self.assertNotIn('"/executive/', javascript)
        self.assertNotIn('"/reasoning/', javascript)

    def test_executive_telemetry_fields_are_rendered(self):
        html = (STATIC / "index.html").read_text(encoding="utf-8")
        for identifier in (
            "executive-mission",
            "executive-objective",
            "executive-activity",
            "last-transition",
            "observations",
            "inferences",
            "plans",
            "pending-decisions",
            "pending-recommendations",
        ):
            self.assertIn(f'id="{identifier}"', html)

    def test_auto_refresh_is_fifteen_seconds(self):
        javascript = (STATIC / "app.js").read_text(encoding="utf-8")
        self.assertIn("setInterval(refresh, 15000)", javascript)

    def test_timeline_supports_canonical_entries(self):
        javascript = (STATIC / "app.js").read_text(encoding="utf-8")
        self.assertIn("Array.isArray(value?.entries)", javascript)
        self.assertIn("event.event_kind", javascript)

    def test_accessibility_contract(self):
        html = (STATIC / "index.html").read_text(encoding="utf-8")
        self.assertIn('role="meter"', html)
        self.assertIn('aria-label="Executive readiness"', html)
        self.assertEqual(html.count('class="primary"'), 1)

    def test_responsive_executive_layout(self):
        css = (STATIC / "styles.css").read_text(encoding="utf-8")
        self.assertIn(".executive-context", css)
        self.assertIn(".cognitive-strip", css)
        self.assertIn("@media(max-width:1100px)", css)


if __name__ == "__main__":
    unittest.main()
