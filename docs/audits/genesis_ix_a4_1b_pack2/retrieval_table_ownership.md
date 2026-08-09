# Genesis IX-A4.1B — Retrieval Table Ownership

| Table | Rows | Readers | Writers | State |
|---|---:|---:|---:|---|
| `SET` | None | 0 | 10 | write-only |
| `a` | None | 1 | 0 | read-only |
| `accepted` | None | 1 | 0 | read-only |
| `acquisition_admission_history` | None | 2 | 1 | active |
| `acquisition_provenance` | None | 4 | 1 | active |
| `canonical` | None | 1 | 0 | read-only |
| `catalog_documents` | 3684 | 2 | 0 | read-only |
| `catalog_enrichment` | 794 | 1 | 0 | read-only |
| `chunk_concepts` | 9 | 1 | 1 | active |
| `chunk_embeddings` | 5 | 4 | 3 | active |
| `chunks` | 0 | 1 | 1 | active |
| `collection_documents` | 3655 | 0 | 0 | unowned |
| `document_assimilation` | 3684 | 0 | 0 | unowned |
| `document_chunks` | 5 | 10 | 5 | active |
| `document_concepts` | 0 | 0 | 0 | unowned |
| `document_keywords` | 0 | 0 | 0 | unowned |
| `document_pages` | 0 | 0 | 0 | unowned |
| `document_pages_fts` | 0 | 1 | 0 | read-only |
| `document_pages_fts_config` | 1 | 0 | 0 | unowned |
| `document_pages_fts_content` | 0 | 0 | 0 | unowned |
| `document_pages_fts_data` | 2 | 0 | 0 | unowned |
| `document_pages_fts_docsize` | 0 | 0 | 0 | unowned |
| `document_pages_fts_idx` | 0 | 0 | 0 | unowned |
| `document_relationships` | 0 | 0 | 0 | unowned |
| `document_structure` | 0 | 2 | 1 | active |
| `document_subjects` | 3572 | 1 | 0 | read-only |
| `document_text` | 14 | 1 | 0 | read-only |
| `document_topics` | 0 | 0 | 1 | write-only |
| `documents` | 0 | 5 | 3 | active |
| `explicit` | None | 1 | 0 | read-only |
| `file_assets` | None | 2 | 1 | active |
| `inspections` | None | 2 | 1 | active |
| `its` | None | 1 | 0 | read-only |
| `knowledge_assimilation_attempts` | None | 0 | 1 | write-only |
| `knowledge_assimilation_queue` | None | 0 | 1 | write-only |
| `knowledge_index` | 0 | 1 | 0 | read-only |
| `knowledge_object_files` | None | 1 | 0 | read-only |
| `knowledge_registry` | 897 | 2 | 3 | active |
| `librarian_catalog` | 794 | 3 | 1 | active |
| `library_catalog` | 0 | 1 | 1 | active |
| `ready_for_embedding` | None | 1 | 0 | read-only |
| `repository` | None | 1 | 0 | read-only |
| `resource_inspections` | 794 | 0 | 0 | unowned |
| `runtime_chunks` | 4674 | 1 | 0 | read-only |
| `runtime_chunks_fts` | 4674 | 1 | 0 | read-only |
| `runtime_chunks_fts_config` | 1 | 0 | 0 | unowned |
| `runtime_chunks_fts_content` | 4674 | 0 | 0 | unowned |
| `runtime_chunks_fts_data` | 1461 | 0 | 0 | unowned |
| `runtime_chunks_fts_docsize` | 4674 | 0 | 0 | unowned |
| `runtime_chunks_fts_idx` | 1593 | 0 | 0 | unowned |
| `runtime_documents` | 69 | 1 | 0 | read-only |
| `sources` | 17 | 3 | 1 | active |
| `sqlite_master` | None | 2 | 0 | read-only |
| `the` | None | 3 | 0 | read-only |
| `topics` | None | 3 | 1 | active |
| `was` | None | 0 | 1 | write-only |

## Detailed ownership

### `SET`

**Readers**
- None discovered

**Writers**
- `CatalogRepository.add_file_asset (core/knowledge_catalog/repository.py:76)`
- `CatalogRepository.upsert_source (core/knowledge_catalog/repository.py:12)`
- `CatalogRepository.upsert_topic (core/knowledge_catalog/repository.py:29)`
- `CatalogStore.upsert_document (knowledge_engine/storage/catalog_store.py:8)`
- `ChunkEmbeddingStore.upsert_embedding (knowledge_engine/embeddings/store.py:36)`
- `KnowledgeCatalog.upsert_document (knowledge_engine/catalog.py:82)`
- `KnowledgeCatalog.upsert_inspection (knowledge_engine/catalog.py:122)`
- `LibraryCatalogStore.upsert (knowledge_engine/library/store.py:10)`
- `ProvenanceRepository.upsert_sighting (knowledge_engine/acquisition/provenance/repository.py:44)`
- `upsert_catalog_entry (knowledge_engine/librarian/store.py:61)`

