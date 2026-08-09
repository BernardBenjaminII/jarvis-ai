import unittest
from core.retrieval.semantic_index.predictive_routing import should_prefragment
class Tests(unittest.TestCase):
 def test_large(self):self.assertTrue(should_prefragment(chunk_text="x"*3000,token_estimate=100)[0])
 def test_token(self):self.assertTrue(should_prefragment(chunk_text="x"*1000,token_estimate=700)[0])
 def test_small(self):self.assertFalse(should_prefragment(chunk_text="x"*500,token_estimate=100)[0])
