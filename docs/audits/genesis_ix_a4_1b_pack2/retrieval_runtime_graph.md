# Genesis IX-A4.1B — Certified Retrieval Runtime Graph

```mermaid
flowchart TD
    N1["core.conversation.service.ExecutiveConversationService"]
    N2["core.conversation.orchestrator.ExecutiveConversationOrchestrator"]
    N3["core.conversation.grounding.CatalogGroundingService"]
    N4["core.knowledge_awareness.service.ExecutiveKnowledgeAwarenessService"]
    N5["core.executive.director.ExecutiveDirector"]
    N6["builtins.function"]
    N7["core.knowledge_catalog.search.search_catalog"]
    N8["core.knowledge_catalog.materialization.search.search_runtime_knowledge"]
    N9["SQLite runtime_chunks_fts"]
    N1 -->|live dependency injection| N2
    N2 -->|live dependency injection| N3
    N2 -->|live dependency injection| N4
    N2 -->|live dependency injection| N5
    N2 -->|live dependency injection| N6
    N3 -->|bound search handler| N7
    N7 -->|canonical search delegation| N8
    N8 -->|full-text retrieval| N9
    N3 -->|grounding assessment| N4
    N3 -->|grounding.synthesis_input()| N6
```

## Certified edges

| Source | Target | Evidence |
|---|---|---|
| `core.conversation.service.ExecutiveConversationService` | `core.conversation.orchestrator.ExecutiveConversationOrchestrator` | live dependency injection |
| `core.conversation.orchestrator.ExecutiveConversationOrchestrator` | `core.conversation.grounding.CatalogGroundingService` | live dependency injection |
| `core.conversation.orchestrator.ExecutiveConversationOrchestrator` | `core.knowledge_awareness.service.ExecutiveKnowledgeAwarenessService` | live dependency injection |
| `core.conversation.orchestrator.ExecutiveConversationOrchestrator` | `core.executive.director.ExecutiveDirector` | live dependency injection |
| `core.conversation.orchestrator.ExecutiveConversationOrchestrator` | `builtins.function` | live dependency injection |
| `core.conversation.grounding.CatalogGroundingService` | `core.knowledge_catalog.search.search_catalog` | bound search handler |
| `core.knowledge_catalog.search.search_catalog` | `core.knowledge_catalog.materialization.search.search_runtime_knowledge` | canonical search delegation |
| `core.knowledge_catalog.materialization.search.search_runtime_knowledge` | `SQLite runtime_chunks_fts` | full-text retrieval |
| `core.conversation.grounding.CatalogGroundingService` | `core.knowledge_awareness.service.ExecutiveKnowledgeAwarenessService` | grounding assessment |
| `core.conversation.grounding.CatalogGroundingService` | `builtins.function` | grounding.synthesis_input() |
