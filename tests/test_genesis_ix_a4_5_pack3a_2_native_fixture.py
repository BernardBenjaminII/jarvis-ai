from __future__ import annotations
import unittest
from core.retrieval.certification.tracer import EndToEndRetrievalTracer, METADATA_TERMS

class Tests(unittest.TestCase):
    def test_sha256_rejected(self):
        self.assertEqual(EndToEndRetrievalTracer._semantic_phrase("sha256"), "")

    def test_metadata_phrase_rejected(self):
        self.assertEqual(
            EndToEndRetrievalTracer._semantic_phrase("file_path confidence chunk_id"),
            "",
        )

    def test_digest_removed(self):
        value = EndToEndRetrievalTracer._semantic_phrase(
            "aabbccddeeff00112233445566778899 Hydraulic Maintenance Manual"
        )
        self.assertEqual(value, "Hydraulic Maintenance Manual")

    def test_semantic_title_survives(self):
        value = EndToEndRetrievalTracer._semantic_phrase(
            "SQLite Full Text Search Architecture"
        )
        self.assertEqual(value, "SQLite Full Search Architecture")

    def test_phrase_bounded(self):
        value = EndToEndRetrievalTracer._semantic_phrase(
            "one two three four five six seven eight nine ten eleven twelve"
        )
        self.assertLessEqual(len(value.split()), 10)

    def test_metadata_vocabulary(self):
        self.assertIn("sha256", METADATA_TERMS)

if __name__ == "__main__":
    unittest.main()
