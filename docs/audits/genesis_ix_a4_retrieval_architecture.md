# Genesis IX-A4 — Retrieval Architecture Audit

**Generated:** 2026-08-04T22:13:14.514652+00:00
**Repository:** `/media/abdullah/JARVISDATA/Projects/jarvis-ai`
**Catalog:** `/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite`
**Fingerprint:** `d5546b20b4959b2b39d88291a009451ba20a6c5c818b3b679f5e6ba4ff6e053b`

## Executive Summary

- **INFO — Embedding storage already exists**: chunk_embeddings=5
- **INFO — Existing catalog grounding component found**: CatalogGroundingService already exists.
- **INFO — Existing conversation orchestration component found**: ExecutiveConversationOrchestrator already exists.
- **INFO — Existing knowledge awareness component found**: ExecutiveKnowledgeAwarenessService already exists.
- **INFO — Existing runtime materialization component found**: RuntimeKnowledgeMaterializer already exists.
- **INFO — Grounding is active in the live composition**: The orchestrator uses CatalogGroundingService.
- **INFO — Ranking-related code already exists**: 1025 ranking references were identified.
- **INFO — Runtime corpus inventory**: runtime_documents=69, runtime_chunks=4674.

## Live Composition

- **conversation_service:** `ExecutiveConversationService`
- **orchestrator:** `ExecutiveConversationOrchestrator`
- **grounding_service:** `CatalogGroundingService`
- **awareness_service:** `ExecutiveKnowledgeAwarenessService`
- **observability_service:** `None`
- **synthesis_handler:** `function`
- **director:** `ExecutiveDirector`
- **catalog_database:** `/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite`
- **catalog_exists:** `True`

## Capability Matrix

| Capability | Existing evidence | Status |
|---|---|---|
| Conversation orchestration | ExecutiveConversationOrchestrator | existing |
| Catalog grounding | CatalogGroundingService | existing |
| Knowledge awareness | ExecutiveKnowledgeAwarenessService | existing |
| Runtime materialization | RuntimeKnowledgeMaterializer/runtime_documents | existing |
| Full-text retrieval | search_runtime_knowledge/runtime_chunks_fts | existing |
| Embedding storage | embedding tables | existing |
| Semantic similarity | vector/similarity references | existing |
| Ranking | rank references | existing |
| Provenance | source/citation/provenance references | existing |

## Existing Retrieval Symbols

