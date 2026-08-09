import unittest
from core.retrieval.certification.genesis_x_b import BENCHMARKS
class Tests(unittest.TestCase):
 def test_suite(self): self.assertGreaterEqual(len(BENCHMARKS),6)
 def test_unique_categories(self): self.assertEqual(len(BENCHMARKS),len({x[0] for x in BENCHMARKS}))
 def test_queries(self): self.assertTrue(all(q.strip() for _,q in BENCHMARKS))
