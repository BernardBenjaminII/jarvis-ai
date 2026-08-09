from pathlib import Path
from core.knowledge_catalog.materialization import extract_text as legacy_extract_text
from .models import ExtractionOutcome
from .epub import extract_epub
class AdvancedExtractor:
 def extract(self,c):
  p=Path(c.path)
  if not p.is_file():return ExtractionOutcome(c.candidate_id,c.path,'inspection','MISSING_SOURCE','', 'Source file missing.',0,None)
  ext=c.extension.lower()
  if ext=='.epub':
   try:text,n=extract_epub(p)
   except Exception as e:return ExtractionOutcome(c.candidate_id,c.path,'epub_zip_spine','FAILED','',f'{type(e).__name__}: {e}',0,None)
   return ExtractionOutcome(c.candidate_id,c.path,'epub_zip_spine','RECOVERABLE' if len(text.strip())>=40 else 'UNRECOVERABLE',text if len(text.strip())>=40 else '',f'EPUB sections={n}',len(text),None)
  if ext=='.pdf':
   try:text=str(legacy_extract_text(p) or '')
   except Exception:text=''
   if len(text.strip())>=40:return ExtractionOutcome(c.candidate_id,c.path,'legacy_pdf','RECOVERABLE',text,'Recovered with legacy PDF extractor.',len(text),None)
   try:
    import fitz; doc=fitz.open(p); parts=[]; image_pages=0; sampled=0; pages=doc.page_count
    for page in doc:
     t=page.get_text('text') or ''
     if t.strip():parts.append(t)
     if sampled<12:
      sampled+=1
      if not t.strip() and page.get_images(full=False):image_pages+=1
    doc.close(); text='\n\n'.join(parts)
   except Exception as e:return ExtractionOutcome(c.candidate_id,c.path,'pymupdf','FAILED','',f'{type(e).__name__}: {e}',0,None)
   if len(text.strip())>=40:return ExtractionOutcome(c.candidate_id,c.path,'pymupdf','RECOVERABLE',text,f'Recovered with PyMuPDF; pages={pages}',len(text),pages)
   needs=sampled>0 and image_pages>=max(1,sampled//2)
   return ExtractionOutcome(c.candidate_id,c.path,'pdf_scan_classifier','OCR_REQUIRED' if needs else 'UNRECOVERABLE','',f'No usable native text; pages={pages}',0,pages)
  try:text=str(legacy_extract_text(p) or '')
  except Exception as e:return ExtractionOutcome(c.candidate_id,c.path,'legacy','FAILED','',f'{type(e).__name__}: {e}',0,None)
  return ExtractionOutcome(c.candidate_id,c.path,'legacy','RECOVERABLE' if len(text.strip())>=40 else 'UNRECOVERABLE',text if len(text.strip())>=40 else '','Legacy retry.',len(text),None)
