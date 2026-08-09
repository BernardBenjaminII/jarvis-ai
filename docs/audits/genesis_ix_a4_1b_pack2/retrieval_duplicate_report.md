# Genesis IX-A4.1B — Production Duplicate Analysis

## Chunking

**Signature:** `('__init__', '', '')`

- `ChunkingService.__init__ (knowledge_engine/services/chunking.py:17, DORMANT)`
- `ChunkingStage.__init__ (knowledge_engine/workflows/stages/chunking.py:12, DORMANT)`

**Recommendation:** No live owner was proven. Confirm consumers before selecting or implementing a canonical service.

## Chunking

**Signature:** `('__init__', 'db', '')`

- `ChunkConceptStore.__init__ (knowledge_engine/concepts/store.py:29, DORMANT)`
- `DocumentChunkBuilder.__init__ (knowledge_engine/chunking/builder.py:13, DORMANT)`
- `DocumentChunkStore.__init__ (knowledge_engine/chunking/store.py:43, DORMANT)`

**Recommendation:** No live owner was proven. Confirm consumers before selecting or implementing a canonical service.

## Chunking

**Signature:** `('chunk', 'text,file_path', 'ChunkingResult')`

- `ChunkingService.chunk (knowledge_engine/services/chunking.py:20, DORMANT)`
- `DocumentChunker.chunk (knowledge_engine/chunking/chunker.py:24, DORMANT)`

**Recommendation:** No live owner was proven. Confirm consumers before selecting or implementing a canonical service.

## Chunking

**Signature:** `('sha256_file', 'path,chunk_size', 'str')`

- `sha256_file (core/governance/audit/filesystem.py:107, DORMANT)`
- `sha256_file (knowledge_engine/discovery/filesystem.py:150, DORMANT)`
- `sha256_file (knowledge_engine/metadata/fingerprints.py:5, DORMANT)`

**Recommendation:** No live owner was proven. Confirm consumers before selecting or implementing a canonical service.

## Embedding

**Signature:** `('__init__', '', '')`

- `EmbeddingService.__init__ (knowledge_engine/services/embeddings.py:19, DORMANT)`
- `EmbeddingStage.__init__ (knowledge_engine/workflows/stages/embeddings.py:12, DORMANT)`

**Recommendation:** No live owner was proven. Confirm consumers before selecting or implementing a canonical service.

## Embedding

**Signature:** `('embed', 'text', 'list[float]')`

- `EmbeddingService.embed (knowledge_engine/services/embeddings.py:22, DORMANT)`
- `LocalEmbeddingProvider.embed (knowledge_engine/embeddings/local_provider.py:27, DORMANT)`

**Recommendation:** No live owner was proven. Confirm consumers before selecting or implementing a canonical service.

## Evidence

**Signature:** `('__post_init__', '', 'None')`

- `CanonicalEvidenceIdentifier.__post_init__ (core/reasoning/evidence/identifiers.py:25, DORMANT)`
- `EvidenceAssessment.__post_init__ (core/evidence/contracts.py:294, DORMANT)`
- `EvidenceAssessment.__post_init__ (core/reasoning/evidence/contracts.py:880, DORMANT)`
- `EvidenceChain.__post_init__ (core/cognition/evidence_chain.py:77, DORMANT)`
- `EvidenceContent.__post_init__ (core/reasoning/evidence/contracts.py:88, DORMANT)`
- `EvidenceGap.__post_init__ (core/evidence/contracts.py:381, DORMANT)`
- `EvidenceItem.__post_init__ (core/reasoning/models.py:78, DORMANT)`
- `EvidenceLink.__post_init__ (core/cognition/evidence_correlation/models.py:110, DORMANT)`
- `EvidenceOrigin.__post_init__ (core/reasoning/evidence/contracts.py:135, DORMANT)`
- `EvidenceProvenance.__post_init__ (core/reasoning/evidence/contracts.py:261, DORMANT)`
- `EvidenceProvenanceStep.__post_init__ (core/reasoning/evidence/contracts.py:203, DORMANT)`
- `EvidenceRecord.__post_init__ (core/cognition/evidence.py:97, DORMANT)`
- `EvidenceRecord.__post_init__ (core/evidence/contracts.py:316, DORMANT)`
- `EvidenceRecord.__post_init__ (core/reasoning/evidence/contracts.py:706, DORMANT)`
- `EvidenceReference.__post_init__ (core/cognition/workspace/models.py:55, DORMANT)`
- `EvidenceReference.__post_init__ (core/executive/planning/models.py:101, DORMANT)`
- `EvidenceRelationship.__post_init__ (core/evidence/contracts.py:348, DORMANT)`
- `EvidenceRelationship.__post_init__ (core/reasoning/evidence/contracts.py:599, DORMANT)`
- `EvidenceSeed.__post_init__ (core/cognition/integration/contracts.py:48, DORMANT)`
- `EvidenceSet.__post_init__ (core/evidence/contracts.py:408, DORMANT)`
- `EvidenceStatusEvent.__post_init__ (core/reasoning/evidence/contracts.py:1038, DORMANT)`
- `EvidenceTemporalScope.__post_init__ (core/reasoning/evidence/contracts.py:297, DORMANT)`
- `EvidenceUncertainty.__post_init__ (core/reasoning/evidence/contracts.py:380, DORMANT)`
- `ProvenanceRecord.__post_init__ (core/cognition/provenance.py:84, DORMANT)`
- `ProvenanceRecord.__post_init__ (knowledge_engine/acquisition/provenance/models.py:62, DORMANT)`
- `ProvenanceReference.__post_init__ (core/cognition/common/object_model.py:48, DORMANT)`
- `VerificationEvidence.__post_init__ (core/engineering/contracts.py:89, DORMANT)`

