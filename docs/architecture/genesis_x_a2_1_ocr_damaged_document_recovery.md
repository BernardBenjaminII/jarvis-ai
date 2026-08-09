# Genesis X-A2.1 — OCR & Damaged Document Recovery

## Mission

Recover the remaining X-A1/X-A2 failed PDF population without disturbing the
successfully materialized corpus.

## Recovery Ladder

```text
FAILED PDF
   |
   +-- structural inspection
   |      |
   |      +-- openable ----------> native retry
   |      |
   |      +-- malformed ---------> PyMuPDF reconstruction
   |                                  |
   |                                  +--> native retry
   |
   +-- still no acceptable text
          |
          +--> bounded page rendering
          +--> Tesseract OCR
          +--> per-page timeout
          +--> quality gate
          |
          +-- pass --> existing X-A1.2 writer --> COMPLETE
          +-- fail --> remains FAILED with X-A2.1 recovery classification
```

## Safety

- Only X-A1 checkpoint rows currently in `FAILED` are selected.
- OCR is never used on already successful documents.
- Default maximum OCR pages per document: 80.
- Default rendering: 180 DPI with a pixel cap.
- Default per-page OCR timeout: 45 seconds.
- OCR results must pass character and quality thresholds.
- Tesseract and required language data are detected before OCR.
- OCR recovery state is stored separately in
  `.runtime/materialization/genesis_x_a2_1_recovery.sqlite`.
- Existing X-A1.2 single-writer/batched transaction infrastructure is reused.

## Provenance Labels

- `native_retry`
- `repaired_native`
- `ocr`
- `repaired_ocr`
- `pdf_repair`
- `ocr_dependency`

X-A2.1 does not silently claim unreadable documents are recovered.
