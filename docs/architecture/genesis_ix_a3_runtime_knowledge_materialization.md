# Genesis IX-A3 — Runtime Knowledge Materialization

IX-A3 bridges `catalog_documents` to executable knowledge:

```text
catalog_documents → extraction → runtime_documents → runtime_chunks → runtime_chunks_fts → grounding
```

The engine is incremental, provenance-preserving, and content-grounded. It supports common text, source, HTML, structured-text, and PDF files. PDF extraction uses `pypdf` or `PyPDF2` when installed.

Start with a controlled batch:

```bash
python -m core.knowledge_catalog.materialization.cli materialize --limit 100
python -m core.knowledge_catalog.materialization.cli search "cybersecurity"
```

Existing metadata-only `document_subjects` search remains a fallback.
