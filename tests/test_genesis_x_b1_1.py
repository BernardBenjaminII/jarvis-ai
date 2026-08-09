import unittest
from core.retrieval.semantic_index.identity import stable_chunk_uuid
from core.retrieval.semantic_index.vector import pack_vector,unpack_vector,cosine

class Tests(unittest.TestCase):
    def test_uuid_deterministic(self):
        a=stable_chunk_uuid(document_id=1,chunk_id=2,content_sha256="abc")
        b=stable_chunk_uuid(document_id=1,chunk_id=2,content_sha256="abc")
        self.assertEqual(a,b)
    def test_vector_roundtrip(self):
        raw,dim,sha=pack_vector([1,2,3])
        self.assertEqual(dim,3)
        self.assertEqual(len(unpack_vector(raw)),3)
    def test_cosine(self):
        self.assertAlmostEqual(cosine([1,0],[1,0]),1.0)
if __name__=="__main__":unittest.main()
