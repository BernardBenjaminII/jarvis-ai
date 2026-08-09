# Genesis IX-A4.1B — Retrieval Component Matrix

| Component | Module | Runtime status | Decision | Rationale |
|---|---|---|---|---|
| `confidence_band` | `core.cognition.confidence` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `EvidenceLink.weighted_score` | `core.cognition.evidence_correlation.models` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `ExecutiveDecisionEngine.rank` | `core.cognition.executive_decision.engine` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `component_scores` | `core.cognition.executive_decision.scoring` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `weighted_score` | `core.cognition.executive_decision.scoring` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `HypothesisRanking.__post_init__` | `core.cognition.reasoner.models` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `HypothesisRanking.to_canonical_dict` | `core.cognition.reasoner.models` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `_require_score` | `core.evidence.contracts` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `CandidateScore.to_dict` | `core.executive.capabilities.models` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `CapabilitySelector._score` | `core.executive.capabilities.selector` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `authority_rank` | `core.governance.constitution.analysis.authority` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `resolve_authority` | `core.governance.constitution.analysis.authority` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `ConstitutionalArticleIntelligenceEngine.assess.ranked` | `core.governance.constitution.coverage.article_intelligence` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `ConstitutionalArticleQueryService.__init__` | `core.governance.constitution.coverage.executive_queries` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `score_document` | `core.knowledge_catalog.assimilation.engine` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `register_file` | `core.knowledge_catalog.service` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `classify_disposition` | `core.reasoning.confidence` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `hypothesis_confidence` | `core.reasoning.confidence` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `_ranking` | `core.reasoning.knowledge` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `ReasoningEngine._select_assessment` | `core.reasoning.service` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `_score_keywords` | `core.src.cognition.intent_classifier` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `AssimilationStateService.mark_document_ready_for_embedding` | `knowledge_engine.assimilation.services.state` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `build_knowledge_registry` | `knowledge_engine.capabilities.registry` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `EmbeddingStage.run` | `knowledge_engine.director.stages.embeddings` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `ChunkEmbeddingBuilder.__init__` | `knowledge_engine.embeddings.builder` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `ChunkEmbeddingBuilder._advance_ready_documents` | `knowledge_engine.embeddings.builder` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `ChunkEmbeddingBuilder._mark_skipped` | `knowledge_engine.embeddings.builder` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `ChunkEmbeddingBuilder.build_pending_embeddings` | `knowledge_engine.embeddings.builder` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `EmbeddingEngine.__init__` | `knowledge_engine.embeddings.engine` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `EmbeddingEngine.build_missing` | `knowledge_engine.embeddings.engine` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `EmbeddingEngine.ensure_schema` | `knowledge_engine.embeddings.engine` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `LocalEmbeddingProvider.__post_init__` | `knowledge_engine.embeddings.local_provider` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `LocalEmbeddingProvider.embed` | `knowledge_engine.embeddings.local_provider` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `LocalEmbeddingProvider.embed_batch` | `knowledge_engine.embeddings.local_provider` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `LocalEmbeddingProvider.embed_text` | `knowledge_engine.embeddings.local_provider` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `ChunkEmbeddingStore.__init__` | `knowledge_engine.embeddings.store` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `ChunkEmbeddingStore.upsert_embedding` | `knowledge_engine.embeddings.store` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `init_embeddings` | `knowledge_engine.embeddings.store` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `build_hnsw_index` | `knowledge_engine.hybrid_retrieval.faiss_store` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `MetadataSearcher.score_resources` | `knowledge_engine.hybrid_retrieval.metadata_search` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `HybridSearcher.search` | `knowledge_engine.hybrid_retrieval.search` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `KnowledgeIntegrityAuditor._audit_embeddings` | `knowledge_engine.integrity.auditor` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `catalog_quality_score` | `knowledge_engine.librarian.quality` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `upsert_catalog_entry` | `knowledge_engine.librarian.store` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `duplicate_similarity` | `knowledge_engine.ranking.duplicates` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `RankingBreakdown.as_dict` | `knowledge_engine.ranking.models` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `RankingCandidate.identity` | `knowledge_engine.ranking.models` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `RankingWeights.__post_init__` | `knowledge_engine.ranking.models` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `normalize_candidate` | `knowledge_engine.ranking.normalization` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `normalize_candidates` | `knowledge_engine.ranking.normalization` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `normalize_quality_score` | `knowledge_engine.ranking.normalization` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `normalize_semantic_score` | `knowledge_engine.ranking.normalization` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `KnowledgeRanker.__init__` | `knowledge_engine.ranking.ranker` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `KnowledgeRanker.rank` | `knowledge_engine.ranking.ranker` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `KnowledgeRanker.rank_candidates` | `knowledge_engine.ranking.ranker` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `rank_results` | `knowledge_engine.ranking.ranker` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `authority_score` | `knowledge_engine.ranking.scorer` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `calculate_breakdown` | `knowledge_engine.ranking.scorer` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `completeness_score` | `knowledge_engine.ranking.scorer` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `diversity_score` | `knowledge_engine.ranking.scorer` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `freshness_score` | `knowledge_engine.ranking.scorer` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `lexical_score` | `knowledge_engine.ranking.scorer` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `jaccard_similarity` | `knowledge_engine.ranking.text` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `VectorSearcher.__init__` | `knowledge_engine.retrieval.vector_search` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `VectorSearcher.cosine` | `knowledge_engine.retrieval.vector_search` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `VectorSearcher.search` | `knowledge_engine.retrieval.vector_search` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `RetrievalDirector.__init__` | `knowledge_engine.retrieval_intelligence.director` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `CandidateFilter.__init__` | `knowledge_engine.retrieval_intelligence.filtering` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `confidence_label` | `knowledge_engine.retrieval_intelligence.filtering` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `RetrievalCandidate.as_mapping` | `knowledge_engine.retrieval_intelligence.models` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `normalize_candidate` | `knowledge_engine.retrieval_intelligence.normalization` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `normalize_similarity` | `knowledge_engine.retrieval_intelligence.normalization` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `VectorRetrievalProvider.__init__` | `knowledge_engine.retrieval_intelligence.providers` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `VectorRetrievalProvider.retrieve` | `knowledge_engine.retrieval_intelligence.providers` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `SearchService._build_search_result` | `knowledge_engine.search.service` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `SearchService._candidate_limit` | `knowledge_engine.search.service` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `SearchService._prepare_candidate` | `knowledge_engine.search.service` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `SearchService._quality_score` | `knowledge_engine.search.service` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `SearchService.execute` | `knowledge_engine.search.service` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `EmbeddingService.__init__` | `knowledge_engine.services.embeddings` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `EmbeddingService.embed` | `knowledge_engine.services.embeddings` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `EmbeddingService.embed_batch` | `knowledge_engine.services.embeddings` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `RankingService.__init__` | `knowledge_engine.services.ranking` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `RankingService.rank` | `knowledge_engine.services.ranking` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `rank_search_results` | `knowledge_engine.services.ranking` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `EmbeddingStage.__init__` | `knowledge_engine.workflows.stages.embeddings` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `EmbeddingStage.run` | `knowledge_engine.workflows.stages.embeddings` | DORMANT | **AUDIT** | Capability exists statically but is not proven live. Inspect callers, data coverage, and compatibility before activation or removal. |
| `CertificationRuntime.certify` | `core.certification.runtime.bootstrap` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `validate_claim_record` | `core.cognition.claim_validation` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceReference.__post_init__` | `core.cognition.common.object_model` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceReference.to_primitive` | `core.cognition.common.object_model` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `confidence_for_direct_source` | `core.cognition.confidence` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceRecord.__post_init__` | `core.cognition.evidence` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceRecord.from_observation` | `core.cognition.evidence` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceRecord.identity_payload` | `core.cognition.evidence` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `make_evidence_id` | `core.cognition.evidence` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceChain.__post_init__` | `core.cognition.evidence_chain` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceChain.identity_payload` | `core.cognition.evidence_chain` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceChain.is_contested` | `core.cognition.evidence_chain` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceChain.neutral_evidence` | `core.cognition.evidence_chain` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceChain.opposing_evidence` | `core.cognition.evidence_chain` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceChain.supporting_evidence` | `core.cognition.evidence_chain` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `_normalize_evidence_records` | `core.cognition.evidence_chain` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `make_evidence_chain_id` | `core.cognition.evidence_chain` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceCorrelator.assess` | `core.cognition.evidence_correlation.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ExecutiveEvidenceCorrelator.assess` | `core.cognition.evidence_correlation.correlator` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceLink.__post_init__` | `core.cognition.evidence_correlation.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceLink.to_canonical_dict` | `core.cognition.evidence_correlation.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ExecutiveEvidenceService.__init__` | `core.cognition.evidence_correlation.service` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ExecutiveEvidenceService.assess` | `core.cognition.evidence_correlation.service` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ExecutiveEvidenceService.repository` | `core.cognition.evidence_correlation.service` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `validate_evidence_chain` | `core.cognition.evidence_validation` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `validate_evidence_object` | `core.cognition.evidence_validation` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `validate_evidence_record` | `core.cognition.evidence_validation` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `validate_provenance_record` | `core.cognition.evidence_validation` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `structured_candidate` | `core.cognition.extraction` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceSeed.__post_init__` | `core.cognition.integration.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `Observation.create` | `core.cognition.observation.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ObservationProvenance.__post_init__` | `core.cognition.observation.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ObservationProvenance.create` | `core.cognition.observation.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ObservationProvenance.to_canonical_dict` | `core.cognition.observation.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ExecutiveObservationService.record` | `core.cognition.observation.service` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceRecord.__post_init__` | `core.cognition.provenance` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceRecord.identity_payload` | `core.cognition.provenance` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `make_provenance_id` | `core.cognition.provenance` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `validate_source_reference` | `core.cognition.validation` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CognitiveWorkspaceCatalog.__init__` | `core.cognition.workspace.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CognitiveWorkspaceCatalog._matches` | `core.cognition.workspace.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CognitiveWorkspaceCatalog._sort_key` | `core.cognition.workspace.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CognitiveWorkspaceCatalog.blocked` | `core.cognition.workspace.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CognitiveWorkspaceCatalog.low_confidence` | `core.cognition.workspace.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CognitiveWorkspaceCatalog.rebuild` | `core.cognition.workspace.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CognitiveWorkspaceCatalog.resumable` | `core.cognition.workspace.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CognitiveWorkspaceCatalog.search` | `core.cognition.workspace.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CognitiveWorkspaceCatalog.search_workspaces` | `core.cognition.workspace.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `WorkspaceCatalogEntry.from_workspace` | `core.cognition.workspace.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceReference.__post_init__` | `core.cognition.workspace.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `Hypothesis.attach_evidence` | `core.cognition.workspace.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CognitiveWorkspaceService.attach_evidence` | `core.cognition.workspace.service` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `VerificationEvidence.__post_init__` | `core.engineering.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceAssessment.__post_init__` | `core.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceGap.__post_init__` | `core.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceRecord.__post_init__` | `core.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceRelationship.__post_init__` | `core.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceSet.__post_init__` | `core.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceError.__init__` | `core.evidence.errors` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceError.as_dict` | `core.evidence.errors` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ExecutiveEventBus.publish_many` | `core.executive.events.bus` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeHandler.__init__` | `core.executive.handlers` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceReference.__post_init__` | `core.executive.planning.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ExecutiveTimelineEngine.append_many` | `core.executive.timeline.engine` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `classify_evidence` | `core.governance.audit.filesystem` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `sha256_file` | `core.governance.audit.filesystem` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `RepositoryInventoryVerifier._verify_evidence_policy` | `core.governance.audit.verification` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ClaimEvidence.to_dict` | `core.governance.constitution.ratification.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `build_knowledge_readiness` | `core.integration.knowledge` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceAssessment.to_dict` | `core.knowledge_awareness.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ResearchRecommendation.to_dict` | `core.knowledge_awareness.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `cmd_search` | `core.knowledge_catalog.cli` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `_schema_script` | `core.knowledge_catalog.database` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `RuntimeKnowledgeMaterializer.__init__` | `core.knowledge_catalog.materialization.engine` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `RuntimeKnowledgeMaterializer._candidates` | `core.knowledge_catalog.materialization.engine` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `chunk_text` | `core.knowledge_catalog.materialization.engine` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CatalogRepository.__init__` | `core.knowledge_catalog.repository` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CatalogRepository.add_file_asset` | `core.knowledge_catalog.repository` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CatalogRepository.create_document` | `core.knowledge_catalog.repository` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CatalogRepository.link_document_topic` | `core.knowledge_catalog.repository` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CatalogRepository.stats` | `core.knowledge_catalog.repository` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CatalogRepository.upsert_source` | `core.knowledge_catalog.repository` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CatalogRepository.upsert_topic` | `core.knowledge_catalog.repository` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `seed_catalog` | `core.knowledge_catalog.seed` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `initialize_catalog` | `core.knowledge_catalog.service` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `scan_observation_exports` | `core.observation.export_audit` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceAssessment.__post_init__` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceAssessment._identity_payload` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceAssessment.create` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceContent.__post_init__` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceContent.content_id` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceOrigin.__post_init__` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceProvenance.__post_init__` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceProvenanceStep.__post_init__` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceRecord.__post_init__` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceRecord._identity_payload` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceRecord.create` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceRelationship.__post_init__` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceRelationship._identity_payload` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceRelationship.create` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceStatusEvent.__post_init__` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceStatusEvent._identity_payload` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceStatusEvent.create` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceTemporalScope.__post_init__` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceUncertainty.__post_init__` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceUncertainty._validate_kind_contract` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `_placeholder_assessment_id` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `_placeholder_evidence_id` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `_placeholder_relationship_id` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `_placeholder_status_event_id` | `core.reasoning.evidence.contracts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CanonicalEvidenceIdentifier.__post_init__` | `core.reasoning.evidence.identifiers` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CanonicalEvidenceIdentifier.__str__` | `core.reasoning.evidence.identifiers` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CanonicalEvidenceIdentifier.canonical_value` | `core.reasoning.evidence.identifiers` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CanonicalEvidenceIdentifier.from_payload` | `core.reasoning.evidence.identifiers` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CanonicalEvidenceIdentifier.parse` | `core.reasoning.evidence.identifiers` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `DeterministicHypothesisGenerator.generate` | `core.reasoning.generation` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `assess_hypothesis` | `core.reasoning.inference` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeEvidenceAdapter.adapt` | `core.reasoning.knowledge` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `_evidence_id` | `core.reasoning.knowledge` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceItem.__post_init__` | `core.reasoning.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceItem.to_dict` | `core.reasoning.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EvidenceItem.weight` | `core.reasoning.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeReasoningPipeline.__init__` | `core.reasoning.pipeline` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `_provenance` | `core.representation.articulation` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EndToEndRetrievalTracer.__init__` | `core.retrieval.certification.tracer` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EndToEndRetrievalTracer._callable_identity` | `core.retrieval.certification.tracer` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EndToEndRetrievalTracer._capture_synthesis` | `core.retrieval.certification.tracer` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EndToEndRetrievalTracer._capture_synthesis.deterministic_synthesis` | `core.retrieval.certification.tracer` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EndToEndRetrievalTracer._database_terms` | `core.retrieval.certification.tracer` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EndToEndRetrievalTracer._discover_known_query` | `core.retrieval.certification.tracer` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EndToEndRetrievalTracer._gap_checks` | `core.retrieval.certification.tracer` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EndToEndRetrievalTracer._identity` | `core.retrieval.certification.tracer` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EndToEndRetrievalTracer._json_safe` | `core.retrieval.certification.tracer` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EndToEndRetrievalTracer._known_checks` | `core.retrieval.certification.tracer` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EndToEndRetrievalTracer._run_request` | `core.retrieval.certification.tracer` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EndToEndRetrievalTracer._sha256` | `core.retrieval.certification.tracer` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EndToEndRetrievalTracer._source_contract_checks` | `core.retrieval.certification.tracer` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `EndToEndRetrievalTracer.certify` | `core.retrieval.certification.tracer` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CertificationFailureAnalyzer._result` | `core.retrieval.failure_analysis.analyzer` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeGapPropagationTracer.__init__` | `core.retrieval.gap_trace.tracer` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `build_inventory` | `core.retrieval.inventory` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `_catalog_database_path` | `core.src.routes.api` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `AcquisitionIntakeService.__init__` | `knowledge_engine.acquisition.intake.service` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceRecord.__post_init__` | `knowledge_engine.acquisition.provenance.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceRecord.to_dict` | `knowledge_engine.acquisition.provenance.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceWriteResult.candidate_id` | `knowledge_engine.acquisition.provenance.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceWriteResult.sighting_count` | `knowledge_engine.acquisition.provenance.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceRepository._map_provenance` | `knowledge_engine.acquisition.provenance.repository` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceRepository.append_history` | `knowledge_engine.acquisition.provenance.repository` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceRepository.find_by_checksum` | `knowledge_engine.acquisition.provenance.repository` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceRepository.get_by_source` | `knowledge_engine.acquisition.provenance.repository` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceRepository.get_history` | `knowledge_engine.acquisition.provenance.repository` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceRepository.list_history` | `knowledge_engine.acquisition.provenance.repository` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceRepository.source_exists` | `knowledge_engine.acquisition.provenance.repository` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceRepository.upsert_sighting` | `knowledge_engine.acquisition.provenance.repository` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ensure_provenance_schema` | `knowledge_engine.acquisition.provenance.schema` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceService.__init__` | `knowledge_engine.acquisition.provenance.service` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceService.known_checksums` | `knowledge_engine.acquisition.provenance.service` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ProvenanceService.record_decision` | `knowledge_engine.acquisition.provenance.service` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `AssimilationHandler.verify` | `knowledge_engine.assimilation.handlers.base` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `AssimilationRunner._complete_success` | `knowledge_engine.assimilation.runner` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `AttemptJournalService.complete_attempt` | `knowledge_engine.assimilation.services.attempts` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ExtractionResult.chunk_count` | `knowledge_engine.assimilation.services.extraction` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ExtractionService.__init__` | `knowledge_engine.assimilation.services.extraction` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ExtractionService.extract` | `knowledge_engine.assimilation.services.extraction` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `DocumentPersistenceResult.persisted` | `knowledge_engine.assimilation.services.persistence` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `DocumentPersistenceService.persist_document` | `knowledge_engine.assimilation.services.persistence` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `DocumentPersistenceService.replace_chunks` | `knowledge_engine.assimilation.services.persistence` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `chunk_text` | `knowledge_engine.assimilation.single_document` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeCatalog.__init__` | `knowledge_engine.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeCatalog.connect` | `knowledge_engine.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeCatalog.duplicate_groups` | `knowledge_engine.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeCatalog.initialize` | `knowledge_engine.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeCatalog.replace_structure` | `knowledge_engine.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeCatalog.structure_summary` | `knowledge_engine.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeCatalog.summary` | `knowledge_engine.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeCatalog.upsert_document` | `knowledge_engine.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeCatalog.upsert_inspection` | `knowledge_engine.catalog` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CatalogEnrichmentBuilder.__init__` | `knowledge_engine.catalog_enrichment.builder` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CatalogEnrichmentBuilder.build` | `knowledge_engine.catalog_enrichment.builder` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `init_catalog_enrichment` | `knowledge_engine.catalog_enrichment.store` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `DocumentChunkBuilder.__init__` | `knowledge_engine.chunking.builder` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `DocumentChunkBuilder._make_chunk` | `knowledge_engine.chunking.builder` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `DocumentChunkBuilder.build_ready_documents` | `knowledge_engine.chunking.builder` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `DocumentChunker.__init__` | `knowledge_engine.chunking.chunker` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `DocumentChunker._chunk_code` | `knowledge_engine.chunking.chunker` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `DocumentChunker._chunk_markdown` | `knowledge_engine.chunking.chunker` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `DocumentChunker._looks_like_code` | `knowledge_engine.chunking.chunker` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `DocumentChunker._looks_like_markdown` | `knowledge_engine.chunking.chunker` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `DocumentChunker._normalize` | `knowledge_engine.chunking.chunker` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `DocumentChunker.chunk` | `knowledge_engine.chunking.chunker` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `DocumentChunkStore.__init__` | `knowledge_engine.chunking.store` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `DocumentChunkStore.replace_chunks` | `knowledge_engine.chunking.store` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `init_chunks` | `knowledge_engine.chunking.store` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `chunk_text` | `knowledge_engine.chunking.strategies` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ConceptBuilder.build_ready_chunks` | `knowledge_engine.concepts.builder` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `_evidence_window` | `knowledge_engine.concepts.extractor` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ChunkConceptStore.__init__` | `knowledge_engine.concepts.store` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ChunkConceptStore.replace_concepts` | `knowledge_engine.concepts.store` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `IntentRouter._strip_search_prefix` | `knowledge_engine.director.router.intent_router` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ChunkStage.run` | `knowledge_engine.director.stages.chunking` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `SearchWorkflow._result_limit` | `knowledge_engine.director.workflows.search` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `SearchWorkflow.run` | `knowledge_engine.director.workflows.search` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `sha256_file` | `knowledge_engine.discovery.filesystem` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `FaissIndexStore.save` | `knowledge_engine.hybrid_retrieval.faiss_store` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `MetadataSearcher.__init__` | `knowledge_engine.hybrid_retrieval.metadata_search` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `HybridSearcher.__init__` | `knowledge_engine.hybrid_retrieval.search` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `cmd_search` | `knowledge_engine.hybrid_search_cli` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeIndexSearch.__init__` | `knowledge_engine.index.search` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeIndexSearch.search` | `knowledge_engine.index.search` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeIntegrityAuditor._audit_chunks` | `knowledge_engine.integrity.auditor` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeIntegrityAuditor.run` | `knowledge_engine.integrity.auditor` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `LibraryCatalogBuilder.__init__` | `knowledge_engine.library.builder` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `LibraryCatalogBuilder._metadata` | `knowledge_engine.library.builder` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `LibraryCatalogBuilder.build` | `knowledge_engine.library.builder` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `LibraryCatalogStore.__init__` | `knowledge_engine.library.store` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `LibraryCatalogStore.summary` | `knowledge_engine.library.store` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `LibraryCatalogStore.upsert` | `knowledge_engine.library.store` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `sha256_file` | `knowledge_engine.metadata.fingerprints` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `run_inventory` | `knowledge_engine.pipeline` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CatalogStage.__init__` | `knowledge_engine.processing.catalog_stage` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CatalogStage.run` | `knowledge_engine.processing.catalog_stage` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeQualityValidator.validate_chunk` | `knowledge_engine.quality.validator` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `QualityValidator.duplicate` | `knowledge_engine.quality.validators` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `QueryAnalyzer._build_retrieval_query` | `knowledge_engine.query_understanding.analyzer` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `_normalize_chunk_index` | `knowledge_engine.ranking.normalization` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `RetrievalDirector._provider_limit` | `knowledge_engine.retrieval_intelligence.director` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `RetrievalDirector.search` | `knowledge_engine.retrieval_intelligence.director` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CandidateFilter.apply` | `knowledge_engine.retrieval_intelligence.filtering` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CandidateMerger.merge` | `knowledge_engine.retrieval_intelligence.merger` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `RetrievalCandidate.identity` | `knowledge_engine.retrieval_intelligence.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `RetrievalDiagnostics.as_dict` | `knowledge_engine.retrieval_intelligence.models` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `RetrievalProvider.retrieve` | `knowledge_engine.retrieval_intelligence.providers` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `StaticRetrievalProvider.__init__` | `knowledge_engine.retrieval_intelligence.providers` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `StaticRetrievalProvider.retrieve` | `knowledge_engine.retrieval_intelligence.providers` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `SearchService.__init__` | `knowledge_engine.search.service` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `SearchService._float_value` | `knowledge_engine.search.service` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `SearchService._integer_value` | `knowledge_engine.search.service` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ChunkingService.__init__` | `knowledge_engine.services.chunking` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ChunkingService.chunk` | `knowledge_engine.services.chunking` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `RetrievalService.__init__` | `knowledge_engine.services.retrieval` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `RetrievalService.search` | `knowledge_engine.services.retrieval` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `WorkflowRegistryService.register` | `knowledge_engine.services.workflow_registry` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CatalogStore.__init__` | `knowledge_engine.storage.catalog_store` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CatalogStore.summary` | `knowledge_engine.storage.catalog_store` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CatalogStore.upsert_document` | `knowledge_engine.storage.catalog_store` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `PageStore.search` | `knowledge_engine.storage.page_store` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `KnowledgeWorker._sha256_file` | `knowledge_engine.worker.worker` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ChunkingStage.__init__` | `knowledge_engine.workflows.stages.chunking` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `ChunkingStage.run` | `knowledge_engine.workflows.stages.chunking` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `RetrievalStage.__init__` | `knowledge_engine.workflows.stages.retrieval` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `RetrievalStage.run` | `knowledge_engine.workflows.stages.retrieval` | DORMANT | **DORMANT** | Static implementation found outside the proven live runtime path. |
| `CatalogGroundingService.__init__` | `core.conversation.grounding` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `CatalogGroundingService._ground_objective` | `core.conversation.grounding` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `CatalogGroundingService._search_catalog` | `core.conversation.grounding` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `CatalogGroundingService.ground` | `core.conversation.grounding` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `CatalogGroundingService.search_for_director` | `core.conversation.grounding` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `GroundingEvidence.to_dict` | `core.conversation.grounding` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `GroundingResult.evidence` | `core.conversation.grounding` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `GroundingResult.for_objective` | `core.conversation.grounding` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `GroundingResult.gaps` | `core.conversation.grounding` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `GroundingResult.status` | `core.conversation.grounding` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `GroundingResult.synthesis_input` | `core.conversation.grounding` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `GroundingResult.to_dict` | `core.conversation.grounding` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `ObjectiveGrounding.status` | `core.conversation.grounding` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `ObjectiveGrounding.to_dict` | `core.conversation.grounding` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `ExecutiveConversationOrchestrator.__init__` | `core.conversation.orchestrator` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `ExecutiveDirector.__init__` | `core.executive.director` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `ExecutiveDirector.director_catalog` | `core.executive.director` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `ExecutiveKnowledgeAwarenessService._answerability` | `core.knowledge_awareness.service` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `ExecutiveKnowledgeAwarenessService._evidence` | `core.knowledge_awareness.service` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `ExecutiveKnowledgeAwarenessService._maturity` | `core.knowledge_awareness.service` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `ExecutiveKnowledgeAwarenessService.assess` | `core.knowledge_awareness.service` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `_confidence` | `core.knowledge_catalog.materialization.search` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `_fts_query` | `core.knowledge_catalog.materialization.search` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `search_runtime_knowledge` | `core.knowledge_catalog.materialization.search` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `search_catalog` | `core.knowledge_catalog.search` | CANONICAL | **KEEP** | Live runtime identity proves this implementation participates in the active retrieval path. |
| `embedding_coverage` | `dev.audits.generate_genesis_ix_a4_1b_pack2_reports` | AUXILIARY | **KEEP-AUXILIARY** | Development or verification utility. It is not a production runtime owner. |
| `render_embedding_report` | `dev.audits.generate_genesis_ix_a4_1b_pack2_reports` | AUXILIARY | **KEEP-AUXILIARY** | Development or verification utility. It is not a production runtime owner. |
| `HealthCheck.score` | `dev.doctor.check` | AUXILIARY | **KEEP-AUXILIARY** | Development or verification utility. It is not a production runtime owner. |
| `SearchWorkflowCheck.run` | `dev.doctor.search` | AUXILIARY | **KEEP-AUXILIARY** | Development or verification utility. It is not a production runtime owner. |
| `score_candidate` | `dev.librarian.discovery.engine` | AUXILIARY | **KEEP-AUXILIARY** | Development or verification utility. It is not a production runtime owner. |
| `search` | `dev.librarian.mit_miner` | AUXILIARY | **KEEP-AUXILIARY** | Development or verification utility. It is not a production runtime owner. |
| `make_chunk_record` | `dev.stabilization.repair_serialized_pdf_text` | AUXILIARY | **KEEP-AUXILIARY** | Development or verification utility. It is not a production runtime owner. |
| `remove_existing_embeddings` | `dev.stabilization.repair_serialized_pdf_text` | AUXILIARY | **KEEP-AUXILIARY** | Development or verification utility. It is not a production runtime owner. |
| `replace_document_chunks` | `dev.stabilization.repair_serialized_pdf_text` | AUXILIARY | **KEEP-AUXILIARY** | Development or verification utility. It is not a production runtime owner. |
