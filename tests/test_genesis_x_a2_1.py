import unittest
from core.knowledge_catalog.ocr_recovery.quality import quality_score
from core.knowledge_catalog.ocr_recovery.models import OCRPolicy

class GenesisXA21Tests(unittest.TestCase):
    def test_quality_good_text(self):
        text="This is a coherent sentence with enough readable words. "*20
        self.assertGreater(quality_score(text),0.45)

    def test_quality_empty(self):
        self.assertEqual(quality_score(""),0.0)

    def test_policy_defaults(self):
        p=OCRPolicy()
        self.assertEqual(p.max_pages,80)
        self.assertEqual(p.languages,"eng")

if __name__=="__main__":
    unittest.main()
