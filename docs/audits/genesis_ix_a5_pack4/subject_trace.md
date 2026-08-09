# Genesis IX-A5 Pack 4 — Subject Qualification Trace

**Status:** **FAILED**
**Classification:** **SUBJECT_METADATA_MISSING_CRITICAL**

## Summary

- Probes: **6**
- Candidates: **50**
- Missing subject metadata: **50**
- Taxonomy mismatches: **0**
- Zero subject scores: **44**
- Top diagnosis: **MISSING_SUBJECT_METADATA**

## Diagnosis Counts

- `MISSING_SUBJECT_METADATA`: **50**

## Subject Heatmap

| Subject | Candidates | Exact | Alias | Missing | Mismatch | Accepted | Acceptance | Avg Subject Score |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `computer_architecture` | 10 | 0 | 0 | 10 | 0 | 0 | 0.0% | 0.000 |
| `cybersecurity` | 10 | 0 | 0 | 10 | 0 | 0 | 0.0% | 0.000 |
| `executive` | 10 | 0 | 0 | 10 | 0 | 0 | 0.0% | 0.000 |
| `medicine` | 0 | 0 | 0 | 0 | 0 | 0 | 0.0% | 0.000 |
| `programming` | 10 | 0 | 0 | 10 | 0 | 6 | 60.0% | 0.478 |
| `retrieval` | 10 | 0 | 0 | 10 | 0 | 0 | 0.0% | 0.000 |

## Probe Traces

### SUBJECT-SHA256 — SHA-256

- Normalized query: `sha-256`
- Query tokens: `['sha-256']`
- Detected subjects: `['cybersecurity', 'cryptography']`
- Raw rows: **10**
- Qualified rows: **0**
- Dominant diagnosis: **MISSING_SUBJECT_METADATA**

| Candidate | Stored Subjects | Domain | Exact | Alias | Overlap | Subject Score | Final | Threshold | Decision | Diagnosis |
|---|---|---|---|---|---:|---:|---:|---:|---|---|
| 735 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.607 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 4247 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.161 | 0.350 | rejected_low_relevance | MISSING_SUBJECT_METADATA |
| 4136 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.162 | 0.350 | rejected_low_relevance | MISSING_SUBJECT_METADATA |
| 678 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.161 | 0.350 | rejected_low_relevance | MISSING_SUBJECT_METADATA |
| 4165 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.161 | 0.350 | rejected_low_relevance | MISSING_SUBJECT_METADATA |
| 225 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.161 | 0.350 | rejected_low_relevance | MISSING_SUBJECT_METADATA |
| 4211 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.160 | 0.350 | rejected_low_relevance | MISSING_SUBJECT_METADATA |
| 890 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.160 | 0.350 | rejected_low_relevance | MISSING_SUBJECT_METADATA |
| 455 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.159 | 0.350 | rejected_low_relevance | MISSING_SUBJECT_METADATA |
| 2826 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.159 | 0.350 | rejected_low_relevance | MISSING_SUBJECT_METADATA |

### SUBJECT-FTS — full text search

- Normalized query: `full text search`
- Query tokens: `['full', 'text', 'search']`
- Detected subjects: `['retrieval', 'database', 'programming']`
- Raw rows: **10**
- Qualified rows: **0**
- Dominant diagnosis: **MISSING_SUBJECT_METADATA**

| Candidate | Stored Subjects | Domain | Exact | Alias | Overlap | Subject Score | Final | Threshold | Decision | Diagnosis |
|---|---|---|---|---|---:|---:|---:|---:|---|---|
| 845 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.409 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 584 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.285 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 4251 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.409 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 582 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.286 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 579 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.285 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 578 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.285 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 3737 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.296 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 1449 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.285 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 2092 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.285 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 523 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.295 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |

### SUBJECT-C — professional C programming

- Normalized query: `professional c programming`
- Query tokens: `['professional', 'c', 'programming']`
- Detected subjects: `['programming', 'computer_science']`
- Raw rows: **10**
- Qualified rows: **6**
- Dominant diagnosis: **MISSING_SUBJECT_METADATA**

