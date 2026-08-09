import unittest
from core.retrieval.semantic_index.context_tree import split_leaf_text,child_fragment_uuid
class Tests(unittest.TestCase):
 def test_split(self): self.assertGreater(len(list(split_leaf_text('abc def. '*500,target_chars=700,overlap_chars=70))),1)
 def test_uuid(self): self.assertEqual(child_fragment_uuid('p',0,'abc'),child_fragment_uuid('p',0,'abc'))
