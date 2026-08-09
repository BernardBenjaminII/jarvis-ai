# Genesis IX-A4.1B — Retrieval Canonicalization Report

## Decision summary

| Decision | Count |
|---|---:|
| AUDIT | 87 |
| DORMANT | 252 |
| KEEP | 25 |
| KEEP-AUXILIARY | 9 |

## Certified canonical path

```text
ExecutiveConversationService
    ↓
ExecutiveConversationOrchestrator
    ↓
CatalogGroundingService
    ↓
core.knowledge_catalog.search.search_catalog
    ↓
core.knowledge_catalog.materialization.search.search_runtime_knowledge
    ↓
runtime_chunks_fts
    ↓
GroundingResult
    ↓
ExecutiveKnowledgeAwarenessService
    ↓
ExecutiveDirector + synthesis_handler
```

## Immediate recommendations

1. Keep the current FTS-backed retrieval path as the Mark I canonical baseline.
2. Do not activate dormant semantic or reranking implementations until their contracts and consumers are certified.
3. Embedding coverage is currently **0.107%**; complete or intentionally scope the embedding pipeline before enabling semantic retrieval.
4. Treat unowned database tables as audit targets, not automatic deletion candidates.
5. Add observability only after the retrieval ownership map is accepted.
