import unittest
from core.knowledge_catalog.corpus_hygiene.classifier import classify_filesystem_artifact
from core.knowledge_catalog.corpus_hygiene.final_recovery import choose_languages
class Tests(unittest.TestCase):
    def test_appledouble(self):self.assertEqual(classify_filesystem_artifact("/x/._foo.pdf")[0],"EXCLUDED_APPLEDOUBLE")
    def test_ds_store(self):self.assertEqual(classify_filesystem_artifact("/x/.DS_Store")[0],"EXCLUDED_FILESYSTEM_METADATA")
    def test_gitignore_preserved(self):self.assertIsNone(classify_filesystem_artifact("/x/.gitignore")[0])
    def test_arabic_routing(self):self.assertEqual(choose_languages("/x/WrightArabicGrammarVol2.pdf"),"eng+ara")
if __name__=="__main__":unittest.main()
