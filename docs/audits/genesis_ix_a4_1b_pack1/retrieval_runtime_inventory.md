# Genesis IX-A4.1B Pack 1 — Retrieval Runtime Inventory

**Generated:** 2026-08-04T22:13:06.955104+00:00
**Repository:** `/media/abdullah/JARVISDATA/Projects/jarvis-ai`
**Database:** `/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite`
**Fingerprint:** `7e462461fb459098503797c0c0e0482d44fc81ea260406d688782159d82f586c`

## Summary

- Functions: **373**
- Classes: **194**
- Imports: **274**
- Runtime objects: **10**
- Database tables: **37**

## Live Runtime

```json
{
  "conversation_ask_signature": "(operator_input: 'str', *, session_id: 'str | None' = None, mode: 'str' = 'full', channel: 'str' = 'text', metadata: 'dict[str, Any] | None' = None) -> 'ExecutiveConversationResponse'",
  "errors": [],
  "objects": [
    {
      "attribute": "conversation_service",
      "details": {},
      "module": "core.conversation.service",
      "owner": "application",
      "type_name": "ExecutiveConversationService"
    },
    {
      "attribute": "compiler",
      "details": {},
      "module": "core.conversation.compiler",
      "owner": "conversation_service",
      "type_name": "ExecutiveRequestCompiler"
    },
    {
      "attribute": "repository",
      "details": {},
      "module": "core.conversation.repository",
      "owner": "conversation_service",
      "type_name": "ConversationRepository"
    },
    {
      "attribute": "orchestrator",
      "details": {},
      "module": "core.conversation.orchestrator",
      "owner": "conversation_service",
      "type_name": "ExecutiveConversationOrchestrator"
    },
    {
      "attribute": "answer_handler",
      "details": {},
      "module": null,
      "owner": "conversation_service",
      "type_name": null
    },
    {
      "attribute": "director",
      "details": {},
      "module": "core.executive.director",
      "owner": "orchestrator",
      "type_name": "ExecutiveDirector"
    },
    {
      "attribute": "grounding_service",
      "details": {
        "database_path": "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite",
        "search_handler": "CatalogGroundingService._search_catalog",
        "search_handler_module": "core.conversation.grounding"
      },
      "module": "core.conversation.grounding",
      "owner": "orchestrator",
      "type_name": "CatalogGroundingService"
    },
    {
      "attribute": "awareness_service",
      "details": {},
      "module": "core.knowledge_awareness.service",
      "owner": "orchestrator",
      "type_name": "ExecutiveKnowledgeAwarenessService"
    },
    {
      "attribute": "observability_service",
      "details": {},
      "module": null,
      "owner": "orchestrator",
      "type_name": null
    },
    {
      "attribute": "synthesis_handler",
      "details": {},
      "module": "builtins",
      "owner": "orchestrator",
      "type_name": "function"
    }
  ],
  "search_functions": [
    {
      "module": "core.knowledge_catalog.search",
      "qualname": "search_catalog",
      "signature": "(query: 'str', db_path: 'Path' = PosixPath('/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite'), limit: 'int' = 25) -> 'list[dict]'"
    },
    {
      "module": "core.knowledge_catalog.materialization.search",
      "qualname": "search_runtime_knowledge",
      "signature": "(query: 'str', *, db_path: 'str | Path' = PosixPath('/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite'), limit: 'int' = 8) -> 'list[dict[str, Any]]'"
    }
  ]
}
```

## Canonical Retrieval Functions

