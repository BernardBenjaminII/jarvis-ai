# Genesis IX-A4.1A — Executive Duplicate Report

## Conversation Services

Multiple similarly named classes exist. Runtime wiring and consumer analysis must determine whether these are canonical objects, adapters, compatibility layers, or duplicates.

- `ExecutiveConversationService (core/conversation/service.py:24)`
- `ExecutiveConversationService (jarvis_convergence_c1/payload/core/conversation/service.py:23)`
- `ExecutiveConversationService (jarvis_convergence_c2/payload/core/conversation/service.py:24)`
- `ExecutiveConversationServiceTests (jarvis_convergence_c1/payload/tests/test_convergence_c1_executive_conversation.py:27)`
- `ExecutiveConversationServiceTests (tests/test_convergence_c1_executive_conversation.py:27)`

## Orchestrators

Multiple similarly named classes exist. Runtime wiring and consumer analysis must determine whether these are canonical objects, adapters, compatibility layers, or duplicates.

- `CapabilityOrchestrator (core/executive/capabilities/orchestrator.py:13)`
- `ExecutionOrchestratorError (core/cognition/execution_orchestrator/errors.py:1)`
- `ExecutionOrchestratorError (genesis_iv_a9/core/cognition/execution_orchestrator/errors.py:1)`
- `ExecutiveConversationOrchestrator (core/conversation/orchestrator.py:69)`
- `ExecutiveConversationOrchestrator (jarvis_convergence_c2/payload/core/conversation/orchestrator.py:58)`
- `ExecutiveConversationOrchestrator (jarvis_convergence_c4/payload/core/conversation/orchestrator.py:59)`
- `ExecutiveConversationOrchestrator (jarvis_convergence_c5/payload/core/conversation/orchestrator.py:64)`
- `ExecutiveConversationOrchestrator (jarvis_convergence_c6/payload/core/conversation/orchestrator.py:69)`
- `ExecutiveExecutionOrchestrator (core/cognition/execution_orchestrator/orchestrator.py:35)`
- `ExecutiveExecutionOrchestrator (genesis_iv_a9/core/cognition/execution_orchestrator/orchestrator.py:35)`

## Compilers

Multiple similarly named classes exist. Runtime wiring and consumer analysis must determine whether these are canonical objects, adapters, compatibility layers, or duplicates.

- `ExecutiveMissionCompiler (core/cognition/mission_compiler/compiler.py:31)`
- `ExecutiveMissionCompiler (genesis_iv_a8/core/cognition/mission_compiler/compiler.py:31)`
- `ExecutiveRequestCompiler (core/conversation/compiler.py:20)`
- `ExecutiveRequestCompiler (jarvis_convergence_c1/payload/core/conversation/compiler.py:20)`
- `ExecutiveRequestCompilerTests (jarvis_convergence_c1/payload/tests/test_convergence_c1_executive_conversation.py:12)`
- `ExecutiveRequestCompilerTests (tests/test_convergence_c1_executive_conversation.py:12)`
- `MissionCompilerError (core/cognition/mission_compiler/errors.py:1)`
- `MissionCompilerError (genesis_iv_a8/core/cognition/mission_compiler/errors.py:1)`

## Repositories

Multiple similarly named classes exist. Runtime wiring and consumer analysis must determine whether these are canonical objects, adapters, compatibility layers, or duplicates.

