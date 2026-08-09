# Genesis X-A1.3 — Materialization Completion & Exception Audit

**Status:** **EXCELLENT**
**Classification:** **MATERIALIZATION_COMPLETE_WITH_ISOLATED_EXCEPTIONS**

## Completion

- Registered: **89,272**
- Complete: **89,121**
- Failed: **151**
- Pending: **0**
- Completion: **99.8309%**

## Runtime Integrity

- integrity_check: **ok**
- documents: **89,190**
- chunks: **778,341**
- FTS: **778,341**
- chunk/FTS parity: **True**
- reconciliation delta: **0**

## Failure Classes

- `NO_EXTRACTABLE_TEXT`: **126**
- `TRANSIENT_RETRYABLE`: **3**
- `UNKNOWN_REQUIRES_REVIEW`: **14**
- `UNSUPPORTED_OR_EXTRACTOR_GAP`: **8**

## Dispositions

- `MANUAL_REVIEW`: **14**
- `QUARANTINE_OR_REPAIR`: **134**
- `RETRY`: **3**

## Checks

| Check | Status |
|---|---|
| `no_pending_candidates` | **PASS** |
| `sqlite_integrity_ok` | **PASS** |
| `chunk_fts_parity` | **PASS** |
| `no_duplicate_runtime_paths` | **PASS** |
| `no_orphan_chunks` | **PASS** |
| `no_orphan_fts_rows` | **PASS** |
| `runtime_document_reconciliation` | **PASS** |
| `failed_not_present_in_runtime` | **PASS** |
