# Genesis X-A2 — Advanced Document Extraction & Recovery

Targets only X-A1 `FAILED` candidates. EPUB uses ZIP/spine extraction. PDF uses legacy extraction, then PyMuPDF fallback, then scan classification. Scan-only PDFs become `OCR_REQUIRED`; OCR is intentionally deferred. Recovered artifacts use the proven X-A1.2 batched single-writer path.
