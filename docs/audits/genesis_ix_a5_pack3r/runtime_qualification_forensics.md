# Genesis IX-A5 Pack 3R — Runtime Qualification Forensics

**Status:** **FAILED**
**Classification:** **QUALIFICATION_RECALL_CRITICAL**

## Summary

- Known probes: **6**
- Raw recall: **83.3%**
- Qualified recall: **16.7%**
- Top failure: **SUBJECT**
- Probe errors: **0**

## Rejection Reasons

- `LEXICAL`: **19**
- `SUBJECT`: **35**

## Probe Matrix

| Probe | Query | Expected | Raw | Qualified | Dominant Failure | Error |
|---|---|---|---:|---:|---|---|
| `KNOWN-SHA256` | SHA-256 | known | 10 | 0 | LEXICAL |  |
| `KNOWN-SQLITE` | SQLite | known | 0 | 0 | None |  |
| `KNOWN-FTS` | full text search | known | 10 | 0 | SUBJECT |  |
| `KNOWN-C` | professional C programming | known | 10 | 6 | SUBJECT |  |
| `KNOWN-COMPUTER-ARCH` | computer architecture | known | 10 | 0 | SUBJECT |  |
| `KNOWN-EXECUTIVE-DIRECTOR` | Executive Director | known | 10 | 0 | SUBJECT |  |
| `POSSIBLE-ANCA` | ANCA vasculitis | possible | 0 | 0 | None |  |
| `GAP-QUANTUM-BANANA` | Quantum Banana Warp Core Mk XII | unknown | 10 | 0 | LEXICAL |  |

## Candidate Forensics

### KNOWN-SHA256 — SHA-256

| Rank | Title | Decision | Retrieval | Lexical | Phrase | Subject | Confidence | Final | Threshold | Margin | Reason |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 735 | rejected_subject_mismatch | — | 1.000 | 0.500 | 0.000 | — | 0.607 | 0.350 | 0.257 | SUBJECT |
| 2 | 4247 | rejected_low_relevance | — | 0.000 | 0.500 | 0.000 | — | 0.161 | 0.350 | -0.189 | LEXICAL |
| 3 | 4136 | rejected_low_relevance | — | 0.000 | 0.500 | 0.000 | — | 0.162 | 0.350 | -0.188 | LEXICAL |
| 4 | 678 | rejected_low_relevance | — | 0.000 | 0.500 | 0.000 | — | 0.161 | 0.350 | -0.189 | LEXICAL |
| 5 | 4165 | rejected_low_relevance | — | 0.000 | 0.500 | 0.000 | — | 0.161 | 0.350 | -0.189 | LEXICAL |
| 6 | 225 | rejected_low_relevance | — | 0.000 | 0.500 | 0.000 | — | 0.161 | 0.350 | -0.189 | LEXICAL |
| 7 | 4211 | rejected_low_relevance | — | 0.000 | 0.500 | 0.000 | — | 0.160 | 0.350 | -0.190 | LEXICAL |
| 8 | 890 | rejected_low_relevance | — | 0.000 | 0.500 | 0.000 | — | 0.160 | 0.350 | -0.190 | LEXICAL |
| 9 | 455 | rejected_low_relevance | — | 0.000 | 0.500 | 0.000 | — | 0.159 | 0.350 | -0.191 | LEXICAL |
| 10 | 2826 | rejected_low_relevance | — | 0.000 | 0.500 | 0.000 | — | 0.159 | 0.350 | -0.191 | LEXICAL |

Recommendations:

- Investigate dominant rejection class: LEXICAL.

### KNOWN-SQLITE — SQLite

| Rank | Title | Decision | Retrieval | Lexical | Phrase | Subject | Confidence | Final | Threshold | Margin | Reason |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| — | No candidate diagnostics | — | — | — | — | — | — | — | — | — | — |

Recommendations:

- Repair retrieval for this query before tuning qualification.

### KNOWN-FTS — full text search