- `AcquisitionMissionRepository (knowledge_engine/acquisition/missions/repository.py:19)`
- `AssessmentRepository (core/cognition/evidence_correlation/contracts.py:14)`
- `AssessmentRepositoryClosedError (core/cognition/evidence_correlation/errors.py:22)`
- `AssimilationDispatchRepository (knowledge_engine/acquisition/dispatch/repository.py:35)`
- `AssimilationHandoffRepository (knowledge_engine/acquisition/handoff/repository.py:18)`
- `CatalogRepository (core/knowledge_catalog/repository.py:8)`
- `CheckpointRepository (core/executive/persistence/recovery.py:148)`
- `CheckpointRepository (core/executive/persistence/repository.py:60)`
- `CheckpointRepositoryError (core/executive/persistence/repository.py:31)`
- `CheckpointRepositoryProtocol (core/executive/persistence/scanner.py:8)`
- `CognitiveWorkspaceRepository (core/cognition/workspace/repository.py:40)`
- `CognitiveWorkspaceRepositoryError (core/cognition/workspace/repository.py:28)`
- `ConstitutionalRepositoryProjection (core/governance/constitution/coverage/graph/repository_graph.py:4)`
- `ConstitutionalRepositoryProjectionEngine (core/governance/constitution/coverage/graph/repository_engine.py:10)`
- `ConstitutionalRepositoryProjectionReporter (core/governance/constitution/coverage/graph/repository_reporting.py:7)`
- `ConstitutionalRepositoryQueryService (core/governance/constitution/coverage/graph/repository_queries.py:2)`
- `ConversationRepository (core/conversation/repository.py:13)`
- `ConversationRepository (jarvis_convergence_c1/payload/core/conversation/repository.py:13)`
- `CourseOfActionRepository (core/cognition/coa/contracts.py:16)`
- `DecisionRepository (core/cognition/decision/contracts.py:21)`
- `DecisionRepositoryClosedError (core/cognition/decision/errors.py:13)`
- `DecisionRepositoryDisposition (core/cognition/decision/enums.py:14)`
- `DemoRepository (dev/demo_genesis_vi_a64.py:58)`
- `ExecutiveTimelineRepository (core/executive/timeline/repository.py:20)`
- `FileCheckpointRepository (core/executive/persistence/repository.py:84)`
- `GenesisIVR0ARepositorySkeletonTests (tests/cognition/test_genesis_4r0a_repository_skeleton.py:75)`
- `GovernmentSnapshotRepository (core/government/registry/repository.py:76)`
- `HypothesisRepository (core/cognition/hypothesis/contracts.py:13)`
- `HypothesisRepositoryClosedError (core/cognition/hypothesis/errors.py:18)`
- `InMemoryAssessmentRepository (core/cognition/evidence_correlation/repository.py:15)`
- `InMemoryCourseOfActionRepository (core/cognition/coa/repository.py:5)`
- `InMemoryDecisionRepository (core/cognition/decision/repository.py:7)`
- `InMemoryHypothesisRepository (core/cognition/hypothesis/repository.py:15)`
- `InMemoryObservationRepository (core/cognition/observation/repository.py:9)`
- `InMemoryPlanRepository (core/executive/planning/repository.py:44)`
- `InMemoryReasoningRepository (core/cognition/reasoner/repository.py:15)`
- `InMemorySituationRepository (core/cognition/situation/repository.py:27)`
- `KnowledgeRegistryRepository (knowledge_engine/assimilation/repositories/knowledge_registry.py:39)`
- `ObjectRepository (core/government/registry/repository.py:17)`
- `ObservationRepositoryClosedError (core/cognition/observation/errors.py:5)`
- `PlanRepository (core/executive/planning/repository.py:16)`
- `ProvenanceRepository (knowledge_engine/acquisition/provenance/repository.py:18)`
- `ReasoningRepository (core/cognition/reasoner/contracts.py:34)`
- `ReasoningRepositoryClosedError (core/cognition/reasoner/errors.py:22)`
- `ReasoningRepositoryDisposition (core/cognition/reasoner/enums.py:25)`
- `RelationshipRepository (core/government/registry/repository.py:47)`
- `Repository (tests/test_genesis_vi_a68_part_b.py:17)`
- `RepositoryAccessError (core/executive/timeline/query_engine.py:20)`
- `RepositoryArtifact (core/governance/constitution/repository_audit/models.py:24)`
- `RepositoryArtifactAssessment (core/governance/constitution/repository_audit/models.py:42)`
- `RepositoryAuditAssessment (core/governance/constitution/repository_audit/models.py:93)`
- `RepositoryAuditDiscoveryError (core/governance/constitution/repository_audit/discovery.py:10)`
- `RepositoryAuditFixture (tests/test_genesis_vii_c0_pack1b.py:17)`
- `RepositoryAuditManifest (core/governance/audit/verification.py:62)`
- `RepositoryAuditPolicy (core/governance/constitution/repository_audit/models.py:8)`
- `RepositoryAuditStatistics (core/governance/constitution/repository_audit/models.py:74)`
- `RepositoryConstitutionalAuditEngine (core/governance/constitution/repository_audit/engine.py:20)`
- `RepositoryConstitutionalAuditReporter (core/governance/constitution/repository_audit/reporting.py:9)`
- `RepositoryConstitutionalAuditTests (tests/test_genesis_vii_c4_2_repository_constitutional_audit.py:67)`
- `RepositoryCoverageStatus (core/governance/constitution/coverage/contracts.py:12)`
- `RepositoryEdge (core/governance/constitution/coverage/graph/repository_models.py:20)`
- `RepositoryEdgeKind (core/governance/constitution/coverage/graph/repository_contracts.py:18)`
- `RepositoryFile (core/governance/audit/models.py:53)`
- `RepositoryHealth (core/governance/audit/verification.py:32)`
- `RepositoryIntegrationAuditor (core/integration/audit.py:10)`
- `RepositoryIntegrationAuditor (genesis_iv_b1/core/integration/audit.py:10)`
- `RepositoryIntegrationAuditor (genesis_iv_b1_rc1/core/integration/audit.py:10)`
- `RepositoryIntegrityStatus (core/executive/timeline/repository_contracts.py:42)`
- `RepositoryInventory (core/governance/audit/models.py:162)`
- `RepositoryInventoryBuilder (core/governance/audit/inventory.py:16)`
- `RepositoryInventoryVerifier (core/governance/audit/verification.py:75)`
- `RepositoryLifecycleState (core/governance/constitution/coverage/graph/repository_contracts.py:27)`
- `RepositoryNode (core/governance/constitution/coverage/graph/repository_models.py:7)`
- `RepositoryNodeKind (core/governance/constitution/coverage/graph/repository_contracts.py:6)`
- `RepositoryNotFoundError (core/certification/runtime/contracts.py:11)`
- `RepositoryPolicy (core/executive/persistence/repository.py:48)`
- `RepositoryProjectionAssessment (core/governance/constitution/coverage/graph/repository_models.py:78)`
- `RepositoryProjectionIntegrity (core/governance/constitution/coverage/graph/repository_models.py:33)`
- `RepositoryProjectionMetrics (core/governance/constitution/coverage/graph/repository_models.py:57)`
- `RepositoryProjectionTests (tests/test_genesis_vii_c4_3_pack3b2a_repository_projection.py:18)`
- `RepositoryRealityModelingTests (tests/test_genesis_5e1a_repository_reality_modeling.py:14)`
- `RepositoryStatistics (core/governance/audit/models.py:139)`
- `RepositoryVerificationReport (core/governance/audit/verification.py:45)`
- `SQLiteCognitiveWorkspaceRepository (core/cognition/workspace/repository.py:220)`
- `SQLiteSourceRegistryRepository (knowledge_engine/source_registry/repository.py:16)`
- `SituationRepository (core/cognition/situation/contracts.py:13)`
- `SituationRepositoryClosedError (core/cognition/situation/errors.py:18)`
- `TestGenesis3A2PersistentWorkspaceRepository (tests/test_genesis_3a2_persistent_workspace_repository.py:16)`
- `TimelineRepositoryConflictError (core/executive/timeline/repository_contracts.py:34)`
- `TimelineRepositoryError (core/executive/timeline/repository_contracts.py:26)`
- `TimelineRepositoryIndexes (core/executive/timeline/indexes.py:14)`
- `TimelineRepositoryIntegrityError (core/executive/timeline/repository_contracts.py:38)`
- `TimelineRepositoryIntegrityReport (core/executive/timeline/repository_contracts.py:99)`
- `TimelineRepositoryStatistics (core/executive/timeline/repository_contracts.py:48)`
- `TimelineRepositoryStorageError (core/executive/timeline/repository_contracts.py:30)`
- `_PrefixRepository (core/executive/persistence/recovery.py:152)`

