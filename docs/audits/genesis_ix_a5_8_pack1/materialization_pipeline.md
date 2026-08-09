# Genesis IX-A5.8 Pack 1 — Materialization Pipeline Trace

| Stage | Table | Present | Rows | Identity Columns |
|---|---|---|---:|---|
| `physical_catalog_registry` | `documents` | True | 0 | `['relative_path', 'sha256', 'id']` |
| `search_metadata_registry` | `knowledge_index` | True | 0 | `['document_path']` |
| `library_registry` | `library_catalog` | True | 0 | `['document_path']` |
| `classified_files` | `knowledge_classifications` | True | 90,003 | `['file_path', 'id']` |
| `runtime_documents` | `runtime_documents` | True | 69 | `['file_path', 'sha256', 'id']` |
| `runtime_chunks` | `runtime_chunks` | True | 4,674 | `['content_sha256', 'document_id', 'id']` |
| `runtime_fts` | `runtime_chunks_fts` | True | 4,674 | `['file_path', 'document_id']` |

## Lineage Edges

| Source | Target | Identity | Match Rate | Target/Source | Classification |
|---|---|---|---:|---:|---|
| `physical_catalog_registry` | `search_metadata_registry` | `None` | — | 0.0000 | `no_identity_join` |
| `search_metadata_registry` | `library_registry` | `None` | — | 0.0000 | `no_identity_join` |
| `library_registry` | `classified_files` | `['document_path', 'file_path']` | 0.00% | 0.0000 | `weak_lineage` |
| `classified_files` | `runtime_documents` | `['file_path', 'file_path']` | 0.01% | 0.0008 | `weak_lineage` |
| `runtime_documents` | `runtime_chunks` | `['id', 'document_id']` | 100.00% | 67.7391 | `strong_lineage` |
| `runtime_chunks` | `runtime_fts` | `['id', 'document_id']` | 1.48% | 1.0000 | `weak_lineage` |
