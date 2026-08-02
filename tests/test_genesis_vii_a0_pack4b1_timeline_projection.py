"""Genesis VII-A0 Pack 4B-1 static certification tests."""
from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
JS_PATH = (
    ROOT
    / "core/src/static/mission_control/timeline_projection.js"
)
CSS_PATH = (
    ROOT
    / "core/src/static/mission_control/timeline_projection.css"
)
HTML_PATH = ROOT / "core/src/static/mission_control/index.html"


class GenesisVIIA0Pack4B1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.javascript = JS_PATH.read_text(encoding="utf-8")
        cls.stylesheet = CSS_PATH.read_text(encoding="utf-8")
        cls.html = HTML_PATH.read_text(encoding="utf-8")

    def test_rest_history_endpoint_is_canonical(self) -> None:
        self.assertIn(
            'restEndpoint: "/operations/executive/events"',
            self.javascript,
        )

    def test_live_endpoint_is_canonical(self) -> None:
        self.assertIn(
            'liveEndpoint: "/operations/executive/live"',
            self.javascript,
        )

    def test_websocket_and_polling_fallback_exist(self) -> None:
        self.assertIn("new WebSocket(url)", self.javascript)
        self.assertIn("startPolling()", self.javascript)
        self.assertIn(
            "fallbackPollMilliseconds",
            self.javascript,
        )

    def test_deterministic_sequence_ordering_exists(self) -> None:
        self.assertIn(
            "rightSequence - leftSequence",
            self.javascript,
        )

    def test_event_details_use_safe_dom_construction(self) -> None:
        self.assertNotIn("innerHTML", self.javascript)
        self.assertIn(
            "document.createElement",
            self.javascript,
        )

    def test_timeline_assets_are_registered(self) -> None:
        self.assertIn(
            "/mission-control/static/timeline_projection.js",
            self.html,
        )
        self.assertIn(
            "/mission-control/static/timeline_projection.css",
            self.html,
        )

    def test_timeline_styles_include_responsive_contract(self) -> None:
        self.assertIn("@media (max-width: 720px)", self.stylesheet)
        self.assertIn(
            ".executive-event-metadata",
            self.stylesheet,
        )


if __name__ == "__main__":
    unittest.main()