## Request Models

Multiple similarly named classes exist. Runtime wiring and consumer analysis must determine whether these are canonical objects, adapters, compatibility layers, or duplicates.

- `AcquisitionRequest (knowledge_engine/acquisition/models.py:29)`
- `AssignmentRequest (core/government/executive/contracts.py:202)`
- `DecisionRequest (core/cognition/executive_decision/contracts.py:46)`
- `DecisionRequest (genesis_iv_a7/core/cognition/executive_decision/contracts.py:46)`
- `DirectiveRequest (core/government/executive/contracts.py:162)`
- `DirectorRequest (knowledge_engine/director/models.py:9)`
- `ExecutiveRequestCompiler (core/conversation/compiler.py:20)`
- `ExecutiveRequestCompiler (jarvis_convergence_c1/payload/core/conversation/compiler.py:20)`
- `ExecutiveRequestCompilerTests (jarvis_convergence_c1/payload/tests/test_convergence_c1_executive_conversation.py:12)`
- `ExecutiveRequestCompilerTests (tests/test_convergence_c1_executive_conversation.py:12)`
- `ExecutiveRequestContext (core/conversation/contracts.py:42)`
- `ExecutiveRequestContext (jarvis_convergence_c1/payload/core/conversation/contracts.py:42)`
- `InvalidReasoningRequestError (core/reasoning/errors.py:10)`
- `MissionCompilationRequest (core/cognition/mission_compiler/contracts.py:110)`
- `MissionCompilationRequest (genesis_iv_a8/core/cognition/mission_compiler/contracts.py:110)`
- `MissionExecutionRequest (core/cognition/execution_orchestrator/contracts.py:62)`
- `MissionExecutionRequest (genesis_iv_a9/core/cognition/execution_orchestrator/contracts.py:62)`
- `ReasoningRequest (core/reasoning/models.py:143)`
- `RecoveryRequest (core/executive/persistence/contracts.py:241)`
- `RepresentationRequest (core/representation/director.py:39)`
- `SegmentationRequest (core/representation/contracts.py:99)`
- `WorkspaceConversationRequest (core/executive/conversation/contracts.py:15)`
- `WorkspaceIntegrationRequest (core/cognition/integration/contracts.py:80)`

