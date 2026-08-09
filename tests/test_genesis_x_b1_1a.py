import unittest
from core.retrieval.semantic_index.reliability import validate_vectors,ProviderFailure,backoff_seconds
class Tests(unittest.TestCase):
    def test_valid(self): self.assertEqual(validate_vectors([[1,0],[0,1]],2,2),2)
    def test_count(self):
        with self.assertRaises(ProviderFailure): validate_vectors([[1]],2,1)
    def test_nan(self):
        with self.assertRaises(ProviderFailure): validate_vectors([[float("nan")]],1,1)
    def test_backoff(self): self.assertLessEqual(backoff_seconds(10),2.0)