| Rank | Title | Decision | Retrieval | Lexical | Phrase | Subject | Confidence | Final | Threshold | Margin | Reason |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 845 | rejected_subject_mismatch | — | 1.000 | 0.000 | 0.000 | — | 0.409 | 0.350 | 0.059 | SUBJECT |
| 2 | 584 | rejected_subject_mismatch | — | 0.646 | 0.000 | 0.000 | — | 0.285 | 0.350 | -0.065 | SUBJECT |
| 3 | 4251 | rejected_subject_mismatch | — | 1.000 | 0.000 | 0.000 | — | 0.409 | 0.350 | 0.059 | SUBJECT |
| 4 | 582 | rejected_subject_mismatch | — | 0.646 | 0.000 | 0.000 | — | 0.286 | 0.350 | -0.064 | SUBJECT |
| 5 | 579 | rejected_subject_mismatch | — | 0.646 | 0.000 | 0.000 | — | 0.285 | 0.350 | -0.065 | SUBJECT |
| 6 | 578 | rejected_subject_mismatch | — | 0.646 | 0.000 | 0.000 | — | 0.285 | 0.350 | -0.065 | SUBJECT |
| 7 | 3737 | rejected_subject_mismatch | — | 0.677 | 0.000 | 0.000 | — | 0.296 | 0.350 | -0.054 | SUBJECT |
| 8 | 1449 | rejected_subject_mismatch | — | 0.646 | 0.000 | 0.000 | — | 0.285 | 0.350 | -0.065 | SUBJECT |
| 9 | 2092 | rejected_subject_mismatch | — | 0.646 | 0.000 | 0.000 | — | 0.285 | 0.350 | -0.065 | SUBJECT |
| 10 | 523 | rejected_subject_mismatch | — | 0.677 | 0.000 | 0.000 | — | 0.295 | 0.350 | -0.055 | SUBJECT |

Recommendations:

- Investigate dominant rejection class: SUBJECT.

### KNOWN-C — professional C programming

| Rank | Title | Decision | Retrieval | Lexical | Phrase | Subject | Confidence | Final | Threshold | Margin | Reason |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 690 | accepted | — | 1.000 | 1.000 | 1.000 | — | 0.909 | 0.350 | 0.559 | — |
| 2 | 695 | accepted | — | 1.000 | 1.000 | 1.000 | — | 0.909 | 0.350 | 0.559 | — |
| 3 | 214 | accepted | — | 1.000 | 0.000 | 0.389 | — | 0.487 | 0.350 | 0.137 | — |
| 4 | 885 | accepted | — | 1.000 | 1.000 | 1.000 | — | 0.909 | 0.350 | 0.559 | — |
| 5 | 217 | accepted | — | 0.784 | 0.000 | 0.389 | — | 0.411 | 0.350 | 0.061 | — |
| 6 | 859 | accepted | — | 1.000 | 1.000 | 1.000 | — | 0.908 | 0.350 | 0.558 | — |
| 7 | 458 | rejected_subject_mismatch | — | 0.784 | 0.000 | 0.000 | — | 0.333 | 0.350 | -0.017 | SUBJECT |
| 8 | 673 | rejected_subject_mismatch | — | 0.784 | 0.000 | 0.000 | — | 0.333 | 0.350 | -0.017 | SUBJECT |
| 9 | 672 | rejected_subject_mismatch | — | 0.784 | 0.000 | 0.000 | — | 0.333 | 0.350 | -0.017 | SUBJECT |
| 10 | 675 | rejected_subject_mismatch | — | 1.000 | 0.000 | 0.000 | — | 0.408 | 0.350 | 0.058 | SUBJECT |

Recommendations:

- Preserve the accepted path as permanent regression coverage.

### KNOWN-COMPUTER-ARCH — computer architecture

| Rank | Title | Decision | Retrieval | Lexical | Phrase | Subject | Confidence | Final | Threshold | Margin | Reason |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 4112 | rejected_subject_mismatch | — | 1.000 | 0.500 | 0.000 | — | 0.607 | 0.350 | 0.257 | SUBJECT |
| 2 | 4111 | rejected_subject_mismatch | — | 1.000 | 0.500 | 0.000 | — | 0.608 | 0.350 | 0.258 | SUBJECT |
| 3 | 3957 | rejected_subject_mismatch | — | 1.000 | 0.500 | 0.000 | — | 0.610 | 0.350 | 0.260 | SUBJECT |
| 4 | 709 | rejected_subject_mismatch | — | 0.517 | 0.500 | 0.000 | — | 0.393 | 0.350 | 0.043 | SUBJECT |
| 5 | 2089 | rejected_subject_mismatch | — | 0.517 | 0.500 | 0.000 | — | 0.394 | 0.350 | 0.044 | SUBJECT |
| 6 | 251 | rejected_subject_mismatch | — | 0.483 | 0.500 | 0.000 | — | 0.379 | 0.350 | 0.029 | SUBJECT |
| 7 | 3736 | rejected_subject_mismatch | — | 0.483 | 0.500 | 0.000 | — | 0.379 | 0.350 | 0.029 | SUBJECT |
| 8 | 255 | rejected_subject_mismatch | — | 0.483 | 0.500 | 0.000 | — | 0.379 | 0.350 | 0.029 | SUBJECT |
| 9 | 4241 | rejected_subject_mismatch | — | 0.483 | 0.500 | 0.000 | — | 0.378 | 0.350 | 0.028 | SUBJECT |
| 10 | 230 | rejected_subject_mismatch | — | 0.483 | 0.500 | 0.000 | — | 0.378 | 0.350 | 0.028 | SUBJECT |

