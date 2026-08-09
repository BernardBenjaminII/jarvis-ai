from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from dev.audits.audit_genesis_ix_a4_1a_executive_conversation_inventory import (
    classify_duplicates,
    route_inventory,
    symbol_inventory,
    ui_inventory,
)


class GenesisIXA41AInventoryTests(unittest.TestCase):
    def test_symbol_inventory_finds_executive_components(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "core/conversation/service.py"
            path.parent.mkdir(parents=True)
            path.write_text(
                "class ExecutiveConversationService:\n"
                "    def ask(self, operator_input: str):\n"
                "        return operator_input\n",
                encoding="utf-8",
            )
            names = {item.name for item in symbol_inventory(root)}
            self.assertIn("ExecutiveConversationService", names)
            self.assertIn("ask", names)

    def test_route_inventory_finds_conversation_route(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "core/src/routes/api.py"
            path.parent.mkdir(parents=True)
            path.write_text(
                '@router.post("/api/conversation/query")\n'
                "def conversation_query():\n"
                "    pass\n",
                encoding="utf-8",
            )
            found = route_inventory(root)
            self.assertEqual(found[0].method, "POST")
            self.assertEqual(found[0].route, "/api/conversation/query")

    def test_ui_inventory_finds_http_and_websocket(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "core/src/static/mission_control/api.js"
            path.parent.mkdir(parents=True)
            path.write_text(
                'postJson("/api/conversation/query", payload);\n'
                'new WebSocket("/operations/executive/live");\n',
                encoding="utf-8",
            )
            endpoints = {item.endpoint for item in ui_inventory(root)}
            self.assertIn("/api/conversation/query", endpoints)
            self.assertIn("/operations/executive/live", endpoints)

    def test_duplicate_detector_groups_response_models(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "core/conversation/models.py"
            path.parent.mkdir(parents=True)
            path.write_text(
                "class ConversationResponse:\n"
                "    pass\n\n"
                "class ExecutiveConversationResponse:\n"
                "    pass\n",
                encoding="utf-8",
            )
            categories = {
                item.category
                for item in classify_duplicates(symbol_inventory(root))
            }
            self.assertIn("response models", categories)


if __name__ == "__main__":
    unittest.main()
