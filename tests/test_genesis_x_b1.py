import unittest
from core.retrieval.hybrid.query_analysis import analyze_query
from core.retrieval.hybrid.dedup import duplicate_key
from core.retrieval.hybrid.metadata import metadata_score

class Tests(unittest.TestCase):
    def test_entity(self):
        q=analyze_query("NIST incident response")
        self.assertIn("NIST",q.entities)
    def test_duplicate_title_collapses(self):
        self.assertEqual(duplicate_key("Book.epub","a"),duplicate_key("Book.epub","b"))
    def test_nist_authority(self):
        q=analyze_query("NIST incident response")
        score,auth=metadata_score(q,"NIST SP 800-61","/x/nist/file.pdf")
        self.assertGreater(auth,0)
if __name__=="__main__":unittest.main()
