import unittest
from dev.materialization_completion_audit.audit import classify
class T(unittest.TestCase):
 def test_transient(self):self.assertEqual(classify('database is locked'),'TRANSIENT_RETRYABLE')
 def test_corrupt(self):self.assertEqual(classify('EOF marker not found'),'CORRUPT_OR_MALFORMED')
 def test_no_text(self):self.assertEqual(classify('Extractor produced no usable text'),'NO_EXTRACTABLE_TEXT')
if __name__=='__main__':unittest.main()