| Candidate | Stored Subjects | Domain | Exact | Alias | Overlap | Subject Score | Final | Threshold | Decision | Diagnosis |
|---|---|---|---|---|---:|---:|---:|---:|---|---|
| 690 | `[]` | `` | `[]` | `[]` | 0.000 | 1.000 | 0.909 | 0.350 | accepted | MISSING_SUBJECT_METADATA |
| 695 | `[]` | `` | `[]` | `[]` | 0.000 | 1.000 | 0.909 | 0.350 | accepted | MISSING_SUBJECT_METADATA |
| 214 | `[]` | `` | `[]` | `[]` | 0.000 | 0.389 | 0.487 | 0.350 | accepted | MISSING_SUBJECT_METADATA |
| 885 | `[]` | `` | `[]` | `[]` | 0.000 | 1.000 | 0.909 | 0.350 | accepted | MISSING_SUBJECT_METADATA |
| 217 | `[]` | `` | `[]` | `[]` | 0.000 | 0.389 | 0.411 | 0.350 | accepted | MISSING_SUBJECT_METADATA |
| 859 | `[]` | `` | `[]` | `[]` | 0.000 | 1.000 | 0.908 | 0.350 | accepted | MISSING_SUBJECT_METADATA |
| 458 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.333 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 673 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.333 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 672 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.333 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 675 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.408 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |

### SUBJECT-COMPUTER-ARCH — computer architecture

- Normalized query: `computer architecture`
- Query tokens: `['computer', 'architecture']`
- Detected subjects: `['computer_architecture', 'computer_science']`
- Raw rows: **10**
- Qualified rows: **0**
- Dominant diagnosis: **MISSING_SUBJECT_METADATA**

| Candidate | Stored Subjects | Domain | Exact | Alias | Overlap | Subject Score | Final | Threshold | Decision | Diagnosis |
|---|---|---|---|---|---:|---:|---:|---:|---|---|
| 4112 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.607 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 4111 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.608 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 3957 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.610 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 709 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.393 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 2089 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.394 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 251 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.379 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 3736 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.379 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 255 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.379 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 4241 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.378 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 230 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.378 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |

### SUBJECT-EXECUTIVE-DIRECTOR — Executive Director

- Normalized query: `executive director`
- Query tokens: `['executive', 'director']`
- Detected subjects: `['executive', 'governance', 'jarvis']`
- Raw rows: **10**
- Qualified rows: **0**
- Dominant diagnosis: **MISSING_SUBJECT_METADATA**

| Candidate | Stored Subjects | Domain | Exact | Alias | Overlap | Subject Score | Final | Threshold | Decision | Diagnosis |
|---|---|---|---|---|---:|---:|---:|---:|---|---|
| 1416 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.607 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 1417 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.607 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 1560 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.607 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 1413 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.607 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 1405 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.607 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 1159 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.607 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 1169 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.606 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 1410 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.606 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 1160 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.606 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |
| 1158 | `[]` | `` | `[]` | `[]` | 0.000 | 0.000 | 0.606 | 0.350 | rejected_subject_mismatch | MISSING_SUBJECT_METADATA |

### SUBJECT-ANCA — ANCA vasculitis

- Normalized query: `anca vasculitis`
- Query tokens: `['anca', 'vasculitis']`
- Detected subjects: `['medicine', 'health']`
- Raw rows: **0**
- Qualified rows: **0**
- Dominant diagnosis: **None**

| Candidate | Stored Subjects | Domain | Exact | Alias | Overlap | Subject Score | Final | Threshold | Decision | Diagnosis |
|---|---|---|---|---|---:|---:|---:|---:|---|---|
| No candidates | — | — | — | — | — | — | — | — | — | — |

## Recommendations

- Run a catalog subject-metadata backfill before changing qualification weights.
- Measure metadata coverage by table and source collection.