### `a`

**Readers**
- `SearchService._quality_score (knowledge_engine/search/service.py:513)`

**Writers**
- None discovered

### `accepted`

**Readers**
- `confidence_label (knowledge_engine/retrieval_intelligence/filtering.py:44)`

**Writers**
- None discovered

### `acquisition_admission_history`

**Readers**
- `ProvenanceRepository.get_history (knowledge_engine/acquisition/provenance/repository.py:261)`
- `ProvenanceRepository.list_history (knowledge_engine/acquisition/provenance/repository.py:221)`

**Writers**
- `ProvenanceRepository.append_history (knowledge_engine/acquisition/provenance/repository.py:108)`

### `acquisition_provenance`

**Readers**
- `ProvenanceRepository.find_by_checksum (knowledge_engine/acquisition/provenance/repository.py:188)`
- `ProvenanceRepository.get_by_source (knowledge_engine/acquisition/provenance/repository.py:150)`
- `ProvenanceRepository.source_exists (knowledge_engine/acquisition/provenance/repository.py:21)`
- `ProvenanceService.known_checksums (knowledge_engine/acquisition/provenance/service.py:126)`

**Writers**
- `ProvenanceRepository.upsert_sighting (knowledge_engine/acquisition/provenance/repository.py:44)`

### `canonical`

**Readers**
- `CanonicalEvidenceIdentifier.from_payload (core/reasoning/evidence/identifiers.py:44)`

**Writers**
- None discovered

### `catalog_documents`

**Readers**
- `DocumentChunkBuilder.build_ready_documents (knowledge_engine/chunking/builder.py:18)`
- `RuntimeKnowledgeMaterializer._candidates (core/knowledge_catalog/materialization/engine.py:130)`

**Writers**
- None discovered

### `catalog_enrichment`

**Readers**
- `MetadataSearcher.score_resources (knowledge_engine/hybrid_retrieval/metadata_search.py:14)`

**Writers**
- None discovered

### `chunk_concepts`

**Readers**
- `ChunkConceptStore.replace_concepts (knowledge_engine/concepts/store.py:32)`

**Writers**
- `ChunkConceptStore.replace_concepts (knowledge_engine/concepts/store.py:32)`

### `chunk_embeddings`

**Readers**
- `EmbeddingEngine.build_missing (knowledge_engine/embeddings/engine.py:31)`
- `KnowledgeIntegrityAuditor._audit_embeddings (knowledge_engine/integrity/auditor.py:269)`
- `VectorSearcher.search (knowledge_engine/retrieval/vector_search.py:14)`
- `remove_existing_embeddings (dev/stabilization/repair_serialized_pdf_text.py:365)`

**Writers**
- `ChunkEmbeddingStore.upsert_embedding (knowledge_engine/embeddings/store.py:36)`
- `EmbeddingEngine.build_missing (knowledge_engine/embeddings/engine.py:31)`
- `remove_existing_embeddings (dev/stabilization/repair_serialized_pdf_text.py:365)`

### `chunks`

**Readers**
- `DocumentPersistenceService.replace_chunks (knowledge_engine/assimilation/services/persistence.py:150)`

**Writers**
- `DocumentPersistenceService.replace_chunks (knowledge_engine/assimilation/services/persistence.py:150)`

### `collection_documents`

**Readers**
- None discovered

**Writers**
- None discovered

### `document_assimilation`

**Readers**
- None discovered

**Writers**
- None discovered

### `document_chunks`

**Readers**
- `ChunkEmbeddingBuilder._advance_ready_documents (knowledge_engine/embeddings/builder.py:88)`
- `ChunkEmbeddingBuilder.build_pending_embeddings (knowledge_engine/embeddings/builder.py:14)`
- `ConceptBuilder.build_ready_chunks (knowledge_engine/concepts/builder.py:12)`
- `DocumentChunkStore.replace_chunks (knowledge_engine/chunking/store.py:46)`
- `EmbeddingEngine.build_missing (knowledge_engine/embeddings/engine.py:31)`
- `HybridSearcher.search (knowledge_engine/hybrid_retrieval/search.py:23)`
- `KnowledgeIntegrityAuditor._audit_chunks (knowledge_engine/integrity/auditor.py:185)`
- `VectorSearcher.search (knowledge_engine/retrieval/vector_search.py:14)`
- `remove_existing_embeddings (dev/stabilization/repair_serialized_pdf_text.py:365)`
- `replace_document_chunks (dev/stabilization/repair_serialized_pdf_text.py:417)`

