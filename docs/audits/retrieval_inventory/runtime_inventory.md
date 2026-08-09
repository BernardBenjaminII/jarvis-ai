# Genesis IX-A4.2A — Retrieval Runtime Inventory

**Generated:** 2026-08-04T22:13:04.463773+00:00
**Repository:** `/media/abdullah/JARVISDATA/Projects/jarvis-ai`
**Catalog:** `/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite`

## Summary

- **component_count:** 929
- **live_component_count:** 27
- **runtime_binding_count:** 12
- **table_count:** 38
- **populated_table_count:** 24
- **graph_edge_count:** 333
- **capability_count:** 9
- **certified_capability_count:** 4

## Runtime bindings

| Owner | Attribute | Module | Type | Callable |
|---|---|---|---|---|
| `application` | `conversation_service` | `core.conversation.service` | `ExecutiveConversationService` | `None` |
| `conversation_service` | `compiler` | `core.conversation.compiler` | `ExecutiveRequestCompiler` | `None` |
| `conversation_service` | `repository` | `core.conversation.repository` | `ConversationRepository` | `None` |
| `conversation_service` | `orchestrator` | `core.conversation.orchestrator` | `ExecutiveConversationOrchestrator` | `None` |
| `conversation_service` | `answer_handler` | `None` | `None` | `None` |
| `orchestrator` | `director` | `core.executive.director` | `ExecutiveDirector` | `None` |
| `orchestrator` | `grounding_service` | `core.conversation.grounding` | `CatalogGroundingService` | `None` |
| `orchestrator` | `awareness_service` | `core.knowledge_awareness.service` | `ExecutiveKnowledgeAwarenessService` | `None` |
| `orchestrator` | `observability_service` | `None` | `None` | `None` |
| `orchestrator` | `synthesis_handler` | `builtins` | `function` | `route_question` |
| `retrieval` | `search_catalog` | `builtins` | `function` | `search_catalog` |
| `retrieval` | `search_runtime_knowledge` | `builtins` | `function` | `search_runtime_knowledge` |
