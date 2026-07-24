from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "core/src/static/mission_control"


class MC1002Tests(unittest.TestCase):
    def test_files(self):
        for name in ("index.html", "styles.css", "app.js"):
            self.assertTrue((STATIC / name).is_file())

    def test_identity(self):
        html = (STATIC / "index.html").read_text()
        self.assertIn("COMMANDER'S BRIDGE", html)
        self.assertIn("What are your orders?", html)

    def test_operations_boundary(self):
        js = (STATIC / "app.js").read_text()
        self.assertIn("/operations/status", js)
        self.assertIn("/operations/missions", js)
        self.assertNotIn("/executive/", js)
        self.assertNotIn("/reasoning/", js)

    def test_single_primary_action(self):
        html = (STATIC / "index.html").read_text()
        self.assertEqual(html.count('class="primary"'), 1)

    def test_responsive(self):
        css = (STATIC / "styles.css").read_text()
        self.assertIn("@media(max-width:850px)", css)
        self.assertIn("@media(max-width:560px)", css)

    def test_semantic_colors(self):
        css = (STATIC / "styles.css").read_text()
        for token in ("--green:", "--amber:", "--red:", "--cyan:", "--purple:"):
            self.assertIn(token, css)
