# Genesis IX-A5.7 Pack 1 — Corpus Intelligence

**Status:** **EXCELLENT**
**Classification:** **CORPUS_INTELLIGENCE_OPERATIONAL**
**Generated:** 2026-08-06T20:58:31.361897+00:00

## Summary

- Candidates: **11**
- Verified databases: **8**
- Invalid candidates: **3**
- Corpora: **131**
- Searchable corpora: **61**
- Runtime corpora: **30**
- FTS corpora: **4**

## Corpora

| Corpus | Rows | Roles | Pipeline | Searchable | Runtime | FTS |
|---|---:|---|---|---|---|---|
| `catalog.sqlite:chunks` | 0 | `['document_content']` | `['extraction_chunking']` | True | False | False |
| `catalog.sqlite:concepts` | 0 | `['document_content', 'taxonomy_ontology']` | `['extraction_chunking', 'semantic_enrichment']` | True | False | False |
| `catalog.sqlite:document_pages` | 0 | `['document_content']` | `['extraction_chunking']` | True | False | False |
| `catalog.sqlite:document_pages_fts` | 0 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | True |
| `catalog.sqlite:document_pages_fts_config` | 1 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.sqlite:document_pages_fts_content` | 0 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.sqlite:document_pages_fts_data` | 2 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.sqlite:document_pages_fts_docsize` | 0 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.sqlite:document_pages_fts_idx` | 0 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.sqlite:document_structure` | 15,612 | `['document_content']` | `['extraction_chunking']` | True | False | False |
| `catalog.sqlite:document_text` | 0 | `['document_content']` | `['extraction_chunking']` | True | False | False |
| `catalog.sqlite:documents` | 50,619 | `['document_registry']` | `['catalog']` | True | False | False |
| `catalog.sqlite:inspections` | 36,721 | `['assimilation_acquisition']` | `['assimilation']` | False | False | False |
| `catalog.sqlite:knowledge_index` | 50,619 | `['document_registry', 'assimilation_acquisition']` | `['catalog', 'assimilation']` | True | False | False |
| `catalog.sqlite:library_catalog` | 11,420 | `['document_registry', 'assimilation_acquisition']` | `['catalog', 'assimilation']` | True | False | False |
| `acquisitions.sqlite:acquisitions` | 24 | `['assimilation_acquisition']` | `['assimilation']` | False | False | False |
| `acquisitions.sqlite:attempts` | 13 | `['unclassified']` | `[]` | False | False | False |
| `conversation.sqlite:conversation_messages` | 129 | `['conversation']` | `['conversation']` | False | False | False |
| `conversation.sqlite:conversation_sessions` | 54 | `['conversation']` | `['conversation']` | False | False | False |
| `missions.sqlite:mission_events` | 1,026 | `['executive_mission']` | `['executive']` | False | False | False |
| `missions.sqlite:missions` | 102 | `['executive_mission']` | `['executive']` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:catalog_documents` | 3,684 | `['document_registry', 'assimilation_acquisition']` | `['catalog', 'assimilation']` | True | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:catalog_enrichment` | 794 | `['taxonomy_ontology']` | `['semantic_enrichment']` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:chunk_concepts` | 9 | `['document_content', 'taxonomy_ontology']` | `['extraction_chunking', 'semantic_enrichment']` | True | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:chunk_embeddings` | 19 | `['runtime_search', 'document_content', 'assimilation_acquisition']` | `['materialization_retrieval', 'extraction_chunking', 'assimilation']` | True | True | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:chunks` | 0 | `['document_content']` | `['extraction_chunking']` | True | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:collection_documents` | 3,655 | `['document_registry']` | `['catalog']` | True | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:collections` | 61 | `['unclassified']` | `[]` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:concepts` | 0 | `['document_content', 'taxonomy_ontology']` | `['extraction_chunking', 'semantic_enrichment']` | True | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:discovered_files` | 90,639 | `['unclassified']` | `[]` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_assimilation` | 3,684 | `['assimilation_acquisition']` | `['assimilation']` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_chunks` | 19 | `['runtime_search', 'document_content', 'taxonomy_ontology']` | `['materialization_retrieval', 'extraction_chunking', 'semantic_enrichment']` | True | True | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_concepts` | 0 | `['taxonomy_ontology']` | `['semantic_enrichment']` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_keywords` | 0 | `['unclassified']` | `[]` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_pages` | 0 | `['document_content']` | `['extraction_chunking']` | True | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_pages_fts` | 0 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | True |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_pages_fts_config` | 1 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_pages_fts_content` | 0 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_pages_fts_data` | 2 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_pages_fts_docsize` | 0 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_pages_fts_idx` | 0 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_relationships` | 0 | `['taxonomy_ontology']` | `['semantic_enrichment']` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_structure` | 0 | `['document_content']` | `['extraction_chunking']` | True | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_subjects` | 3,572 | `['unclassified']` | `[]` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_text` | 14 | `['document_content']` | `['extraction_chunking']` | True | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:document_topics` | 0 | `['taxonomy_ontology']` | `['semantic_enrichment']` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:documents` | 0 | `['document_registry']` | `['catalog']` | True | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:file_assets` | 0 | `['conversation']` | `['conversation']` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:graph_edges` | 2,814 | `['taxonomy_ontology']` | `['semantic_enrichment']` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:graph_nodes` | 820 | `['unclassified']` | `[]` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:inspections` | 0 | `['assimilation_acquisition']` | `['assimilation']` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:knowledge_assimilation_queue` | 791 | `['assimilation_acquisition']` | `['assimilation']` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:knowledge_classifications` | 90,003 | `['unclassified']` | `[]` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:knowledge_index` | 0 | `['document_registry', 'assimilation_acquisition']` | `['catalog', 'assimilation']` | True | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:knowledge_object_files` | 90,633 | `['unclassified']` | `[]` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:knowledge_object_members` | 0 | `['unclassified']` | `[]` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:knowledge_objects` | 794 | `['unclassified']` | `[]` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:knowledge_registry` | 897 | `['assimilation_acquisition']` | `['assimilation']` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:knowledge_validation` | 935 | `['unclassified']` | `[]` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:librarian_catalog` | 794 | `['unclassified']` | `[]` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:library_catalog` | 0 | `['document_registry', 'assimilation_acquisition']` | `['catalog', 'assimilation']` | True | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:promotion_history` | 25 | `['unclassified']` | `[]` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:resource_inspections` | 794 | `['assimilation_acquisition']` | `['assimilation']` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:schema_info` | 0 | `['unclassified']` | `[]` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:schema_migrations` | 5 | `['unclassified']` | `[]` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:sources` | 17 | `['unclassified']` | `[]` | False | False | False |
| `catalog.before_pdf_repair.20260710_040337.sqlite:topics` | 90 | `['taxonomy_ontology']` | `['semantic_enrichment']` | False | False | False |
| `catalog.sqlite:catalog_documents` | 3,684 | `['document_registry', 'assimilation_acquisition']` | `['catalog', 'assimilation']` | True | False | False |
| `catalog.sqlite:catalog_enrichment` | 794 | `['taxonomy_ontology']` | `['semantic_enrichment']` | False | False | False |
| `catalog.sqlite:chunk_concepts` | 9 | `['document_content', 'taxonomy_ontology']` | `['extraction_chunking', 'semantic_enrichment']` | True | False | False |
| `catalog.sqlite:chunk_embeddings` | 5 | `['runtime_search', 'document_content', 'assimilation_acquisition']` | `['materialization_retrieval', 'extraction_chunking', 'assimilation']` | True | True | False |
| `catalog.sqlite:chunks` | 0 | `['document_content']` | `['extraction_chunking']` | True | False | False |
| `catalog.sqlite:collection_documents` | 3,655 | `['document_registry']` | `['catalog']` | True | False | False |
| `catalog.sqlite:collections` | 61 | `['unclassified']` | `[]` | False | False | False |
| `catalog.sqlite:concepts` | 0 | `['document_content', 'taxonomy_ontology']` | `['extraction_chunking', 'semantic_enrichment']` | True | False | False |
| `catalog.sqlite:discovered_files` | 90,639 | `['unclassified']` | `[]` | False | False | False |
| `catalog.sqlite:document_assimilation` | 3,684 | `['assimilation_acquisition']` | `['assimilation']` | False | False | False |
| `catalog.sqlite:document_chunks` | 5 | `['runtime_search', 'document_content', 'taxonomy_ontology']` | `['materialization_retrieval', 'extraction_chunking', 'semantic_enrichment']` | True | True | False |
| `catalog.sqlite:document_concepts` | 0 | `['taxonomy_ontology']` | `['semantic_enrichment']` | False | False | False |
| `catalog.sqlite:document_keywords` | 0 | `['unclassified']` | `[]` | False | False | False |
| `catalog.sqlite:document_pages` | 0 | `['document_content']` | `['extraction_chunking']` | True | False | False |
| `catalog.sqlite:document_pages_fts` | 0 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | True |
| `catalog.sqlite:document_pages_fts_config` | 1 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.sqlite:document_pages_fts_content` | 0 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.sqlite:document_pages_fts_data` | 2 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.sqlite:document_pages_fts_docsize` | 0 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.sqlite:document_pages_fts_idx` | 0 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.sqlite:document_relationships` | 0 | `['taxonomy_ontology']` | `['semantic_enrichment']` | False | False | False |
| `catalog.sqlite:document_structure` | 0 | `['document_content']` | `['extraction_chunking']` | True | False | False |
| `catalog.sqlite:document_subjects` | 3,572 | `['unclassified']` | `[]` | False | False | False |
| `catalog.sqlite:document_text` | 14 | `['document_content']` | `['extraction_chunking']` | True | False | False |
| `catalog.sqlite:document_topics` | 0 | `['taxonomy_ontology']` | `['semantic_enrichment']` | False | False | False |
| `catalog.sqlite:documents` | 0 | `['document_registry']` | `['catalog']` | True | False | False |
| `catalog.sqlite:file_assets` | 0 | `['conversation']` | `['conversation']` | False | False | False |
| `catalog.sqlite:graph_edges` | 2,814 | `['taxonomy_ontology']` | `['semantic_enrichment']` | False | False | False |
| `catalog.sqlite:graph_nodes` | 820 | `['unclassified']` | `[]` | False | False | False |
| `catalog.sqlite:inspections` | 0 | `['assimilation_acquisition']` | `['assimilation']` | False | False | False |
| `catalog.sqlite:knowledge_assimilation_queue` | 791 | `['assimilation_acquisition']` | `['assimilation']` | False | False | False |
| `catalog.sqlite:knowledge_classifications` | 90,003 | `['unclassified']` | `[]` | False | False | False |
| `catalog.sqlite:knowledge_index` | 0 | `['document_registry', 'assimilation_acquisition']` | `['catalog', 'assimilation']` | True | False | False |
| `catalog.sqlite:knowledge_object_files` | 90,633 | `['unclassified']` | `[]` | False | False | False |
| `catalog.sqlite:knowledge_object_members` | 0 | `['unclassified']` | `[]` | False | False | False |
| `catalog.sqlite:knowledge_objects` | 794 | `['unclassified']` | `[]` | False | False | False |
| `catalog.sqlite:knowledge_registry` | 897 | `['assimilation_acquisition']` | `['assimilation']` | False | False | False |
| `catalog.sqlite:knowledge_validation` | 935 | `['unclassified']` | `[]` | False | False | False |
| `catalog.sqlite:librarian_catalog` | 794 | `['unclassified']` | `[]` | False | False | False |
| `catalog.sqlite:library_catalog` | 0 | `['document_registry', 'assimilation_acquisition']` | `['catalog', 'assimilation']` | True | False | False |
| `catalog.sqlite:promotion_history` | 25 | `['unclassified']` | `[]` | False | False | False |
| `catalog.sqlite:resource_inspections` | 794 | `['assimilation_acquisition']` | `['assimilation']` | False | False | False |
| `catalog.sqlite:runtime_chunks` | 4,674 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.sqlite:runtime_chunks_fts` | 4,674 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | True |
| `catalog.sqlite:runtime_chunks_fts_config` | 1 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.sqlite:runtime_chunks_fts_content` | 4,674 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.sqlite:runtime_chunks_fts_data` | 1,461 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.sqlite:runtime_chunks_fts_docsize` | 4,674 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.sqlite:runtime_chunks_fts_idx` | 1,593 | `['runtime_search', 'document_content']` | `['materialization_retrieval', 'extraction_chunking']` | True | True | False |
| `catalog.sqlite:runtime_documents` | 69 | `['runtime_search', 'document_registry']` | `['materialization_retrieval', 'catalog']` | True | True | False |
| `catalog.sqlite:schema_info` | 0 | `['unclassified']` | `[]` | False | False | False |
| `catalog.sqlite:schema_migrations` | 5 | `['unclassified']` | `[]` | False | False | False |
| `catalog.sqlite:sources` | 17 | `['unclassified']` | `[]` | False | False | False |
| `catalog.sqlite:topics` | 90 | `['taxonomy_ontology']` | `['semantic_enrichment']` | False | False | False |
| `cko.sqlite:knowledge_objects` | 256 | `['taxonomy_ontology']` | `['semantic_enrichment']` | False | False | False |
| `cko.sqlite:representations` | 672 | `['unclassified']` | `[]` | False | False | False |
| `librarian.sqlite:audit_runs` | 2 | `['telemetry_audit']` | `['observability']` | False | False | False |
| `librarian.sqlite:collection_issues` | 37 | `['conversation']` | `['conversation']` | False | False | False |
| `librarian.sqlite:coverage_scores` | 33 | `['unclassified']` | `[]` | False | False | False |
| `librarian.sqlite:document_concepts` | 0 | `['taxonomy_ontology']` | `['semantic_enrichment']` | False | False | False |
| `librarian.sqlite:document_subjects` | 4 | `['unclassified']` | `[]` | False | False | False |
| `librarian.sqlite:documents` | 3,655 | `['document_registry', 'conversation']` | `['catalog', 'conversation']` | True | False | False |
| `librarian.sqlite:duplicates` | 2 | `['unclassified']` | `[]` | False | False | False |
| `librarian.sqlite:gaps` | 90 | `['unclassified']` | `[]` | False | False | False |

## Recommendations

- Use this inventory as the canonical input to IX-A5.7 Pack 2.
- Do not infer metadata quality from table existence alone.
- Classify invalid database candidates without aborting the audit.