| Source | Line | Kind | Symbol | Terms |
|---|---:|---|---|---|
| `architecture_contract_20260724_091739/core/capabilities/loader.py` | 18 | class | `CapabilityLoader` | registry |
| `architecture_contract_20260724_091739/core/capabilities/registry.py` | 6 | class | `CapabilityRegistry` | registry |
| `architecture_contract_20260724_091739/core/cognition/claim.py` | 57 | class | `ClaimStatus` | evidence, ground |
| `architecture_contract_20260724_091739/core/cognition/claim.py` | 172 | class | `ClaimRecord` | evidence, ground |
| `architecture_contract_20260724_091739/core/cognition/claim_construction.py` | 110 | class | `ClaimConstructionEngine` | evidence |
| `architecture_contract_20260724_091739/core/cognition/claim_validation.py` | 14 | function | `validate_claim_record` | evidence |
| `architecture_contract_20260724_091739/core/cognition/common/contracts.py` | 95 | class | `SourceReference` | provenance, source |
| `architecture_contract_20260724_091739/core/cognition/common/contracts.py` | 175 | function | `SourceReference.identity_payload` | source |
| `architecture_contract_20260724_091739/core/cognition/common/contracts.py` | 189 | class | `ObservationValue` | source |
| `architecture_contract_20260724_091739/core/cognition/common/normalization.py` | 198 | function | `normalize_display_text` | source |
| `architecture_contract_20260724_091739/core/cognition/common/normalization.py` | 336 | function | `parse_quantity` | source |
| `architecture_contract_20260724_091739/core/cognition/common/normalization.py` | 394 | function | `normalize_observation_value` | source |
| `architecture_contract_20260724_091739/core/cognition/common/object_model.py` | 43 | class | `ProvenanceReference` | provenance |
| `architecture_contract_20260724_091739/core/cognition/confidence.py` | 22 | class | `SourceReliability` | source |
| `architecture_contract_20260724_091739/core/cognition/confidence.py` | 215 | function | `confidence_for_direct_source` | source |
| `architecture_contract_20260724_091739/core/cognition/evidence.py` | 29 | class | `EvidenceKind` | evidence |
| `architecture_contract_20260724_091739/core/cognition/evidence.py` | 40 | class | `EvidenceDirection` | evidence |
| `architecture_contract_20260724_091739/core/cognition/evidence.py` | 48 | class | `EvidenceQuality` | evidence |
| `architecture_contract_20260724_091739/core/cognition/evidence.py` | 76 | function | `make_evidence_id` | evidence |
| `architecture_contract_20260724_091739/core/cognition/evidence.py` | 83 | class | `EvidenceRecord` | evidence |
| `architecture_contract_20260724_091739/core/cognition/evidence.py` | 213 | function | `EvidenceRecord.from_observation` | evidence |
| `architecture_contract_20260724_091739/core/cognition/evidence_chain.py` | 18 | class | `EvidenceChainStatus` | evidence |
| `architecture_contract_20260724_091739/core/cognition/evidence_chain.py` | 27 | function | `make_evidence_chain_id` | evidence |
| `architecture_contract_20260724_091739/core/cognition/evidence_chain.py` | 33 | function | `_normalize_evidence_records` | evidence |
| `architecture_contract_20260724_091739/core/cognition/evidence_chain.py` | 65 | class | `EvidenceChain` | evidence |
| `architecture_contract_20260724_091739/core/cognition/evidence_chain.py` | 168 | function | `EvidenceChain.supporting_evidence` | evidence |
| `architecture_contract_20260724_091739/core/cognition/evidence_chain.py` | 178 | function | `EvidenceChain.opposing_evidence` | evidence |
| `architecture_contract_20260724_091739/core/cognition/evidence_chain.py` | 188 | function | `EvidenceChain.neutral_evidence` | evidence |
| `architecture_contract_20260724_091739/core/cognition/evidence_validation.py` | 18 | function | `validate_provenance_record` | provenance |
| `architecture_contract_20260724_091739/core/cognition/evidence_validation.py` | 41 | function | `validate_evidence_record` | evidence |
| `architecture_contract_20260724_091739/core/cognition/evidence_validation.py` | 68 | function | `validate_evidence_chain` | evidence |
| `architecture_contract_20260724_091739/core/cognition/evidence_validation.py` | 109 | function | `validate_evidence_object` | evidence |
| `architecture_contract_20260724_091739/core/cognition/extraction.py` | 128 | class | `ExtractionSource` | source |
| `architecture_contract_20260724_091739/core/cognition/extraction.py` | 214 | class | `ObservationCandidate` | source |
| `architecture_contract_20260724_091739/core/cognition/extraction.py` | 524 | function | `extract_many` | source |
| `architecture_contract_20260724_091739/core/cognition/layers/observation/enums.py` | 15 | class | `ObservationSourceMode` | source |
| `architecture_contract_20260724_091739/core/cognition/layers/observation/registry.py` | 12 | class | `ObservationRegistry` | registry |
| `architecture_contract_20260724_091739/core/cognition/observation.py` | 51 | class | `ObservationBatch` | source |
| `architecture_contract_20260724_091739/core/cognition/observation.py` | 89 | function | `ObservationEngine.default_source_reliability` | source |
| `architecture_contract_20260724_091739/core/cognition/observation.py` | 246 | function | `ObservationEngine.observe` | source |
| `architecture_contract_20260724_091739/core/cognition/observation.py` | 281 | function | `observe_source` | source |
| `architecture_contract_20260724_091739/core/cognition/provenance.py` | 22 | class | `ProvenanceKind` | provenance |
| `architecture_contract_20260724_091739/core/cognition/provenance.py` | 34 | class | `AcquisitionMethod` | source |
| `architecture_contract_20260724_091739/core/cognition/provenance.py` | 64 | function | `make_provenance_id` | provenance |
| `architecture_contract_20260724_091739/core/cognition/provenance.py` | 71 | class | `ProvenanceRecord` | evidence, provenance, source |
| `architecture_contract_20260724_091739/core/cognition/validation.py` | 22 | function | `validate_source_reference` | provenance, source |
| `architecture_contract_20260724_091739/core/cognition/workspace/catalog.py` | 18 | class | `WorkspaceSortField` | catalog |
| `architecture_contract_20260724_091739/core/cognition/workspace/catalog.py` | 80 | class | `WorkspaceCatalogEntry` | catalog, search |
| `architecture_contract_20260724_091739/core/cognition/workspace/catalog.py` | 140 | class | `CognitiveWorkspaceCatalog` | catalog, search |
| `architecture_contract_20260724_091739/core/cognition/workspace/catalog.py` | 149 | function | `CognitiveWorkspaceCatalog.rebuild` | catalog, materializ |
| `architecture_contract_20260724_091739/core/cognition/workspace/catalog.py` | 159 | function | `CognitiveWorkspaceCatalog.search` | search |
| `architecture_contract_20260724_091739/core/cognition/workspace/catalog.py` | 298 | function | `CognitiveWorkspaceCatalog.search_workspaces` | catalog, search |
| `architecture_contract_20260724_091739/core/cognition/workspace/models.py` | 47 | class | `EvidenceReference` | evidence |
| `architecture_contract_20260724_091739/core/cognition/workspace/models.py` | 137 | function | `Hypothesis.attach_evidence` | evidence |
| `architecture_contract_20260724_091739/core/cognition/workspace/service.py` | 62 | function | `CognitiveWorkspaceService.attach_evidence` | evidence |
| `architecture_contract_20260724_091739/core/conversation/grounding.py` | 16 | class | `GroundingEvidence` | evidence, ground, grounding |
| `architecture_contract_20260724_091739/core/conversation/grounding.py` | 54 | class | `ObjectiveGrounding` | ground, grounding |
| `architecture_contract_20260724_091739/core/conversation/grounding.py` | 75 | class | `GroundingResult` | ground, grounding |
| `architecture_contract_20260724_091739/core/conversation/grounding.py` | 80 | function | `GroundingResult.evidence` | evidence |
| `architecture_contract_20260724_091739/core/conversation/grounding.py` | 108 | function | `GroundingResult.synthesis_input` | synthesis |
| `architecture_contract_20260724_091739/core/conversation/grounding.py` | 130 | class | `CatalogGroundingService` | catalog, evidence, ground, grounding, retrieve |
| `architecture_contract_20260724_091739/core/conversation/grounding.py` | 144 | function | `CatalogGroundingService._search_catalog` | catalog, search |
| `architecture_contract_20260724_091739/core/conversation/grounding.py` | 148 | function | `CatalogGroundingService.ground` | ground |
| `architecture_contract_20260724_091739/core/conversation/grounding.py` | 157 | function | `CatalogGroundingService.search_for_director` | search |
| `architecture_contract_20260724_091739/core/conversation/grounding.py` | 174 | function | `CatalogGroundingService._ground_objective` | ground |
| `architecture_contract_20260724_091739/core/conversation/orchestrator.py` | 59 | class | `ExecutiveConversationOrchestrator` | ground |
| `architecture_contract_20260724_091739/core/engineering/contracts.py` | 78 | class | `VerificationEvidence` | evidence |
| `architecture_contract_20260724_091739/core/engineering/enums.py` | 28 | class | `EvidenceStatus` | evidence |
| `architecture_contract_20260724_091739/core/engineering/errors.py` | 10 | class | `EngineeringEvidenceError` | evidence |
| `architecture_contract_20260724_091739/core/engineering/public_surface.py` | 42 | function | `StaticPublicSurfaceEvaluator.evaluate` | source |
| `architecture_contract_20260724_091739/core/evidence/contracts.py` | 173 | class | `SerializableContract` | evidence |
| `architecture_contract_20260724_091739/core/evidence/contracts.py` | 281 | class | `EvidenceAssessment` | evidence |
| `architecture_contract_20260724_091739/core/evidence/contracts.py` | 301 | class | `EvidenceRecord` | evidence |
| `architecture_contract_20260724_091739/core/evidence/contracts.py` | 337 | class | `EvidenceRelationship` | evidence |
| `architecture_contract_20260724_091739/core/evidence/contracts.py` | 372 | class | `EvidenceGap` | evidence |
| `architecture_contract_20260724_091739/core/evidence/contracts.py` | 390 | class | `EvidenceSet` | evidence |
| `architecture_contract_20260724_091739/core/evidence/enums.py` | 22 | class | `EvidenceDirection` | evidence |
| `architecture_contract_20260724_091739/core/evidence/enums.py` | 32 | class | `EvidenceStatus` | evidence |
| `architecture_contract_20260724_091739/core/evidence/enums.py` | 47 | class | `AdmissibilityStatus` | evidence |
| `architecture_contract_20260724_091739/core/evidence/enums.py` | 76 | class | `EvidenceRelationshipType` | evidence |
| `architecture_contract_20260724_091739/core/evidence/enums.py` | 89 | class | `EvidenceDirectness` | evidence |
| `architecture_contract_20260724_091739/core/evidence/enums.py` | 99 | class | `SourceReliabilityClass` | source |
| `architecture_contract_20260724_091739/core/evidence/enums.py` | 115 | class | `EvidenceGapType` | evidence |
| `architecture_contract_20260724_091739/core/evidence/enums.py` | 132 | class | `EvidenceSufficiencyStatus` | evidence |
| `architecture_contract_20260724_091739/core/evidence/enums.py` | 163 | class | `AssessmentMethod` | evidence |
| `architecture_contract_20260724_091739/core/evidence/enums.py` | 173 | class | `IntegrityStatus` | evidence, source |
| `architecture_contract_20260724_091739/core/evidence/errors.py` | 10 | class | `EvidenceError` | evidence |
| `architecture_contract_20260724_091739/core/evidence/errors.py` | 44 | class | `EvidenceValidationError` | evidence |
| `architecture_contract_20260724_091739/core/evidence/errors.py` | 50 | class | `EvidenceAdmissibilityError` | evidence |
| `architecture_contract_20260724_091739/core/evidence/errors.py` | 56 | class | `EvidenceConstructionError` | evidence |
| `architecture_contract_20260724_091739/core/evidence/errors.py` | 62 | class | `EvidenceIntegrityError` | evidence, provenance |
| `architecture_contract_20260724_091739/core/evidence/errors.py` | 68 | class | `EvidenceConflictError` | evidence |
| `architecture_contract_20260724_091739/core/evidence/errors.py` | 74 | class | `EvidenceRelationshipError` | evidence |
| `architecture_contract_20260724_091739/core/evidence/errors.py` | 80 | class | `EvidenceAggregationError` | evidence |
| `architecture_contract_20260724_091739/core/evidence/errors.py` | 86 | class | `EvidenceFingerprintError` | evidence |
| `architecture_contract_20260724_091739/core/evidence/errors.py` | 92 | class | `EvidenceSerializationError` | evidence |
| `architecture_contract_20260724_091739/core/evidence/errors.py` | 98 | class | `EvidenceStateTransitionError` | evidence |
| `architecture_contract_20260724_091739/core/evidence/errors.py` | 122 | class | `EvidenceNotFoundError` | evidence |
| `architecture_contract_20260724_091739/core/evidence/errors.py` | 128 | class | `ObservationReferenceError` | evidence |
| `architecture_contract_20260724_091739/core/evidence/errors.py` | 134 | class | `UnsupportedObservationError` | evidence |
| `architecture_contract_20260724_091739/core/evidence/errors.py` | 140 | class | `EvidencePolicyError` | evidence |
| `architecture_contract_20260724_091739/core/executive/director.py` | 165 | function | `ExecutiveDirector.director_catalog` | catalog |
| `architecture_contract_20260724_091739/core/executive/handlers.py` | 11 | function | `executive_handler` | synthesis |
| `architecture_contract_20260724_091739/core/executive/handlers.py` | 92 | class | `KnowledgeHandler` | search |
| `architecture_contract_20260724_091739/core/executive/persistence/checkpoint.py` | 93 | class | `ExecutiveCheckpoint` | materializ |
| `architecture_contract_20260724_091739/core/executive/persistence/contracts.py` | 232 | function | `MigrationPath.source` | source |
| `architecture_contract_20260724_091739/core/executive/planner.py` | 16 | function | `MissionPlanner.bind_registry` | registry |
| `architecture_contract_20260724_091739/core/executive/planning/enums.py` | 104 | class | `ResourceKind` | source |
| `architecture_contract_20260724_091739/core/executive/planning/models.py` | 92 | class | `EvidenceReference` | evidence |
| `architecture_contract_20260724_091739/core/executive/planning/models.py` | 145 | class | `ResourceRequirement` | source |
| `architecture_contract_20260724_091739/core/executive/registry.py` | 19 | class | `DirectorRegistry` | registry |
| `architecture_contract_20260724_091739/core/integration/registry.py` | 5 | class | `ProjectionRegistry` | registry |
| `architecture_contract_20260724_091739/core/knowledge_catalog/assimilation/engine.py` | 22 | class | `AssimilationResult` | assimilat |
| `architecture_contract_20260724_091739/core/knowledge_catalog/assimilation/engine.py` | 326 | function | `assimilate_file` | assimilat |
| `architecture_contract_20260724_091739/core/knowledge_catalog/assimilation/engine.py` | 334 | function | `assimilate_tree` | assimilat |
| `architecture_contract_20260724_091739/core/knowledge_catalog/cli.py` | 46 | function | `cmd_sources` | source |
| `architecture_contract_20260724_091739/core/knowledge_catalog/cli.py` | 68 | function | `cmd_search` | search |
| `architecture_contract_20260724_091739/core/knowledge_catalog/database.py` | 19 | function | `_schema_script` | catalog |
| `architecture_contract_20260724_091739/core/knowledge_catalog/models.py` | 13 | class | `Source` | source |
| `architecture_contract_20260724_091739/core/knowledge_catalog/repository.py` | 8 | class | `CatalogRepository` | catalog |
| `architecture_contract_20260724_091739/core/knowledge_catalog/repository.py` | 12 | function | `CatalogRepository.upsert_source` | source |
| `architecture_contract_20260724_091739/core/knowledge_catalog/search.py` | 10 | function | `search_catalog` | catalog, search |
| `architecture_contract_20260724_091739/core/knowledge_catalog/seed.py` | 131 | function | `seed_catalog` | catalog |
| `architecture_contract_20260724_091739/core/knowledge_catalog/service.py` | 11 | function | `initialize_catalog` | catalog |
| `architecture_contract_20260724_091739/core/operations/contracts.py` | 39 | class | `ResourceProvider` | source |
| `architecture_contract_20260724_091739/core/operations/contracts.py` | 42 | function | `ResourceProvider.collect_resources` | source |
| `architecture_contract_20260724_091739/core/operations/models.py` | 58 | class | `Provenance` | provenance |
| `architecture_contract_20260724_091739/core/operations/models.py` | 131 | class | `ResourceSnapshot` | source |
| `architecture_contract_20260724_091739/core/operations/registry.py` | 10 | class | `OperationsEventRegistry` | registry |
| `architecture_contract_20260724_091739/core/operations/resources.py` | 15 | class | `SystemResourceProvider` | source |
| `architecture_contract_20260724_091739/core/operations/resources.py` | 21 | function | `SystemResourceProvider.collect_resources` | source |
| `architecture_contract_20260724_091739/core/operations/resources.py` | 49 | class | `ResourceCollector` | source |
| `architecture_contract_20260724_091739/core/operations/service.py` | 45 | function | `OperationsService.event_registry` | registry |
| `architecture_contract_20260724_091739/core/operations/service.py` | 60 | function | `OperationsService.resources` | source |
| `architecture_contract_20260724_091739/core/reasoning/context/contracts.py` | 212 | class | `ReasoningContext` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/enums.py` | 8 | class | `EvidenceKind` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/enums.py` | 19 | class | `EvidenceStance` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/errors.py` | 14 | class | `UnknownEvidenceReferenceError` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/errors.py` | 18 | class | `DuplicateReasoningElementError` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/contracts.py` | 49 | function | `_placeholder_evidence_id` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/contracts.py` | 80 | class | `EvidenceContent` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/contracts.py` | 124 | class | `EvidenceOrigin` | evidence, source |
| `architecture_contract_20260724_091739/core/reasoning/evidence/contracts.py` | 193 | class | `EvidenceProvenanceStep` | evidence, provenance |
| `architecture_contract_20260724_091739/core/reasoning/evidence/contracts.py` | 256 | class | `EvidenceProvenance` | evidence, provenance |
| `architecture_contract_20260724_091739/core/reasoning/evidence/contracts.py` | 288 | class | `EvidenceTemporalScope` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/contracts.py` | 369 | class | `EvidenceUncertainty` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/contracts.py` | 589 | class | `EvidenceRelationship` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/contracts.py` | 691 | class | `EvidenceRecord` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/contracts.py` | 799 | function | `EvidenceRecord._identity_payload` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/contracts.py` | 860 | class | `EvidenceAssessment` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/contracts.py` | 1027 | class | `EvidenceStatusEvent` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/enums.py` | 15 | class | `EvidenceSourceType` | evidence, source |
| `architecture_contract_20260724_091739/core/reasoning/evidence/enums.py` | 32 | class | `EvidenceModality` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/enums.py` | 47 | class | `EvidenceStatus` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/enums.py` | 58 | class | `EvidenceRelationshipType` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/enums.py` | 87 | class | `AssessmentMethod` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/enums.py` | 100 | class | `ClassificationLevel` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/errors.py` | 6 | class | `EvidenceError` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/errors.py` | 10 | class | `EvidenceValidationError` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/errors.py` | 14 | class | `EvidenceIdentityError` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/errors.py` | 18 | class | `EvidenceSerializationError` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/errors.py` | 22 | class | `EvidenceUncertaintyError` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/errors.py` | 26 | class | `EvidenceTemporalError` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/errors.py` | 30 | class | `EvidenceRelationshipError` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/identifiers.py` | 18 | class | `CanonicalEvidenceIdentifier` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/identifiers.py` | 73 | class | `EvidenceContentId` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/identifiers.py` | 80 | class | `EvidenceId` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/identifiers.py` | 87 | class | `EvidenceAssessmentId` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/identifiers.py` | 94 | class | `EvidenceStatusEventId` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/evidence/identifiers.py` | 101 | class | `EvidenceRelationshipId` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/inference.py` | 19 | function | `assess_hypothesis` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/knowledge.py` | 13 | class | `KnowledgeEvidenceAdapterError` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/knowledge.py` | 18 | class | `AdaptedEvidenceBatch` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/knowledge.py` | 56 | function | `_ranking` | rank |
| `architecture_contract_20260724_091739/core/reasoning/knowledge.py` | 63 | function | `_evidence_id` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/knowledge.py` | 78 | class | `KnowledgeEvidenceAdapter` | evidence, rank, search |
| `architecture_contract_20260724_091739/core/reasoning/models.py` | 66 | class | `EvidenceItem` | evidence |
| `architecture_contract_20260724_091739/core/reasoning/pipeline.py` | 33 | class | `KnowledgeReasoningPipeline` | search |
| `architecture_contract_20260724_091739/core/reasoning/service.py` | 32 | class | `ReasoningEngine` | evidence, retrieve |
| `architecture_contract_20260724_091739/core/representation/articulation.py` | 97 | function | `ArticulatedUnit.source_segment_ids` | source |
| `architecture_contract_20260724_091739/core/representation/articulation.py` | 158 | class | `SemanticArticulator` | provenance |
| `architecture_contract_20260724_091739/core/representation/articulation.py` | 285 | function | `SemanticArticulator._materialize` | materializ |
| `architecture_contract_20260724_091739/core/representation/articulation.py` | 384 | function | `SemanticArticulator._derive_source_id` | source |
| `architecture_contract_20260724_091739/core/representation/articulation.py` | 452 | function | `_provenance` | provenance |
| `architecture_contract_20260724_091739/core/representation/contracts.py` | 35 | class | `ArtifactKind` | source |
| `architecture_contract_20260724_091739/core/representation/contracts.py` | 66 | class | `SourceSpan` | source |
| `architecture_contract_20260724_091739/core/representation/contracts.py` | 110 | function | `SegmentationRequest.source_id` | source |
| `architecture_contract_20260724_091739/core/representation/contracts.py` | 119 | class | `SemanticSegment` | source |
| `architecture_contract_20260724_091739/core/representation/contracts.py` | 151 | function | `SemanticSegment.source_id` | source |
| `architecture_contract_20260724_091739/core/representation/contracts.py` | 172 | function | `SegmentationResult.source_id` | source |
| `architecture_contract_20260724_091739/core/representation/contracts.py` | 268 | class | `Observation` | ground, source |
| `architecture_contract_20260724_091739/core/representation/contracts.py` | 320 | class | `RepresentationBundle` | source |
| `architecture_contract_20260724_091739/core/representation/director.py` | 77 | function | `RepresentationResult.source_id` | source |
| `architecture_contract_20260724_091739/core/representation/director.py` | 91 | class | `RepresentationDirector` | registry |
| `architecture_contract_20260724_091739/core/representation/director.py` | 169 | function | `RepresentationDirector._attach_request_metadata` | source |
| `architecture_contract_20260724_091739/core/representation/registry.py` | 22 | class | `RepresentationRegistryError` | registry |
| `architecture_contract_20260724_091739/core/representation/registry.py` | 39 | class | `RepresentationPipeline` | registry |
| `architecture_contract_20260724_091739/core/representation/registry.py` | 103 | class | `RepresentationRegistry` | registry |
| `architecture_contract_20260724_091739/core/representation/registry.py` | 269 | function | `RepresentationRegistry.snapshot` | registry |
| `architecture_contract_20260724_091739/core/src/routes/api.py` | 37 | function | `_catalog_database_path` | catalog |
| `architecture_contract_20260724_091739/core/src/routes/operations.py` | 30 | function | `get_capability_registry` | registry |
| `architecture_contract_20260724_091739/core/src/routes/operations.py` | 68 | function | `operations_resources` | source |
| `architecture_contract_20260724_091739/core/src/routes/operations.py` | 125 | function | `operations_capability` | registry |
| `architecture_contract_20260724_091739/core/src/runtime/tool_registry.py` | 7 | class | `ToolRegistry` | registry |
| `architecture_contract_20260724_091739/core/src/runtime/tool_registry.py` | 63 | function | `registry` | registry |
| `architecture_contract_20260724_091739/dev/audit_phase_7a7_interfaces.py` | 91 | class | `SourceFileContract` | source |
| `architecture_contract_20260724_091739/dev/audit_phase_7a7_interfaces.py` | 292 | function | `discover_assimilation_modules` | assimilat |
| `architecture_contract_20260724_091739/dev/audit_phase_7a7_interfaces.py` | 320 | function | `static_source_contract` | source |
| `architecture_contract_20260724_091739/dev/audit_phase_7a7_interfaces.py` | 390 | function | `inspect_source_tree` | assimilat, source |
| `architecture_contract_20260724_091739/dev/doctor/search.py` | 7 | class | `SearchWorkflowCheck` | search |
| `architecture_contract_20260724_091739/dev/execute_genesis_5e1b_cognition_api_restoration.py` | 52 | function | `validate_sources` | source |
| `architecture_contract_20260724_091739/dev/integration/knowledge_pipeline_check.py` | 20 | class | `KnowledgePipelineIntegrationCheck` | catalog |
| `architecture_contract_20260724_091739/dev/librarian/cko/mit_cko_builder.py` | 111 | function | `find_pdf_for_resource` | source |
| `architecture_contract_20260724_091739/dev/librarian/cko/mit_cko_builder.py` | 182 | function | `materialize_representation` | materializ |
| `architecture_contract_20260724_091739/dev/librarian/discovery/engine.py` | 60 | function | `load_sources` | source |
| `architecture_contract_20260724_091739/dev/librarian/discovery/engine.py` | 65 | function | `source_matches_topic` | source |
| `architecture_contract_20260724_091739/dev/librarian/discovery/models.py` | 12 | class | `TrustedSource` | source |
| `architecture_contract_20260724_091739/dev/librarian/mit_miner.py` | 91 | function | `search` | search |
| `architecture_contract_20260724_091739/dev/stabilization/repair_serialized_pdf_text.py` | 198 | function | `make_chunk_record` | chunk |
| `architecture_contract_20260724_091739/dev/stabilization/repair_serialized_pdf_text.py` | 365 | function | `remove_existing_embeddings` | embedding |
| `architecture_contract_20260724_091739/dev/stabilization/repair_serialized_pdf_text.py` | 417 | function | `replace_document_chunks` | chunk |
| `architecture_contract_20260724_091739/dev/stabilization/repair_serialized_pdf_text.py` | 508 | function | `update_registry_state` | registry |
| `architecture_contract_20260724_091739/dev/tests/acquisition/test_admission_registry.py` | 19 | function | `verify_empty_registry` | registry |
| `architecture_contract_20260724_091739/dev/tests/acquisition/test_phase_7a2.py` | 23 | function | `verify_default_registry` | registry |
| `architecture_contract_20260724_091739/dev/tests/acquisition/test_phase_7a3.py` | 192 | function | `verify_same_content_different_source` | source |
| `architecture_contract_20260724_091739/dev/tests/acquisition/test_phase_7a7.py` | 53 | class | `FakeRegistrationPort` | registry |
| `architecture_contract_20260724_091739/dev/tests/acquisition/test_phase_7a7.py` | 101 | class | `FakeExecutionPort` | assimilat |
| `architecture_contract_20260724_091739/dev/tests/acquisition/test_phase_7a7.py` | 524 | function | `verify_wrong_phase_vi_uuid_is_rejected` | registry |
| `architecture_contract_20260724_091739/dev/tests/acquisition/test_phase_7a8.py` | 107 | function | `imports_for_path` | source |
| `architecture_contract_20260724_091739/dev/tests/acquisition/test_phase_7a8.py` | 264 | function | `verify_forward_dependency_direction` | provenance |
| `architecture_contract_20260724_091739/dev/tests/acquisition/test_phase_7a8.py` | 337 | function | `verify_phase_vi_import_isolation` | assimilat |
| `architecture_contract_20260724_091739/dev/tests/test_architecture_contracts.py` | 60 | class | `SourceFacts` | source |
| `architecture_contract_20260724_091739/dev/tests/test_architecture_contracts.py` | 112 | function | `inspect_source` | source |
| `architecture_contract_20260724_091739/dev/tests/test_architecture_contracts.py` | 390 | function | `verify_registry_builder_composition_root` | registry |
| `architecture_contract_20260724_091739/dev/tests/test_architecture_contracts.py` | 493 | function | `verify_repository_ownership` | registry |
| `architecture_contract_20260724_091739/dev/tests/test_performance_contracts.py` | 63 | function | `create_catalog` | assimilat, catalog |
| `architecture_contract_20260724_091739/dev/tests/test_performance_contracts.py` | 151 | function | `create_registry_only_catalog` | catalog, registry |
| `architecture_contract_20260724_091739/dev/tests/test_phase_7a1.py` | 75 | function | `verify_registry` | registry |
| `architecture_contract_20260724_091739/dev/tools/audit_reasoning_contracts.py` | 99 | function | `_unparse` | source |
| `architecture_contract_20260724_091739/dev/tools/audit_reasoning_contracts.py` | 222 | function | `_module_functions` | source |
| `architecture_contract_20260724_091739/dev/tools/audit_reasoning_knowledge_integration.py` | 159 | function | `_unparse` | source |
| `architecture_contract_20260724_091739/dev/tools/audit_reasoning_services.py` | 33 | function | `source_text` | source |
| `architecture_contract_20260724_091739/dev/verification/registry.py` | 242 | function | `validate_registry` | registry |
| `architecture_contract_20260724_091739/tests/cognition/test_genesis_4r1_cognitive_object_model.py` | 21 | function | `GenesisIVR1Tests.test_provenance` | provenance |
| `architecture_contract_20260724_091739/tests/cognition/test_genesis_4r2_observation_models.py` | 41 | function | `ObservationModelTests.test_missing_provenance_is_rejected` | provenance |
| `architecture_contract_20260724_091739/tests/cognition/test_genesis_4r2_observation_registry.py` | 16 | class | `ObservationRegistryTests` | registry |
| `architecture_contract_20260724_091739/tests/test_convergence_c2_director_activation.py` | 39 | function | `DirectorActivationTests.test_assignment_exposes_routing_evidence_and_task_results` | evidence |
| `architecture_contract_20260724_091739/tests/test_convergence_c2a_certification_repair.py` | 12 | function | `CertificationRepairTests.test_c1_http_contract_patches_active_synthesis_boundary` | synthesis |
| `architecture_contract_20260724_091739/tests/test_convergence_c3_capability_routing.py` | 10 | function | `CapabilityRoutingTests.test_catalog_request_routes_to_knowledge` | catalog |
| `architecture_contract_20260724_091739/tests/test_convergence_c3_capability_routing.py` | 30 | function | `CapabilityRoutingTests.test_mission_records_router_evidence` | evidence |
| `architecture_contract_20260724_091739/tests/test_convergence_c4_knowledge_grounding.py` | 12 | class | `KnowledgeGroundingTests` | ground, grounding |
| `architecture_contract_20260724_091739/tests/test_convergence_c4_knowledge_grounding.py` | 47 | function | `KnowledgeGroundingTests.test_catalog_evidence_is_exposed_in_response_metadata` | catalog, evidence |
| `architecture_contract_20260724_091739/tests/test_convergence_c4_knowledge_grounding.py` | 58 | function | `KnowledgeGroundingTests.test_missing_evidence_declares_a_knowledge_gap` | evidence |
| `architecture_contract_20260724_091739/tests/test_convergence_c4_knowledge_grounding.py` | 66 | function | `KnowledgeGroundingTests.test_synthesis_receives_evidence_and_gap_instructions` | evidence, synthesis |
| `architecture_contract_20260724_091739/tests/test_convergence_c4_knowledge_grounding.py` | 74 | function | `KnowledgeGroundingTests.test_knowledge_director_executes_live_catalog_adapter` | catalog |
| `architecture_contract_20260724_091739/tests/test_convergence_c4_knowledge_grounding.py` | 83 | function | `KnowledgeGroundingTests.test_trace_records_grounding_lifecycle` | ground, grounding |
| `architecture_contract_20260724_091739/tests/test_convergence_c4a_knowledge_compatibility.py` | 37 | function | `KnowledgeCompatibilityRepairTests.test_search_catalog_operates_after_compatibility_migration` | catalog, search |
| `architecture_contract_20260724_091739/tests/test_gen2_capability_routing.py` | 30 | function | `CapabilityRoutingTests.test_registry_selects_best_capability_coverage` | registry |
| `architecture_contract_20260724_091739/tests/test_gen2_capability_routing.py` | 84 | function | `CapabilityRoutingTests.test_planner_records_routing_evidence` | evidence |
| `architecture_contract_20260724_091739/tests/test_gen2_capability_routing.py` | 106 | function | `CapabilityRoutingTests.test_director_catalog_exposes_capabilities` | catalog |
| `architecture_contract_20260724_091739/tests/test_gen2_capability_routing.py` | 117 | function | `CapabilityRoutingTests.test_live_knowledge_bridge_is_ready.fake_search` | search |
| `architecture_contract_20260724_091739/tests/test_gen2_executive.py` | 46 | function | `ExecutiveDirectorTests.test_knowledge_mission_routes_to_knowledge_director.fake_search` | search |
| `architecture_contract_20260724_091739/tests/test_gen2_executive.py` | 85 | function | `ExecutiveDirectorTests.test_failed_director_blocks_dependent_synthesis` | synthesis |
| `architecture_contract_20260724_091739/tests/test_genesis_2a4_evidence_contracts.py` | 103 | function | `test_evidence_record_is_deterministic` | evidence |
| `architecture_contract_20260724_091739/tests/test_genesis_2a4_evidence_contracts.py` | 141 | function | `test_evidence_contracts_are_immutable` | evidence |
| `architecture_contract_20260724_091739/tests/test_genesis_2a4_evidence_contracts.py` | 148 | function | `test_evidence_revision_uses_status_event` | evidence |
| `architecture_contract_20260724_091739/tests/test_genesis_2a4_evidence_contracts.py` | 208 | function | `test_source_reliability_and_content_credibility_are_separate` | source |
| `architecture_contract_20260724_091739/tests/test_genesis_2a4_evidence_contracts.py` | 373 | function | `test_provenance_sequence_must_be_contiguous` | provenance |
| `architecture_contract_20260724_091739/tests/test_genesis_2a4_evidence_contracts.py` | 571 | function | `test_related_evidence_order_does_not_change_event_identity` | evidence |
| `architecture_contract_20260724_091739/tests/test_genesis_3a1_cognitive_workspace.py` | 43 | function | `TestGenesis3A1CognitiveWorkspace.test_evidence_is_attached_to_known_hypothesis` | evidence |
| `architecture_contract_20260724_091739/tests/test_genesis_3a3_workspace_catalog_search.py` | 19 | class | `TestGenesis3A3WorkspaceCatalogSearch` | catalog, search |
| `architecture_contract_20260724_091739/tests/test_genesis_3a3_workspace_catalog_search.py` | 75 | function | `TestGenesis3A3WorkspaceCatalogSearch.test_catalog_rebuilds_from_repository` | catalog |
| `architecture_contract_20260724_091739/tests/test_genesis_3a3_workspace_catalog_search.py` | 85 | function | `TestGenesis3A3WorkspaceCatalogSearch.test_text_search_matches_objective` | search |
| `architecture_contract_20260724_091739/tests/test_genesis_3a3_workspace_catalog_search.py` | 104 | function | `TestGenesis3A3WorkspaceCatalogSearch.test_text_search_matches_hypothesis_content` | search |
| `architecture_contract_20260724_091739/tests/test_genesis_3a3_workspace_catalog_search.py` | 228 | function | `TestGenesis3A3WorkspaceCatalogSearch.test_search_workspaces_returns_full_models` | search |
| `architecture_contract_20260724_091739/tests/test_genesis_4a3_claim_construction.py` | 53 | function | `GenesisIVA3ClaimConstructionTests.make_evidence` | evidence |
| `architecture_contract_20260724_091739/tests/test_genesis_4r3a_pack1_evidence_foundation.py` | 48 | class | `EvidenceEnumTests` | evidence |
| `architecture_contract_20260724_091739/tests/test_genesis_4r3a_pack1_evidence_foundation.py` | 106 | class | `EvidenceErrorTests` | evidence |
| `architecture_contract_20260724_091739/tests/test_genesis_4r3a_pack1_evidence_foundation.py` | 169 | class | `EvidencePublicApiTests` | evidence |
| `architecture_contract_20260724_091739/tests/test_genesis_4r3a_pack2a_contracts.py` | 35 | class | `EvidenceContractTests` | evidence |
| `architecture_contract_20260724_091739/tests/test_genesis_4r3a_pack2a_contracts.py` | 133 | function | `EvidenceContractTests.test_evidence_set_rejects_mismatched_proposition` | evidence |
| `architecture_contract_20260724_091739/tests/test_genesis_4r3a_pack2a_contracts.py` | 155 | function | `EvidenceContractTests.test_evidence_set_rejects_duplicate_record` | evidence |
| `architecture_contract_20260724_091739/tests/test_genesis_4r3a_pack2a_contracts.py` | 196 | function | `EvidenceContractTests.test_evidence_set_serializes` | evidence |
| `architecture_contract_20260724_091739/tests/test_genesis_5e0_engineering_os_foundation.py` | 41 | function | `EngineeringOSFoundationTests.test_sufficient_evidence_cannot_fail` | evidence |
| `architecture_contract_20260724_091739/tests/test_genesis_5e0_engineering_os_foundation.py` | 55 | function | `EngineeringOSFoundationTests.test_approved_decision_requires_evidence` | evidence |
| `architecture_contract_20260724_091739/tests/test_genesis_5e0_engineering_os_foundation.py` | 86 | function | `EngineeringOSFoundationTests.test_unknown_decision_evidence_rejected` | evidence |
| `architecture_contract_20260724_091739/tests/test_genesis_5e1a_repository_reality_modeling.py` | 58 | function | `RepositoryRealityModelingTests.test_missing_target_is_inventory_evidence` | evidence |
| `architecture_contract_20260724_091739/tests/test_genesis_ui_a2_executive_projection_framework.py` | 30 | function | `ExecutiveProjectionFrameworkTests.test_registry_registers_provider` | registry |
| `architecture_contract_20260724_091739/tests/test_genesis_ui_a2_executive_projection_framework.py` | 33 | function | `ExecutiveProjectionFrameworkTests.test_registry_rejects_duplicates` | registry |
| `architecture_contract_20260724_091739/tests/test_genesis_ui_a3_capability_discovery_registration.py` | 25 | class | `FakeEventRegistry` | registry |
| `architecture_contract_20260724_091739/tests/test_genesis_ui_a3_capability_discovery_registration.py` | 46 | function | `FakeOperationsService.resources` | source |
| `architecture_contract_20260724_091739/tests/test_genesis_ui_a41_knowledge_inventory_projection.py` | 21 | class | `FakeEventRegistry` | registry |
| `architecture_contract_20260724_091739/tests/test_genesis_ui_a41_knowledge_inventory_projection.py` | 42 | function | `FakeOperationsService.resources` | source |
| `architecture_contract_20260724_091739/tests/test_genesis_vi_a1_executive_telemetry.py` | 68 | class | `StaticResourceProvider` | source |
| `architecture_contract_20260724_091739/tests/test_genesis_vi_a1_executive_telemetry.py` | 69 | function | `StaticResourceProvider.collect_resources` | source |
| `architecture_contract_20260724_091739/tests/test_genesis_vi_a61_persistence_contracts.py` | 131 | function | `PersistenceContractTests.test_migration_path_exposes_source_and_target` | source |
| `architecture_contract_20260724_091739/tests/test_mc1001_operations.py` | 38 | class | `StaticResourceProvider` | source |
| `architecture_contract_20260724_091739/tests/test_mc1001_operations.py` | 39 | function | `StaticResourceProvider.collect_resources` | source |
| `architecture_contract_20260724_091739/tests/test_phase_7b1_source_admission.py` | 22 | class | `SourceNormalizationTests` | source |
| `architecture_contract_20260724_091739/tests/test_phase_7b1_source_admission.py` | 23 | function | `SourceNormalizationTests.test_https_source_is_canonicalized` | source |
| `architecture_contract_20260724_091739/tests/test_phase_7b1_source_admission.py` | 104 | function | `SourceNormalizationTests.test_invalid_source_id_is_rejected` | source |
| `architecture_contract_20260724_091739/tests/test_phase_7b1_source_admission.py` | 135 | class | `SourceAdmissionPolicyTests` | source |
| `architecture_contract_20260724_091739/tests/test_phase_7b1_source_admission.py` | 136 | function | `SourceAdmissionPolicyTests.test_official_source_is_accepted` | source |
| `architecture_contract_20260724_091739/tests/test_phase_7b1_source_admission.py` | 153 | function | `SourceAdmissionPolicyTests.test_unknown_source_requires_review` | source |
| `architecture_contract_20260724_091739/tests/test_phase_7b1_source_admission.py` | 170 | function | `SourceAdmissionPolicyTests.test_community_source_requires_review` | source |
| `architecture_contract_20260724_091739/tests/test_phase_7b1_source_admission.py` | 187 | function | `SourceAdmissionPolicyTests.test_restricted_source_is_rejected` | source |
| `architecture_contract_20260724_091739/tests/test_phase_7b1_source_admission.py` | 204 | function | `SourceAdmissionPolicyTests.test_network_sources_can_be_disabled` | source |
| `architecture_contract_20260724_091739/tests/test_phase_7b1_source_admission.py` | 287 | function | `SourceAdmissionPolicyTests.test_local_source_within_allowed_root_is_accepted` | source |
| `architecture_contract_20260724_091739/tests/test_phase_7b1_source_admission.py` | 310 | function | `SourceAdmissionPolicyTests.test_local_source_outside_allowed_root_is_rejected` | source |
| `architecture_contract_20260724_091739/tests/test_phase_7b2_source_registry.py` | 25 | class | `SourceRegistryTests` | registry, source |
| `architecture_contract_20260724_091739/tests/test_phase_7b2_source_registry.py` | 46 | function | `SourceRegistryTests.test_registers_accepted_source` | source |
| `architecture_contract_20260724_091739/tests/test_phase_7b2_source_registry.py` | 81 | function | `SourceRegistryTests.test_source_id_conflict_is_detected` | source |
| `architecture_contract_20260724_091739/tests/test_phase_7b2_source_registry.py` | 133 | function | `SourceRegistryTests.test_retired_source_cannot_reactivate` | source |
| `architecture_contract_20260724_091739/tests/test_phase_x_reasoning_foundation.py` | 162 | function | `ReasoningFoundationTests.test_rejects_unknown_evidence_reference` | evidence |
| `architecture_contract_20260724_091739/tests/test_phase_xb_hypothesis_knowledge.py` | 21 | class | `SearchResultFixture` | search |
| `architecture_contract_20260724_091739/tests/test_phase_xb_hypothesis_knowledge.py` | 56 | function | `AdapterTests.test_ranked_mapping_shape` | rank |
| `architecture_contract_20260724_091739/tests/test_phase_xb_hypothesis_knowledge.py` | 95 | function | `PipelineTests.test_complete_cycle.search` | search |
| `architecture_contract_20260724_091739/tests/test_phase_xc1_cognitive_representation.py` | 66 | function | `CognitiveRepresentationTests.test_source_identity_changes_ids` | source |
| `architecture_contract_20260724_091739/tests/test_phase_xc2_semantic_articulation.py` | 69 | function | `ArticulationTests.test_provenance_is_immutable` | provenance |
| `artifacts/architecture_contract_20260724_015711/core/capabilities/loader.py` | 18 | class | `CapabilityLoader` | registry |
| `artifacts/architecture_contract_20260724_015711/core/capabilities/registry.py` | 6 | class | `CapabilityRegistry` | registry |
| `artifacts/architecture_contract_20260724_015711/core/cognition/claim.py` | 57 | class | `ClaimStatus` | evidence, ground |
| `artifacts/architecture_contract_20260724_015711/core/cognition/claim.py` | 172 | class | `ClaimRecord` | evidence, ground |
| `artifacts/architecture_contract_20260724_015711/core/cognition/claim_construction.py` | 110 | class | `ClaimConstructionEngine` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/claim_validation.py` | 14 | function | `validate_claim_record` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/common/contracts.py` | 95 | class | `SourceReference` | provenance, source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/common/contracts.py` | 175 | function | `SourceReference.identity_payload` | source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/common/contracts.py` | 189 | class | `ObservationValue` | source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/common/normalization.py` | 198 | function | `normalize_display_text` | source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/common/normalization.py` | 336 | function | `parse_quantity` | source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/common/normalization.py` | 394 | function | `normalize_observation_value` | source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/common/object_model.py` | 43 | class | `ProvenanceReference` | provenance |
| `artifacts/architecture_contract_20260724_015711/core/cognition/confidence.py` | 22 | class | `SourceReliability` | source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/confidence.py` | 215 | function | `confidence_for_direct_source` | source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/evidence.py` | 29 | class | `EvidenceKind` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/evidence.py` | 40 | class | `EvidenceDirection` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/evidence.py` | 48 | class | `EvidenceQuality` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/evidence.py` | 76 | function | `make_evidence_id` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/evidence.py` | 83 | class | `EvidenceRecord` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/evidence.py` | 213 | function | `EvidenceRecord.from_observation` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/evidence_chain.py` | 18 | class | `EvidenceChainStatus` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/evidence_chain.py` | 27 | function | `make_evidence_chain_id` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/evidence_chain.py` | 33 | function | `_normalize_evidence_records` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/evidence_chain.py` | 65 | class | `EvidenceChain` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/evidence_chain.py` | 168 | function | `EvidenceChain.supporting_evidence` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/evidence_chain.py` | 178 | function | `EvidenceChain.opposing_evidence` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/evidence_chain.py` | 188 | function | `EvidenceChain.neutral_evidence` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/evidence_validation.py` | 18 | function | `validate_provenance_record` | provenance |
| `artifacts/architecture_contract_20260724_015711/core/cognition/evidence_validation.py` | 41 | function | `validate_evidence_record` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/evidence_validation.py` | 68 | function | `validate_evidence_chain` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/evidence_validation.py` | 109 | function | `validate_evidence_object` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/extraction.py` | 128 | class | `ExtractionSource` | source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/extraction.py` | 214 | class | `ObservationCandidate` | source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/extraction.py` | 524 | function | `extract_many` | source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/layers/observation/enums.py` | 15 | class | `ObservationSourceMode` | source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/layers/observation/registry.py` | 12 | class | `ObservationRegistry` | registry |
| `artifacts/architecture_contract_20260724_015711/core/cognition/observation.py` | 51 | class | `ObservationBatch` | source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/observation.py` | 89 | function | `ObservationEngine.default_source_reliability` | source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/observation.py` | 246 | function | `ObservationEngine.observe` | source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/observation.py` | 281 | function | `observe_source` | source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/provenance.py` | 22 | class | `ProvenanceKind` | provenance |
| `artifacts/architecture_contract_20260724_015711/core/cognition/provenance.py` | 34 | class | `AcquisitionMethod` | source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/provenance.py` | 64 | function | `make_provenance_id` | provenance |
| `artifacts/architecture_contract_20260724_015711/core/cognition/provenance.py` | 71 | class | `ProvenanceRecord` | evidence, provenance, source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/validation.py` | 22 | function | `validate_source_reference` | provenance, source |
| `artifacts/architecture_contract_20260724_015711/core/cognition/workspace/catalog.py` | 18 | class | `WorkspaceSortField` | catalog |
| `artifacts/architecture_contract_20260724_015711/core/cognition/workspace/catalog.py` | 80 | class | `WorkspaceCatalogEntry` | catalog, search |
| `artifacts/architecture_contract_20260724_015711/core/cognition/workspace/catalog.py` | 140 | class | `CognitiveWorkspaceCatalog` | catalog, search |
| `artifacts/architecture_contract_20260724_015711/core/cognition/workspace/catalog.py` | 149 | function | `CognitiveWorkspaceCatalog.rebuild` | catalog, materializ |
| `artifacts/architecture_contract_20260724_015711/core/cognition/workspace/catalog.py` | 159 | function | `CognitiveWorkspaceCatalog.search` | search |
| `artifacts/architecture_contract_20260724_015711/core/cognition/workspace/catalog.py` | 298 | function | `CognitiveWorkspaceCatalog.search_workspaces` | catalog, search |
| `artifacts/architecture_contract_20260724_015711/core/cognition/workspace/models.py` | 47 | class | `EvidenceReference` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/workspace/models.py` | 137 | function | `Hypothesis.attach_evidence` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/cognition/workspace/service.py` | 62 | function | `CognitiveWorkspaceService.attach_evidence` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/engineering/contracts.py` | 78 | class | `VerificationEvidence` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/engineering/enums.py` | 28 | class | `EvidenceStatus` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/engineering/errors.py` | 10 | class | `EngineeringEvidenceError` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/engineering/public_surface.py` | 42 | function | `StaticPublicSurfaceEvaluator.evaluate` | source |
| `artifacts/architecture_contract_20260724_015711/core/evidence/contracts.py` | 173 | class | `SerializableContract` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/evidence/contracts.py` | 281 | class | `EvidenceAssessment` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/evidence/contracts.py` | 301 | class | `EvidenceRecord` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/evidence/contracts.py` | 337 | class | `EvidenceRelationship` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/evidence/contracts.py` | 372 | class | `EvidenceGap` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/evidence/contracts.py` | 390 | class | `EvidenceSet` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/evidence/enums.py` | 22 | class | `EvidenceDirection` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/evidence/enums.py` | 32 | class | `EvidenceStatus` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/evidence/enums.py` | 47 | class | `AdmissibilityStatus` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/evidence/enums.py` | 76 | class | `EvidenceRelationshipType` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/evidence/enums.py` | 89 | class | `EvidenceDirectness` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/evidence/enums.py` | 99 | class | `SourceReliabilityClass` | source |
| `artifacts/architecture_contract_20260724_015711/core/evidence/enums.py` | 115 | class | `EvidenceGapType` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/evidence/enums.py` | 132 | class | `EvidenceSufficiencyStatus` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/evidence/enums.py` | 163 | class | `AssessmentMethod` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/evidence/enums.py` | 173 | class | `IntegrityStatus` | evidence, source |
| `artifacts/architecture_contract_20260724_015711/core/evidence/errors.py` | 10 | class | `EvidenceError` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/evidence/errors.py` | 44 | class | `EvidenceValidationError` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/evidence/errors.py` | 50 | class | `EvidenceAdmissibilityError` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/evidence/errors.py` | 56 | class | `EvidenceConstructionError` | evidence |
| `artifacts/architecture_contract_20260724_015711/core/evidence/errors.py` | 62 | class | `EvidenceIntegrityError` | evidence, provenance |
| `artifacts/architecture_contract_20260724_015711/core/evidence/errors.py` | 68 | class | `EvidenceConflictError` | evidence |

## API Routes

| Method | Route | Function | Source |
|---|---|---|---|
| POST | `/api/conversation/query` | `conversation_query` | `core/src/routes/api.py:82` |
| GET | `/api/conversation/sessions/{session_id}` | `conversation_session` | `core/src/routes/api.py:93` |
| GET | `/api/conversation/sessions/{session_id}/messages` | `conversation_messages` | `core/src/routes/api.py:101` |
| POST | `/ask` | `ask` | `core/src/routes/api.py:74` |
| GET | `/bridge` | `executive_bridge_snapshot` | `core/src/routes/operations.py:161` |
| GET | `/bridge` | `commanders_bridge` | `core/src/routes/mission_control.py:13` |
| GET | `/bridge/manifest` | `executive_bridge_manifest` | `core/src/routes/operations.py:171` |
| GET | `/bridge/projections/{projection_id}` | `executive_bridge_projection` | `core/src/routes/operations.py:176` |
| GET | `/bridge/readiness` | `executive_bridge_readiness` | `core/src/routes/operations.py:166` |
| GET | `/capabilities` | `operations_capabilities` | `core/src/routes/operations.py:133` |
| GET | `/capabilities/{capability_name}` | `operations_capability` | `core/src/routes/operations.py:140` |
| POST | `/conversation` | `knowledge_workspace_conversation` | `core/src/routes/knowledge_workspace.py:27` |
| GET | `/event-runtime` | `executive_event_runtime_status` | `core/src/routes/executive_event_runtime.py:27` |
| GET | `/events` | `operations_events` | `core/src/routes/operations.py:95` |
| GET | `/executive` | `operations_executive` | `core/src/routes/operations.py:48` |
| GET | `/health` | `operations_health` | `core/src/routes/operations.py:55` |
| GET | `/mission-control` | `commanders_bridge` | `core/src/routes/mission_control.py:14` |
| GET | `/missions` | `operations_missions` | `core/src/routes/operations.py:60` |
| GET | `/projections` | `operations_projections` | `core/src/routes/operations.py:109` |
| GET | `/projections/{projection_id}` | `operations_projection` | `core/src/routes/operations.py:120` |
| GET | `/resources` | `operations_resources` | `core/src/routes/operations.py:68` |
| GET | `/status` | `operations_status` | `core/src/routes/operations.py:43` |
| GET | `/timeline` | `operations_timeline` | `core/src/routes/operations.py:73` |
| GET | `/transparency` | `operations_transparency` | `core/src/routes/operations.py:82` |

## Knowledge Database

| Table | Rows | Columns |
|---|---:|---|
| `catalog_documents` | 3684 | id, file_path, sha256, title, file_type, size_bytes, source_name, collection_id, created_at, updated_at, detected_type, inspection_reason, readable, content_chars |
| `catalog_enrichment` | 794 | object_uuid, aliases, search_terms, entities, topics, enrichment_json, status, error, enriched_at |
| `chunk_concepts` | 9 | id, chunk_uuid, file_path, concept, concept_type, domain, confidence, evidence, extractor, created_at |
| `chunk_embeddings` | 5 | chunk_uuid, provider, model, dimensions, vector_json, created_at |
| `chunks` | 0 | id, document_path, chunk_index, text, source_page, structure_title, created_at |
| `collection_documents` | 3655 | collection_id, file_path, sha256, confidence, assigned_by, created_at |
| `concepts` | 0 | id, name, document_path, chunk_id, confidence, created_at |
| `document_assimilation` | 3684 | file_path, sha256, title, domain, discipline, subject, collection_id, confidence, evidence_json, content_chars, assigned_by, updated_at |
| `document_chunks` | 5 | chunk_uuid, file_path, chunk_index, chunk_type, heading, text, char_count, checksum, embedding_state, created_at, concept_state |
| `document_concepts` | 0 | file_path, sha256, concept, confidence, assigned_by, created_at |
| `document_keywords` | 0 | file_path, keyword, confidence, assigned_by, created_at |
| `document_pages` | 0 | id, document_path, page_number, text, extracted_at |
| `document_pages_fts` | 0 | document_path, page_number, text |
| `document_pages_fts_config` | 1 | k, v |
| `document_pages_fts_content` | 0 | id, c0, c1, c2 |
| `document_pages_fts_data` | 2 | id, block |
| `document_pages_fts_docsize` | 0 | id, sz |
| `document_pages_fts_idx` | 0 | segid, term, pgno |
| `document_relationships` | 0 | id, from_document_id, to_document_id, relationship_type, notes, created_at |
| `document_structure` | 0 | id, document_path, title, level, page, order_index, parent_title, source, created_at |
| `document_subjects` | 3572 | file_path, sha256, subject, confidence, assigned_by, created_at |
| `document_text` | 14 | file_path, text, extractor, content_chars, checksum, status, error, extracted_at |
| `document_topics` | 0 | document_id, topic_id, confidence, created_at |
| `documents` | 0 | id, title, document_type, language, publication_year, edition, source_id, trust_score, quality_score, status, created_at, updated_at, sha256, relative_path, filename, extension, size_bytes, modified_time, category, first_seen, last_seen |
| `knowledge_index` | 0 | document_path, filename, extension, category, provider, title, author, subject, keywords, pages, toc_entries, structure_terms, language, fingerprint, indexed_at |
| `knowledge_registry` | 897 | id, object_uuid, object_path, object_type, title, status, lifecycle_state, validation_state, assimilation_state, source, trust_level, duplicate_of, notes, registered_at, updated_at, canonical_type, canonical_confidence, canonical_reason |
| `librarian_catalog` | 794 | object_uuid, object_path, object_type, canonical_title, display_title, subject, subject_confidence, subject_reason, keywords, language, description, quality_score, work_key, duplicate_group, metadata_json, cataloged_at, updated_at |
| `library_catalog` | 0 | document_path, filename, extension, category, provider, title, subtitle, author, publisher, publication_year, edition, isbn, subject, keywords, language, pages, fingerprint, cataloged_at |
| `resource_inspections` | 794 | object_uuid, object_path, object_type, title, description, language, primary_subject, keywords, metadata_json, status, error, inspected_at |
| `runtime_chunks` | 4674 | id, document_id, chunk_index, chunk_text, start_char, end_char, token_estimate, content_sha256, created_at |
| `runtime_chunks_fts` | 4674 | chunk_text, title, file_path, document_id, chunk_id |
| `runtime_chunks_fts_config` | 1 | k, v |
| `runtime_chunks_fts_content` | 4674 | id, c0, c1, c2, c3, c4 |
| `runtime_chunks_fts_data` | 1461 | id, block |
| `runtime_chunks_fts_docsize` | 4674 | id, sz |
| `runtime_chunks_fts_idx` | 1593 | segid, term, pgno |
| `runtime_documents` | 69 | id, file_path, sha256, title, media_type, content_text, content_chars, materialized_at, updated_at |
| `sources` | 17 | id, name, trust_tier, source_type, base_url, notes, created_at, updated_at |
| `topics` | 90 | id, path, name, parent_path, desired_depth, created_at, updated_at |

## Recommended IX-A4 Boundary

1. Preserve the existing conversation, grounding, awareness, materialization, and UI contracts.
2. Select one canonical query-planning owner.
3. Consolidate existing FTS, embedding, vector, and ranking implementations.
4. Add new retrieval code only where this audit proves a gap.
5. Project actual evidence, confidence, trace, and provenance into Mission Control.
6. Require grounded-answer end-to-end acceptance tests.

## Findings and Actions

### EMBEDDING-ASSETS — Embedding storage already exists

- **Severity:** info
- **Detail:** chunk_embeddings=5
- **Recommendation:** Audit producers, dimensions, models, and consumers before adding a new vector store.

### EXISTING-CatalogGroundingService — Existing catalog grounding component found

- **Severity:** info
- **Detail:** CatalogGroundingService already exists.
- **Recommendation:** Reuse and certify it before adding another implementation.

### EXISTING-ExecutiveConversationOrchestrator — Existing conversation orchestration component found

- **Severity:** info
- **Detail:** ExecutiveConversationOrchestrator already exists.
- **Recommendation:** Reuse and certify it before adding another implementation.

### EXISTING-ExecutiveKnowledgeAwarenessService — Existing knowledge awareness component found

- **Severity:** info
- **Detail:** ExecutiveKnowledgeAwarenessService already exists.
- **Recommendation:** Reuse and certify it before adding another implementation.

### EXISTING-RuntimeKnowledgeMaterializer — Existing runtime materialization component found

- **Severity:** info
- **Detail:** RuntimeKnowledgeMaterializer already exists.
- **Recommendation:** Reuse and certify it before adding another implementation.

### LIVE-GROUNDING-ACTIVE — Grounding is active in the live composition

- **Severity:** info
- **Detail:** The orchestrator uses CatalogGroundingService.
- **Recommendation:** Preserve this integration seam.

### RANKING-REFERENCES — Ranking-related code already exists

- **Severity:** info
- **Detail:** 1025 ranking references were identified.
- **Recommendation:** Inspect and consolidate existing ranking implementations.

### RUNTIME-CORPUS — Runtime corpus inventory

- **Severity:** info
- **Detail:** runtime_documents=69, runtime_chunks=4674.
- **Recommendation:** Audit retrieval quality next.
