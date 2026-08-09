# Genesis IX-A4.1B Pack 3A — Executive Runtime Certification

## Mission

Certify the exact live Executive and retrieval ownership chain.

Pack 3A does not infer ownership from filenames or class names. It certifies
exact module-and-class identities and verifies the live dependency graph.

## Certified Chain

```text
ExecutiveConversationService
    ↓
ExecutiveRequestCompiler
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
ExecutiveDirector
    ↓
synthesis_handler
```

## Certification Domains

- canonical conversation service identity;
- compiler and repository identity;
- canonical orchestrator identity;
- grounding, awareness, and director identity;
- absence of legacy `answer_handler` bypass;
- bound grounding search handler;
- canonical catalog search identity;
- runtime materialized search identity;
- catalog database existence;
- populated runtime document, chunk, and FTS tables;
- grounding and knowledge-awareness prompt integration;
- synthesis-handler invocation;
- canonical search delegation to runtime retrieval.

## Outputs

```text
docs/audits/genesis_ix_a4_1b_pack3a/
    executive_runtime_certification.json
    executive_runtime_certification.md
```

## Failure Policy

Any incorrect module identity, missing dependency, fallback path, absent
runtime table, or missing synthesis edge fails certification.

Pack 3B may begin only after Pack 3A reports `EXCELLENT`.
