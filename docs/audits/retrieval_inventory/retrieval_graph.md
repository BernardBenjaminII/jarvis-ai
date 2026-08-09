# Genesis IX-A4.2A — Retrieval Graph

```mermaid
flowchart TD
    N1["core.conversation.service.ExecutiveConversationService"]
    N2["core.conversation.orchestrator.ExecutiveConversationOrchestrator"]
    N3["core.conversation.grounding.CatalogGroundingService"]
    N4["core.knowledge_awareness.service.ExecutiveKnowledgeAwarenessService"]
    N5["core.executive.director.ExecutiveDirector"]
    N6["builtins.function"]
    N7["SQLite runtime_chunks_fts"]
    N8["core.capabilities.discovery.CapabilityDiscovery._register"]
    N9["registry.all"]
    N10["core.capabilities.discovery.CapabilityDiscovery.discover"]
    N11["core.capabilities.operations.register_operations_capabilities"]
    N12["event_registry.list_events"]
    N13["registry.register"]
    N14["core.certification.runtime.bootstrap.CertificationRuntime.certify"]
    N15["self.catalog_database.is_file"]
    N16["core.cognition.claim_validation.validate_claim_record"]
    N17["validate_evidence_chain"]
    N18["core.cognition.evidence.EvidenceRecord.__post_init__"]
    N19["EvidenceDirection"]
    N20["EvidenceKind"]
    N21["EvidenceQuality"]
    N22["make_evidence_id"]
    N23["core.cognition.evidence_chain.EvidenceChain.__post_init__"]
    N24["EvidenceChainStatus"]
    N25["_normalize_evidence_records"]
    N26["make_evidence_chain_id"]
    N27["core.cognition.evidence_correlation.models.EvidenceLink.__post_init__"]
    N28["EvidencePolarity"]
    N29["EvidenceStrength"]
    N30["InvalidEvidenceLinkError"]
    N31["core.cognition.evidence_correlation.service.ExecutiveEvidenceService.__init__"]
    N32["ExecutiveEvidenceCorrelator"]
    N33["core.cognition.evidence_validation.validate_provenance_record"]
    N34["make_provenance_id"]
    N35["core.cognition.evidence_validation.validate_evidence_record"]
    N36["validate_provenance_record"]
    N37["core.cognition.evidence_validation.validate_evidence_chain"]
    N38["validate_evidence_record"]
    N39["core.cognition.evidence_validation.validate_evidence_object"]
    N40["core.cognition.execution_orchestrator.orchestrator.ExecutiveExecutionOrchestrator.__init__"]
    N41["ExecutorRegistry"]
    N42["core.cognition.layers.observation.director.ObservationDirector.__init__"]
    N43["ObservationRegistry"]
    N44["core.cognition.observation.models.Observation.create"]
    N45["provenance.to_canonical_dict"]
    N46["core.cognition.observation.service.ExecutiveObservationService.record"]
    N47["ObservationProvenance.create"]
    N48["core.cognition.provenance.ProvenanceRecord.__post_init__"]
    N49["ProvenanceKind"]
    N50["core.cognition.workspace.catalog.WorkspaceCatalogEntry.from_workspace"]
    N51["'\n'.join((part.strip() for part in searchable_parts if part and part.strip())).casefold"]
    N52["core.cognition.workspace.catalog.CognitiveWorkspaceCatalog.rebuild"]
    N53["WorkspaceCatalogEntry.from_workspace"]
    N54["core.cognition.workspace.catalog.CognitiveWorkspaceCatalog.resumable"]
    N55["self.search"]
    N56["core.cognition.workspace.catalog.CognitiveWorkspaceCatalog.blocked"]
    N57["core.cognition.workspace.catalog.CognitiveWorkspaceCatalog.low_confidence"]
    N58["core.cognition.workspace.catalog.CognitiveWorkspaceCatalog.search_workspaces"]
    N59["core.cognition.workspace.service.CognitiveWorkspaceService.attach_evidence"]
    N60["hypothesis.attach_evidence"]
    N61["core.conversation.grounding.CatalogGroundingService._search_catalog"]
    N62["search_catalog"]
    N63["core.conversation.grounding.CatalogGroundingService.ground"]
    N64["GroundingResult"]
    N65["core.conversation.grounding.CatalogGroundingService._ground_objective"]
    N66["GroundingEvidence"]
    N67["ObjectiveGrounding"]
    N68["evidence.append"]
    N69["self.search_handler"]
    N70["core.evidence.contracts._require_score"]
    N71["EvidenceValidationError"]
    N72["core.evidence.contracts.EvidenceRelationship.__post_init__"]
    N73["_require_score"]
    N74["core.evidence.contracts.EvidenceGap.__post_init__"]
    N75["core.evidence.contracts.EvidenceSet.__post_init__"]
    N76["evidence_ids.count"]
    N77["core.executive.capabilities.selector.CapabilitySelector._score"]
    N78["CandidateScore"]
    N79["core.executive.director.ExecutiveDirector.__init__"]
    N80["DirectorRegistry"]
    N81["self.planner.bind_registry"]
    N82["self.registry.contains"]
    N83["self.registry.register"]
    N84["core.executive.director.ExecutiveDirector.director_catalog"]
    N85["self.registry.descriptors"]
    N86["core.executive.operations_center.collectors.MetricsCollector.__init__"]
    N87["RegistryCounter"]
    N88["core.executive.operations_center.services.TimedCache.get_or_create"]
    N89["_CacheEntry"]
    N90["core.executive.operations_center.services.ExecutiveHealthService.__init__"]
    N91["TimedCache"]
    N92["core.executive.operations_center.services.ExecutiveMetricsService.__init__"]
    N93["core.government.registry.memory.InMemoryGovernmentRegistry.register_object"]
    N94["RegistryEvent"]
    N95["core.government.registry.memory.InMemoryGovernmentRegistry.update_object"]
    N96["core.government.registry.memory.InMemoryGovernmentRegistry.remove_object"]
    N97["core.government.registry.memory.InMemoryGovernmentRegistry.register_relationship"]
    N98["core.government.registry.memory.InMemoryGovernmentRegistry.remove_relationship"]
    N99["core.government.registry.memory.InMemoryGovernmentRegistry.restore"]
    N100["core.government.registry.memory.InMemoryGovernmentRegistry.transaction"]
    N101["MemoryRegistryTransaction"]
    N102["core.government.registry.provider_memory.InMemoryRegistryProvider.__init__"]
    N103["InMemoryGovernmentRegistry"]
    N104["core.government.registry.provider_memory.InMemoryRegistryProvider.create_transaction"]
    N105["self._registry.transaction"]
    N106["core.integration.audit.RepositoryIntegrationAuditor.audit"]
    N107["CapabilityRegistry"]
    N108["core.integration.catalog.build_genesis_iv_capability_registry"]
    N109["core.knowledge_awareness.service.ExecutiveKnowledgeAwarenessService.assess"]
    N110["EvidenceAssessment"]
    N111["ResearchRecommendation"]
    N112["research.append"]
    N113["self._evidence"]
    N114["core.knowledge_awareness.service.ExecutiveKnowledgeAwarenessService._evidence"]
    N115["EvidenceItem"]
    N116["core.knowledge_catalog.cli.cmd_semantic_backfill"]
    N117["semantic_backfill"]
    N118["core.knowledge_catalog.cli.cmd_search"]
    N119["core.knowledge_catalog.materialization.search.search_runtime_knowledge"]
    N120["_fts_query"]
    N121["conn.execute('SELECT 1 FROM sqlite_master WHERE name='runtime_chunks_fts'').fetchone"]
    N122["conn.execute('SELECT c.id AS chunk_id,c.document_id,d.title,d.file_path,c.chunk_text,1.0 AS rank\n                FROM runtime_chunks c JOIN runtime_documents d ON d.id=c.document_id\n                WHERE lower(c.chunk_text) LIKE ? OR lower(d.title) LIKE ? OR lower(d.file_path) LIKE ?\n                ORDER BY d.file_path,c.chunk_index LIMIT ?', (p, p, p, max(1, int(limit)))).fetchall"]
    N123["conn.execute('SELECT f.chunk_id,f.document_id,f.title,f.file_path,f.chunk_text,bm25(runtime_chunks_fts) AS rank\n                FROM runtime_chunks_fts f WHERE runtime_chunks_fts MATCH ? ORDER BY rank LIMIT ?', (_fts_query(normalized), max(1, int(limit)))).fetchall"]
    N124["core.knowledge_catalog.search.search_catalog"]
    N125["search_runtime_knowledge"]
    N126["core.knowledge_catalog.service.initialize_catalog"]
    N127["CatalogRepository"]
    N128["seed_catalog"]
    N129["core.knowledge_catalog.service.register_file"]
    N130["core.observation.migration_registry.migration_registry_fingerprint"]
    N131["json.dumps(migration_registry_payload(), sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode"]
    N132["migration_registry_payload"]
    N133["core.operations.service.OperationsService.__init__"]
    N134["OperationsEventRegistry"]
    N135["core.reasoning.evidence.contracts._placeholder_evidence_id"]
    N136["EvidenceId"]
    N137["core.reasoning.evidence.contracts.EvidenceContent.content_id"]
    N138["EvidenceContentId.from_payload"]
    N139["core.reasoning.evidence.contracts.EvidenceOrigin.__post_init__"]
    N140["core.reasoning.evidence.contracts.EvidenceProvenance.__post_init__"]
    N141["core.reasoning.evidence.contracts.EvidenceTemporalScope.__post_init__"]
    N142["EvidenceTemporalError"]
    N143["core.reasoning.evidence.contracts.EvidenceUncertainty.__post_init__"]
    N144["EvidenceUncertaintyError"]
    N145["core.reasoning.evidence.contracts.EvidenceUncertainty._validate_kind_contract"]
    N146["core.reasoning.evidence.contracts.EvidenceRelationship.__post_init__"]
    N147["EvidenceRelationshipError"]
    N148["core.reasoning.evidence.contracts.EvidenceRelationship.create"]
    N149["EvidenceRelationshipId.from_payload"]
    N150["core.reasoning.evidence.contracts.EvidenceRecord.__post_init__"]
    N151["core.reasoning.evidence.contracts.EvidenceRecord.create"]
    N152["EvidenceId.from_payload"]
    N153["_placeholder_evidence_id"]
    N154["core.reasoning.evidence.contracts.EvidenceAssessment.__post_init__"]
    N155["core.reasoning.evidence.contracts.EvidenceAssessment.create"]
    N156["EvidenceAssessmentId.from_payload"]
    N157["core.reasoning.evidence.contracts.EvidenceStatusEvent.__post_init__"]
    N158["core.reasoning.evidence.contracts.EvidenceStatusEvent.create"]
    N159["EvidenceStatusEventId.from_payload"]
    N160["core.reasoning.evidence.identifiers.CanonicalEvidenceIdentifier.__post_init__"]
    N161["EvidenceIdentityError"]
    N162["core.reasoning.knowledge._evidence_id"]
    N163["f'{source}\x1f{chunk}\x1f{text}'.encode"]
    N164["hashlib.sha256(f'{source}\x1f{chunk}\x1f{text}'.encode('utf-8')).hexdigest"]
    N165["core.reasoning.knowledge.KnowledgeEvidenceAdapter.adapt"]
    N166["AdaptedEvidenceBatch"]
    N167["KnowledgeEvidenceAdapterError"]
    N168["_evidence_id"]
    N169["_ranking"]
    N170["evidence.sort"]
    N171["core.reasoning.pipeline.KnowledgeReasoningPipeline.__init__"]
    N172["KnowledgeEvidenceAdapter"]
    N173["core.representation.articulation.SemanticArticulator._normalize"]
    N174["_provenance"]
    N175["core.representation.articulation.SemanticArticulator._derive_source_id"]
    N176["reference.provenance.get"]
    N177["core.representation.registry.RepresentationRegistry._build_registration"]
    N178["RepresentationRegistry._normalize_artifact_kinds"]
    N179["core.representation.segmentation.DeterministicSemanticSegmenter.segment"]
    N180["SemanticSegment"]
    N181["core.representation.segmentation.DeterministicSemanticSegmenter._blocks"]
    N182["DeterministicSemanticSegmenter._trim"]
    N183["core.representation.segmentation.DeterministicSemanticSegmenter._lines"]
    N184["core.retrieval.certification.tracer.EndToEndRetrievalTracer.__init__"]
    N185["catalog_database.resolve"]
    N186["core.retrieval.certification.tracer.EndToEndRetrievalTracer._discover_known_query"]
    N187["core.retrieval.certification.tracer.EndToEndRetrievalTracer._database_terms"]
    N188["core.retrieval.certification.tracer.EndToEndRetrievalTracer._known_checks"]
    N189["grounding.get"]
    N190["str(grounding_status).casefold"]
    N191["core.retrieval.certification.tracer.EndToEndRetrievalTracer._gap_checks"]
    N192["core.retrieval.certification.tracer.EndToEndRetrievalTracer._source_contract_checks"]
    N193["catalog_path.read_text"]
    N194["grounding_path.read_text"]
    N195["runtime_search_path.read_text"]
    N196["core.retrieval.certification.tracer.EndToEndRetrievalTracer._json_safe"]
    N197["EndToEndRetrievalTracer._json_safe"]
    N198["core.retrieval.gap_trace.tracer.KnowledgeGapPropagationTracer.__init__"]
    N199["core.semantic_digest.analyzer.analyze_semantics"]
    N200["concept_scores.get"]
    N201["concept_scores.items"]
    N202["keyword_scores.get"]
    N203["keyword_scores.items"]
    N204["subject_scores.get"]
    N205["subject_scores.items"]
    N206["core.src.cognition.intent_classifier._score_keywords"]
    N207["re.search"]
    N208["knowledge_engine.acquisition.__init__.build_default_provider_registry"]
    N209["AcquisitionProviderRegistry"]
    N210["knowledge_engine.acquisition.admission.__init__.build_default_admission_registry"]
    N211["AdmissionPolicyRegistry"]
    N212["knowledge_engine.acquisition.admission.director.AdmissionDirector.evaluate_candidate"]
    N213["self.registry.ordered_policies"]
    N214["knowledge_engine.acquisition.admission.director.AdmissionDirector._validate_evaluations"]
    N215["self.registry.policy_ids"]
    N216["knowledge_engine.acquisition.intake.service.AcquisitionIntakeService.__init__"]
    N217["ProvenanceService"]
    N218["knowledge_engine.acquisition.provenance.repository.ProvenanceRepository.source_exists"]
    N219["conn.execute('\n            SELECT 1\n            FROM acquisition_provenance\n            WHERE provider_id=?\n              AND source_uri=?\n            LIMIT 1\n            ', (provider_id, source_uri)).fetchone"]
    N220["knowledge_engine.acquisition.provenance.repository.ProvenanceRepository.get_by_source"]
    N221["conn.execute('\n            SELECT\n                candidate_id,\n                provider_id,\n                source_uri,\n                local_path,\n                filename,\n                checksum_sha256,\n                first_seen_at,\n                last_seen_at,\n                sighting_count,\n                last_action,\n                last_decision_fingerprint,\n                campaign_id\n            FROM acquisition_provenance\n            WHERE provider_id=?\n              AND source_uri=?\n            ', (provider_id, source_uri)).fetchone"]
    N222["self._map_provenance"]
    N223["knowledge_engine.acquisition.provenance.repository.ProvenanceRepository.find_by_checksum"]
    N224["conn.execute('\n            SELECT\n                candidate_id,\n                provider_id,\n                source_uri,\n                local_path,\n                filename,\n                checksum_sha256,\n                first_seen_at,\n                last_seen_at,\n                sighting_count,\n                last_action,\n                last_decision_fingerprint,\n                campaign_id\n            FROM acquisition_provenance\n            WHERE checksum_sha256=?\n            ORDER BY provider_id, source_uri\n            ', (checksum_sha256,)).fetchall"]
    N225["knowledge_engine.acquisition.provenance.repository.ProvenanceRepository._map_provenance"]
    N226["ProvenanceRecord"]
    N227["knowledge_engine.acquisition.provenance.service.ProvenanceService.__init__"]
    N228["ProvenanceRepository"]
    N229["knowledge_engine.acquisition.provenance.service.ProvenanceService.record_decision"]
    N230["ProvenanceWriteResult"]
    N231["ensure_provenance_schema"]
    N232["knowledge_engine.acquisition.provenance.service.ProvenanceService.known_checksums"]
    N233["conn.execute('\n            SELECT DISTINCT checksum_sha256\n            FROM acquisition_provenance\n            ORDER BY checksum_sha256\n            ').fetchall"]
    N234["knowledge_engine.assimilation.handlers.source_collection.SourceCollectionHandler.__init__"]
    N235["KnowledgeRegistryRepository"]
    N236["knowledge_engine.assimilation.planner.AssimilationPlanner.inventory"]
    N237["conn.execute('\n                SELECT\n                    object_type,\n                    lifecycle_state,\n                    assimilation_state,\n                    COUNT(*) AS total\n                FROM knowledge_registry\n                GROUP BY\n                    object_type,\n                    lifecycle_state,\n                    assimilation_state\n                ORDER BY total DESC, object_type ASC\n                ').fetchall"]
    N238["knowledge_engine.assimilation.registry_builder.build_handler_registry"]
    N239["HandlerRegistry"]
    N240["knowledge_engine.assimilation.repositories.knowledge_registry.KnowledgeRegistryRepository._map_row"]
    N241["KnowledgeRegistryObject"]
    N242["knowledge_engine.assimilation.runner.AssimilationRunner._complete_success"]
    N243["self.state_service.mark_document_ready_for_embedding"]
    N244["knowledge_engine.assimilation.services.extraction.ExtractionService.extract"]
    N245["chunk.strip"]
    N246["chunk_text"]
    N247["knowledge_engine.assimilation.services.persistence.DocumentPersistenceService.persist_document"]
    N248["self.replace_chunks"]
    N249["knowledge_engine.assimilation.single_document.chunk_text"]
    N250["chunks.append"]
    N251["knowledge_engine.capabilities.__init__.register_capabilities"]
    N252["build_knowledge_registry"]
    N253["knowledge_registry.all"]
    N254["knowledge_engine.capabilities.knowledge_registry.KnowledgeRegistryCapability.execute"]
    N255["RegistryService"]
    N256["RegistryService(context.database).run"]
    N257["knowledge_engine.capabilities.registry.build_knowledge_registry"]
    N258["knowledge_engine.catalog_enrichment.builder.CatalogEnrichmentBuilder.build"]
    N259["CatalogEnrichment"]
    N260["init_catalog_enrichment"]
    N261["knowledge_engine.chunking.builder.DocumentChunkBuilder.__init__"]
    N262["DocumentChunkStore"]
    N263["DocumentChunker"]
    N264["knowledge_engine.chunking.builder.DocumentChunkBuilder.build_ready_documents"]
    N265["conn.execute('\n                SELECT kr.object_uuid,\n                       dt.file_path,\n                       dt.text\n                FROM knowledge_registry kr\n                JOIN catalog_documents cd\n                  ON cd.file_path = kr.object_path\n                     OR cd.file_path LIKE kr.object_path || '/%'\n                JOIN document_text dt\n                  ON dt.file_path = cd.file_path\n                WHERE kr.assimilation_state='ready_for_chunking'\n                  AND dt.status='processed'\n                  AND dt.content_chars > 0\n                ORDER BY kr.updated_at ASC\n                LIMIT ?\n                ', (limit,)).fetchall"]
    N266["self._make_chunk"]
    N267["self.chunker.chunk"]
    N268["self.store.replace_chunks"]
    N269["knowledge_engine.chunking.builder.DocumentChunkBuilder._make_chunk"]
    N270["DocumentChunk"]
    N271["knowledge_engine.chunking.chunker.DocumentChunker.chunk"]
    N272["ChunkingResult"]
    N273["self._chunk_code"]
    N274["self._chunk_markdown"]
    N275["knowledge_engine.chunking.chunker.DocumentChunker._looks_like_markdown"]
    N276["knowledge_engine.chunking.chunker.DocumentChunker._chunk_markdown"]
    N277["final_chunks.append"]
    N278["final_chunks.extend"]
    N279["knowledge_engine.chunking.chunker.DocumentChunker._chunk_code"]
    N280["knowledge_engine.chunking.store.DocumentChunkStore.replace_chunks"]
    N281["init_chunks"]
    N282["knowledge_engine.chunking.strategies.chunk_text"]
    N283["knowledge_engine.concepts.builder.ConceptBuilder.build_ready_chunks"]
    N284["conn.execute('\n                SELECT chunk_uuid,\n                       file_path,\n                       text\n                FROM document_chunks\n                WHERE embedding_state='not_embedded'\n                  AND COALESCE(concept_state, 'not_extracted')='not_extracted'\n                ORDER BY created_at ASC\n                LIMIT ?\n                ', (limit,)).fetchall"]
    N285["knowledge_engine.director.registry.StageRegistry.register_defaults"]
    N286["ChunkStage"]
    N287["EmbeddingStage"]
    N288["knowledge_engine.director.stages.chunking.ChunkStage.run"]
    N289["ChunkBuilder"]
    N290["knowledge_engine.director.stages.embeddings.EmbeddingStage.run"]
    N291["ChunkEmbeddingBuilder"]
    N292["builder.build_pending_embeddings"]
    N293["knowledge_engine.director.workflows.search.SearchWorkflow.run"]
    N294["SearchService"]
    N295["knowledge_engine.embeddings.builder.ChunkEmbeddingBuilder.__init__"]
    N296["ChunkEmbeddingStore"]
    N297["LocalEmbeddingProvider"]
    N298["knowledge_engine.embeddings.builder.ChunkEmbeddingBuilder.build_pending_embeddings"]
    N299["ChunkEmbedding"]
    N300["conn.execute('\n                SELECT chunk_uuid,\n                       file_path,\n                       chunk_index,\n                       text,\n                       char_count\n                FROM document_chunks\n                WHERE embedding_state='not_embedded'\n                ORDER BY created_at ASC\n                LIMIT ?\n                ', (limit,)).fetchall"]
    N301["init_embeddings"]
    N302["self.provider.embed"]
    N303["self.store.upsert_embedding"]
    N304["knowledge_engine.embeddings.builder.ChunkEmbeddingBuilder._advance_ready_documents"]
    N305["conn.execute('\n                    SELECT COUNT(*)\n                    FROM document_chunks\n                    WHERE file_path = ?\n                      AND embedding_state='not_embedded'\n                    ', (object_path,)).fetchone"]
    N306["conn.execute('\n                SELECT kr.object_uuid,\n                       kr.object_path\n                FROM knowledge_registry kr\n                WHERE kr.assimilation_state='ready_for_embedding'\n                ').fetchall"]
    N307["knowledge_engine.embeddings.engine.EmbeddingEngine.__init__"]
    N308["knowledge_engine.embeddings.engine.EmbeddingEngine.build_missing"]
    N309["knowledge_engine.embeddings.local_provider.LocalEmbeddingProvider.embed"]
    N310["self.embed_text"]
    N311["knowledge_engine.embeddings.local_provider.LocalEmbeddingProvider.embed_text"]
    N312["vector.astype"]
    N313["vector.astype(float).tolist"]
    N314["knowledge_engine.embeddings.store.ChunkEmbeddingStore.upsert_embedding"]
    N315["knowledge_engine.hybrid_retrieval.faiss_store.build_hnsw_index"]
    N316["vectors.astype"]
    N317["knowledge_engine.hybrid_retrieval.index_builder.HybridIndexBuilder.rebuild"]
    N318["chunk_uuids.append"]
    N319["vectors.append"]
    N320["knowledge_engine.hybrid_retrieval.metadata_search.MetadataSearcher.score_resources"]
    N321["conn.execute('\n                SELECT\n                    lc.object_uuid,\n                    lc.object_path,\n                    lc.object_type,\n                    lc.canonical_title,\n                    lc.display_title,\n                    lc.subject,\n                    lc.keywords,\n                    lc.description,\n                    lc.quality_score,\n                    lc.subject_confidence,\n                    COALESCE(ce.aliases, '') AS aliases,\n                    COALESCE(ce.search_terms, '') AS search_terms,\n                    COALESCE(ce.entities, '') AS entities,\n                    COALESCE(ce.topics, '') AS topics\n                FROM librarian_catalog lc\n                LEFT JOIN catalog_enrichment ce\n                  ON ce.object_uuid = lc.object_uuid\n                ').fetchall"]
    N322["str(row['search_terms'] or '').lower"]
    N323["knowledge_engine.hybrid_retrieval.search.HybridSearcher.__init__"]
    N324["MetadataSearcher"]
    N325["knowledge_engine.hybrid_retrieval.search.HybridSearcher.search"]
    N326["RetrievalResult"]
    N327["conn.execute(sql, list(vector_hits.keys())).fetchall"]
    N328["index.search"]
    N329["metadata_scores.get"]
    N330["self.embedding_provider.embed"]
    N331["self.metadata_searcher.score_resources"]
    N332["vector_hits.keys"]
    N333["knowledge_engine.hybrid_search_cli.cmd_search"]
    N334["HybridSearcher"]
    N335["searcher.search"]
    N336["knowledge_engine.integrity.auditor.KnowledgeIntegrityAuditor.run"]
    N337["self._audit_chunks"]
    N338["self._audit_embeddings"]
    N339["knowledge_engine.integrity.auditor.KnowledgeIntegrityAuditor._audit_chunks"]
    N340["conn.execute('\n            SELECT chunk_uuid,\n                   file_path,\n                   chunk_index,\n                   text,\n                   char_count,\n                   checksum\n            FROM document_chunks\n            ORDER BY file_path, chunk_index\n            LIMIT ?\n            ', (limit,)).fetchall"]
    N341["knowledge_engine.integrity.auditor.KnowledgeIntegrityAuditor._audit_embeddings"]
    N342["conn.execute('\n            SELECT chunk_uuid,\n                   vector_json,\n                   dimensions\n            FROM chunk_embeddings\n            ORDER BY chunk_uuid\n            LIMIT ?\n            ', (limit,)).fetchall"]
    N343["knowledge_engine.library.store.LibraryCatalogStore.summary"]
    N344["conn.execute('SELECT COUNT(*) FROM library_catalog').fetchone"]
    N345["knowledge_engine.processing.catalog_stage.CatalogStage.run"]
    N346["self.catalog_store.upsert_document"]
    N347["knowledge_engine.processors.registry.default_registry"]
    N348["ProcessorRegistry"]
    N349["knowledge_engine.ranking.duplicates.duplicate_similarity"]
    N350["jaccard_similarity"]
    N351["knowledge_engine.ranking.normalization.normalize_candidate"]
    N352["RankingCandidate"]
    N353["_normalize_chunk_index"]
    N354["normalize_quality_score"]
    N355["normalize_semantic_score"]
    N356["knowledge_engine.ranking.ranker.KnowledgeRanker.__init__"]
    N357["RankingWeights"]
    N358["knowledge_engine.ranking.ranker.KnowledgeRanker.rank"]
    N359["self.rank_candidates"]
    N360["knowledge_engine.ranking.ranker.rank_results"]
    N361["KnowledgeRanker"]
    N362["ranker.rank"]
    N363["knowledge_engine.ranking.scorer.lexical_score"]
    N364["knowledge_engine.registry.builder.KnowledgeRegistryBuilder.__init__"]
    N365["KnowledgeRegistryStore"]
    N366["knowledge_engine.registry.builder.KnowledgeRegistryBuilder.build"]
    N367["RegistryRecord"]
    N368["knowledge_engine.registry.service.RegistryService.run"]
    N369["KnowledgeRegistryBuilder"]
    N370["knowledge_engine.registry.store.KnowledgeRegistryStore.initialize"]
    N371["init_registry"]
    N372["knowledge_engine.registry.store.KnowledgeRegistryStore.upsert"]
    N373["knowledge_engine.registry.store.KnowledgeRegistryStore.summary"]
    N374["conn.execute('SELECT COUNT(*) FROM knowledge_registry').fetchone"]
    N375["knowledge_engine.retrieval.vector_search.VectorSearcher.__init__"]
    N376["knowledge_engine.retrieval.vector_search.VectorSearcher.search"]
    N377["self.cosine"]
    N378["knowledge_engine.retrieval_intelligence.director.RetrievalDirector.__init__"]
    N379["VectorRetrievalProvider"]
    N380["knowledge_engine.retrieval_intelligence.director.RetrievalDirector.search"]
    N381["RetrievalDiagnostics"]
    N382["provider.retrieve"]
    N383["knowledge_engine.retrieval_intelligence.normalization.normalize_candidate"]
    N384["RetrievalCandidate"]
    N385["normalize_similarity"]
    N386["knowledge_engine.retrieval_intelligence.providers.VectorRetrievalProvider.__init__"]
    N387["RetrievalService"]
    N388["knowledge_engine.retrieval_intelligence.providers.VectorRetrievalProvider.retrieve"]
    N389["self._service.search"]
    N390["knowledge_engine.search.service.SearchService.__init__"]
    N391["RankingService"]
    N392["RetrievalDirector"]
    N393["knowledge_engine.search.service.SearchService.execute"]
    N394["SearchResponse"]
    N395["quality_scores.append"]
    N396["self._build_search_result"]
    N397["self._quality_score"]
    N398["self.ranking.rank"]
    N399["self.retrieval.search"]
    N400["knowledge_engine.search.service.SearchService._prepare_candidate"]
    N401["QualityService.validator.validate_chunk"]
    N402["SearchService._float_value"]
    N403["SearchService._integer_value"]
    N404["SearchService._quality_score"]
    N405["knowledge_engine.search.service.SearchService._build_search_result"]
    N406["SearchResult"]
    N407["ranked_result.get"]
    N408["knowledge_engine.services.chunking.ChunkingService.__init__"]
    N409["knowledge_engine.services.chunking.ChunkingService.chunk"]
    N410["knowledge_engine.services.embeddings.EmbeddingService.__init__"]
    N411["knowledge_engine.services.embeddings.EmbeddingService.embed"]
    N412["knowledge_engine.services.embeddings.EmbeddingService.embed_batch"]
    N413["self.provider.embed_batch"]
    N414["knowledge_engine.services.ranking.RankingService.__init__"]
    N415["knowledge_engine.services.ranking.RankingService.rank"]
    N416["self._ranker.rank"]
    N417["knowledge_engine.services.ranking.rank_search_results"]
    N418["RankingService().rank"]
    N419["knowledge_engine.services.retrieval.RetrievalService.__init__"]
    N420["VectorSearcher"]
    N421["knowledge_engine.services.retrieval.RetrievalService.search"]
    N422["self.searcher.search"]
    N423["knowledge_engine.source_registry.repository.SQLiteSourceRegistryRepository.get_by_id"]
    N424["SourceRegistryNotFoundError"]
    N425["conn.execute('SELECT * FROM source_registry WHERE registry_id = ?', (registry_id,)).fetchone"]
    N426["knowledge_engine.source_registry.repository.SQLiteSourceRegistryRepository.get_by_source_id"]
    N427["conn.execute('SELECT * FROM source_registry WHERE source_id = ?', (source_id,)).fetchone"]
    N428["knowledge_engine.source_registry.repository.SQLiteSourceRegistryRepository.get_by_fingerprint"]
    N429["conn.execute('SELECT * FROM source_registry WHERE fingerprint = ?', (fingerprint,)).fetchone"]
    N430["knowledge_engine.source_registry.repository.SQLiteSourceRegistryRepository.list_all"]
    N431["conn.execute('SELECT * FROM source_registry ORDER BY registry_id').fetchall"]
    N432["knowledge_engine.source_registry.repository.SQLiteSourceRegistryRepository.update_state"]
    N433["knowledge_engine.source_registry.repository.SQLiteSourceRegistryRepository.stats"]
    N434["RegistryStats"]
    N435["conn.execute('\n                SELECT lifecycle_state, COUNT(*)\n                FROM source_registry\n                GROUP BY lifecycle_state\n                ').fetchall"]
    N436["knowledge_engine.source_registry.service.SourceRegistryService.__init__"]
    N437["SQLiteSourceRegistryRepository"]
    N438["knowledge_engine.source_registry.service.SourceRegistryService.register_source"]
    N439["SourceRegistryConflictError"]
    N440["knowledge_engine.storage.page_store.PageStore.search"]
    N441["conn.execute('\n                SELECT\n                    document_path,\n                    page_number,\n                    snippet(document_pages_fts, 2, '[', ']', '...', 32)\n                FROM document_pages_fts\n                WHERE document_pages_fts MATCH ?\n                LIMIT ?\n                ', (query, limit)).fetchall"]
    N442["knowledge_engine.workflow.smoke.build_smoke_registry"]
    N443["WorkflowRegistry"]
    N444["knowledge_engine.workflows.stages.chunking.ChunkingStage.__init__"]
    N445["ChunkingService"]
    N446["knowledge_engine.workflows.stages.chunking.ChunkingStage.run"]
    N447["self.service.chunk"]
    N448["knowledge_engine.workflows.stages.embeddings.EmbeddingStage.__init__"]
    N449["EmbeddingService"]
    N450["knowledge_engine.workflows.stages.embeddings.EmbeddingStage.run"]
    N451["self.service.embed_batch"]
    N452["knowledge_engine.workflows.stages.registry.RegistryStage.__init__"]
    N453["WorkflowRegistryService"]
    N454["knowledge_engine.workflows.stages.retrieval.RetrievalStage.__init__"]
    N1 -->|injects| N2
    N2 -->|injects| N3
    N2 -->|injects| N4
    N2 -->|injects| N5
    N2 -->|injects| N6
    N3 -->|calls| N6
    N6 -->|delegates| N6
    N6 -->|queries| N7
    N3 -->|provides| N4
    N3 -->|augments| N6
    N8 -->|calls| N9
    N10 -->|calls| N9
    N11 -->|calls| N12
    N11 -->|calls| N9
    N11 -->|calls| N13
    N14 -->|calls| N15
    N16 -->|calls| N17
    N18 -->|calls| N19
    N18 -->|calls| N20
    N18 -->|calls| N21
    N18 -->|calls| N22
    N23 -->|calls| N24
    N23 -->|calls| N25
    N23 -->|calls| N26
    N27 -->|calls| N28
    N27 -->|calls| N29
    N27 -->|calls| N30
    N31 -->|calls| N32
    N33 -->|calls| N34
    N35 -->|calls| N22
    N35 -->|calls| N36
    N37 -->|calls| N26
    N37 -->|calls| N38
    N39 -->|calls| N17
    N39 -->|calls| N38
    N39 -->|calls| N36
    N40 -->|calls| N41
    N42 -->|calls| N43
    N44 -->|calls| N45
    N46 -->|calls| N47
    N48 -->|calls| N49
    N48 -->|calls| N34
    N50 -->|calls| N51
    N52 -->|calls| N53
    N54 -->|calls| N55
    N56 -->|calls| N55
    N57 -->|calls| N55
    N58 -->|calls| N55
    N59 -->|calls| N60
    N61 -->|calls| N62
    N63 -->|calls| N64
    N65 -->|calls| N66
    N65 -->|calls| N67
    N65 -->|calls| N68
    N65 -->|calls| N69
    N70 -->|calls| N71
    N72 -->|calls| N71
    N72 -->|calls| N73
    N74 -->|calls| N73
    N75 -->|calls| N71
    N75 -->|calls| N73
    N75 -->|calls| N76
    N77 -->|calls| N78
    N79 -->|calls| N80
    N79 -->|calls| N81
    N79 -->|calls| N82
    N79 -->|calls| N83
    N84 -->|calls| N85
    N86 -->|calls| N87
    N88 -->|calls| N89
    N90 -->|calls| N91
    N92 -->|calls| N91
    N93 -->|calls| N94
    N95 -->|calls| N94
    N96 -->|calls| N94
    N97 -->|calls| N94
    N98 -->|calls| N94
    N99 -->|calls| N94
    N100 -->|calls| N101
    N102 -->|calls| N103
    N104 -->|calls| N105
    N106 -->|calls| N107
    N106 -->|calls| N9
    N108 -->|calls| N107
    N109 -->|calls| N110
    N109 -->|calls| N111
    N109 -->|calls| N112
    N109 -->|calls| N113
    N114 -->|calls| N115
    N116 -->|calls| N117
    N118 -->|calls| N62
    N119 -->|calls| N120
    N119 -->|calls| N121
    N119 -->|calls| N122
    N119 -->|calls| N123
    N124 -->|calls| N125
    N126 -->|calls| N127
    N126 -->|calls| N128
    N129 -->|calls| N127
    N130 -->|calls| N131
    N130 -->|calls| N132
    N133 -->|calls| N134
    N135 -->|calls| N136
    N137 -->|calls| N138
    N139 -->|calls| N71
    N140 -->|calls| N71
    N141 -->|calls| N142
    N143 -->|calls| N144
    N145 -->|calls| N144
    N146 -->|calls| N147
    N148 -->|calls| N149
    N150 -->|calls| N71
    N151 -->|calls| N152
    N151 -->|calls| N153
    N154 -->|calls| N71
    N155 -->|calls| N156
    N157 -->|calls| N71
    N158 -->|calls| N159
    N160 -->|calls| N161
    N162 -->|calls| N163
    N162 -->|calls| N164
    N165 -->|calls| N166
    N165 -->|calls| N115
    N165 -->|calls| N167
    N165 -->|calls| N168
    N165 -->|calls| N169
    N165 -->|calls| N68
    N165 -->|calls| N170
    N171 -->|calls| N172
    N173 -->|calls| N174
    N175 -->|calls| N176
    N177 -->|calls| N178
    N179 -->|calls| N180
    N181 -->|calls| N182
    N183 -->|calls| N182
    N184 -->|calls| N185
    N186 -->|calls| N62
    N187 -->|calls| N15
    N188 -->|calls| N189
    N188 -->|calls| N190
    N191 -->|calls| N189
    N191 -->|calls| N190
    N192 -->|calls| N193
    N192 -->|calls| N194
    N192 -->|calls| N195
    N196 -->|calls| N197
    N198 -->|calls| N185
    N199 -->|calls| N200
    N199 -->|calls| N201
    N199 -->|calls| N202
    N199 -->|calls| N203
    N199 -->|calls| N204
    N199 -->|calls| N205
    N206 -->|calls| N207
    N208 -->|calls| N209
    N208 -->|calls| N13
    N210 -->|calls| N211
    N210 -->|calls| N13
    N212 -->|calls| N213
    N214 -->|calls| N213
    N214 -->|calls| N215
    N216 -->|calls| N217
    N218 -->|calls| N219
    N220 -->|calls| N221
    N220 -->|calls| N222
    N223 -->|calls| N224
    N223 -->|calls| N222
    N225 -->|calls| N226
    N227 -->|calls| N228
    N229 -->|calls| N230
    N229 -->|calls| N231
    N232 -->|calls| N233
    N232 -->|calls| N231
    N234 -->|calls| N235
    N236 -->|calls| N237
    N238 -->|calls| N239
    N238 -->|calls| N13
    N240 -->|calls| N241
    N242 -->|calls| N243
    N244 -->|calls| N245
    N244 -->|calls| N246
    N247 -->|calls| N245
    N247 -->|calls| N248
    N249 -->|calls| N250
    N251 -->|calls| N252
    N251 -->|calls| N253
    N251 -->|calls| N13
    N254 -->|calls| N255
    N254 -->|calls| N256
    N257 -->|calls| N107
    N257 -->|calls| N13
    N258 -->|calls| N259
    N258 -->|calls| N260
    N261 -->|calls| N262
    N261 -->|calls| N263
    N264 -->|calls| N265
    N264 -->|calls| N266
    N264 -->|calls| N267
    N264 -->|calls| N268
    N269 -->|calls| N270
    N271 -->|calls| N272
    N271 -->|calls| N246
    N271 -->|calls| N273
    N271 -->|calls| N274
    N275 -->|calls| N207
    N276 -->|calls| N245
    N276 -->|calls| N246
    N276 -->|calls| N277
    N276 -->|calls| N278
    N279 -->|calls| N245
    N279 -->|calls| N250
    N280 -->|calls| N281
    N282 -->|calls| N250
    N283 -->|calls| N284
    N285 -->|calls| N286
    N285 -->|calls| N287
    N288 -->|calls| N289
    N290 -->|calls| N291
    N290 -->|calls| N292
    N293 -->|calls| N294
    N295 -->|calls| N296
    N295 -->|calls| N297
    N298 -->|calls| N299
    N298 -->|calls| N300
    N298 -->|calls| N301
    N298 -->|calls| N302
    N298 -->|calls| N303
    N304 -->|calls| N305
    N304 -->|calls| N306
    N307 -->|calls| N297
    N308 -->|calls| N302
    N309 -->|calls| N310
    N311 -->|calls| N312
    N311 -->|calls| N313
    N314 -->|calls| N301
    N315 -->|calls| N316
    N317 -->|calls| N318
    N317 -->|calls| N319
    N320 -->|calls| N321
    N320 -->|calls| N322
    N323 -->|calls| N297
    N323 -->|calls| N324
    N325 -->|calls| N326
    N325 -->|calls| N327
    N325 -->|calls| N328
    N325 -->|calls| N329
    N325 -->|calls| N330
    N325 -->|calls| N331
    N325 -->|calls| N332
    N333 -->|calls| N334
    N333 -->|calls| N335
    N336 -->|calls| N337
    N336 -->|calls| N338
    N339 -->|calls| N340
    N341 -->|calls| N342
    N343 -->|calls| N344
    N345 -->|calls| N346
    N347 -->|calls| N348
    N347 -->|calls| N13
    N349 -->|calls| N350
    N351 -->|calls| N352
    N351 -->|calls| N353
    N351 -->|calls| N354
    N351 -->|calls| N355
    N356 -->|calls| N357
    N358 -->|calls| N359
    N360 -->|calls| N361
    N360 -->|calls| N362
    N363 -->|calls| N350
    N364 -->|calls| N365
    N366 -->|calls| N367
    N368 -->|calls| N369
    N370 -->|calls| N371
    N372 -->|calls| N371
    N373 -->|calls| N374
    N373 -->|calls| N371
    N375 -->|calls| N297
    N376 -->|calls| N377
    N376 -->|calls| N302
    N378 -->|calls| N379
    N380 -->|calls| N381
    N380 -->|calls| N382
    N383 -->|calls| N384
    N383 -->|calls| N385
    N386 -->|calls| N387
    N388 -->|calls| N389
    N390 -->|calls| N391
    N390 -->|calls| N392
    N393 -->|calls| N394
    N393 -->|calls| N395
    N393 -->|calls| N396
    N393 -->|calls| N397
    N393 -->|calls| N398
    N393 -->|calls| N399
    N400 -->|calls| N401
    N400 -->|calls| N402
    N400 -->|calls| N403
    N400 -->|calls| N404
    N405 -->|calls| N401
    N405 -->|calls| N406
    N405 -->|calls| N402
    N405 -->|calls| N403
    N405 -->|calls| N407
    N408 -->|calls| N263
    N409 -->|calls| N267
    N410 -->|calls| N297
    N411 -->|calls| N302
    N412 -->|calls| N413
    N414 -->|calls| N361
    N415 -->|calls| N416
    N417 -->|calls| N391
    N417 -->|calls| N418
    N419 -->|calls| N420
    N421 -->|calls| N422
    N423 -->|calls| N424
    N423 -->|calls| N425
    N426 -->|calls| N427
    N428 -->|calls| N429
    N430 -->|calls| N431
    N432 -->|calls| N424
    N433 -->|calls| N434
    N433 -->|calls| N435
    N436 -->|calls| N437
    N438 -->|calls| N439
    N440 -->|calls| N441
    N442 -->|calls| N443
    N442 -->|calls| N13
    N444 -->|calls| N445
    N446 -->|calls| N447
    N448 -->|calls| N449
    N450 -->|calls| N451
    N452 -->|calls| N453
    N454 -->|calls| N387
```

