import tempfile,unittest,zipfile
from pathlib import Path
from core.knowledge_catalog.advanced_extraction.epub import extract_epub
class Tests(unittest.TestCase):
 def test_epub(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'a.epub';z=zipfile.ZipFile(p,'w');z.writestr('a.xhtml','<html><body><h1>Hello</h1><p>'+('world '*20)+'</p></body></html>');z.close();text,n=extract_epub(p);self.assertIn('Hello',text);self.assertEqual(n,1)
if __name__=='__main__':unittest.main()
