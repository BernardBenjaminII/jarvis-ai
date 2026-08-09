import unittest
from core.retrieval.semantic_index.context_tree import child_fragment_uuid
class Tests(unittest.TestCase):
    def test_child_uuid_changes_by_parent(self):
        self.assertNotEqual(child_fragment_uuid("a",0,"x"),child_fragment_uuid("b",0,"x"))