**Writers**
- `ChunkConceptStore.replace_concepts (knowledge_engine/concepts/store.py:32)`
- `ChunkEmbeddingBuilder._mark_skipped (knowledge_engine/embeddings/builder.py:76)`
- `ChunkEmbeddingStore.upsert_embedding (knowledge_engine/embeddings/store.py:36)`
- `DocumentChunkStore.replace_chunks (knowledge_engine/chunking/store.py:46)`
- `replace_document_chunks (dev/stabilization/repair_serialized_pdf_text.py:417)`

### `document_concepts`

**Readers**
- None discovered

**Writers**
- None discovered

### `document_keywords`

**Readers**
- None discovered

**Writers**
- None discovered

### `document_pages`

**Readers**
- None discovered

**Writers**
- None discovered

### `document_pages_fts`

**Readers**
- `PageStore.search (knowledge_engine/storage/page_store.py:49)`

**Writers**
- None discovered

### `document_pages_fts_config`

**Readers**
- None discovered

**Writers**
- None discovered

### `document_pages_fts_content`

**Readers**
- None discovered

**Writers**
- None discovered

### `document_pages_fts_data`

**Readers**
- None discovered

**Writers**
- None discovered

### `document_pages_fts_docsize`

**Readers**
- None discovered

**Writers**
- None discovered

### `document_pages_fts_idx`

**Readers**
- None discovered

**Writers**
- None discovered

### `document_relationships`

**Readers**
- None discovered

**Writers**
- None discovered

### `document_structure`

**Readers**
- `KnowledgeCatalog.replace_structure (knowledge_engine/catalog.py:228)`
- `KnowledgeCatalog.structure_summary (knowledge_engine/catalog.py:262)`

**Writers**
- `KnowledgeCatalog.replace_structure (knowledge_engine/catalog.py:228)`

### `document_subjects`

**Readers**
- `search_catalog (core/knowledge_catalog/search.py:8)`

**Writers**
- None discovered

### `document_text`

**Readers**
- `DocumentChunkBuilder.build_ready_documents (knowledge_engine/chunking/builder.py:18)`

**Writers**
- None discovered

### `document_topics`

**Readers**
- None discovered

**Writers**
- `CatalogRepository.link_document_topic (core/knowledge_catalog/repository.py:111)`

### `documents`

**Readers**
- `CatalogRepository.stats (core/knowledge_catalog/repository.py:126)`
- `CatalogStore.summary (knowledge_engine/storage/catalog_store.py:41)`
- `KnowledgeCatalog.duplicate_groups (knowledge_engine/catalog.py:207)`
- `KnowledgeCatalog.summary (knowledge_engine/catalog.py:157)`
- `LibraryCatalogBuilder.build (knowledge_engine/library/builder.py:22)`

**Writers**
- `CatalogRepository.create_document (core/knowledge_catalog/repository.py:45)`
- `CatalogStore.upsert_document (knowledge_engine/storage/catalog_store.py:8)`
- `KnowledgeCatalog.upsert_document (knowledge_engine/catalog.py:82)`

### `explicit`

**Readers**
- `structured_candidate (core/cognition/extraction.py:532)`

**Writers**
- None discovered

### `file_assets`

**Readers**
- `CatalogRepository.add_file_asset (core/knowledge_catalog/repository.py:76)`
- `CatalogRepository.stats (core/knowledge_catalog/repository.py:126)`

**Writers**
- `CatalogRepository.add_file_asset (core/knowledge_catalog/repository.py:76)`

### `inspections`

**Readers**
- `KnowledgeCatalog.summary (knowledge_engine/catalog.py:157)`
- `LibraryCatalogBuilder._metadata (knowledge_engine/library/builder.py:122)`

**Writers**
- `KnowledgeCatalog.upsert_inspection (knowledge_engine/catalog.py:122)`

### `its`

**Readers**
- `validate_claim_record (core/cognition/claim_validation.py:14)`

**Writers**
- None discovered

### `knowledge_assimilation_attempts`

**Readers**
- None discovered

**Writers**
- `AttemptJournalService.complete_attempt (knowledge_engine/assimilation/services/attempts.py:107)`

### `knowledge_assimilation_queue`

**Readers**
- None discovered

**Writers**
- `AssimilationStateService.mark_document_ready_for_embedding (knowledge_engine/assimilation/services/state.py:91)`

### `knowledge_index`