## Response Models

Multiple similarly named classes exist. Runtime wiring and consumer analysis must determine whether these are canonical objects, adapters, compatibility layers, or duplicates.

- `DirectorResponse (knowledge_engine/director/models.py:17)`
- `ExecutiveConversationResponse (core/conversation/contracts.py:134)`
- `ExecutiveConversationResponse (jarvis_convergence_c1/payload/core/conversation/contracts.py:134)`
- `SearchResponse (knowledge_engine/search/service.py:46)`
- `WorkspaceConversationResponse (core/executive/conversation/contracts.py:44)`

## Trace Models

Multiple similarly named classes exist. Runtime wiring and consumer analysis must determine whether these are canonical objects, adapters, compatibility layers, or duplicates.

- `ConversationTraceEvent (core/conversation/contracts.py:87)`
- `ConversationTraceEvent (jarvis_convergence_c1/payload/core/conversation/contracts.py:87)`
- `DecisionTrace (core/cognition/executive_decision/contracts.py:36)`
- `DecisionTrace (genesis_iv_a7/core/cognition/executive_decision/contracts.py:36)`
- `EndToEndRetrievalTracer (core/retrieval/certification/tracer.py:48)`
- `KnowledgeGapPropagationTracer (core/retrieval/gap_trace/tracer.py:69)`
- `MissionTrace (core/cognition/mission_compiler/contracts.py:218)`
- `MissionTrace (genesis_iv_a8/core/cognition/mission_compiler/contracts.py:218)`
- `ReasoningTraceStep (core/reasoning/models.py:207)`
- `SelectionTrace (core/executive/capabilities/models.py:125)`
- `TraceabilityRecord (core/governance/constitution/ratification/models.py:64)`

## Session Models

Multiple similarly named classes exist. Runtime wiring and consumer analysis must determine whether these are canonical objects, adapters, compatibility layers, or duplicates.

- `ExecutiveSession (core/cognition/session.py:78)`
- `ExecutiveSession (core/executive/lifecycle/contracts.py:87)`
- `ExecutiveSessionEvent (core/cognition/session.py:27)`
- `ExecutiveSessionSnapshot (core/cognition/session.py:46)`
- `ExecutiveSessionStatus (core/cognition/session.py:17)`
- `ExecutiveSessionStatus (core/executive/lifecycle/contracts.py:59)`
- `ExecutiveSessionTests (tests/test_genesis_vi_a5_executive_session.py:21)`
- `InvalidReasoningSessionTransitionError (core/reasoning/session/errors.py:10)`
- `ReasoningSession (core/reasoning/session/contracts.py:147)`
- `ReasoningSessionContractError (core/reasoning/session/errors.py:20)`
- `ReasoningSessionId (core/reasoning/session/contracts.py:53)`
- `ReasoningSessionLifecycle (core/reasoning/session/lifecycle.py:76)`
- `ReasoningSessionLifecycleError (core/reasoning/session/errors.py:6)`
- `ReasoningSessionMetadata (core/reasoning/session/contracts.py:89)`
- `ReasoningSessionState (core/reasoning/session/contracts.py:17)`
- `SessionAlreadyActiveError (core/executive/lifecycle/contracts.py:39)`
- `SessionAttribute (core/reasoning/session/contracts.py:35)`
- `SessionNotActiveError (core/executive/lifecycle/contracts.py:43)`
- `TerminalReasoningSessionError (core/reasoning/session/errors.py:14)`
