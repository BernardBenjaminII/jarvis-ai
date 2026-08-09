import unittest
from core.retrieval.semantic_index.throughput import should_backpressure

class Tests(unittest.TestCase):
    def test_backpressure_shape(self):
        p,r,t=should_backpressure(max_load1=999,min_mem_gib=0)
        self.assertIsInstance(p,bool)
        self.assertIsInstance(r,list)
        self.assertIn("load1",t)
