# Table Inventory

| Database | Table | Rows | Columns | PK | FK | Virtual | FTS | Roles |
|---|---|---:|---:|---|---:|---|---|---|
| catalog.sqlite | `chunks` | 0 | 7 | `['id']` | 0 | False | False | `['document_content']` |
| catalog.sqlite | `concepts` | 0 | 6 | `['id']` | 0 | False | False | `['document_content', 'taxonomy_ontology']` |
| catalog.sqlite | `document_pages` | 0 | 5 | `['id']` | 0 | False | False | `['document_content']` |
| catalog.sqlite | `document_pages_fts` | 0 | 3 | `[]` | 0 | True | True | `['runtime_search', 'document_content']` |
| catalog.sqlite | `document_pages_fts_config` | 1 | 2 | `['k']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.sqlite | `document_pages_fts_content` | 0 | 4 | `['id']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.sqlite | `document_pages_fts_data` | 2 | 2 | `['id']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.sqlite | `document_pages_fts_docsize` | 0 | 2 | `['id']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.sqlite | `document_pages_fts_idx` | 0 | 3 | `['segid', 'term']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.sqlite | `document_structure` | 15,612 | 9 | `['id']` | 0 | False | False | `['document_content']` |
| catalog.sqlite | `document_text` | 0 | 7 | `['document_path']` | 0 | False | False | `['document_content']` |
| catalog.sqlite | `documents` | 50,619 | 12 | `['id']` | 0 | False | False | `['document_registry']` |
| catalog.sqlite | `inspections` | 36,721 | 6 | `['document_path']` | 0 | False | False | `['assimilation_acquisition']` |
| catalog.sqlite | `knowledge_index` | 50,619 | 15 | `['document_path']` | 0 | False | False | `['document_registry', 'assimilation_acquisition']` |
| catalog.sqlite | `library_catalog` | 11,420 | 18 | `['document_path']` | 0 | False | False | `['document_registry', 'assimilation_acquisition']` |
| acquisitions.sqlite | `acquisitions` | 24 | 18 | `['item_id']` | 0 | False | False | `['assimilation_acquisition']` |
| acquisitions.sqlite | `attempts` | 13 | 6 | `['id']` | 1 | False | False | `['unclassified']` |
| conversation.sqlite | `conversation_messages` | 129 | 7 | `['message_id']` | 1 | False | False | `['conversation']` |
| conversation.sqlite | `conversation_sessions` | 54 | 4 | `['session_id']` | 0 | False | False | `['conversation']` |
| missions.sqlite | `mission_events` | 1,026 | 5 | `['event_id']` | 1 | False | False | `['executive_mission']` |
| missions.sqlite | `missions` | 102 | 6 | `['mission_id']` | 0 | False | False | `['executive_mission']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `catalog_documents` | 3,684 | 14 | `['id']` | 0 | False | False | `['document_registry', 'assimilation_acquisition']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `catalog_enrichment` | 794 | 9 | `['object_uuid']` | 1 | False | False | `['taxonomy_ontology']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `chunk_concepts` | 9 | 10 | `['id']` | 0 | False | False | `['document_content', 'taxonomy_ontology']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `chunk_embeddings` | 19 | 6 | `['chunk_uuid']` | 1 | False | False | `['runtime_search', 'document_content', 'assimilation_acquisition']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `chunks` | 0 | 7 | `['id']` | 0 | False | False | `['document_content']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `collection_documents` | 3,655 | 6 | `['collection_id', 'file_path']` | 0 | False | False | `['document_registry']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `collections` | 61 | 10 | `['id']` | 0 | False | False | `['unclassified']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `concepts` | 0 | 6 | `['id']` | 0 | False | False | `['document_content', 'taxonomy_ontology']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `discovered_files` | 90,639 | 12 | `['id']` | 0 | False | False | `['unclassified']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `document_assimilation` | 3,684 | 12 | `['file_path']` | 0 | False | False | `['assimilation_acquisition']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `document_chunks` | 19 | 11 | `['chunk_uuid']` | 0 | False | False | `['runtime_search', 'document_content', 'taxonomy_ontology']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `document_concepts` | 0 | 6 | `['file_path', 'concept']` | 0 | False | False | `['taxonomy_ontology']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `document_keywords` | 0 | 5 | `['file_path', 'keyword']` | 0 | False | False | `['unclassified']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `document_pages` | 0 | 5 | `['id']` | 0 | False | False | `['document_content']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `document_pages_fts` | 0 | 3 | `[]` | 0 | True | True | `['runtime_search', 'document_content']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `document_pages_fts_config` | 1 | 2 | `['k']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `document_pages_fts_content` | 0 | 4 | `['id']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `document_pages_fts_data` | 2 | 2 | `['id']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `document_pages_fts_docsize` | 0 | 2 | `['id']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `document_pages_fts_idx` | 0 | 3 | `['segid', 'term']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `document_relationships` | 0 | 6 | `['id']` | 2 | False | False | `['taxonomy_ontology']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `document_structure` | 0 | 9 | `['id']` | 0 | False | False | `['document_content']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `document_subjects` | 3,572 | 6 | `['file_path', 'subject']` | 0 | False | False | `['unclassified']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `document_text` | 14 | 8 | `['file_path']` | 0 | False | False | `['document_content']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `document_topics` | 0 | 4 | `['document_id', 'topic_id']` | 2 | False | False | `['taxonomy_ontology']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `documents` | 0 | 21 | `['id']` | 1 | False | False | `['document_registry']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `file_assets` | 0 | 13 | `['id']` | 1 | False | False | `['conversation']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `graph_edges` | 2,814 | 9 | `['edge_uuid']` | 2 | False | False | `['taxonomy_ontology']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `graph_nodes` | 820 | 8 | `['node_uuid']` | 0 | False | False | `['unclassified']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `inspections` | 0 | 6 | `['document_path']` | 0 | False | False | `['assimilation_acquisition']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `knowledge_assimilation_queue` | 791 | 9 | `['id']` | 0 | False | False | `['assimilation_acquisition']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `knowledge_classifications` | 90,003 | 10 | `['id']` | 1 | False | False | `['unclassified']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `knowledge_index` | 0 | 15 | `['document_path']` | 0 | False | False | `['document_registry', 'assimilation_acquisition']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `knowledge_object_files` | 90,633 | 5 | `['id']` | 2 | False | False | `['unclassified']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `knowledge_object_members` | 0 | 9 | `['id']` | 0 | False | False | `['unclassified']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `knowledge_objects` | 794 | 18 | `['id']` | 0 | False | False | `['unclassified']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `knowledge_registry` | 897 | 18 | `['id']` | 0 | False | False | `['assimilation_acquisition']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `knowledge_validation` | 935 | 8 | `['id']` | 0 | False | False | `['unclassified']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `librarian_catalog` | 794 | 17 | `['object_uuid']` | 1 | False | False | `['unclassified']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `library_catalog` | 0 | 18 | `['document_path']` | 0 | False | False | `['document_registry', 'assimilation_acquisition']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `promotion_history` | 25 | 7 | `['id']` | 0 | False | False | `['unclassified']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `resource_inspections` | 794 | 12 | `['object_uuid']` | 1 | False | False | `['assimilation_acquisition']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `schema_info` | 0 | 2 | `['key']` | 0 | False | False | `['unclassified']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `schema_migrations` | 5 | 2 | `['version']` | 0 | False | False | `['unclassified']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `sources` | 17 | 8 | `['id']` | 0 | False | False | `['unclassified']` |
| catalog.before_pdf_repair.20260710_040337.sqlite | `topics` | 90 | 7 | `['id']` | 0 | False | False | `['taxonomy_ontology']` |
| catalog.sqlite | `catalog_documents` | 3,684 | 14 | `['id']` | 0 | False | False | `['document_registry', 'assimilation_acquisition']` |
| catalog.sqlite | `catalog_enrichment` | 794 | 9 | `['object_uuid']` | 1 | False | False | `['taxonomy_ontology']` |
| catalog.sqlite | `chunk_concepts` | 9 | 10 | `['id']` | 0 | False | False | `['document_content', 'taxonomy_ontology']` |
| catalog.sqlite | `chunk_embeddings` | 5 | 6 | `['chunk_uuid']` | 1 | False | False | `['runtime_search', 'document_content', 'assimilation_acquisition']` |
| catalog.sqlite | `chunks` | 0 | 7 | `['id']` | 0 | False | False | `['document_content']` |
| catalog.sqlite | `collection_documents` | 3,655 | 6 | `['collection_id', 'file_path']` | 0 | False | False | `['document_registry']` |
| catalog.sqlite | `collections` | 61 | 10 | `['id']` | 0 | False | False | `['unclassified']` |
| catalog.sqlite | `concepts` | 0 | 6 | `['id']` | 0 | False | False | `['document_content', 'taxonomy_ontology']` |
| catalog.sqlite | `discovered_files` | 90,639 | 12 | `['id']` | 0 | False | False | `['unclassified']` |
| catalog.sqlite | `document_assimilation` | 3,684 | 12 | `['file_path']` | 0 | False | False | `['assimilation_acquisition']` |
| catalog.sqlite | `document_chunks` | 5 | 11 | `['chunk_uuid']` | 0 | False | False | `['runtime_search', 'document_content', 'taxonomy_ontology']` |
| catalog.sqlite | `document_concepts` | 0 | 6 | `['file_path', 'concept']` | 0 | False | False | `['taxonomy_ontology']` |
| catalog.sqlite | `document_keywords` | 0 | 5 | `['file_path', 'keyword']` | 0 | False | False | `['unclassified']` |
| catalog.sqlite | `document_pages` | 0 | 5 | `['id']` | 0 | False | False | `['document_content']` |
| catalog.sqlite | `document_pages_fts` | 0 | 3 | `[]` | 0 | True | True | `['runtime_search', 'document_content']` |
| catalog.sqlite | `document_pages_fts_config` | 1 | 2 | `['k']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.sqlite | `document_pages_fts_content` | 0 | 4 | `['id']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.sqlite | `document_pages_fts_data` | 2 | 2 | `['id']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.sqlite | `document_pages_fts_docsize` | 0 | 2 | `['id']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.sqlite | `document_pages_fts_idx` | 0 | 3 | `['segid', 'term']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.sqlite | `document_relationships` | 0 | 6 | `['id']` | 2 | False | False | `['taxonomy_ontology']` |
| catalog.sqlite | `document_structure` | 0 | 9 | `['id']` | 0 | False | False | `['document_content']` |
| catalog.sqlite | `document_subjects` | 3,572 | 6 | `['file_path', 'subject']` | 0 | False | False | `['unclassified']` |
| catalog.sqlite | `document_text` | 14 | 8 | `['file_path']` | 0 | False | False | `['document_content']` |
| catalog.sqlite | `document_topics` | 0 | 4 | `['document_id', 'topic_id']` | 2 | False | False | `['taxonomy_ontology']` |
| catalog.sqlite | `documents` | 0 | 21 | `['id']` | 1 | False | False | `['document_registry']` |
| catalog.sqlite | `file_assets` | 0 | 13 | `['id']` | 1 | False | False | `['conversation']` |
| catalog.sqlite | `graph_edges` | 2,814 | 9 | `['edge_uuid']` | 2 | False | False | `['taxonomy_ontology']` |
| catalog.sqlite | `graph_nodes` | 820 | 8 | `['node_uuid']` | 0 | False | False | `['unclassified']` |
| catalog.sqlite | `inspections` | 0 | 6 | `['document_path']` | 0 | False | False | `['assimilation_acquisition']` |
| catalog.sqlite | `knowledge_assimilation_queue` | 791 | 9 | `['id']` | 0 | False | False | `['assimilation_acquisition']` |
| catalog.sqlite | `knowledge_classifications` | 90,003 | 10 | `['id']` | 1 | False | False | `['unclassified']` |
| catalog.sqlite | `knowledge_index` | 0 | 15 | `['document_path']` | 0 | False | False | `['document_registry', 'assimilation_acquisition']` |
| catalog.sqlite | `knowledge_object_files` | 90,633 | 5 | `['id']` | 2 | False | False | `['unclassified']` |
| catalog.sqlite | `knowledge_object_members` | 0 | 9 | `['id']` | 0 | False | False | `['unclassified']` |
| catalog.sqlite | `knowledge_objects` | 794 | 18 | `['id']` | 0 | False | False | `['unclassified']` |
| catalog.sqlite | `knowledge_registry` | 897 | 18 | `['id']` | 0 | False | False | `['assimilation_acquisition']` |
| catalog.sqlite | `knowledge_validation` | 935 | 8 | `['id']` | 0 | False | False | `['unclassified']` |
| catalog.sqlite | `librarian_catalog` | 794 | 17 | `['object_uuid']` | 1 | False | False | `['unclassified']` |
| catalog.sqlite | `library_catalog` | 0 | 18 | `['document_path']` | 0 | False | False | `['document_registry', 'assimilation_acquisition']` |
| catalog.sqlite | `promotion_history` | 25 | 7 | `['id']` | 0 | False | False | `['unclassified']` |
| catalog.sqlite | `resource_inspections` | 794 | 12 | `['object_uuid']` | 1 | False | False | `['assimilation_acquisition']` |
| catalog.sqlite | `runtime_chunks` | 4,674 | 9 | `['id']` | 1 | False | False | `['runtime_search', 'document_content']` |
| catalog.sqlite | `runtime_chunks_fts` | 4,674 | 5 | `[]` | 0 | True | True | `['runtime_search', 'document_content']` |
| catalog.sqlite | `runtime_chunks_fts_config` | 1 | 2 | `['k']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.sqlite | `runtime_chunks_fts_content` | 4,674 | 6 | `['id']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.sqlite | `runtime_chunks_fts_data` | 1,461 | 2 | `['id']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.sqlite | `runtime_chunks_fts_docsize` | 4,674 | 2 | `['id']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.sqlite | `runtime_chunks_fts_idx` | 1,593 | 3 | `['segid', 'term']` | 0 | False | False | `['runtime_search', 'document_content']` |
| catalog.sqlite | `runtime_documents` | 69 | 9 | `['id']` | 0 | False | False | `['runtime_search', 'document_registry']` |
| catalog.sqlite | `schema_info` | 0 | 2 | `['key']` | 0 | False | False | `['unclassified']` |
| catalog.sqlite | `schema_migrations` | 5 | 2 | `['version']` | 0 | False | False | `['unclassified']` |
| catalog.sqlite | `sources` | 17 | 8 | `['id']` | 0 | False | False | `['unclassified']` |
| catalog.sqlite | `topics` | 90 | 7 | `['id']` | 0 | False | False | `['taxonomy_ontology']` |
| cko.sqlite | `knowledge_objects` | 256 | 9 | `['id']` | 0 | False | False | `['taxonomy_ontology']` |
| cko.sqlite | `representations` | 672 | 8 | `['id']` | 1 | False | False | `['unclassified']` |
| librarian.sqlite | `audit_runs` | 2 | 5 | `['id']` | 0 | False | False | `['telemetry_audit']` |
| librarian.sqlite | `collection_issues` | 37 | 6 | `['id']` | 0 | False | False | `['conversation']` |
| librarian.sqlite | `coverage_scores` | 33 | 7 | `['id']` | 0 | False | False | `['unclassified']` |
| librarian.sqlite | `document_concepts` | 0 | 7 | `['id']` | 0 | False | False | `['taxonomy_ontology']` |
| librarian.sqlite | `document_subjects` | 4 | 7 | `['id']` | 0 | False | False | `['unclassified']` |
| librarian.sqlite | `documents` | 3,655 | 20 | `['id']` | 0 | False | False | `['document_registry', 'conversation']` |
| librarian.sqlite | `duplicates` | 2 | 5 | `['id']` | 0 | False | False | `['unclassified']` |
| librarian.sqlite | `gaps` | 90 | 6 | `['id']` | 0 | False | False | `['unclassified']` |
