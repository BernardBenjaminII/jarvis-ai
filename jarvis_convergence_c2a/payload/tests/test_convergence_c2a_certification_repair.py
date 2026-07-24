"""Regression tests for Convergence C-2A certification isolation."""
from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CertificationRepairTests(unittest.TestCase):
    def test_c1_http_contract_patches_active_synthesis_boundary(self) -> None:
        source = (ROOT / "tests/test_convergence_c1_http_contract.py").read_text(encoding="utf-8")
        self.assertIn("conversation_orchestrator", source)
        self.assertIn("synthesis_handler", source)
        self.assertNotIn('patch.object(api.conversation_service, "answer_handler"', source)

    def test_c2_http_contract_does_not_require_live_model_output(self) -> None:
        source = (ROOT / "tests/test_convergence_c2_http_contract.py").read_text(encoding="utf-8")
        self.assertIn("synthesis_handler", source)
        self.assertIn("SYNTHESIZED: {question}", source)

    def test_production_route_still_uses_real_route_question_handler(self) -> None:
        source = (ROOT / "core/src/routes/api.py").read_text(encoding="utf-8")
        self.assertIn("synthesis_handler=route_question", source)
        self.assertIn("ExecutiveConversationOrchestrator", source)


if __name__ == "__main__":
    unittest.main()