Recommendations:

- Investigate dominant rejection class: SUBJECT.

### KNOWN-EXECUTIVE-DIRECTOR — Executive Director

| Rank | Title | Decision | Retrieval | Lexical | Phrase | Subject | Confidence | Final | Threshold | Margin | Reason |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 1416 | rejected_subject_mismatch | — | 1.000 | 0.500 | 0.000 | — | 0.607 | 0.350 | 0.257 | SUBJECT |
| 2 | 1417 | rejected_subject_mismatch | — | 1.000 | 0.500 | 0.000 | — | 0.607 | 0.350 | 0.257 | SUBJECT |
| 3 | 1560 | rejected_subject_mismatch | — | 1.000 | 0.500 | 0.000 | — | 0.607 | 0.350 | 0.257 | SUBJECT |
| 4 | 1413 | rejected_subject_mismatch | — | 1.000 | 0.500 | 0.000 | — | 0.607 | 0.350 | 0.257 | SUBJECT |
| 5 | 1405 | rejected_subject_mismatch | — | 1.000 | 0.500 | 0.000 | — | 0.607 | 0.350 | 0.257 | SUBJECT |
| 6 | 1159 | rejected_subject_mismatch | — | 1.000 | 0.500 | 0.000 | — | 0.607 | 0.350 | 0.257 | SUBJECT |
| 7 | 1169 | rejected_subject_mismatch | — | 1.000 | 0.500 | 0.000 | — | 0.606 | 0.350 | 0.256 | SUBJECT |
| 8 | 1410 | rejected_subject_mismatch | — | 1.000 | 0.500 | 0.000 | — | 0.606 | 0.350 | 0.256 | SUBJECT |
| 9 | 1160 | rejected_subject_mismatch | — | 1.000 | 0.500 | 0.000 | — | 0.606 | 0.350 | 0.256 | SUBJECT |
| 10 | 1158 | rejected_subject_mismatch | — | 1.000 | 0.500 | 0.000 | — | 0.606 | 0.350 | 0.256 | SUBJECT |

Recommendations:

- Investigate dominant rejection class: SUBJECT.

### POSSIBLE-ANCA — ANCA vasculitis

| Rank | Title | Decision | Retrieval | Lexical | Phrase | Subject | Confidence | Final | Threshold | Margin | Reason |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| — | No candidate diagnostics | — | — | — | — | — | — | — | — | — | — |

Recommendations:

- Repair retrieval for this query before tuning qualification.

### GAP-QUANTUM-BANANA — Quantum Banana Warp Core Mk XII

| Rank | Title | Decision | Retrieval | Lexical | Phrase | Subject | Confidence | Final | Threshold | Margin | Reason |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 2997 | rejected_low_relevance | — | 0.000 | 0.000 | 0.000 | — | 0.059 | 0.350 | -0.291 | LEXICAL |
| 2 | 2730 | rejected_low_relevance | — | 0.000 | 0.000 | 0.000 | — | 0.058 | 0.350 | -0.292 | LEXICAL |
| 3 | 3268 | rejected_low_relevance | — | 0.000 | 0.000 | 0.000 | — | 0.058 | 0.350 | -0.292 | LEXICAL |
| 4 | 463 | rejected_low_relevance | — | 0.189 | 0.000 | 0.000 | — | 0.124 | 0.350 | -0.226 | LEXICAL |
| 5 | 1630 | rejected_low_relevance | — | 0.155 | 0.000 | 0.000 | — | 0.114 | 0.350 | -0.236 | LEXICAL |
| 6 | 3570 | rejected_low_relevance | — | 0.167 | 0.000 | 0.000 | — | 0.118 | 0.350 | -0.232 | LEXICAL |
| 7 | 456 | rejected_low_relevance | — | 0.189 | 0.000 | 0.000 | — | 0.126 | 0.350 | -0.224 | LEXICAL |
| 8 | 902 | rejected_low_relevance | — | 0.155 | 0.000 | 0.000 | — | 0.114 | 0.350 | -0.236 | LEXICAL |
| 9 | 455 | rejected_low_relevance | — | 0.155 | 0.000 | 0.000 | — | 0.113 | 0.350 | -0.237 | LEXICAL |
| 10 | 3958 | rejected_low_relevance | — | 0.155 | 0.000 | 0.000 | — | 0.113 | 0.350 | -0.237 | LEXICAL |

Recommendations:

- Investigate dominant rejection class: LEXICAL.

## Global Recommendations

- Do not modify qualification behavior until candidate diagnostics are reviewed.
- Promote each known probe into permanent regression coverage.
- Prioritize the dominant rejection class: SUBJECT.
