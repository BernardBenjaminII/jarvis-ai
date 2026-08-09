# Materializer Implementation Intelligence

- Files inspected: `['/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/knowledge_catalog/materialization/engine.py', '/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/knowledge_catalog/materialization/cli.py', '/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/knowledge_catalog/materialization/search.py', '/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/knowledge_catalog/backfill.py']`
- Supported extensions inferred: `['.csv', '.epub', '.htm', '.html', '.json', '.md', '.pdf', '.txt', '.xml']`
- Selection/materialization functions: `['_candidates', 'chunk_text', 'extract_text', 'materialize', 'migrate_runtime_materialization']`
- Size limits: `['self.overlap_chars = max(0, min(int(overlap_chars), self.target_chunk_chars // 2))', 'self.target_chunk_chars = max(500, int(target_chunk_chars))', 'service = RuntimeKnowledgeMaterializer(database_path=args.database,target_chunk_chars=args.chunk_chars,overlap_chars=args.overlap_chars)']`

## Filters

- `file.suffix.lower() not in SUPPORTED`
- `str(row[0]) == candidate.sha256`
- `suffix == '.json'`
- `suffix == '.pdf'`
- `suffix in {'.html','.htm'}`
- `suffix not in _TEXT_SUFFIXES`

## Errors

- None.
