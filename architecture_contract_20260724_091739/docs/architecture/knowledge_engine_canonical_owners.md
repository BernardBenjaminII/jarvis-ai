# Knowledge Engine Canonical Owners

## Rule

No new top-level knowledge_engine package may be created unless an ADR approves it.

## Canonical Owners

| Capability | Canonical Package |
|---|---|
| Discovery | knowledge_engine.discovery |
| Knowledge Objects | knowledge_engine.objects |
| Collections | knowledge_engine.collections |
| Knowledge Registry | knowledge_engine.library |
| Classification | knowledge_engine.classification |
| Processing Pipeline | knowledge_engine.processing |
| Extraction | knowledge_engine.extraction |
| Inspection | knowledge_engine.inspectors |
| Structure | knowledge_engine.structure |
| Chunking | knowledge_engine.chunking |
| Embeddings | knowledge_engine.embeddings |
| Storage | knowledge_engine.storage |
| Queue | knowledge_engine.queue |
| Search | knowledge_engine.search |
| Providers | knowledge_engine.providers |
| Reports | knowledge_engine.reports |
| Metadata | knowledge_engine.metadata |
| Ontology Data | knowledge/ontology |

## Design Rule

The Librarian orchestrates the Knowledge Engine.

The Librarian does not own core Knowledge Engine capabilities.