- `GroundingEvidence.to_dict` (`core/conversation/grounding.py:26`)
- `ObjectiveGrounding.status` (`core/conversation/grounding.py:63`)
- `ObjectiveGrounding.to_dict` (`core/conversation/grounding.py:66`)
- `GroundingResult.evidence` (`core/conversation/grounding.py:82`)
- `GroundingResult.gaps` (`core/conversation/grounding.py:86`)
- `GroundingResult.status` (`core/conversation/grounding.py:90`)
- `GroundingResult.to_dict` (`core/conversation/grounding.py:97`)
- `GroundingResult.for_objective` (`core/conversation/grounding.py:107`)
- `GroundingResult.synthesis_input` (`core/conversation/grounding.py:110`)
- `CatalogGroundingService.__init__` (`core/conversation/grounding.py:137`)
- `CatalogGroundingService._search_catalog` (`core/conversation/grounding.py:148`)
- `CatalogGroundingService.ground` (`core/conversation/grounding.py:152`)
- `CatalogGroundingService.search_for_director` (`core/conversation/grounding.py:161`)
- `CatalogGroundingService._ground_objective` (`core/conversation/grounding.py:178`)
- `ExecutiveConversationOrchestrator.__init__` (`core/conversation/orchestrator.py:72`)
- `ExecutiveDirector.__init__` (`core/executive/director.py:23`)
- `ExecutiveDirector.director_catalog` (`core/executive/director.py:165`)
- `ExecutiveKnowledgeAwarenessService.assess` (`core/knowledge_awareness/service.py:20`)
- `ExecutiveKnowledgeAwarenessService._evidence` (`core/knowledge_awareness/service.py:82`)
- `ExecutiveKnowledgeAwarenessService._maturity` (`core/knowledge_awareness/service.py:95`)
- `ExecutiveKnowledgeAwarenessService._answerability` (`core/knowledge_awareness/service.py:98`)
- `_fts_query` (`core/knowledge_catalog/materialization/search.py:8`)
- `_confidence` (`core/knowledge_catalog/materialization/search.py:12`)
- `search_runtime_knowledge` (`core/knowledge_catalog/materialization/search.py:17`)
- `search_catalog` (`core/knowledge_catalog/search.py:8`)

## Database Ownership

| Table | Readers | Writers |
|---|---:|---:|
| `SET` | 0 | 10 |
| `a` | 1 | 0 |
| `accepted` | 1 | 0 |
| `acquisition_admission_history` | 2 | 1 |
| `acquisition_provenance` | 4 | 1 |
| `canonical` | 1 | 0 |
| `catalog_documents` | 2 | 0 |
| `catalog_enrichment` | 1 | 0 |
| `chunk_concepts` | 1 | 1 |
| `chunk_embeddings` | 4 | 3 |
| `chunks` | 1 | 1 |
| `collection_documents` | 0 | 0 |
| `document_assimilation` | 0 | 0 |
| `document_chunks` | 10 | 5 |
| `document_concepts` | 0 | 0 |
| `document_keywords` | 0 | 0 |
| `document_pages` | 0 | 0 |
| `document_pages_fts` | 1 | 0 |
| `document_pages_fts_config` | 0 | 0 |
| `document_pages_fts_content` | 0 | 0 |
| `document_pages_fts_data` | 0 | 0 |
| `document_pages_fts_docsize` | 0 | 0 |
| `document_pages_fts_idx` | 0 | 0 |
| `document_relationships` | 0 | 0 |
| `document_structure` | 2 | 1 |
| `document_subjects` | 1 | 0 |
| `document_text` | 1 | 0 |
| `document_topics` | 0 | 1 |
| `documents` | 5 | 3 |
| `explicit` | 1 | 0 |
| `file_assets` | 2 | 1 |
| `inspections` | 2 | 1 |
| `its` | 1 | 0 |
| `knowledge_assimilation_attempts` | 0 | 1 |
| `knowledge_assimilation_queue` | 0 | 1 |
| `knowledge_index` | 1 | 0 |
| `knowledge_object_files` | 1 | 0 |
| `knowledge_registry` | 2 | 3 |
| `librarian_catalog` | 3 | 1 |
| `library_catalog` | 1 | 1 |
| `ready_for_embedding` | 1 | 0 |
| `repository` | 1 | 0 |
| `resource_inspections` | 0 | 0 |
| `runtime_chunks` | 1 | 0 |
| `runtime_chunks_fts` | 1 | 0 |
| `runtime_chunks_fts_config` | 0 | 0 |
| `runtime_chunks_fts_content` | 0 | 0 |
| `runtime_chunks_fts_data` | 0 | 0 |
| `runtime_chunks_fts_docsize` | 0 | 0 |
| `runtime_chunks_fts_idx` | 0 | 0 |
| `runtime_documents` | 1 | 0 |
| `sources` | 3 | 1 |
| `sqlite_master` | 2 | 0 |
| `the` | 3 | 0 |
| `topics` | 3 | 1 |
| `was` | 0 | 1 |

## Pack Boundary

Pack 1 produces the machine-readable retrieval census. Pack 2 will derive the runtime graph, duplicate report, component matrix, and canonicalization decisions from this inventory.