| Source | Target | Relation | Evidence |
|---|---|---|---|
| `core.conversation.service.ExecutiveConversationService` | `core.conversation.orchestrator.ExecutiveConversationOrchestrator` | injects | runtime binding |
| `core.conversation.orchestrator.ExecutiveConversationOrchestrator` | `core.conversation.grounding.CatalogGroundingService` | injects | runtime binding |
| `core.conversation.orchestrator.ExecutiveConversationOrchestrator` | `core.knowledge_awareness.service.ExecutiveKnowledgeAwarenessService` | injects | runtime binding |
| `core.conversation.orchestrator.ExecutiveConversationOrchestrator` | `core.executive.director.ExecutiveDirector` | injects | runtime binding |
| `core.conversation.orchestrator.ExecutiveConversationOrchestrator` | `builtins.function` | injects | runtime binding |
| `core.conversation.grounding.CatalogGroundingService` | `builtins.function` | calls | bound search handler |
| `builtins.function` | `builtins.function` | delegates | canonical search path |
| `builtins.function` | `SQLite runtime_chunks_fts` | queries | FTS |
| `core.conversation.grounding.CatalogGroundingService` | `core.knowledge_awareness.service.ExecutiveKnowledgeAwarenessService` | provides | GroundingResult |
| `core.conversation.grounding.CatalogGroundingService` | `builtins.function` | augments | synthesis_input |
| `core.capabilities.discovery.CapabilityDiscovery._register` | `registry.all` | calls | core/capabilities/discovery.py:55 |
| `core.capabilities.discovery.CapabilityDiscovery.discover` | `registry.all` | calls | core/capabilities/discovery.py:69 |
| `core.capabilities.operations.register_operations_capabilities` | `event_registry.list_events` | calls | core/capabilities/operations.py:91 |
| `core.capabilities.operations.register_operations_capabilities` | `registry.all` | calls | core/capabilities/operations.py:91 |
| `core.capabilities.operations.register_operations_capabilities` | `registry.register` | calls | core/capabilities/operations.py:91 |
| `core.certification.runtime.bootstrap.CertificationRuntime.certify` | `self.catalog_database.is_file` | calls | core/certification/runtime/bootstrap.py:76 |
| `core.cognition.claim_validation.validate_claim_record` | `validate_evidence_chain` | calls | core/cognition/claim_validation.py:14 |
| `core.cognition.evidence.EvidenceRecord.__post_init__` | `EvidenceDirection` | calls | core/cognition/evidence.py:97 |
| `core.cognition.evidence.EvidenceRecord.__post_init__` | `EvidenceKind` | calls | core/cognition/evidence.py:97 |
| `core.cognition.evidence.EvidenceRecord.__post_init__` | `EvidenceQuality` | calls | core/cognition/evidence.py:97 |
| `core.cognition.evidence.EvidenceRecord.__post_init__` | `make_evidence_id` | calls | core/cognition/evidence.py:97 |
| `core.cognition.evidence_chain.EvidenceChain.__post_init__` | `EvidenceChainStatus` | calls | core/cognition/evidence_chain.py:77 |
| `core.cognition.evidence_chain.EvidenceChain.__post_init__` | `_normalize_evidence_records` | calls | core/cognition/evidence_chain.py:77 |
| `core.cognition.evidence_chain.EvidenceChain.__post_init__` | `make_evidence_chain_id` | calls | core/cognition/evidence_chain.py:77 |
| `core.cognition.evidence_correlation.models.EvidenceLink.__post_init__` | `EvidencePolarity` | calls | core/cognition/evidence_correlation/models.py:110 |
| `core.cognition.evidence_correlation.models.EvidenceLink.__post_init__` | `EvidenceStrength` | calls | core/cognition/evidence_correlation/models.py:110 |
| `core.cognition.evidence_correlation.models.EvidenceLink.__post_init__` | `InvalidEvidenceLinkError` | calls | core/cognition/evidence_correlation/models.py:110 |
| `core.cognition.evidence_correlation.service.ExecutiveEvidenceService.__init__` | `ExecutiveEvidenceCorrelator` | calls | core/cognition/evidence_correlation/service.py:19 |
| `core.cognition.evidence_validation.validate_provenance_record` | `make_provenance_id` | calls | core/cognition/evidence_validation.py:18 |
| `core.cognition.evidence_validation.validate_evidence_record` | `make_evidence_id` | calls | core/cognition/evidence_validation.py:41 |
| `core.cognition.evidence_validation.validate_evidence_record` | `validate_provenance_record` | calls | core/cognition/evidence_validation.py:41 |
| `core.cognition.evidence_validation.validate_evidence_chain` | `make_evidence_chain_id` | calls | core/cognition/evidence_validation.py:68 |
| `core.cognition.evidence_validation.validate_evidence_chain` | `validate_evidence_record` | calls | core/cognition/evidence_validation.py:68 |
| `core.cognition.evidence_validation.validate_evidence_object` | `validate_evidence_chain` | calls | core/cognition/evidence_validation.py:109 |
| `core.cognition.evidence_validation.validate_evidence_object` | `validate_evidence_record` | calls | core/cognition/evidence_validation.py:109 |
| `core.cognition.evidence_validation.validate_evidence_object` | `validate_provenance_record` | calls | core/cognition/evidence_validation.py:109 |
| `core.cognition.execution_orchestrator.orchestrator.ExecutiveExecutionOrchestrator.__init__` | `ExecutorRegistry` | calls | core/cognition/execution_orchestrator/orchestrator.py:38 |
| `core.cognition.layers.observation.director.ObservationDirector.__init__` | `ObservationRegistry` | calls | core/cognition/layers/observation/director.py:21 |
| `core.cognition.observation.models.Observation.create` | `provenance.to_canonical_dict` | calls | core/cognition/observation/models.py:87 |
| `core.cognition.observation.service.ExecutiveObservationService.record` | `ObservationProvenance.create` | calls | core/cognition/observation/service.py:7 |
| `core.cognition.provenance.ProvenanceRecord.__post_init__` | `ProvenanceKind` | calls | core/cognition/provenance.py:84 |
| `core.cognition.provenance.ProvenanceRecord.__post_init__` | `make_provenance_id` | calls | core/cognition/provenance.py:84 |
| `core.cognition.workspace.catalog.WorkspaceCatalogEntry.from_workspace` | `'\n'.join((part.strip() for part in searchable_parts if part and part.strip())).casefold` | calls | core/cognition/workspace/catalog.py:98 |
| `core.cognition.workspace.catalog.CognitiveWorkspaceCatalog.rebuild` | `WorkspaceCatalogEntry.from_workspace` | calls | core/cognition/workspace/catalog.py:149 |
| `core.cognition.workspace.catalog.CognitiveWorkspaceCatalog.resumable` | `self.search` | calls | core/cognition/workspace/catalog.py:182 |
| `core.cognition.workspace.catalog.CognitiveWorkspaceCatalog.blocked` | `self.search` | calls | core/cognition/workspace/catalog.py:201 |
| `core.cognition.workspace.catalog.CognitiveWorkspaceCatalog.low_confidence` | `self.search` | calls | core/cognition/workspace/catalog.py:221 |
| `core.cognition.workspace.catalog.CognitiveWorkspaceCatalog.search_workspaces` | `self.search` | calls | core/cognition/workspace/catalog.py:298 |
| `core.cognition.workspace.service.CognitiveWorkspaceService.attach_evidence` | `hypothesis.attach_evidence` | calls | core/cognition/workspace/service.py:62 |
| `core.conversation.grounding.CatalogGroundingService._search_catalog` | `search_catalog` | calls | core/conversation/grounding.py:148 |
| `core.conversation.grounding.CatalogGroundingService.ground` | `GroundingResult` | calls | core/conversation/grounding.py:152 |
| `core.conversation.grounding.CatalogGroundingService._ground_objective` | `GroundingEvidence` | calls | core/conversation/grounding.py:178 |
| `core.conversation.grounding.CatalogGroundingService._ground_objective` | `ObjectiveGrounding` | calls | core/conversation/grounding.py:178 |
| `core.conversation.grounding.CatalogGroundingService._ground_objective` | `evidence.append` | calls | core/conversation/grounding.py:178 |
| `core.conversation.grounding.CatalogGroundingService._ground_objective` | `self.search_handler` | calls | core/conversation/grounding.py:178 |
| `core.evidence.contracts._require_score` | `EvidenceValidationError` | calls | core/evidence/contracts.py:72 |
| `core.evidence.contracts.EvidenceRelationship.__post_init__` | `EvidenceValidationError` | calls | core/evidence/contracts.py:348 |
| `core.evidence.contracts.EvidenceRelationship.__post_init__` | `_require_score` | calls | core/evidence/contracts.py:348 |
| `core.evidence.contracts.EvidenceGap.__post_init__` | `_require_score` | calls | core/evidence/contracts.py:381 |
| `core.evidence.contracts.EvidenceSet.__post_init__` | `EvidenceValidationError` | calls | core/evidence/contracts.py:408 |
| `core.evidence.contracts.EvidenceSet.__post_init__` | `_require_score` | calls | core/evidence/contracts.py:408 |
| `core.evidence.contracts.EvidenceSet.__post_init__` | `evidence_ids.count` | calls | core/evidence/contracts.py:408 |
| `core.executive.capabilities.selector.CapabilitySelector._score` | `CandidateScore` | calls | core/executive/capabilities/selector.py:53 |
| `core.executive.director.ExecutiveDirector.__init__` | `DirectorRegistry` | calls | core/executive/director.py:23 |
| `core.executive.director.ExecutiveDirector.__init__` | `self.planner.bind_registry` | calls | core/executive/director.py:23 |
| `core.executive.director.ExecutiveDirector.__init__` | `self.registry.contains` | calls | core/executive/director.py:23 |
| `core.executive.director.ExecutiveDirector.__init__` | `self.registry.register` | calls | core/executive/director.py:23 |
| `core.executive.director.ExecutiveDirector.director_catalog` | `self.registry.descriptors` | calls | core/executive/director.py:165 |
| `core.executive.operations_center.collectors.MetricsCollector.__init__` | `RegistryCounter` | calls | core/executive/operations_center/collectors.py:455 |
| `core.executive.operations_center.services.TimedCache.get_or_create` | `_CacheEntry` | calls | core/executive/operations_center/services.py:49 |
| `core.executive.operations_center.services.ExecutiveHealthService.__init__` | `TimedCache` | calls | core/executive/operations_center/services.py:71 |
| `core.executive.operations_center.services.ExecutiveMetricsService.__init__` | `TimedCache` | calls | core/executive/operations_center/services.py:103 |
| `core.government.registry.memory.InMemoryGovernmentRegistry.register_object` | `RegistryEvent` | calls | core/government/registry/memory.py:78 |
| `core.government.registry.memory.InMemoryGovernmentRegistry.update_object` | `RegistryEvent` | calls | core/government/registry/memory.py:87 |
| `core.government.registry.memory.InMemoryGovernmentRegistry.remove_object` | `RegistryEvent` | calls | core/government/registry/memory.py:96 |
| `core.government.registry.memory.InMemoryGovernmentRegistry.register_relationship` | `RegistryEvent` | calls | core/government/registry/memory.py:116 |
| `core.government.registry.memory.InMemoryGovernmentRegistry.remove_relationship` | `RegistryEvent` | calls | core/government/registry/memory.py:136 |
| `core.government.registry.memory.InMemoryGovernmentRegistry.restore` | `RegistryEvent` | calls | core/government/registry/memory.py:216 |
| `core.government.registry.memory.InMemoryGovernmentRegistry.transaction` | `MemoryRegistryTransaction` | calls | core/government/registry/memory.py:231 |
| `core.government.registry.provider_memory.InMemoryRegistryProvider.__init__` | `InMemoryGovernmentRegistry` | calls | core/government/registry/provider_memory.py:19 |
| `core.government.registry.provider_memory.InMemoryRegistryProvider.create_transaction` | `self._registry.transaction` | calls | core/government/registry/provider_memory.py:40 |
| `core.integration.audit.RepositoryIntegrationAuditor.audit` | `CapabilityRegistry` | calls | core/integration/audit.py:11 |
| `core.integration.audit.RepositoryIntegrationAuditor.audit` | `registry.all` | calls | core/integration/audit.py:11 |
| `core.integration.catalog.build_genesis_iv_capability_registry` | `CapabilityRegistry` | calls | core/integration/catalog.py:5 |
| `core.knowledge_awareness.service.ExecutiveKnowledgeAwarenessService.assess` | `EvidenceAssessment` | calls | core/knowledge_awareness/service.py:20 |
| `core.knowledge_awareness.service.ExecutiveKnowledgeAwarenessService.assess` | `ResearchRecommendation` | calls | core/knowledge_awareness/service.py:20 |
| `core.knowledge_awareness.service.ExecutiveKnowledgeAwarenessService.assess` | `research.append` | calls | core/knowledge_awareness/service.py:20 |
| `core.knowledge_awareness.service.ExecutiveKnowledgeAwarenessService.assess` | `self._evidence` | calls | core/knowledge_awareness/service.py:20 |
| `core.knowledge_awareness.service.ExecutiveKnowledgeAwarenessService._evidence` | `EvidenceItem` | calls | core/knowledge_awareness/service.py:82 |
| `core.knowledge_catalog.cli.cmd_semantic_backfill` | `semantic_backfill` | calls | core/knowledge_catalog/cli.py:64 |
| `core.knowledge_catalog.cli.cmd_search` | `search_catalog` | calls | core/knowledge_catalog/cli.py:68 |
| `core.knowledge_catalog.materialization.search.search_runtime_knowledge` | `_fts_query` | calls | core/knowledge_catalog/materialization/search.py:17 |
| `core.knowledge_catalog.materialization.search.search_runtime_knowledge` | `conn.execute("SELECT 1 FROM sqlite_master WHERE name='runtime_chunks_fts'").fetchone` | calls | core/knowledge_catalog/materialization/search.py:17 |
| `core.knowledge_catalog.materialization.search.search_runtime_knowledge` | `conn.execute('SELECT c.id AS chunk_id,c.document_id,d.title,d.file_path,c.chunk_text,1.0 AS rank\n                FROM runtime_chunks c JOIN runtime_documents d ON d.id=c.document_id\n                WHERE lower(c.chunk_text) LIKE ? OR lower(d.title) LIKE ? OR lower(d.file_path) LIKE ?\n                ORDER BY d.file_path,c.chunk_index LIMIT ?', (p, p, p, max(1, int(limit)))).fetchall` | calls | core/knowledge_catalog/materialization/search.py:17 |
| `core.knowledge_catalog.materialization.search.search_runtime_knowledge` | `conn.execute('SELECT f.chunk_id,f.document_id,f.title,f.file_path,f.chunk_text,bm25(runtime_chunks_fts) AS rank\n                FROM runtime_chunks_fts f WHERE runtime_chunks_fts MATCH ? ORDER BY rank LIMIT ?', (_fts_query(normalized), max(1, int(limit)))).fetchall` | calls | core/knowledge_catalog/materialization/search.py:17 |
| `core.knowledge_catalog.search.search_catalog` | `search_runtime_knowledge` | calls | core/knowledge_catalog/search.py:8 |
| `core.knowledge_catalog.service.initialize_catalog` | `CatalogRepository` | calls | core/knowledge_catalog/service.py:11 |
| `core.knowledge_catalog.service.initialize_catalog` | `seed_catalog` | calls | core/knowledge_catalog/service.py:11 |
| `core.knowledge_catalog.service.register_file` | `CatalogRepository` | calls | core/knowledge_catalog/service.py:20 |
| `core.observation.migration_registry.migration_registry_fingerprint` | `json.dumps(migration_registry_payload(), sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode` | calls | core/observation/migration_registry.py:247 |
| `core.observation.migration_registry.migration_registry_fingerprint` | `migration_registry_payload` | calls | core/observation/migration_registry.py:247 |
| `core.operations.service.OperationsService.__init__` | `OperationsEventRegistry` | calls | core/operations/service.py:26 |
| `core.reasoning.evidence.contracts._placeholder_evidence_id` | `EvidenceId` | calls | core/reasoning/evidence/contracts.py:49 |
| `core.reasoning.evidence.contracts.EvidenceContent.content_id` | `EvidenceContentId.from_payload` | calls | core/reasoning/evidence/contracts.py:117 |
| `core.reasoning.evidence.contracts.EvidenceOrigin.__post_init__` | `EvidenceValidationError` | calls | core/reasoning/evidence/contracts.py:135 |
| `core.reasoning.evidence.contracts.EvidenceProvenance.__post_init__` | `EvidenceValidationError` | calls | core/reasoning/evidence/contracts.py:261 |
| `core.reasoning.evidence.contracts.EvidenceTemporalScope.__post_init__` | `EvidenceTemporalError` | calls | core/reasoning/evidence/contracts.py:297 |
| `core.reasoning.evidence.contracts.EvidenceUncertainty.__post_init__` | `EvidenceUncertaintyError` | calls | core/reasoning/evidence/contracts.py:380 |
| `core.reasoning.evidence.contracts.EvidenceUncertainty._validate_kind_contract` | `EvidenceUncertaintyError` | calls | core/reasoning/evidence/contracts.py:453 |
| `core.reasoning.evidence.contracts.EvidenceRelationship.__post_init__` | `EvidenceRelationshipError` | calls | core/reasoning/evidence/contracts.py:599 |
| `core.reasoning.evidence.contracts.EvidenceRelationship.create` | `EvidenceRelationshipId.from_payload` | calls | core/reasoning/evidence/contracts.py:660 |
| `core.reasoning.evidence.contracts.EvidenceRecord.__post_init__` | `EvidenceValidationError` | calls | core/reasoning/evidence/contracts.py:706 |
| `core.reasoning.evidence.contracts.EvidenceRecord.create` | `EvidenceId.from_payload` | calls | core/reasoning/evidence/contracts.py:819 |
| `core.reasoning.evidence.contracts.EvidenceRecord.create` | `_placeholder_evidence_id` | calls | core/reasoning/evidence/contracts.py:819 |
| `core.reasoning.evidence.contracts.EvidenceAssessment.__post_init__` | `EvidenceValidationError` | calls | core/reasoning/evidence/contracts.py:880 |
| `core.reasoning.evidence.contracts.EvidenceAssessment.create` | `EvidenceAssessmentId.from_payload` | calls | core/reasoning/evidence/contracts.py:976 |
| `core.reasoning.evidence.contracts.EvidenceStatusEvent.__post_init__` | `EvidenceValidationError` | calls | core/reasoning/evidence/contracts.py:1038 |
| `core.reasoning.evidence.contracts.EvidenceStatusEvent.create` | `EvidenceStatusEventId.from_payload` | calls | core/reasoning/evidence/contracts.py:1128 |
| `core.reasoning.evidence.identifiers.CanonicalEvidenceIdentifier.__post_init__` | `EvidenceIdentityError` | calls | core/reasoning/evidence/identifiers.py:25 |
| `core.reasoning.knowledge._evidence_id` | `f'{source}\x1f{chunk}\x1f{text}'.encode` | calls | core/reasoning/knowledge.py:63 |
| `core.reasoning.knowledge._evidence_id` | `hashlib.sha256(f'{source}\x1f{chunk}\x1f{text}'.encode('utf-8')).hexdigest` | calls | core/reasoning/knowledge.py:63 |
| `core.reasoning.knowledge.KnowledgeEvidenceAdapter.adapt` | `AdaptedEvidenceBatch` | calls | core/reasoning/knowledge.py:81 |
| `core.reasoning.knowledge.KnowledgeEvidenceAdapter.adapt` | `EvidenceItem` | calls | core/reasoning/knowledge.py:81 |
| `core.reasoning.knowledge.KnowledgeEvidenceAdapter.adapt` | `KnowledgeEvidenceAdapterError` | calls | core/reasoning/knowledge.py:81 |
| `core.reasoning.knowledge.KnowledgeEvidenceAdapter.adapt` | `_evidence_id` | calls | core/reasoning/knowledge.py:81 |
| `core.reasoning.knowledge.KnowledgeEvidenceAdapter.adapt` | `_ranking` | calls | core/reasoning/knowledge.py:81 |
| `core.reasoning.knowledge.KnowledgeEvidenceAdapter.adapt` | `evidence.append` | calls | core/reasoning/knowledge.py:81 |
| `core.reasoning.knowledge.KnowledgeEvidenceAdapter.adapt` | `evidence.sort` | calls | core/reasoning/knowledge.py:81 |
| `core.reasoning.pipeline.KnowledgeReasoningPipeline.__init__` | `KnowledgeEvidenceAdapter` | calls | core/reasoning/pipeline.py:36 |
| `core.representation.articulation.SemanticArticulator._normalize` | `_provenance` | calls | core/representation/articulation.py:259 |
| `core.representation.articulation.SemanticArticulator._derive_source_id` | `reference.provenance.get` | calls | core/representation/articulation.py:384 |
| `core.representation.registry.RepresentationRegistry._build_registration` | `RepresentationRegistry._normalize_artifact_kinds` | calls | core/representation/registry.py:286 |
| `core.representation.segmentation.DeterministicSemanticSegmenter.segment` | `SemanticSegment` | calls | core/representation/segmentation.py:41 |
| `core.representation.segmentation.DeterministicSemanticSegmenter._blocks` | `DeterministicSemanticSegmenter._trim` | calls | core/representation/segmentation.py:99 |
| `core.representation.segmentation.DeterministicSemanticSegmenter._lines` | `DeterministicSemanticSegmenter._trim` | calls | core/representation/segmentation.py:111 |
| `core.retrieval.certification.tracer.EndToEndRetrievalTracer.__init__` | `catalog_database.resolve` | calls | core/retrieval/certification/tracer.py:49 |
| `core.retrieval.certification.tracer.EndToEndRetrievalTracer._discover_known_query` | `search_catalog` | calls | core/retrieval/certification/tracer.py:180 |
| `core.retrieval.certification.tracer.EndToEndRetrievalTracer._database_terms` | `self.catalog_database.is_file` | calls | core/retrieval/certification/tracer.py:205 |
| `core.retrieval.certification.tracer.EndToEndRetrievalTracer._known_checks` | `grounding.get` | calls | core/retrieval/certification/tracer.py:368 |
| `core.retrieval.certification.tracer.EndToEndRetrievalTracer._known_checks` | `str(grounding_status).casefold` | calls | core/retrieval/certification/tracer.py:368 |
| `core.retrieval.certification.tracer.EndToEndRetrievalTracer._gap_checks` | `grounding.get` | calls | core/retrieval/certification/tracer.py:455 |
| `core.retrieval.certification.tracer.EndToEndRetrievalTracer._gap_checks` | `str(grounding_status).casefold` | calls | core/retrieval/certification/tracer.py:455 |
| `core.retrieval.certification.tracer.EndToEndRetrievalTracer._source_contract_checks` | `catalog_path.read_text` | calls | core/retrieval/certification/tracer.py:526 |
| `core.retrieval.certification.tracer.EndToEndRetrievalTracer._source_contract_checks` | `grounding_path.read_text` | calls | core/retrieval/certification/tracer.py:526 |
| `core.retrieval.certification.tracer.EndToEndRetrievalTracer._source_contract_checks` | `runtime_search_path.read_text` | calls | core/retrieval/certification/tracer.py:526 |
| `core.retrieval.certification.tracer.EndToEndRetrievalTracer._json_safe` | `EndToEndRetrievalTracer._json_safe` | calls | core/retrieval/certification/tracer.py:640 |
| `core.retrieval.gap_trace.tracer.KnowledgeGapPropagationTracer.__init__` | `catalog_database.resolve` | calls | core/retrieval/gap_trace/tracer.py:70 |
| `core.semantic_digest.analyzer.analyze_semantics` | `concept_scores.get` | calls | core/semantic_digest/analyzer.py:28 |
| `core.semantic_digest.analyzer.analyze_semantics` | `concept_scores.items` | calls | core/semantic_digest/analyzer.py:28 |
| `core.semantic_digest.analyzer.analyze_semantics` | `keyword_scores.get` | calls | core/semantic_digest/analyzer.py:28 |
| `core.semantic_digest.analyzer.analyze_semantics` | `keyword_scores.items` | calls | core/semantic_digest/analyzer.py:28 |
| `core.semantic_digest.analyzer.analyze_semantics` | `subject_scores.get` | calls | core/semantic_digest/analyzer.py:28 |
| `core.semantic_digest.analyzer.analyze_semantics` | `subject_scores.items` | calls | core/semantic_digest/analyzer.py:28 |
| `core.src.cognition.intent_classifier._score_keywords` | `re.search` | calls | core/src/cognition/intent_classifier.py:93 |
| `knowledge_engine.acquisition.__init__.build_default_provider_registry` | `AcquisitionProviderRegistry` | calls | knowledge_engine/acquisition/__init__.py:22 |
| `knowledge_engine.acquisition.__init__.build_default_provider_registry` | `registry.register` | calls | knowledge_engine/acquisition/__init__.py:22 |
| `knowledge_engine.acquisition.admission.__init__.build_default_admission_registry` | `AdmissionPolicyRegistry` | calls | knowledge_engine/acquisition/admission/__init__.py:31 |
| `knowledge_engine.acquisition.admission.__init__.build_default_admission_registry` | `registry.register` | calls | knowledge_engine/acquisition/admission/__init__.py:31 |
| `knowledge_engine.acquisition.admission.director.AdmissionDirector.evaluate_candidate` | `self.registry.ordered_policies` | calls | knowledge_engine/acquisition/admission/director.py:57 |
| `knowledge_engine.acquisition.admission.director.AdmissionDirector._validate_evaluations` | `self.registry.ordered_policies` | calls | knowledge_engine/acquisition/admission/director.py:147 |
| `knowledge_engine.acquisition.admission.director.AdmissionDirector._validate_evaluations` | `self.registry.policy_ids` | calls | knowledge_engine/acquisition/admission/director.py:147 |
| `knowledge_engine.acquisition.intake.service.AcquisitionIntakeService.__init__` | `ProvenanceService` | calls | knowledge_engine/acquisition/intake/service.py:38 |
| `knowledge_engine.acquisition.provenance.repository.ProvenanceRepository.source_exists` | `conn.execute('\n            SELECT 1\n            FROM acquisition_provenance\n            WHERE provider_id=?\n              AND source_uri=?\n            LIMIT 1\n            ', (provider_id, source_uri)).fetchone` | calls | knowledge_engine/acquisition/provenance/repository.py:21 |
| `knowledge_engine.acquisition.provenance.repository.ProvenanceRepository.get_by_source` | `conn.execute('\n            SELECT\n                candidate_id,\n                provider_id,\n                source_uri,\n                local_path,\n                filename,\n                checksum_sha256,\n                first_seen_at,\n                last_seen_at,\n                sighting_count,\n                last_action,\n                last_decision_fingerprint,\n                campaign_id\n            FROM acquisition_provenance\n            WHERE provider_id=?\n              AND source_uri=?\n            ', (provider_id, source_uri)).fetchone` | calls | knowledge_engine/acquisition/provenance/repository.py:150 |
| `knowledge_engine.acquisition.provenance.repository.ProvenanceRepository.get_by_source` | `self._map_provenance` | calls | knowledge_engine/acquisition/provenance/repository.py:150 |
| `knowledge_engine.acquisition.provenance.repository.ProvenanceRepository.find_by_checksum` | `conn.execute('\n            SELECT\n                candidate_id,\n                provider_id,\n                source_uri,\n                local_path,\n                filename,\n                checksum_sha256,\n                first_seen_at,\n                last_seen_at,\n                sighting_count,\n                last_action,\n                last_decision_fingerprint,\n                campaign_id\n            FROM acquisition_provenance\n            WHERE checksum_sha256=?\n            ORDER BY provider_id, source_uri\n            ', (checksum_sha256,)).fetchall` | calls | knowledge_engine/acquisition/provenance/repository.py:188 |
| `knowledge_engine.acquisition.provenance.repository.ProvenanceRepository.find_by_checksum` | `self._map_provenance` | calls | knowledge_engine/acquisition/provenance/repository.py:188 |
| `knowledge_engine.acquisition.provenance.repository.ProvenanceRepository._map_provenance` | `ProvenanceRecord` | calls | knowledge_engine/acquisition/provenance/repository.py:303 |
| `knowledge_engine.acquisition.provenance.service.ProvenanceService.__init__` | `ProvenanceRepository` | calls | knowledge_engine/acquisition/provenance/service.py:31 |
| `knowledge_engine.acquisition.provenance.service.ProvenanceService.record_decision` | `ProvenanceWriteResult` | calls | knowledge_engine/acquisition/provenance/service.py:41 |
| `knowledge_engine.acquisition.provenance.service.ProvenanceService.record_decision` | `ensure_provenance_schema` | calls | knowledge_engine/acquisition/provenance/service.py:41 |
| `knowledge_engine.acquisition.provenance.service.ProvenanceService.known_checksums` | `conn.execute('\n            SELECT DISTINCT checksum_sha256\n            FROM acquisition_provenance\n            ORDER BY checksum_sha256\n            ').fetchall` | calls | knowledge_engine/acquisition/provenance/service.py:126 |
| `knowledge_engine.acquisition.provenance.service.ProvenanceService.known_checksums` | `ensure_provenance_schema` | calls | knowledge_engine/acquisition/provenance/service.py:126 |
| `knowledge_engine.assimilation.handlers.source_collection.SourceCollectionHandler.__init__` | `KnowledgeRegistryRepository` | calls | knowledge_engine/assimilation/handlers/source_collection.py:31 |
| `knowledge_engine.assimilation.planner.AssimilationPlanner.inventory` | `conn.execute('\n                SELECT\n                    object_type,\n                    lifecycle_state,\n                    assimilation_state,\n                    COUNT(*) AS total\n                FROM knowledge_registry\n                GROUP BY\n                    object_type,\n                    lifecycle_state,\n                    assimilation_state\n                ORDER BY total DESC, object_type ASC\n                ').fetchall` | calls | knowledge_engine/assimilation/planner.py:112 |
| `knowledge_engine.assimilation.registry_builder.build_handler_registry` | `HandlerRegistry` | calls | knowledge_engine/assimilation/registry_builder.py:19 |
| `knowledge_engine.assimilation.registry_builder.build_handler_registry` | `registry.register` | calls | knowledge_engine/assimilation/registry_builder.py:19 |
| `knowledge_engine.assimilation.repositories.knowledge_registry.KnowledgeRegistryRepository._map_row` | `KnowledgeRegistryObject` | calls | knowledge_engine/assimilation/repositories/knowledge_registry.py:126 |
| `knowledge_engine.assimilation.runner.AssimilationRunner._complete_success` | `self.state_service.mark_document_ready_for_embedding` | calls | knowledge_engine/assimilation/runner.py:436 |
| `knowledge_engine.assimilation.services.extraction.ExtractionService.extract` | `chunk.strip` | calls | knowledge_engine/assimilation/services/extraction.py:86 |
| `knowledge_engine.assimilation.services.extraction.ExtractionService.extract` | `chunk_text` | calls | knowledge_engine/assimilation/services/extraction.py:86 |
| `knowledge_engine.assimilation.services.persistence.DocumentPersistenceService.persist_document` | `chunk.strip` | calls | knowledge_engine/assimilation/services/persistence.py:49 |
| `knowledge_engine.assimilation.services.persistence.DocumentPersistenceService.persist_document` | `self.replace_chunks` | calls | knowledge_engine/assimilation/services/persistence.py:49 |
| `knowledge_engine.assimilation.single_document.chunk_text` | `chunks.append` | calls | knowledge_engine/assimilation/single_document.py:31 |
| `knowledge_engine.capabilities.__init__.register_capabilities` | `build_knowledge_registry` | calls | knowledge_engine/capabilities/__init__.py:7 |
| `knowledge_engine.capabilities.__init__.register_capabilities` | `knowledge_registry.all` | calls | knowledge_engine/capabilities/__init__.py:7 |
| `knowledge_engine.capabilities.__init__.register_capabilities` | `registry.register` | calls | knowledge_engine/capabilities/__init__.py:7 |
| `knowledge_engine.capabilities.knowledge_registry.KnowledgeRegistryCapability.execute` | `RegistryService` | calls | knowledge_engine/capabilities/knowledge_registry.py:22 |
| `knowledge_engine.capabilities.knowledge_registry.KnowledgeRegistryCapability.execute` | `RegistryService(context.database).run` | calls | knowledge_engine/capabilities/knowledge_registry.py:22 |
| `knowledge_engine.capabilities.registry.build_knowledge_registry` | `CapabilityRegistry` | calls | knowledge_engine/capabilities/registry.py:12 |
| `knowledge_engine.capabilities.registry.build_knowledge_registry` | `registry.register` | calls | knowledge_engine/capabilities/registry.py:12 |
| `knowledge_engine.catalog_enrichment.builder.CatalogEnrichmentBuilder.build` | `CatalogEnrichment` | calls | knowledge_engine/catalog_enrichment/builder.py:17 |
| `knowledge_engine.catalog_enrichment.builder.CatalogEnrichmentBuilder.build` | `init_catalog_enrichment` | calls | knowledge_engine/catalog_enrichment/builder.py:17 |
| `knowledge_engine.chunking.builder.DocumentChunkBuilder.__init__` | `DocumentChunkStore` | calls | knowledge_engine/chunking/builder.py:13 |
| `knowledge_engine.chunking.builder.DocumentChunkBuilder.__init__` | `DocumentChunker` | calls | knowledge_engine/chunking/builder.py:13 |
| `knowledge_engine.chunking.builder.DocumentChunkBuilder.build_ready_documents` | `conn.execute("\n                SELECT kr.object_uuid,\n                       dt.file_path,\n                       dt.text\n                FROM knowledge_registry kr\n                JOIN catalog_documents cd\n                  ON cd.file_path = kr.object_path\n                     OR cd.file_path LIKE kr.object_path || '/%'\n                JOIN document_text dt\n                  ON dt.file_path = cd.file_path\n                WHERE kr.assimilation_state='ready_for_chunking'\n                  AND dt.status='processed'\n                  AND dt.content_chars > 0\n                ORDER BY kr.updated_at ASC\n                LIMIT ?\n                ", (limit,)).fetchall` | calls | knowledge_engine/chunking/builder.py:18 |
| `knowledge_engine.chunking.builder.DocumentChunkBuilder.build_ready_documents` | `self._make_chunk` | calls | knowledge_engine/chunking/builder.py:18 |
| `knowledge_engine.chunking.builder.DocumentChunkBuilder.build_ready_documents` | `self.chunker.chunk` | calls | knowledge_engine/chunking/builder.py:18 |
| `knowledge_engine.chunking.builder.DocumentChunkBuilder.build_ready_documents` | `self.store.replace_chunks` | calls | knowledge_engine/chunking/builder.py:18 |
| `knowledge_engine.chunking.builder.DocumentChunkBuilder._make_chunk` | `DocumentChunk` | calls | knowledge_engine/chunking/builder.py:85 |
| `knowledge_engine.chunking.chunker.DocumentChunker.chunk` | `ChunkingResult` | calls | knowledge_engine/chunking/chunker.py:24 |
| `knowledge_engine.chunking.chunker.DocumentChunker.chunk` | `chunk_text` | calls | knowledge_engine/chunking/chunker.py:24 |
| `knowledge_engine.chunking.chunker.DocumentChunker.chunk` | `self._chunk_code` | calls | knowledge_engine/chunking/chunker.py:24 |
| `knowledge_engine.chunking.chunker.DocumentChunker.chunk` | `self._chunk_markdown` | calls | knowledge_engine/chunking/chunker.py:24 |
| `knowledge_engine.chunking.chunker.DocumentChunker._looks_like_markdown` | `re.search` | calls | knowledge_engine/chunking/chunker.py:57 |
| `knowledge_engine.chunking.chunker.DocumentChunker._chunk_markdown` | `chunk.strip` | calls | knowledge_engine/chunking/chunker.py:98 |
| `knowledge_engine.chunking.chunker.DocumentChunker._chunk_markdown` | `chunk_text` | calls | knowledge_engine/chunking/chunker.py:98 |
| `knowledge_engine.chunking.chunker.DocumentChunker._chunk_markdown` | `final_chunks.append` | calls | knowledge_engine/chunking/chunker.py:98 |
| `knowledge_engine.chunking.chunker.DocumentChunker._chunk_markdown` | `final_chunks.extend` | calls | knowledge_engine/chunking/chunker.py:98 |
| `knowledge_engine.chunking.chunker.DocumentChunker._chunk_code` | `chunk.strip` | calls | knowledge_engine/chunking/chunker.py:128 |
| `knowledge_engine.chunking.chunker.DocumentChunker._chunk_code` | `chunks.append` | calls | knowledge_engine/chunking/chunker.py:128 |
| `knowledge_engine.chunking.store.DocumentChunkStore.replace_chunks` | `init_chunks` | calls | knowledge_engine/chunking/store.py:46 |
| `knowledge_engine.chunking.strategies.chunk_text` | `chunks.append` | calls | knowledge_engine/chunking/strategies.py:6 |
| `knowledge_engine.concepts.builder.ConceptBuilder.build_ready_chunks` | `conn.execute("\n                SELECT chunk_uuid,\n                       file_path,\n                       text\n                FROM document_chunks\n                WHERE embedding_state='not_embedded'\n                  AND COALESCE(concept_state, 'not_extracted')='not_extracted'\n                ORDER BY created_at ASC\n                LIMIT ?\n                ", (limit,)).fetchall` | calls | knowledge_engine/concepts/builder.py:12 |
| `knowledge_engine.director.registry.StageRegistry.register_defaults` | `ChunkStage` | calls | knowledge_engine/director/registry.py:21 |
| `knowledge_engine.director.registry.StageRegistry.register_defaults` | `EmbeddingStage` | calls | knowledge_engine/director/registry.py:21 |
| `knowledge_engine.director.stages.chunking.ChunkStage.run` | `ChunkBuilder` | calls | knowledge_engine/director/stages/chunking.py:17 |
| `knowledge_engine.director.stages.embeddings.EmbeddingStage.run` | `ChunkEmbeddingBuilder` | calls | knowledge_engine/director/stages/embeddings.py:17 |
| `knowledge_engine.director.stages.embeddings.EmbeddingStage.run` | `builder.build_pending_embeddings` | calls | knowledge_engine/director/stages/embeddings.py:17 |
| `knowledge_engine.director.workflows.search.SearchWorkflow.run` | `SearchService` | calls | knowledge_engine/director/workflows/search.py:26 |
| `knowledge_engine.embeddings.builder.ChunkEmbeddingBuilder.__init__` | `ChunkEmbeddingStore` | calls | knowledge_engine/embeddings/builder.py:9 |
| `knowledge_engine.embeddings.builder.ChunkEmbeddingBuilder.__init__` | `LocalEmbeddingProvider` | calls | knowledge_engine/embeddings/builder.py:9 |
| `knowledge_engine.embeddings.builder.ChunkEmbeddingBuilder.build_pending_embeddings` | `ChunkEmbedding` | calls | knowledge_engine/embeddings/builder.py:14 |
| `knowledge_engine.embeddings.builder.ChunkEmbeddingBuilder.build_pending_embeddings` | `conn.execute("\n                SELECT chunk_uuid,\n                       file_path,\n                       chunk_index,\n                       text,\n                       char_count\n                FROM document_chunks\n                WHERE embedding_state='not_embedded'\n                ORDER BY created_at ASC\n                LIMIT ?\n                ", (limit,)).fetchall` | calls | knowledge_engine/embeddings/builder.py:14 |
| `knowledge_engine.embeddings.builder.ChunkEmbeddingBuilder.build_pending_embeddings` | `init_embeddings` | calls | knowledge_engine/embeddings/builder.py:14 |
| `knowledge_engine.embeddings.builder.ChunkEmbeddingBuilder.build_pending_embeddings` | `self.provider.embed` | calls | knowledge_engine/embeddings/builder.py:14 |
| `knowledge_engine.embeddings.builder.ChunkEmbeddingBuilder.build_pending_embeddings` | `self.store.upsert_embedding` | calls | knowledge_engine/embeddings/builder.py:14 |
| `knowledge_engine.embeddings.builder.ChunkEmbeddingBuilder._advance_ready_documents` | `conn.execute("\n                    SELECT COUNT(*)\n                    FROM document_chunks\n                    WHERE file_path = ?\n                      AND embedding_state='not_embedded'\n                    ", (object_path,)).fetchone` | calls | knowledge_engine/embeddings/builder.py:88 |
| `knowledge_engine.embeddings.builder.ChunkEmbeddingBuilder._advance_ready_documents` | `conn.execute("\n                SELECT kr.object_uuid,\n                       kr.object_path\n                FROM knowledge_registry kr\n                WHERE kr.assimilation_state='ready_for_embedding'\n                ").fetchall` | calls | knowledge_engine/embeddings/builder.py:88 |
| `knowledge_engine.embeddings.engine.EmbeddingEngine.__init__` | `LocalEmbeddingProvider` | calls | knowledge_engine/embeddings/engine.py:11 |
| `knowledge_engine.embeddings.engine.EmbeddingEngine.build_missing` | `self.provider.embed` | calls | knowledge_engine/embeddings/engine.py:31 |
| `knowledge_engine.embeddings.local_provider.LocalEmbeddingProvider.embed` | `self.embed_text` | calls | knowledge_engine/embeddings/local_provider.py:27 |
| `knowledge_engine.embeddings.local_provider.LocalEmbeddingProvider.embed_text` | `vector.astype` | calls | knowledge_engine/embeddings/local_provider.py:30 |
| `knowledge_engine.embeddings.local_provider.LocalEmbeddingProvider.embed_text` | `vector.astype(float).tolist` | calls | knowledge_engine/embeddings/local_provider.py:30 |
| `knowledge_engine.embeddings.store.ChunkEmbeddingStore.upsert_embedding` | `init_embeddings` | calls | knowledge_engine/embeddings/store.py:36 |
| `knowledge_engine.hybrid_retrieval.faiss_store.build_hnsw_index` | `vectors.astype` | calls | knowledge_engine/hybrid_retrieval/faiss_store.py:42 |
| `knowledge_engine.hybrid_retrieval.index_builder.HybridIndexBuilder.rebuild` | `chunk_uuids.append` | calls | knowledge_engine/hybrid_retrieval/index_builder.py:22 |
| `knowledge_engine.hybrid_retrieval.index_builder.HybridIndexBuilder.rebuild` | `vectors.append` | calls | knowledge_engine/hybrid_retrieval/index_builder.py:22 |
| `knowledge_engine.hybrid_retrieval.metadata_search.MetadataSearcher.score_resources` | `conn.execute("\n                SELECT\n                    lc.object_uuid,\n                    lc.object_path,\n                    lc.object_type,\n                    lc.canonical_title,\n                    lc.display_title,\n                    lc.subject,\n                    lc.keywords,\n                    lc.description,\n                    lc.quality_score,\n                    lc.subject_confidence,\n                    COALESCE(ce.aliases, '') AS aliases,\n                    COALESCE(ce.search_terms, '') AS search_terms,\n                    COALESCE(ce.entities, '') AS entities,\n                    COALESCE(ce.topics, '') AS topics\n                FROM librarian_catalog lc\n                LEFT JOIN catalog_enrichment ce\n                  ON ce.object_uuid = lc.object_uuid\n                ").fetchall` | calls | knowledge_engine/hybrid_retrieval/metadata_search.py:14 |
| `knowledge_engine.hybrid_retrieval.metadata_search.MetadataSearcher.score_resources` | `str(row['search_terms'] or '').lower` | calls | knowledge_engine/hybrid_retrieval/metadata_search.py:14 |
| `knowledge_engine.hybrid_retrieval.search.HybridSearcher.__init__` | `LocalEmbeddingProvider` | calls | knowledge_engine/hybrid_retrieval/search.py:17 |
| `knowledge_engine.hybrid_retrieval.search.HybridSearcher.__init__` | `MetadataSearcher` | calls | knowledge_engine/hybrid_retrieval/search.py:17 |
| `knowledge_engine.hybrid_retrieval.search.HybridSearcher.search` | `RetrievalResult` | calls | knowledge_engine/hybrid_retrieval/search.py:23 |
| `knowledge_engine.hybrid_retrieval.search.HybridSearcher.search` | `conn.execute(sql, list(vector_hits.keys())).fetchall` | calls | knowledge_engine/hybrid_retrieval/search.py:23 |
| `knowledge_engine.hybrid_retrieval.search.HybridSearcher.search` | `index.search` | calls | knowledge_engine/hybrid_retrieval/search.py:23 |
| `knowledge_engine.hybrid_retrieval.search.HybridSearcher.search` | `metadata_scores.get` | calls | knowledge_engine/hybrid_retrieval/search.py:23 |
| `knowledge_engine.hybrid_retrieval.search.HybridSearcher.search` | `self.embedding_provider.embed` | calls | knowledge_engine/hybrid_retrieval/search.py:23 |
| `knowledge_engine.hybrid_retrieval.search.HybridSearcher.search` | `self.metadata_searcher.score_resources` | calls | knowledge_engine/hybrid_retrieval/search.py:23 |
| `knowledge_engine.hybrid_retrieval.search.HybridSearcher.search` | `vector_hits.keys` | calls | knowledge_engine/hybrid_retrieval/search.py:23 |
| `knowledge_engine.hybrid_search_cli.cmd_search` | `HybridSearcher` | calls | knowledge_engine/hybrid_search_cli.py:23 |
| `knowledge_engine.hybrid_search_cli.cmd_search` | `searcher.search` | calls | knowledge_engine/hybrid_search_cli.py:23 |
| `knowledge_engine.integrity.auditor.KnowledgeIntegrityAuditor.run` | `self._audit_chunks` | calls | knowledge_engine/integrity/auditor.py:45 |
| `knowledge_engine.integrity.auditor.KnowledgeIntegrityAuditor.run` | `self._audit_embeddings` | calls | knowledge_engine/integrity/auditor.py:45 |
| `knowledge_engine.integrity.auditor.KnowledgeIntegrityAuditor._audit_chunks` | `conn.execute('\n            SELECT chunk_uuid,\n                   file_path,\n                   chunk_index,\n                   text,\n                   char_count,\n                   checksum\n            FROM document_chunks\n            ORDER BY file_path, chunk_index\n            LIMIT ?\n            ', (limit,)).fetchall` | calls | knowledge_engine/integrity/auditor.py:185 |
| `knowledge_engine.integrity.auditor.KnowledgeIntegrityAuditor._audit_embeddings` | `conn.execute('\n            SELECT chunk_uuid,\n                   vector_json,\n                   dimensions\n            FROM chunk_embeddings\n            ORDER BY chunk_uuid\n            LIMIT ?\n            ', (limit,)).fetchall` | calls | knowledge_engine/integrity/auditor.py:269 |
| `knowledge_engine.library.store.LibraryCatalogStore.summary` | `conn.execute('SELECT COUNT(*) FROM library_catalog').fetchone` | calls | knowledge_engine/library/store.py:137 |
| `knowledge_engine.processing.catalog_stage.CatalogStage.run` | `self.catalog_store.upsert_document` | calls | knowledge_engine/processing/catalog_stage.py:32 |
| `knowledge_engine.processors.registry.default_registry` | `ProcessorRegistry` | calls | knowledge_engine/processors/registry.py:24 |
| `knowledge_engine.processors.registry.default_registry` | `registry.register` | calls | knowledge_engine/processors/registry.py:24 |
| `knowledge_engine.ranking.duplicates.duplicate_similarity` | `jaccard_similarity` | calls | knowledge_engine/ranking/duplicates.py:13 |
| `knowledge_engine.ranking.normalization.normalize_candidate` | `RankingCandidate` | calls | knowledge_engine/ranking/normalization.py:158 |
| `knowledge_engine.ranking.normalization.normalize_candidate` | `_normalize_chunk_index` | calls | knowledge_engine/ranking/normalization.py:158 |
| `knowledge_engine.ranking.normalization.normalize_candidate` | `normalize_quality_score` | calls | knowledge_engine/ranking/normalization.py:158 |
| `knowledge_engine.ranking.normalization.normalize_candidate` | `normalize_semantic_score` | calls | knowledge_engine/ranking/normalization.py:158 |
| `knowledge_engine.ranking.ranker.KnowledgeRanker.__init__` | `RankingWeights` | calls | knowledge_engine/ranking/ranker.py:55 |
| `knowledge_engine.ranking.ranker.KnowledgeRanker.rank` | `self.rank_candidates` | calls | knowledge_engine/ranking/ranker.py:148 |
| `knowledge_engine.ranking.ranker.rank_results` | `KnowledgeRanker` | calls | knowledge_engine/ranking/ranker.py:159 |
| `knowledge_engine.ranking.ranker.rank_results` | `ranker.rank` | calls | knowledge_engine/ranking/ranker.py:159 |
| `knowledge_engine.ranking.scorer.lexical_score` | `jaccard_similarity` | calls | knowledge_engine/ranking/scorer.py:66 |
| `knowledge_engine.registry.builder.KnowledgeRegistryBuilder.__init__` | `KnowledgeRegistryStore` | calls | knowledge_engine/registry/builder.py:8 |
| `knowledge_engine.registry.builder.KnowledgeRegistryBuilder.build` | `RegistryRecord` | calls | knowledge_engine/registry/builder.py:12 |
| `knowledge_engine.registry.service.RegistryService.run` | `KnowledgeRegistryBuilder` | calls | knowledge_engine/registry/service.py:15 |
| `knowledge_engine.registry.store.KnowledgeRegistryStore.initialize` | `init_registry` | calls | knowledge_engine/registry/store.py:73 |
| `knowledge_engine.registry.store.KnowledgeRegistryStore.upsert` | `init_registry` | calls | knowledge_engine/registry/store.py:77 |
| `knowledge_engine.registry.store.KnowledgeRegistryStore.summary` | `conn.execute('SELECT COUNT(*) FROM knowledge_registry').fetchone` | calls | knowledge_engine/registry/store.py:132 |
| `knowledge_engine.registry.store.KnowledgeRegistryStore.summary` | `init_registry` | calls | knowledge_engine/registry/store.py:132 |
| `knowledge_engine.retrieval.vector_search.VectorSearcher.__init__` | `LocalEmbeddingProvider` | calls | knowledge_engine/retrieval/vector_search.py:10 |
| `knowledge_engine.retrieval.vector_search.VectorSearcher.search` | `self.cosine` | calls | knowledge_engine/retrieval/vector_search.py:14 |
| `knowledge_engine.retrieval.vector_search.VectorSearcher.search` | `self.provider.embed` | calls | knowledge_engine/retrieval/vector_search.py:14 |
| `knowledge_engine.retrieval_intelligence.director.RetrievalDirector.__init__` | `VectorRetrievalProvider` | calls | knowledge_engine/retrieval_intelligence/director.py:32 |
| `knowledge_engine.retrieval_intelligence.director.RetrievalDirector.search` | `RetrievalDiagnostics` | calls | knowledge_engine/retrieval_intelligence/director.py:58 |
| `knowledge_engine.retrieval_intelligence.director.RetrievalDirector.search` | `provider.retrieve` | calls | knowledge_engine/retrieval_intelligence/director.py:58 |
| `knowledge_engine.retrieval_intelligence.normalization.normalize_candidate` | `RetrievalCandidate` | calls | knowledge_engine/retrieval_intelligence/normalization.py:56 |
| `knowledge_engine.retrieval_intelligence.normalization.normalize_candidate` | `normalize_similarity` | calls | knowledge_engine/retrieval_intelligence/normalization.py:56 |
| `knowledge_engine.retrieval_intelligence.providers.VectorRetrievalProvider.__init__` | `RetrievalService` | calls | knowledge_engine/retrieval_intelligence/providers.py:34 |
| `knowledge_engine.retrieval_intelligence.providers.VectorRetrievalProvider.retrieve` | `self._service.search` | calls | knowledge_engine/retrieval_intelligence/providers.py:37 |
| `knowledge_engine.search.service.SearchService.__init__` | `RankingService` | calls | knowledge_engine/search/service.py:72 |
| `knowledge_engine.search.service.SearchService.__init__` | `RetrievalDirector` | calls | knowledge_engine/search/service.py:72 |
| `knowledge_engine.search.service.SearchService.execute` | `SearchResponse` | calls | knowledge_engine/search/service.py:78 |
| `knowledge_engine.search.service.SearchService.execute` | `quality_scores.append` | calls | knowledge_engine/search/service.py:78 |
| `knowledge_engine.search.service.SearchService.execute` | `self._build_search_result` | calls | knowledge_engine/search/service.py:78 |
| `knowledge_engine.search.service.SearchService.execute` | `self._quality_score` | calls | knowledge_engine/search/service.py:78 |
| `knowledge_engine.search.service.SearchService.execute` | `self.ranking.rank` | calls | knowledge_engine/search/service.py:78 |
| `knowledge_engine.search.service.SearchService.execute` | `self.retrieval.search` | calls | knowledge_engine/search/service.py:78 |
| `knowledge_engine.search.service.SearchService._prepare_candidate` | `QualityService.validator.validate_chunk` | calls | knowledge_engine/search/service.py:218 |
| `knowledge_engine.search.service.SearchService._prepare_candidate` | `SearchService._float_value` | calls | knowledge_engine/search/service.py:218 |
| `knowledge_engine.search.service.SearchService._prepare_candidate` | `SearchService._integer_value` | calls | knowledge_engine/search/service.py:218 |
| `knowledge_engine.search.service.SearchService._prepare_candidate` | `SearchService._quality_score` | calls | knowledge_engine/search/service.py:218 |
| `knowledge_engine.search.service.SearchService._build_search_result` | `QualityService.validator.validate_chunk` | calls | knowledge_engine/search/service.py:369 |
| `knowledge_engine.search.service.SearchService._build_search_result` | `SearchResult` | calls | knowledge_engine/search/service.py:369 |
| `knowledge_engine.search.service.SearchService._build_search_result` | `SearchService._float_value` | calls | knowledge_engine/search/service.py:369 |
| `knowledge_engine.search.service.SearchService._build_search_result` | `SearchService._integer_value` | calls | knowledge_engine/search/service.py:369 |
| `knowledge_engine.search.service.SearchService._build_search_result` | `ranked_result.get` | calls | knowledge_engine/search/service.py:369 |
| `knowledge_engine.services.chunking.ChunkingService.__init__` | `DocumentChunker` | calls | knowledge_engine/services/chunking.py:17 |
| `knowledge_engine.services.chunking.ChunkingService.chunk` | `self.chunker.chunk` | calls | knowledge_engine/services/chunking.py:20 |
| `knowledge_engine.services.embeddings.EmbeddingService.__init__` | `LocalEmbeddingProvider` | calls | knowledge_engine/services/embeddings.py:19 |
| `knowledge_engine.services.embeddings.EmbeddingService.embed` | `self.provider.embed` | calls | knowledge_engine/services/embeddings.py:22 |
| `knowledge_engine.services.embeddings.EmbeddingService.embed_batch` | `self.provider.embed_batch` | calls | knowledge_engine/services/embeddings.py:25 |
| `knowledge_engine.services.ranking.RankingService.__init__` | `KnowledgeRanker` | calls | knowledge_engine/services/ranking.py:14 |
| `knowledge_engine.services.ranking.RankingService.rank` | `self._ranker.rank` | calls | knowledge_engine/services/ranking.py:21 |
| `knowledge_engine.services.ranking.rank_search_results` | `RankingService` | calls | knowledge_engine/services/ranking.py:35 |
| `knowledge_engine.services.ranking.rank_search_results` | `RankingService().rank` | calls | knowledge_engine/services/ranking.py:35 |
| `knowledge_engine.services.retrieval.RetrievalService.__init__` | `VectorSearcher` | calls | knowledge_engine/services/retrieval.py:13 |
| `knowledge_engine.services.retrieval.RetrievalService.search` | `self.searcher.search` | calls | knowledge_engine/services/retrieval.py:16 |
| `knowledge_engine.source_registry.repository.SQLiteSourceRegistryRepository.get_by_id` | `SourceRegistryNotFoundError` | calls | knowledge_engine/source_registry/repository.py:104 |
| `knowledge_engine.source_registry.repository.SQLiteSourceRegistryRepository.get_by_id` | `conn.execute('SELECT * FROM source_registry WHERE registry_id = ?', (registry_id,)).fetchone` | calls | knowledge_engine/source_registry/repository.py:104 |
| `knowledge_engine.source_registry.repository.SQLiteSourceRegistryRepository.get_by_source_id` | `conn.execute('SELECT * FROM source_registry WHERE source_id = ?', (source_id,)).fetchone` | calls | knowledge_engine/source_registry/repository.py:117 |
| `knowledge_engine.source_registry.repository.SQLiteSourceRegistryRepository.get_by_fingerprint` | `conn.execute('SELECT * FROM source_registry WHERE fingerprint = ?', (fingerprint,)).fetchone` | calls | knowledge_engine/source_registry/repository.py:126 |
| `knowledge_engine.source_registry.repository.SQLiteSourceRegistryRepository.list_all` | `conn.execute('SELECT * FROM source_registry ORDER BY registry_id').fetchall` | calls | knowledge_engine/source_registry/repository.py:135 |
| `knowledge_engine.source_registry.repository.SQLiteSourceRegistryRepository.update_state` | `SourceRegistryNotFoundError` | calls | knowledge_engine/source_registry/repository.py:143 |
| `knowledge_engine.source_registry.repository.SQLiteSourceRegistryRepository.stats` | `RegistryStats` | calls | knowledge_engine/source_registry/repository.py:165 |
| `knowledge_engine.source_registry.repository.SQLiteSourceRegistryRepository.stats` | `conn.execute('\n                SELECT lifecycle_state, COUNT(*)\n                FROM source_registry\n                GROUP BY lifecycle_state\n                ').fetchall` | calls | knowledge_engine/source_registry/repository.py:165 |
| `knowledge_engine.source_registry.service.SourceRegistryService.__init__` | `SQLiteSourceRegistryRepository` | calls | knowledge_engine/source_registry/service.py:49 |
| `knowledge_engine.source_registry.service.SourceRegistryService.register_source` | `SourceRegistryConflictError` | calls | knowledge_engine/source_registry/service.py:71 |
| `knowledge_engine.storage.page_store.PageStore.search` | `conn.execute("\n                SELECT\n                    document_path,\n                    page_number,\n                    snippet(document_pages_fts, 2, '[', ']', '...', 32)\n                FROM document_pages_fts\n                WHERE document_pages_fts MATCH ?\n                LIMIT ?\n                ", (query, limit)).fetchall` | calls | knowledge_engine/storage/page_store.py:49 |
| `knowledge_engine.workflow.smoke.build_smoke_registry` | `WorkflowRegistry` | calls | knowledge_engine/workflow/smoke.py:45 |
| `knowledge_engine.workflow.smoke.build_smoke_registry` | `registry.register` | calls | knowledge_engine/workflow/smoke.py:45 |
| `knowledge_engine.workflows.stages.chunking.ChunkingStage.__init__` | `ChunkingService` | calls | knowledge_engine/workflows/stages/chunking.py:12 |
| `knowledge_engine.workflows.stages.chunking.ChunkingStage.run` | `self.service.chunk` | calls | knowledge_engine/workflows/stages/chunking.py:15 |
| `knowledge_engine.workflows.stages.embeddings.EmbeddingStage.__init__` | `EmbeddingService` | calls | knowledge_engine/workflows/stages/embeddings.py:12 |
| `knowledge_engine.workflows.stages.embeddings.EmbeddingStage.run` | `self.service.embed_batch` | calls | knowledge_engine/workflows/stages/embeddings.py:15 |
| `knowledge_engine.workflows.stages.registry.RegistryStage.__init__` | `WorkflowRegistryService` | calls | knowledge_engine/workflows/stages/registry.py:12 |
| `knowledge_engine.workflows.stages.retrieval.RetrievalStage.__init__` | `RetrievalService` | calls | knowledge_engine/workflows/stages/retrieval.py:12 |
