import unittest
from core.retrieval.semantic_index.context_router import is_context_overflow
class Tests(unittest.TestCase):
    def test_context_detection(self):
        self.assertTrue(is_context_overflow('HTTP 400 body={"error":"the input length exceeds the context length"}'))
    def test_non_context(self):
        self.assertFalse(is_context_overflow("connection reset"))
