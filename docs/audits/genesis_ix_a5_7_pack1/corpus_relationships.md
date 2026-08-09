# Corpus Relationships

| Source | Relation | Target | Confidence | Evidence |
|---|---|---|---:|---|
| `acquisitions.sqlite:attempts` | `foreign_key` | `acquisitions.sqlite:acquisitions` | 1.00 | `{'from': 'item_id', 'to': 'item_id'}` |
| `conversation.sqlite:conversation_messages` | `foreign_key` | `conversation.sqlite:conversation_sessions` | 1.00 | `{'from': 'session_id', 'to': 'session_id'}` |
| `missions.sqlite:mission_events` | `foreign_key` | `missions.sqlite:missions` | 1.00 | `{'from': 'mission_id', 'to': 'mission_id'}` |
| `catalog.before_pdf_repair.20260710_040337.sqlite:catalog_enrichment` | `foreign_key` | `catalog.before_pdf_repair.20260710_040337.sqlite:knowledge_objects` | 1.00 | `{'from': 'object_uuid', 'to': 'object_uuid'}` |
| `catalog.before_pdf_repair.20260710_040337.sqlite:chunk_embeddings` | `foreign_key` | `catalog.before_pdf_repair.20260710_040337.sqlite:document_chunks` | 1.00 | `{'from': 'chunk_uuid', 'to': 'chunk_uuid'}` |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_relationships` | `foreign_key` | `catalog.before_pdf_repair.20260710_040337.sqlite:documents` | 1.00 | `{'from': 'to_document_id', 'to': 'id'}` |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_relationships` | `foreign_key` | `catalog.before_pdf_repair.20260710_040337.sqlite:documents` | 1.00 | `{'from': 'from_document_id', 'to': 'id'}` |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_topics` | `foreign_key` | `catalog.before_pdf_repair.20260710_040337.sqlite:topics` | 1.00 | `{'from': 'topic_id', 'to': 'id'}` |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_topics` | `foreign_key` | `catalog.before_pdf_repair.20260710_040337.sqlite:documents` | 1.00 | `{'from': 'document_id', 'to': 'id'}` |
| `catalog.before_pdf_repair.20260710_040337.sqlite:documents` | `foreign_key` | `catalog.before_pdf_repair.20260710_040337.sqlite:sources` | 1.00 | `{'from': 'source_id', 'to': 'id'}` |
| `catalog.before_pdf_repair.20260710_040337.sqlite:file_assets` | `foreign_key` | `catalog.before_pdf_repair.20260710_040337.sqlite:documents` | 1.00 | `{'from': 'document_id', 'to': 'id'}` |
| `catalog.before_pdf_repair.20260710_040337.sqlite:graph_edges` | `foreign_key` | `catalog.before_pdf_repair.20260710_040337.sqlite:graph_nodes` | 1.00 | `{'from': 'target_node_uuid', 'to': 'node_uuid'}` |
| `catalog.before_pdf_repair.20260710_040337.sqlite:graph_edges` | `foreign_key` | `catalog.before_pdf_repair.20260710_040337.sqlite:graph_nodes` | 1.00 | `{'from': 'source_node_uuid', 'to': 'node_uuid'}` |
| `catalog.before_pdf_repair.20260710_040337.sqlite:knowledge_classifications` | `foreign_key` | `catalog.before_pdf_repair.20260710_040337.sqlite:discovered_files` | 1.00 | `{'from': 'discovered_file_id', 'to': 'id'}` |
| `catalog.before_pdf_repair.20260710_040337.sqlite:knowledge_object_files` | `foreign_key` | `catalog.before_pdf_repair.20260710_040337.sqlite:discovered_files` | 1.00 | `{'from': 'discovered_file_id', 'to': 'id'}` |
| `catalog.before_pdf_repair.20260710_040337.sqlite:knowledge_object_files` | `foreign_key` | `catalog.before_pdf_repair.20260710_040337.sqlite:knowledge_objects` | 1.00 | `{'from': 'object_uuid', 'to': 'object_uuid'}` |
| `catalog.before_pdf_repair.20260710_040337.sqlite:librarian_catalog` | `foreign_key` | `catalog.before_pdf_repair.20260710_040337.sqlite:knowledge_objects` | 1.00 | `{'from': 'object_uuid', 'to': 'object_uuid'}` |
| `catalog.before_pdf_repair.20260710_040337.sqlite:resource_inspections` | `foreign_key` | `catalog.before_pdf_repair.20260710_040337.sqlite:knowledge_objects` | 1.00 | `{'from': 'object_uuid', 'to': 'object_uuid'}` |
| `catalog.sqlite:catalog_enrichment` | `foreign_key` | `catalog.sqlite:knowledge_objects` | 1.00 | `{'from': 'object_uuid', 'to': 'object_uuid'}` |
| `catalog.sqlite:chunk_embeddings` | `foreign_key` | `catalog.sqlite:document_chunks` | 1.00 | `{'from': 'chunk_uuid', 'to': 'chunk_uuid'}` |
| `catalog.sqlite:document_relationships` | `foreign_key` | `catalog.sqlite:documents` | 1.00 | `{'from': 'to_document_id', 'to': 'id'}` |
| `catalog.sqlite:document_relationships` | `foreign_key` | `catalog.sqlite:documents` | 1.00 | `{'from': 'from_document_id', 'to': 'id'}` |
| `catalog.sqlite:document_topics` | `foreign_key` | `catalog.sqlite:topics` | 1.00 | `{'from': 'topic_id', 'to': 'id'}` |
| `catalog.sqlite:document_topics` | `foreign_key` | `catalog.sqlite:documents` | 1.00 | `{'from': 'document_id', 'to': 'id'}` |
| `catalog.sqlite:documents` | `foreign_key` | `catalog.sqlite:sources` | 1.00 | `{'from': 'source_id', 'to': 'id'}` |
| `catalog.sqlite:file_assets` | `foreign_key` | `catalog.sqlite:documents` | 1.00 | `{'from': 'document_id', 'to': 'id'}` |
| `catalog.sqlite:graph_edges` | `foreign_key` | `catalog.sqlite:graph_nodes` | 1.00 | `{'from': 'target_node_uuid', 'to': 'node_uuid'}` |
| `catalog.sqlite:graph_edges` | `foreign_key` | `catalog.sqlite:graph_nodes` | 1.00 | `{'from': 'source_node_uuid', 'to': 'node_uuid'}` |
| `catalog.sqlite:knowledge_classifications` | `foreign_key` | `catalog.sqlite:discovered_files` | 1.00 | `{'from': 'discovered_file_id', 'to': 'id'}` |
| `catalog.sqlite:knowledge_object_files` | `foreign_key` | `catalog.sqlite:discovered_files` | 1.00 | `{'from': 'discovered_file_id', 'to': 'id'}` |
| `catalog.sqlite:knowledge_object_files` | `foreign_key` | `catalog.sqlite:knowledge_objects` | 1.00 | `{'from': 'object_uuid', 'to': 'object_uuid'}` |
| `catalog.sqlite:librarian_catalog` | `foreign_key` | `catalog.sqlite:knowledge_objects` | 1.00 | `{'from': 'object_uuid', 'to': 'object_uuid'}` |
| `catalog.sqlite:resource_inspections` | `foreign_key` | `catalog.sqlite:knowledge_objects` | 1.00 | `{'from': 'object_uuid', 'to': 'object_uuid'}` |
| `catalog.sqlite:runtime_chunks` | `foreign_key` | `catalog.sqlite:runtime_documents` | 1.00 | `{'from': 'document_id', 'to': 'id'}` |
| `catalog.sqlite:runtime_documents` | `materializes_to_chunks` | `catalog.sqlite:runtime_chunks` | 0.95 | `{'observed_tables': True}` |
| `catalog.sqlite:runtime_chunks` | `indexed_by_fts` | `catalog.sqlite:runtime_chunks_fts` | 0.95 | `{'observed_tables': True}` |
| `cko.sqlite:representations` | `foreign_key` | `cko.sqlite:knowledge_objects` | 1.00 | `{'from': 'cko_id', 'to': 'cko_id'}` |