**Readers**
- `KnowledgeIndexSearch.search (knowledge_engine/index/search.py:5)`

**Writers**
- None discovered

### `knowledge_object_files`

**Readers**
- `HybridSearcher.search (knowledge_engine/hybrid_retrieval/search.py:23)`

**Writers**
- None discovered

### `knowledge_registry`

**Readers**
- `ChunkEmbeddingBuilder._advance_ready_documents (knowledge_engine/embeddings/builder.py:88)`
- `DocumentChunkBuilder.build_ready_documents (knowledge_engine/chunking/builder.py:18)`

**Writers**
- `AssimilationStateService.mark_document_ready_for_embedding (knowledge_engine/assimilation/services/state.py:91)`
- `ChunkEmbeddingBuilder._advance_ready_documents (knowledge_engine/embeddings/builder.py:88)`
- `DocumentChunkBuilder.build_ready_documents (knowledge_engine/chunking/builder.py:18)`

### `librarian_catalog`

**Readers**
- `CatalogEnrichmentBuilder.build (knowledge_engine/catalog_enrichment/builder.py:17)`
- `HybridSearcher.search (knowledge_engine/hybrid_retrieval/search.py:23)`
- `MetadataSearcher.score_resources (knowledge_engine/hybrid_retrieval/metadata_search.py:14)`

**Writers**
- `upsert_catalog_entry (knowledge_engine/librarian/store.py:61)`

### `library_catalog`

**Readers**
- `LibraryCatalogStore.summary (knowledge_engine/library/store.py:137)`

**Writers**
- `LibraryCatalogStore.upsert (knowledge_engine/library/store.py:10)`

### `ready_for_embedding`

**Readers**
- `ChunkEmbeddingBuilder._advance_ready_documents (knowledge_engine/embeddings/builder.py:88)`

**Writers**
- None discovered

### `repository`

**Readers**
- `CognitiveWorkspaceCatalog.rebuild (core/cognition/workspace/catalog.py:149)`

**Writers**
- None discovered

### `resource_inspections`

**Readers**
- None discovered

**Writers**
- None discovered

### `runtime_chunks`

**Readers**
- `search_runtime_knowledge (core/knowledge_catalog/materialization/search.py:17)`

**Writers**
- None discovered

### `runtime_chunks_fts`

**Readers**
- `search_runtime_knowledge (core/knowledge_catalog/materialization/search.py:17)`

**Writers**
- None discovered

### `runtime_chunks_fts_config`

**Readers**
- None discovered

**Writers**
- None discovered

### `runtime_chunks_fts_content`

**Readers**
- None discovered

**Writers**
- None discovered

### `runtime_chunks_fts_data`

**Readers**
- None discovered

**Writers**
- None discovered

### `runtime_chunks_fts_docsize`

**Readers**
- None discovered

**Writers**
- None discovered

### `runtime_chunks_fts_idx`

**Readers**
- None discovered

**Writers**
- None discovered

### `runtime_documents`

**Readers**
- `search_runtime_knowledge (core/knowledge_catalog/materialization/search.py:17)`

**Writers**
- None discovered

### `sources`

**Readers**
- `CatalogRepository.create_document (core/knowledge_catalog/repository.py:45)`
- `CatalogRepository.stats (core/knowledge_catalog/repository.py:126)`
- `CatalogRepository.upsert_source (core/knowledge_catalog/repository.py:12)`

**Writers**
- `CatalogRepository.upsert_source (core/knowledge_catalog/repository.py:12)`

### `sqlite_master`

**Readers**
- `EndToEndRetrievalTracer._database_terms (core/retrieval/certification/tracer.py:205)`
- `search_runtime_knowledge (core/knowledge_catalog/materialization/search.py:17)`

**Writers**
- None discovered

### `the`

**Readers**
- `CertificationRuntime.certify (core/certification/runtime/bootstrap.py:76)`
- `EndToEndRetrievalTracer.certify (core/retrieval/certification/tracer.py:62)`
- `ExecutiveDirector.__init__ (core/executive/director.py:23)`

**Writers**
- None discovered

### `topics`

**Readers**
- `CatalogRepository.link_document_topic (core/knowledge_catalog/repository.py:111)`
- `CatalogRepository.stats (core/knowledge_catalog/repository.py:126)`
- `CatalogRepository.upsert_topic (core/knowledge_catalog/repository.py:29)`

**Writers**
- `CatalogRepository.upsert_topic (core/knowledge_catalog/repository.py:29)`

### `was`

**Readers**
- None discovered

**Writers**
- `AssimilationRunner._complete_success (knowledge_engine/assimilation/runner.py:436)`
