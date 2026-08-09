import unittest
from core.retrieval.semantic_index.context_adaptation import split_text,fragment_uuid
class Tests(unittest.TestCase):
 def test_short(self): self.assertEqual(len(list(split_text("abc",target_chars=10))),1)
 def test_long(self): self.assertGreater(len(list(split_text("alpha beta. "*500,target_chars=500,overlap_chars=50))),1)
 def test_uuid(self): self.assertEqual(fragment_uuid("x",0,"abc"),fragment_uuid("x",0,"abc"))
