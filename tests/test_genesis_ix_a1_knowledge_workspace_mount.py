from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "core/src/static/mission_control/knowledge_workspace.js"
STYLE = ROOT / "core/src/static/mission_control/knowledge_workspace.css"

class KnowledgeWorkspaceMountTests(unittest.TestCase):
    def test_assets_exist(self):
        self.assertTrue(SCRIPT.is_file())
        self.assertTrue(STYLE.is_file())

    def test_mounts_existing_progressive_workspace(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('progressive-workspace-content', source)
        self.assertIn('workspace-placeholder', source)
        self.assertIn('JARVIS_KNOWLEDGE_WORKSPACE', source)

    def test_preserves_all_three_entry_points(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('data-view="knowledge"', source)
        self.assertIn('data-open-view="knowledge"', source)
        self.assertIn('data-command="open-knowledge"', source)

    def test_uses_existing_conversation_api(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('/api/conversation/query', source)
        self.assertIn('/ask', source)

    def test_exposes_mark_i_panels(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for identifier in (
            'knowledge-answer',
            'knowledge-activity-list',
            'knowledge-evidence-list',
            'knowledge-source-list',
            'knowledge-confidence',
        ):
            self.assertIn(identifier, source)

if __name__ == "__main__":
    unittest.main()