**Recommendation:** No live owner was proven. Confirm consumers before selecting or implementing a canonical service.

## Evidence

**Signature:** `('identity_payload', '', 'dict[str, object]')`

- `EvidenceChain.identity_payload (core/cognition/evidence_chain.py:151, DORMANT)`
- `EvidenceRecord.identity_payload (core/cognition/evidence.py:197, DORMANT)`
- `ProvenanceRecord.identity_payload (core/cognition/provenance.py:169, DORMANT)`

**Recommendation:** No live owner was proven. Confirm consumers before selecting or implementing a canonical service.

## Evidence

**Signature:** `('to_dict', '', 'dict[str, Any]')`

- `ClaimEvidence.to_dict (core/governance/constitution/ratification/models.py:25, DORMANT)`
- `EvidenceAssessment.to_dict (core/knowledge_awareness/contracts.py:35, DORMANT)`
- `EvidenceItem.to_dict (core/reasoning/models.py:89, DORMANT)`
- `ProvenanceRecord.to_dict (knowledge_engine/acquisition/provenance/models.py:108, DORMANT)`

**Recommendation:** No live owner was proven. Confirm consumers before selecting or implementing a canonical service.

## Other

**Signature:** `('__init__', 'db', '')`

- `CatalogEnrichmentBuilder.__init__ (knowledge_engine/catalog_enrichment/builder.py:14, DORMANT)`
- `CatalogStore.__init__ (knowledge_engine/storage/catalog_store.py:5, DORMANT)`
- `LibraryCatalogStore.__init__ (knowledge_engine/library/store.py:6, DORMANT)`

**Recommendation:** No live owner was proven. Confirm consumers before selecting or implementing a canonical service.

## Other

**Signature:** `('summary', '', 'dict')`

- `CatalogStore.summary (knowledge_engine/storage/catalog_store.py:41, DORMANT)`
- `KnowledgeCatalog.summary (knowledge_engine/catalog.py:157, DORMANT)`

**Recommendation:** No live owner was proven. Confirm consumers before selecting or implementing a canonical service.

## Other

**Signature:** `('upsert_document', 'doc', 'None')`

- `CatalogStore.upsert_document (knowledge_engine/storage/catalog_store.py:8, DORMANT)`
- `KnowledgeCatalog.upsert_document (knowledge_engine/catalog.py:82, DORMANT)`

**Recommendation:** No live owner was proven. Confirm consumers before selecting or implementing a canonical service.

## Ranking

**Signature:** `('__post_init__', '', 'None')`

- `HypothesisRanking.__post_init__ (core/cognition/reasoner/models.py:75, DORMANT)`
- `RankingWeights.__post_init__ (knowledge_engine/ranking/models.py:21, DORMANT)`

**Recommendation:** No live owner was proven. Confirm consumers before selecting or implementing a canonical service.

## Ranking

**Signature:** `('rank', 'query,results,limit', 'list[dict[str, Any]]')`

- `KnowledgeRanker.rank (knowledge_engine/ranking/ranker.py:148, DORMANT)`
- `RankingService.rank (knowledge_engine/services/ranking.py:21, DORMANT)`

**Recommendation:** No live owner was proven. Confirm consumers before selecting or implementing a canonical service.

## Retrieval

**Signature:** `('__init__', 'db', '')`

- `KnowledgeIndexSearch.__init__ (knowledge_engine/index/search.py:2, DORMANT)`
- `MetadataSearcher.__init__ (knowledge_engine/hybrid_retrieval/metadata_search.py:11, DORMANT)`

**Recommendation:** No live owner was proven. Confirm consumers before selecting or implementing a canonical service.

## Retrieval

**Signature:** `('cmd_search', 'args', 'None')`

- `cmd_search (core/knowledge_catalog/cli.py:68, DORMANT)`
- `cmd_search (knowledge_engine/hybrid_search_cli.py:23, DORMANT)`

**Recommendation:** No live owner was proven. Confirm consumers before selecting or implementing a canonical service.

## Retrieval

**Signature:** `('search', 'query,limit', 'list[dict]')`

- `KnowledgeIndexSearch.search (knowledge_engine/index/search.py:5, DORMANT)`
- `PageStore.search (knowledge_engine/storage/page_store.py:49, DORMANT)`

**Recommendation:** No live owner was proven. Confirm consumers before selecting or implementing a canonical service.
