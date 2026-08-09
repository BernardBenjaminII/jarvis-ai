# Genesis IX-A4.1A — Executive Component Matrix

| Component | Live | Domains | Source |
|---|---|---|---|
| `AcademyContractValidationError` | no | executive | `core/academy/errors.py:12` |
| `AcademyDormantError` | no | executive, request | `core/academy/errors.py:8` |
| `AcquisitionMissionRepository` | no | repository | `knowledge_engine/acquisition/missions/repository.py:19` |
| `AcquisitionRequest` | no | request | `knowledge_engine/acquisition/models.py:29` |
| `AdmissionDirector` | no | director | `knowledge_engine/acquisition/admission/director.py:38` |
| `AssessmentDisposition` | no | repository | `core/cognition/evidence_correlation/enums.py:36` |
| `AssessmentNotFoundError` | no | request | `core/cognition/evidence_correlation/errors.py:18` |
| `AssessmentQuery` | no | repository | `core/cognition/evidence_correlation/models.py:310` |
| `AssessmentRepository` | no | repository | `core/cognition/evidence_correlation/contracts.py:14` |
| `AssessmentRepositoryClosedError` | no | repository | `core/cognition/evidence_correlation/errors.py:22` |
| `AssignmentRequest` | no | request | `core/government/executive/contracts.py:202` |
| `AssimilationDirector` | no | director | `knowledge_engine/assimilation/director.py:35` |
| `AssimilationDirector` | no | director | `knowledge_engine/director/director.py:8` |
| `AssimilationDispatchRepository` | no | repository | `knowledge_engine/acquisition/dispatch/repository.py:35` |
| `AssimilationDispatchResult` | no | dispatcher | `knowledge_engine/acquisition/dispatch/models.py:18` |
| `AssimilationHandler` | no | director | `knowledge_engine/assimilation/handlers/base.py:8` |
| `AssimilationHandoffRecord` | no | request | `knowledge_engine/acquisition/handoff/models.py:28` |
| `AssimilationHandoffRepository` | no | repository | `knowledge_engine/acquisition/handoff/repository.py:18` |
| `AssimilationPlanner` | no | planner | `knowledge_engine/assimilation/planner.py:23` |
| `AttentionCandidate` | no | executive, request | `core/cognition/models.py:67` |
| `AttentionReason` | no | executive | `core/cognition/enums.py:54` |
| `BootstrapRunner` | no | orchestrator | `core/bootstrap/runner.py:7` |
| `CanonicalAssimilationDispatcher` | no | dispatcher | `knowledge_engine/acquisition/dispatch/service.py:34` |
| `CanonicalSnapshotSerializer` | no | executive | `core/executive/persistence/serializer.py:46` |
| `CapabilityEventPublisher` | no | executive | `core/executive/events/publishers.py:117` |
| `CapabilityOrchestrator` | no | orchestrator | `core/executive/capabilities/orchestrator.py:13` |
| `CapabilityPlanner` | no | planner | `core/executive/capabilities/planner.py:11` |
| `CapabilityRegistry` | no | executive | `core/integration/registry.py:15` |
| `CatalogGroundingService` | yes | grounding | `core/conversation/grounding.py:134` |
| `CatalogGroundingService` | yes | grounding | `jarvis_convergence_c4/payload/core/conversation/grounding.py:130` |
| `CatalogRepository` | no | repository | `core/knowledge_catalog/repository.py:8` |
| `CheckpointConflictError` | no | repository | `core/executive/persistence/repository.py:39` |
| `CheckpointDescriptor` | no | executive | `core/executive/persistence/contracts.py:161` |
| `CheckpointHistoryError` | no | repository, session | `core/executive/persistence/repository.py:43` |
| `CheckpointNotFoundError` | no | repository, request | `core/executive/persistence/repository.py:35` |
| `CheckpointReason` | no | executive, request | `core/executive/persistence/contracts.py:59` |
| `CheckpointRepository` | no | repository | `core/executive/persistence/recovery.py:148` |
| `CheckpointRepository` | no | repository | `core/executive/persistence/repository.py:60` |
| `CheckpointRepositoryError` | no | repository | `core/executive/persistence/repository.py:31` |
| `CheckpointRepositoryProtocol` | no | repository | `core/executive/persistence/scanner.py:8` |
| `CognitionCycleController` | no | controller | `core/cognition/cycle.py:26` |
| `CognitiveCycleStatus` | no | executive | `core/cognition/enums.py:27` |
| `CognitiveEvent` | no | executive | `core/cognition/models.py:159` |
| `CognitiveEventKind` | no | executive | `core/cognition/enums.py:68` |
| `CognitiveState` | no | executive | `core/cognition/enums.py:8` |
| `CognitiveStateMachine` | no | controller, executive | `core/cognition/state_machine.py:188` |
| `CognitiveWorkspaceCatalog` | no | repository | `core/cognition/workspace/catalog.py:140` |
| `CognitiveWorkspaceConflictError` | no | repository | `core/cognition/workspace/repository.py:36` |
| `CognitiveWorkspaceIntegrationDirector` | no | director, executive | `core/cognition/integration/director.py:10` |
| `CognitiveWorkspaceNotFoundError` | no | repository, request | `core/cognition/workspace/repository.py:32` |
| `CognitiveWorkspaceRepository` | no | repository | `core/cognition/workspace/repository.py:40` |
| `CognitiveWorkspaceRepositoryError` | no | repository | `core/cognition/workspace/repository.py:28` |
| `CollectionExpansionPlanner` | no | planner | `knowledge_engine/assimilation/collection_plan.py:173` |
| `ConstitutionalDirectorateFoundationEngine` | no | director | `core/governance/constitution/coverage/graph/directorate_foundation.py:13` |
| `ConstitutionalDirectorateGraph` | no | director | `core/governance/constitution/coverage/graph/directorate_graph.py:10` |
| `ConstitutionalDirectorateProjectionEngine` | no | director | `core/governance/constitution/coverage/graph/directorate_projection.py:14` |
| `ConstitutionalDirectorateProjectionReporter` | no | director | `core/governance/constitution/coverage/graph/directorate_reporting.py:17` |
| `ConstitutionalDirectorateQueryService` | no | director | `core/governance/constitution/coverage/graph/directorate_queries.py:6` |
| `ConstitutionalExtractionEngine` | no | repository | `core/governance/constitution/extraction/engine.py:35` |
| `ConstitutionalRepositoryProjection` | no | repository | `core/governance/constitution/coverage/graph/repository_graph.py:4` |
| `ConstitutionalRepositoryProjectionEngine` | no | repository | `core/governance/constitution/coverage/graph/repository_engine.py:10` |
| `ConstitutionalRepositoryProjectionReporter` | no | repository | `core/governance/constitution/coverage/graph/repository_reporting.py:7` |
| `ConstitutionalRepositoryQueryService` | no | repository | `core/governance/constitution/coverage/graph/repository_queries.py:2` |
| `ConversationHTTPContractTests` | no | conversation | `jarvis_convergence_c1/payload/tests/test_convergence_c1_http_contract.py:11` |
| `ConversationHTTPContractTests` | no | conversation | `jarvis_convergence_c2a/payload/tests/test_convergence_c1_http_contract.py:28` |
| `ConversationHTTPContractTests` | no | conversation | `jarvis_convergence_c4a/payload/tests/test_convergence_c1_http_contract.py:28` |
| `ConversationHTTPContractTests` | no | conversation | `tests/test_convergence_c1_http_contract.py:28` |
| `ConversationMessage` | no | conversation | `core/conversation/contracts.py:99` |
| `ConversationMessage` | no | conversation | `jarvis_convergence_c1/payload/core/conversation/contracts.py:99` |
| `ConversationQuery` | no | conversation | `core/src/routes/api.py:66` |
| `ConversationQuery` | no | conversation | `jarvis_convergence_c1/payload/core/src/routes/api.py:37` |
| `ConversationQuery` | no | conversation | `jarvis_convergence_c2/payload/core/src/routes/api.py:49` |
| `ConversationQuery` | no | conversation | `jarvis_convergence_c4/payload/core/src/routes/api.py:63` |
| `ConversationQuery` | no | conversation | `jarvis_convergence_c5/payload/core/src/routes/api.py:66` |
| `ConversationRepository` | yes | conversation, repository | `core/conversation/repository.py:13` |
| `ConversationRepository` | yes | conversation, repository | `jarvis_convergence_c1/payload/core/conversation/repository.py:13` |
| `ConversationRole` | no | conversation | `core/conversation/contracts.py:15` |
| `ConversationRole` | no | conversation | `jarvis_convergence_c1/payload/core/conversation/contracts.py:15` |
| `ConversationState` | no | conversation | `core/conversation/contracts.py:21` |
| `ConversationState` | no | conversation | `jarvis_convergence_c1/payload/core/conversation/contracts.py:21` |
| `ConversationTraceEvent` | no | conversation, trace | `core/conversation/contracts.py:87` |
| `ConversationTraceEvent` | no | conversation, trace | `jarvis_convergence_c1/payload/core/conversation/contracts.py:87` |
| `CourseOfActionError` | no | executive | `core/cognition/coa/errors.py:1` |
| `CourseOfActionRepository` | no | repository | `core/cognition/coa/contracts.py:16` |
| `DecisionNotApprovedError` | no | compiler, executive | `core/cognition/mission_compiler/errors.py:17` |
| `DecisionNotApprovedError` | no | compiler, executive | `genesis_iv_a8/core/cognition/mission_compiler/errors.py:17` |
| `DecisionNotFoundError` | no | executive | `core/cognition/decision/errors.py:10` |
| `DecisionPolicyError` | no | executive | `core/cognition/executive_decision/errors.py:4` |
| `DecisionPolicyError` | no | executive | `genesis_iv_a7/core/cognition/executive_decision/errors.py:4` |
| `DecisionRepository` | no | repository | `core/cognition/decision/contracts.py:21` |
| `DecisionRepositoryClosedError` | no | executive, repository | `core/cognition/decision/errors.py:13` |
| `DecisionRepositoryDisposition` | no | repository | `core/cognition/decision/enums.py:14` |
| `DecisionRequest` | no | request | `core/cognition/executive_decision/contracts.py:46` |
| `DecisionRequest` | no | request | `genesis_iv_a7/core/cognition/executive_decision/contracts.py:46` |
| `DecisionTrace` | no | trace | `core/cognition/executive_decision/contracts.py:36` |
| `DecisionTrace` | no | trace | `genesis_iv_a7/core/cognition/executive_decision/contracts.py:36` |
| `DefaultExecutiveProvider` | no | executive | `core/operations/executive.py:9` |
| `DemoRepository` | no | repository | `dev/demo_genesis_vi_a64.py:58` |
| `DeterministicExecutiveReasoner` | no | executive | `core/cognition/reasoner/engine.py:21` |
| `DirectiveRequest` | no | request | `core/government/executive/contracts.py:162` |
| `Director` | no | director | `tests/test_genesis_ix_a4_3c_call_graph_reconstruction.py:4` |
| `DirectorActivationHttpTests` | no | director | `jarvis_convergence_c2/payload/tests/test_convergence_c2_http_contract.py:10` |
| `DirectorActivationHttpTests` | no | director | `jarvis_convergence_c2a/payload/tests/test_convergence_c2_http_contract.py:23` |
| `DirectorActivationHttpTests` | no | director | `jarvis_convergence_c4a/payload/tests/test_convergence_c2_http_contract.py:22` |
| `DirectorActivationHttpTests` | no | director | `tests/test_convergence_c2_http_contract.py:22` |
| `DirectorActivationTests` | no | director | `jarvis_convergence_c2/payload/tests/test_convergence_c2_director_activation.py:9` |
| `DirectorActivationTests` | no | director | `tests/test_convergence_c2_director_activation.py:9` |
| `DirectorAssignment` | no | director | `core/conversation/orchestrator.py:18` |
| `DirectorAssignment` | no | director | `jarvis_convergence_c2/payload/core/conversation/orchestrator.py:19` |
| `DirectorAssignment` | no | director | `jarvis_convergence_c4/payload/core/conversation/orchestrator.py:16` |
| `DirectorAssignment` | no | director | `jarvis_convergence_c5/payload/core/conversation/orchestrator.py:17` |
| `DirectorAssignment` | no | director | `jarvis_convergence_c6/payload/core/conversation/orchestrator.py:18` |
| `DirectorDescriptor` | no | director | `core/executive/capability_contracts.py:26` |
| `DirectorDispatchError` | no | director, dispatcher, executive | `core/executive/director_dispatch.py:8` |
| `DirectorEventPublisher` | no | director, executive | `core/executive/events/publishers.py:138` |
| `DirectorHandler` | no | director | `core/executive/contracts.py:10` |
| `DirectorNotRegisteredError` | no | director, executive | `core/executive/contracts.py:25` |
| `DirectorReadiness` | no | director | `core/executive/capability_contracts.py:10` |
| `DirectorRegistry` | no | director | `core/executive/registry.py:25` |
| `DirectorRequest` | no | director, request | `knowledge_engine/director/models.py:9` |
| `DirectorResponse` | no | director, response | `knowledge_engine/director/models.py:17` |
| `Directorate` | no | director | `core/government/models/objects.py:17` |
| `DirectorateAssignmentRule` | no | director | `core/governance/constitution/coverage/graph/directorate_assignment.py:13` |
| `DirectorateAuthorityResolver` | no | director | `core/governance/constitution/coverage/graph/directorate_authority.py:36` |
| `DirectorateCapabilityResolver` | no | director | `core/governance/constitution/coverage/graph/directorate_capabilities.py:23` |
| `DirectorateEdge` | no | director | `core/governance/constitution/coverage/graph/directorate_models.py:30` |
| `DirectorateEdgeKind` | no | director | `core/governance/constitution/coverage/graph/directorate_contracts.py:15` |
| `DirectorateFoundationAssessment` | no | director | `core/governance/constitution/coverage/graph/directorate_models.py:85` |
| `DirectorateFoundationTests` | no | director | `tests/test_genesis_vii_c4_3_pack3b2b1_directorate_foundation.py:37` |
| `DirectorateImpactAnalyzer` | no | director | `core/governance/constitution/coverage/graph/directorate_impact.py:20` |
| `DirectorateImpactAssessment` | no | director | `core/governance/constitution/coverage/graph/directorate_impact.py:9` |
| `DirectorateNode` | no | director | `core/governance/constitution/coverage/graph/directorate_models.py:10` |
| `DirectorateNodeKind` | no | director | `core/governance/constitution/coverage/graph/directorate_contracts.py:8` |
| `DirectorateProjectionIntegrity` | no | director | `core/governance/constitution/coverage/graph/directorate_models.py:50` |
| `DirectorateProjectionTests` | no | director | `tests/test_genesis_vii_c4_3_pack3b2b2_directorate_projection.py:128` |
| `DirectorateReviewEngine` | no | director | `core/governance/constitution/coverage/graph/directorate_review.py:14` |
| `Dispatcher` | no | dispatcher, request | `tools/dispatcher.py:6` |
| `EmptyMissionProvider` | no | executive | `core/operations/missions.py:20` |
| `EndToEndRetrievalTracer` | no | trace | `core/retrieval/certification/tracer.py:48` |
| `EvidenceClass` | no | repository | `core/governance/audit/models.py:20` |
| `EvidenceItem` | no | session | `core/reasoning/models.py:66` |
| `EvidenceNotFoundError` | no | request | `core/evidence/errors.py:122` |
| `EvidenceStateTransitionError` | no | request | `core/evidence/errors.py:98` |
| `ExecuteOnlyDirector` | no | director | `tests/test_genesis_ix_a4_4_runtime_integration.py:20` |
| `ExecutionApprovalRequiredError` | no | orchestrator | `core/cognition/execution_orchestrator/errors.py:17` |
| `ExecutionApprovalRequiredError` | no | orchestrator | `genesis_iv_a9/core/cognition/execution_orchestrator/errors.py:17` |
| `ExecutionOrchestratorError` | no | orchestrator | `core/cognition/execution_orchestrator/errors.py:1` |
| `ExecutionOrchestratorError` | no | orchestrator | `genesis_iv_a9/core/cognition/execution_orchestrator/errors.py:1` |
| `ExecutionPlan` | no | planner | `core/src/planner/execution_plan.py:8` |
| `ExecutiveAcademyBaseline` | no | executive | `core/academy/models.py:10` |
| `ExecutiveAcademyError` | no | executive | `core/academy/errors.py:4` |
| `ExecutiveAlternativeGenerationService` | no | executive | `core/cognition/coa/service.py:7` |
| `ExecutiveApiEnvelope` | no | executive | `core/integration/api.py:8` |
| `ExecutiveApiEnvelope` | no | executive | `genesis_iv_b1/core/integration/api.py:8` |
| `ExecutiveApiEnvelope` | no | executive | `genesis_iv_b1_rc1/core/integration/api.py:8` |
| `ExecutiveApiTests` | no | executive | `tests/test_genesis_vii_a0_pack2_executive_api.py:73` |
| `ExecutiveCheckpoint` | no | executive | `core/executive/persistence/checkpoint.py:93` |
| `ExecutiveContext` | no | executive | `core/cognition/models.py:179` |
| `ExecutiveConversationAdapter` | no | conversation, executive | `core/executive/conversation/adapter.py:71` |
| `ExecutiveConversationOrchestrator` | yes | conversation, director, executive, orchestrator, planner | `jarvis_convergence_c2/payload/core/conversation/orchestrator.py:58` |
| `ExecutiveConversationOrchestrator` | yes | conversation, executive, orchestrator, request | `core/conversation/orchestrator.py:69` |
| `ExecutiveConversationOrchestrator` | yes | conversation, executive, orchestrator, request | `jarvis_convergence_c4/payload/core/conversation/orchestrator.py:59` |
| `ExecutiveConversationOrchestrator` | yes | conversation, executive, orchestrator, request | `jarvis_convergence_c5/payload/core/conversation/orchestrator.py:64` |
| `ExecutiveConversationOrchestrator` | yes | conversation, executive, orchestrator, request | `jarvis_convergence_c6/payload/core/conversation/orchestrator.py:69` |
| `ExecutiveConversationResponse` | no | conversation, executive, response | `core/conversation/contracts.py:134` |
| `ExecutiveConversationResponse` | no | conversation, executive, response | `jarvis_convergence_c1/payload/core/conversation/contracts.py:134` |
| `ExecutiveConversationService` | yes | conversation, director, executive, orchestrator | `jarvis_convergence_c1/payload/core/conversation/service.py:23` |
| `ExecutiveConversationService` | yes | conversation, executive | `core/conversation/service.py:24` |
| `ExecutiveConversationService` | yes | conversation, executive | `jarvis_convergence_c2/payload/core/conversation/service.py:24` |
| `ExecutiveConversationServiceTests` | no | conversation, executive | `jarvis_convergence_c1/payload/tests/test_convergence_c1_executive_conversation.py:27` |
| `ExecutiveConversationServiceTests` | no | conversation, executive | `tests/test_convergence_c1_executive_conversation.py:27` |
| `ExecutiveDashboardService` | no | executive | `core/executive/operations_center/services.py:202` |
| `ExecutiveDecision` | no | executive | `core/cognition/executive_decision/contracts.py:42` |
| `ExecutiveDecision` | no | executive | `genesis_iv_a7/core/cognition/executive_decision/contracts.py:42` |
| `ExecutiveDecisionEngine` | no | executive | `core/cognition/executive_decision/engine.py:9` |
| `ExecutiveDecisionEngine` | no | executive | `genesis_iv_a7/core/cognition/executive_decision/engine.py:9` |
| `ExecutiveDecisionError` | no | executive | `core/cognition/decision/errors.py:1` |
| `ExecutiveDecisionError` | no | executive | `core/cognition/executive_decision/errors.py:1` |
| `ExecutiveDecisionError` | no | executive | `genesis_iv_a7/core/cognition/executive_decision/errors.py:1` |
| `ExecutiveDecisionService` | no | executive | `core/cognition/decision/service.py:13` |
| `ExecutiveDirector` | yes | director, executive | `core/executive/director.py:22` |
| `ExecutiveDirectorTests` | no | director, executive | `tests/test_gen2_executive.py:23` |
| `ExecutiveError` | no | executive | `core/executive/contracts.py:21` |
| `ExecutiveEventBus` | no | executive, repository | `core/executive/events/bus.py:35` |
| `ExecutiveEventRuntime` | no | executive | `core/executive/events/bootstrap.py:52` |
| `ExecutiveEventRuntimeSnapshot` | no | executive | `core/executive/events/bootstrap.py:33` |
| `ExecutiveEventRuntimeState` | no | executive | `core/executive/events/bootstrap.py:23` |
| `ExecutiveEventSubscriber` | no | executive | `core/executive/events/contracts.py:11` |
| `ExecutiveEvidenceCorrelator` | no | executive | `core/cognition/evidence_correlation/correlator.py:19` |
| `ExecutiveEvidenceService` | no | executive | `core/cognition/evidence_correlation/service.py:16` |
| `ExecutiveExecutionOrchestrator` | no | coordinator, executive, orchestrator | `core/cognition/execution_orchestrator/orchestrator.py:35` |
| `ExecutiveExecutionOrchestrator` | no | coordinator, executive, orchestrator | `genesis_iv_a9/core/cognition/execution_orchestrator/orchestrator.py:35` |
| `ExecutiveGovernanceService` | no | executive | `core/governance/constitution/coverage/graph/directorate_governance.py:12` |
| `ExecutiveGovernmentProvider` | no | executive | `core/government/executive/interfaces.py:21` |
| `ExecutiveGovernmentSnapshot` | no | executive | `core/government/executive/contracts.py:346` |
| `ExecutiveGovernmentView` | no | executive | `core/government/executive/contracts.py:272` |
| `ExecutiveHealth` | no | executive, response | `core/executive/operations_center/models.py:67` |
| `ExecutiveHealthService` | no | executive | `core/executive/operations_center/services.py:68` |
| `ExecutiveHypothesisGenerator` | no | executive | `core/cognition/hypothesis/generator.py:18` |
| `ExecutiveHypothesisService` | no | executive | `core/cognition/hypothesis/service.py:15` |
| `ExecutiveIntegrationContractTests` | no | executive | `tests/test_genesis_viii_a0_5_executive_integration_contracts.py:32` |
| `ExecutiveIntegrationProvider` | no | executive | `core/government/executive/interfaces.py:98` |
| `ExecutiveIntegrationRuntime` | no | executive | `core/integration/bootstrap.py:24` |
| `ExecutiveIntegrationRuntime` | no | executive | `genesis_vi_a3b_contract/core/integration/bootstrap.py:24` |
| `ExecutiveIntegrationService` | no | executive | `genesis_iv_b1/core/integration/service.py:6` |
| `ExecutiveIntegrationService` | no | executive | `genesis_iv_b1_rc1/core/integration/service.py:6` |
| `ExecutiveIntegrationService` | no | executive, repository | `core/integration/service.py:198` |
| `ExecutiveIntegrityEngine` | no | executive | `core/executive/persistence/integrity.py:6` |
| `ExecutiveKnowledgeAwarenessService` | yes | awareness, executive, grounding | `core/knowledge_awareness/service.py:13` |
| `ExecutiveKnowledgeAwarenessService` | yes | awareness, executive, grounding | `jarvis_convergence_c5/payload/core/knowledge_awareness/service.py:13` |
| `ExecutiveKnowledgeState` | no | executive | `core/knowledge_awareness/contracts.py:60` |
| `ExecutiveKnowledgeState` | no | executive | `jarvis_convergence_c5/payload/core/knowledge_awareness/contracts.py:60` |
| `ExecutiveLifecycleManager` | no | executive, session | `core/executive/lifecycle/manager.py:42` |
| `ExecutiveLifecycleState` | no | executive | `core/executive/lifecycle/contracts.py:47` |
| `ExecutiveLiveBroker` | no | executive | `core/executive/operations_center/transport.py:115` |
| `ExecutiveLiveBrokerTests` | no | executive | `tests/test_genesis_vii_a0_pack2_executive_api.py:26` |
| `ExecutiveLiveEnvelope` | no | executive | `core/executive/operations_center/transport.py:33` |
| `ExecutiveLiveEventBridge` | no | executive | `core/executive/events/integration.py:23` |
| `ExecutiveMetric` | no | executive | `core/executive/operations_center/models.py:85` |
| `ExecutiveMetrics` | no | executive, response | `core/executive/operations_center/models.py:103` |
| `ExecutiveMetricsService` | no | executive | `core/executive/operations_center/services.py:100` |
| `ExecutiveMissionCompiler` | no | compiler, executive | `core/cognition/mission_compiler/compiler.py:31` |
| `ExecutiveMissionCompiler` | no | compiler, executive | `genesis_iv_a8/core/cognition/mission_compiler/compiler.py:31` |
| `ExecutiveObservabilityService` | no | executive | `core/observability/service.py:13` |
| `ExecutiveObservabilityService` | no | executive | `jarvis_convergence_c6/payload/core/observability/service.py:11` |
| `ExecutiveObservationBus` | no | executive | `core/cognition/observation/bus.py:7` |
| `ExecutiveObservationService` | no | executive | `core/cognition/observation/service.py:5` |
| `ExecutiveOffice` | no | executive | `core/government/models/objects.py:13` |
| `ExecutiveOperationsRuntime` | no | executive | `core/executive/operations_center/api.py:45` |
| `ExecutiveProjection` | no | executive | `core/integration/contracts.py:232` |
| `ExecutiveProjectionBus` | no | executive | `core/integration/bus.py:45` |
| `ExecutiveProjectionFrameworkTests` | no | executive | `genesis_vi_a3b_contract/tests/test_genesis_ui_a2_executive_projection_framework.py:29` |
| `ExecutiveProjectionFrameworkTests` | no | executive | `tests/test_genesis_ui_a2_executive_projection_framework.py:36` |
| `ExecutiveProjectionService` | no | executive | `core/integration/service.py:23` |
| `ExecutiveProjectionService` | no | executive | `genesis_vi_a3b_contract/core/integration/service.py:7` |
| `ExecutiveProvider` | no | executive | `core/operations/contracts.py:10` |
| `ExecutivePublication` | no | executive | `core/executive/events/contracts.py:25` |
| `ExecutivePublisher` | no | executive | `core/executive/events/publishers.py:18` |
| `ExecutiveReadiness` | no | executive | `core/integration/readiness.py:25` |
| `ExecutiveReasoner` | no | executive | `core/cognition/reasoner/contracts.py:19` |
| `ExecutiveReasoningError` | no | executive | `core/cognition/reasoner/errors.py:6` |
| `ExecutiveReasoningResult` | no | executive | `core/cognition/reasoner/models.py:122` |
| `ExecutiveReasoningService` | no | executive | `core/cognition/reasoner/service.py:17` |
| `ExecutiveRecommendation` | no | executive | `core/government/executive/contracts.py:127` |
| `ExecutiveRecommendationProvider` | no | executive | `core/government/executive/interfaces.py:50` |
| `ExecutiveRecoveryEngine` | no | executive | `core/executive/persistence/recovery.py:169` |
| `ExecutiveRequestCompiler` | yes | compiler, executive, request | `core/conversation/compiler.py:20` |
| `ExecutiveRequestCompiler` | yes | compiler, executive, request | `jarvis_convergence_c1/payload/core/conversation/compiler.py:20` |
| `ExecutiveRequestCompilerTests` | no | compiler, executive, request | `jarvis_convergence_c1/payload/tests/test_convergence_c1_executive_conversation.py:12` |
| `ExecutiveRequestCompilerTests` | no | compiler, executive, request | `tests/test_convergence_c1_executive_conversation.py:12` |
| `ExecutiveRequestContext` | no | executive, request | `core/conversation/contracts.py:42` |
| `ExecutiveRequestContext` | no | executive, request | `jarvis_convergence_c1/payload/core/conversation/contracts.py:42` |
| `ExecutiveRuntime` | no | executive | `core/operational/runtime.py:6` |
| `ExecutiveRuntimeCallGraphReconstructor` | no | executive | `core/retrieval/call_graph/reconstructor.py:15` |
| `ExecutiveSession` | no | executive, session | `core/cognition/session.py:78` |
| `ExecutiveSession` | no | executive, session | `core/executive/lifecycle/contracts.py:87` |
| `ExecutiveSessionEvent` | no | executive, session | `core/cognition/session.py:27` |
| `ExecutiveSessionSnapshot` | no | executive, session | `core/cognition/session.py:46` |
| `ExecutiveSessionStatus` | no | executive, session | `core/cognition/session.py:17` |
| `ExecutiveSessionStatus` | no | executive, session | `core/executive/lifecycle/contracts.py:59` |
| `ExecutiveSessionTests` | no | executive, session | `tests/test_genesis_vi_a5_executive_session.py:21` |
| `ExecutiveSituationProjector` | no | executive | `core/cognition/situation/projector.py:21` |
| `ExecutiveSituationService` | no | executive | `core/cognition/situation/service.py:15` |
| `ExecutiveSnapshot` | no | executive | `core/operations/models.py:65` |
| `ExecutiveSnapshotProvider` | no | executive | `core/government/executive/interfaces.py:85` |
| `ExecutiveSnapshotPublisher` | no | executive | `core/executive/operations_center/transport.py:189` |
| `ExecutiveState` | no | executive | `core/operations/enums.py:19` |
| `ExecutiveStatus` | no | executive | `core/executive/operations_center/models.py:122` |
| `ExecutiveStatusService` | no | executive | `core/executive/operations_center/services.py:126` |
| `ExecutiveSubscriberFailure` | no | executive | `core/executive/events/contracts.py:17` |
| `ExecutiveSubscription` | no | executive | `core/executive/events/bus.py:28` |
| `ExecutiveSubscription` | no | executive | `core/executive/operations_center/transport.py:68` |
| `ExecutiveTelemetryAdapter` | no | executive | `core/operations/executive.py:13` |
| `ExecutiveTimelineEngine` | no | executive | `core/executive/timeline/engine.py:19` |
| `ExecutiveTimelineNode` | no | executive | `core/integration/contracts.py:508` |
| `ExecutiveTimelineNode` | no | executive | `genesis_iv_b1/core/integration/contracts.py:76` |
| `ExecutiveTimelineNode` | no | executive | `genesis_iv_b1_rc1/core/integration/contracts.py:76` |
| `ExecutiveTimelineRepository` | no | executive, repository | `core/executive/timeline/repository.py:20` |
| `Executor` | no | planner | `core/src/runtime/executor.py:10` |
| `ExecutorUnavailableError` | no | orchestrator | `core/cognition/execution_orchestrator/errors.py:13` |
| `ExecutorUnavailableError` | no | orchestrator | `genesis_iv_a9/core/cognition/execution_orchestrator/errors.py:13` |
| `FailingExecutiveProvider` | no | executive | `tests/test_genesis_vi_a1_executive_telemetry.py:45` |
| `FileCheckpointRepository` | no | repository, session | `core/executive/persistence/repository.py:84` |
| `FilesystemTests` | no | repository | `tests/test_genesis_vii_c0_pack1b.py:52` |
| `FreezeAuditError` | no | repository | `dev/tools/audit_genesis_3f1.py:53` |
| `GenesisIVR0ARepositorySkeletonTests` | no | repository | `tests/cognition/test_genesis_4r0a_repository_skeleton.py:75` |
| `GenesisVIA1ExecutiveTelemetryTests` | no | executive | `tests/test_genesis_vi_a1_executive_telemetry.py:80` |
| `GenesisVIA2ExecutiveMissionControlTests` | no | executive | `genesis_vi_a3b_contract/tests/test_genesis_vi_a2_executive_mission_control.py:13` |
| `GenesisVIA2ExecutiveMissionControlTests` | no | executive | `tests/test_genesis_vi_a2_executive_mission_control.py:13` |
| `GovernmentSnapshotRepository` | no | repository | `core/government/registry/repository.py:76` |
| `Grounding` | no | grounding | `jarvis_convergence_c6/payload/tests/test_convergence_c6_executive_observability.py:14` |
| `Grounding` | no | grounding | `tests/test_convergence_c6_executive_observability.py:14` |
| `Grounding` | no | grounding | `tests/test_genesis_ix_a4_3b_gap_propagation_trace.py:14` |
| `GroundingEvidence` | no | grounding | `core/conversation/grounding.py:16` |
| `GroundingEvidence` | no | grounding | `jarvis_convergence_c4/payload/core/conversation/grounding.py:16` |
| `GroundingResult` | no | grounding | `core/conversation/grounding.py:77` |
| `GroundingResult` | no | grounding | `jarvis_convergence_c4/payload/core/conversation/grounding.py:75` |
| `HealthEventPublisher` | no | executive | `core/executive/events/publishers.py:96` |
| `Hypothesis` | no | executive | `core/cognition/hypothesis/models.py:75` |
| `HypothesisDisposition` | no | repository | `core/cognition/hypothesis/enums.py:30` |
| `HypothesisGenerator` | no | executive | `core/cognition/hypothesis/contracts.py:33` |
| `HypothesisNotFoundError` | no | request | `core/cognition/hypothesis/errors.py:14` |
| `HypothesisQuery` | no | repository | `core/cognition/hypothesis/models.py:271` |
| `HypothesisRepository` | no | executive, repository | `core/cognition/hypothesis/contracts.py:13` |
| `HypothesisRepositoryClosedError` | no | repository | `core/cognition/hypothesis/errors.py:18` |
| `HypothesisStatus` | no | executive | `core/cognition/hypothesis/enums.py:8` |
| `IllegalExecutionTransitionError` | no | orchestrator | `core/cognition/execution_orchestrator/errors.py:9` |
| `IllegalExecutionTransitionError` | no | orchestrator | `genesis_iv_a9/core/cognition/execution_orchestrator/errors.py:9` |
| `InMemoryAssessmentRepository` | no | repository | `core/cognition/evidence_correlation/repository.py:15` |
| `InMemoryCourseOfActionRepository` | no | repository | `core/cognition/coa/repository.py:5` |
| `InMemoryDecisionRepository` | no | repository | `core/cognition/decision/repository.py:7` |
| `InMemoryHypothesisRepository` | no | repository | `core/cognition/hypothesis/repository.py:15` |
| `InMemoryObservationRepository` | no | repository | `core/cognition/observation/repository.py:9` |
| `InMemoryPlanRepository` | no | repository | `core/executive/planning/repository.py:44` |
| `InMemoryReasoningRepository` | no | repository | `core/cognition/reasoner/repository.py:15` |
| `InMemorySituationRepository` | no | repository | `core/cognition/situation/repository.py:27` |
| `IntegrationError` | no | executive | `core/integration/errors.py:6` |
| `IntentRouter` | no | director, request | `knowledge_engine/director/router/intent_router.py:8` |
| `InvalidCognitiveContextError` | no | executive | `core/cognition/errors.py:10` |
| `InvalidDecisionInputError` | no | executive | `core/cognition/decision/errors.py:4` |
| `InvalidDecisionInputError` | no | executive | `core/cognition/executive_decision/errors.py:2` |
| `InvalidDecisionInputError` | no | executive | `genesis_iv_a7/core/cognition/executive_decision/errors.py:2` |
| `InvalidDecisionRecordError` | no | executive | `core/cognition/decision/errors.py:7` |
| `InvalidExecutionPlanError` | no | orchestrator | `core/cognition/execution_orchestrator/errors.py:5` |
| `InvalidExecutionPlanError` | no | orchestrator | `genesis_iv_a9/core/cognition/execution_orchestrator/errors.py:5` |
| `InvalidLifecycleTransitionError` | no | request | `core/executive/lifecycle/contracts.py:35` |
| `InvalidMissionPlanError` | no | executive | `core/executive/contracts.py:33` |
| `InvalidMissionSpecificationError` | no | compiler | `core/cognition/mission_compiler/errors.py:5` |
| `InvalidMissionSpecificationError` | no | compiler | `genesis_iv_a8/core/cognition/mission_compiler/errors.py:5` |
| `InvalidPlanTransitionError` | no | request | `core/executive/planning/errors.py:42` |
| `InvalidReasoningInputError` | no | executive | `core/cognition/reasoner/errors.py:10` |
| `InvalidReasoningRequestError` | no | request | `core/reasoning/errors.py:10` |
| `InvalidReasoningResultError` | no | executive | `core/cognition/reasoner/errors.py:14` |
| `InvalidReasoningSessionTransitionError` | no | request, session | `core/reasoning/session/errors.py:10` |
| `InvalidStateTransitionError` | no | request | `core/cognition/errors.py:18` |
| `InventoryTests` | no | repository | `tests/test_genesis_vii_c0_pack1b.py:83` |
| `KnowledgeAcquisitionDirector` | no | director | `knowledge_engine/acquisition/director.py:19` |
| `KnowledgeDirector` | no | director | `knowledge_engine/director/knowledge_director.py:10` |
| `KnowledgeDirectorCheck` | no | director | `dev/doctor/director.py:11` |
| `KnowledgeGapPropagationTracer` | no | trace | `core/retrieval/gap_trace/tracer.py:69` |
| `KnowledgeGroundingTests` | no | grounding | `jarvis_convergence_c4/payload/tests/test_convergence_c4_knowledge_grounding.py:12` |
| `KnowledgeGroundingTests` | no | grounding | `tests/test_convergence_c4_knowledge_grounding.py:12` |
| `KnowledgeHandler` | no | director | `core/executive/handlers.py:92` |
| `KnowledgeRegistryRepository` | no | repository | `knowledge_engine/assimilation/repositories/knowledge_registry.py:39` |
| `LifecycleError` | no | executive | `core/executive/lifecycle/contracts.py:31` |
| `MarkdownParserTests` | no | repository | `tests/test_genesis_vii_c0_pack1b.py:73` |
| `MemoryEntry` | no | executive | `core/cognition/models.py:39` |
| `MemoryEntryKind` | no | executive | `core/cognition/enums.py:37` |
| `MetricState` | no | executive | `core/executive/operations_center/models.py:31` |
| `Mission` | no | executive | `core/executive/planning/models.py:369` |
| `MissionCompilationRequest` | no | request | `core/cognition/mission_compiler/contracts.py:110` |
| `MissionCompilationRequest` | no | request | `genesis_iv_a8/core/cognition/mission_compiler/contracts.py:110` |
| `MissionCompilerError` | no | compiler | `core/cognition/mission_compiler/errors.py:1` |
| `MissionCompilerError` | no | compiler | `genesis_iv_a8/core/cognition/mission_compiler/errors.py:1` |
| `MissionDependencyCycleError` | no | compiler | `core/cognition/mission_compiler/errors.py:9` |
| `MissionDependencyCycleError` | no | compiler | `genesis_iv_a8/core/cognition/mission_compiler/errors.py:9` |
| `MissionEventPublisher` | no | executive | `core/executive/events/publishers.py:63` |
| `MissionExecutionRequest` | no | request | `core/cognition/execution_orchestrator/contracts.py:62` |
| `MissionExecutionRequest` | no | request | `genesis_iv_a9/core/cognition/execution_orchestrator/contracts.py:62` |
| `MissionNotFoundError` | no | executive | `core/executive/contracts.py:29` |
| `MissionNotFoundError` | no | request | `knowledge_engine/assimilation/mission_store.py:21` |
| `MissionPlanner` | no | planner | `core/executive/planner.py:9` |
| `MissionPlanner` | no | planner | `jarvis_convergence_c3/payload/core/executive/planner.py:9` |
| `MissionPriority` | no | executive | `core/executive/planning/enums.py:29` |
| `MissionProvider` | no | executive | `core/operations/contracts.py:23` |
| `MissionStore` | no | repository | `core/executive/store.py:15` |
| `MissionTrace` | no | trace | `core/cognition/mission_compiler/contracts.py:218` |
| `MissionTrace` | no | trace | `genesis_iv_a8/core/cognition/mission_compiler/contracts.py:218` |
| `NoAdmissibleCourseOfActionError` | no | executive | `core/cognition/executive_decision/errors.py:3` |
| `NoAdmissibleCourseOfActionError` | no | executive | `genesis_iv_a7/core/cognition/executive_decision/errors.py:3` |
| `NoDirectorMethods` | no | director | `tests/test_genesis_ix_a4_4_runtime_integration.py:25` |
| `ObjectRepository` | no | repository | `core/government/registry/repository.py:17` |
| `ObjectiveGrounding` | no | grounding | `core/conversation/grounding.py:56` |
| `ObjectiveGrounding` | no | grounding | `jarvis_convergence_c4/payload/core/conversation/grounding.py:54` |
| `ObservationDirector` | no | director | `core/cognition/layers/observation/director.py:18` |
| `ObservationDirectorTests` | no | director | `tests/cognition/test_genesis_4r2_observation_director.py:14` |
| `ObservationRepositoryClosedError` | no | repository | `core/cognition/observation/errors.py:5` |
| `OrganizationalSupervisor` | no | supervisor | `core/government/executive/interfaces.py:31` |
| `OrphanPlanNodeError` | no | compiler | `core/cognition/mission_compiler/errors.py:13` |
| `OrphanPlanNodeError` | no | compiler | `genesis_iv_a8/core/cognition/mission_compiler/errors.py:13` |
| `PersistenceRecordKind` | no | executive | `core/executive/persistence/contracts.py:42` |
| `PlanNotFoundError` | no | request | `core/executive/planning/errors.py:46` |
| `PlanRepository` | no | repository | `core/executive/planning/repository.py:16` |
| `ProjectionProviderNotFoundError` | no | request | `core/integration/errors.py:26` |
| `ProjectionRegistry` | no | executive | `core/integration/registry.py:54` |
| `PromotionPlanner` | no | planner | `knowledge_engine/promotion/planner.py:8` |
| `PropositionNotFoundError` | no | request | `core/evidence/errors.py:116` |
| `ProvenanceRepository` | no | repository | `knowledge_engine/acquisition/provenance/repository.py:18` |
| `PythonParserTests` | no | repository | `tests/test_genesis_vii_c0_pack1b.py:62` |
| `QueryUnderstanding` | no | request | `knowledge_engine/query_understanding/models.py:10` |
| `ReasoningDisposition` | no | executive | `core/cognition/reasoner/enums.py:8` |
| `ReasoningPolicy` | no | executive | `core/cognition/reasoner/models.py:256` |
| `ReasoningQuery` | no | executive, repository | `core/cognition/reasoner/models.py:287` |
| `ReasoningRepository` | no | executive, repository | `core/cognition/reasoner/contracts.py:34` |
| `ReasoningRepositoryClosedError` | no | executive, repository | `core/cognition/reasoner/errors.py:22` |
| `ReasoningRepositoryDisposition` | no | repository | `core/cognition/reasoner/enums.py:25` |
| `ReasoningRequest` | no | request | `core/reasoning/models.py:143` |
| `ReasoningResult` | no | session | `core/reasoning/models.py:249` |
| `ReasoningResultNotFoundError` | no | executive, request | `core/cognition/reasoner/errors.py:18` |
| `ReasoningSession` | no | session | `core/reasoning/session/contracts.py:147` |
| `ReasoningSessionContractError` | no | session | `core/reasoning/session/errors.py:20` |
| `ReasoningSessionId` | no | session | `core/reasoning/session/contracts.py:53` |
| `ReasoningSessionLifecycle` | no | session | `core/reasoning/session/lifecycle.py:76` |
| `ReasoningSessionLifecycleError` | no | session | `core/reasoning/session/errors.py:6` |
| `ReasoningSessionMetadata` | no | executive, session | `core/reasoning/session/contracts.py:89` |
| `ReasoningSessionState` | no | session | `core/reasoning/session/contracts.py:17` |
| `ReasoningTraceStep` | no | trace | `core/reasoning/models.py:207` |
| `RecoveryRequest` | no | executive, request, session | `core/executive/persistence/contracts.py:241` |
| `RegistryCounter` | no | director | `core/executive/operations_center/collectors.py:373` |
| `RelationshipRepository` | no | repository | `core/government/registry/repository.py:47` |
| `Repository` | no | repository | `tests/test_genesis_vi_a68_part_b.py:17` |
| `RepositoryAccessError` | no | repository | `core/executive/timeline/query_engine.py:20` |
| `RepositoryArtifact` | no | repository | `core/governance/constitution/repository_audit/models.py:24` |
| `RepositoryArtifactAssessment` | no | repository | `core/governance/constitution/repository_audit/models.py:42` |
| `RepositoryAuditAssessment` | no | repository | `core/governance/constitution/repository_audit/models.py:93` |
| `RepositoryAuditDiscoveryError` | no | repository | `core/governance/constitution/repository_audit/discovery.py:10` |
| `RepositoryAuditFixture` | no | repository | `tests/test_genesis_vii_c0_pack1b.py:17` |
| `RepositoryAuditManifest` | no | repository | `core/governance/audit/verification.py:62` |
| `RepositoryAuditPolicy` | no | repository | `core/governance/constitution/repository_audit/models.py:8` |
| `RepositoryAuditStatistics` | no | repository | `core/governance/constitution/repository_audit/models.py:74` |
| `RepositoryConstitutionalAuditEngine` | no | repository | `core/governance/constitution/repository_audit/engine.py:20` |
| `RepositoryConstitutionalAuditReporter` | no | repository | `core/governance/constitution/repository_audit/reporting.py:9` |
| `RepositoryConstitutionalAuditTests` | no | repository | `tests/test_genesis_vii_c4_2_repository_constitutional_audit.py:67` |
| `RepositoryCoverageStatus` | no | repository | `core/governance/constitution/coverage/contracts.py:12` |
| `RepositoryEdge` | no | repository | `core/governance/constitution/coverage/graph/repository_models.py:20` |
| `RepositoryEdgeKind` | no | repository | `core/governance/constitution/coverage/graph/repository_contracts.py:18` |
| `RepositoryFile` | no | repository | `core/governance/audit/models.py:53` |
| `RepositoryHealth` | no | repository | `core/governance/audit/verification.py:32` |
| `RepositoryIntegrationAuditor` | no | repository | `core/integration/audit.py:10` |
| `RepositoryIntegrationAuditor` | no | repository | `genesis_iv_b1/core/integration/audit.py:10` |
| `RepositoryIntegrationAuditor` | no | repository | `genesis_iv_b1_rc1/core/integration/audit.py:10` |
| `RepositoryIntegrityStatus` | no | repository | `core/executive/timeline/repository_contracts.py:42` |
| `RepositoryInventory` | no | repository | `core/governance/audit/models.py:162` |
| `RepositoryInventoryBuilder` | no | repository | `core/governance/audit/inventory.py:16` |
| `RepositoryInventoryVerifier` | no | repository | `core/governance/audit/verification.py:75` |
| `RepositoryLifecycleState` | no | repository | `core/governance/constitution/coverage/graph/repository_contracts.py:27` |
| `RepositoryNode` | no | repository | `core/governance/constitution/coverage/graph/repository_models.py:7` |
| `RepositoryNodeKind` | no | repository | `core/governance/constitution/coverage/graph/repository_contracts.py:6` |
| `RepositoryNotFoundError` | no | repository | `core/certification/runtime/contracts.py:11` |
| `RepositoryPolicy` | no | repository | `core/executive/persistence/repository.py:48` |
| `RepositoryProjectionAssessment` | no | repository | `core/governance/constitution/coverage/graph/repository_models.py:78` |
| `RepositoryProjectionIntegrity` | no | repository | `core/governance/constitution/coverage/graph/repository_models.py:33` |
| `RepositoryProjectionMetrics` | no | repository | `core/governance/constitution/coverage/graph/repository_models.py:57` |
| `RepositoryProjectionTests` | no | repository | `tests/test_genesis_vii_c4_3_pack3b2a_repository_projection.py:18` |
| `RepositoryRealityModelingTests` | no | repository | `tests/test_genesis_5e1a_repository_reality_modeling.py:14` |
| `RepositoryStatistics` | no | repository | `core/governance/audit/models.py:139` |
| `RepositoryVerificationReport` | no | repository | `core/governance/audit/verification.py:45` |
| `RepresentationDirector` | no | director | `core/representation/director.py:91` |
| `RepresentationRequest` | no | director, request | `core/representation/director.py:39` |
| `RepresentationResult` | no | director | `core/representation/director.py:68` |
| `ResolvedDirectorDispatch` | no | director | `core/executive/director_dispatch.py:13` |
| `RetrievalDirector` | no | director | `knowledge_engine/retrieval_intelligence/director.py:29` |
| `RetrievalDirectorTests` | no | director | `knowledge_engine/tests/test_retrieval_intelligence.py:137` |
| `RuntimeLocator` | no | director | `core/src/discovery/runtime_locator.py:15` |
| `SQLiteCognitiveWorkspaceRepository` | no | repository | `core/cognition/workspace/repository.py:220` |
| `SQLiteSourceRegistryRepository` | no | repository | `knowledge_engine/source_registry/repository.py:16` |
| `SafeCommitError` | no | repository | `dev/release/safe_commit.py:41` |
| `SearchResponse` | no | response | `knowledge_engine/search/service.py:46` |
| `SegmentationRequest` | no | request | `core/representation/contracts.py:99` |
| `SelectionTrace` | no | trace | `core/executive/capabilities/models.py:125` |
| `SessionAlreadyActiveError` | no | session | `core/executive/lifecycle/contracts.py:39` |
| `SessionAttribute` | no | session | `core/reasoning/session/contracts.py:35` |
| `SessionNotActiveError` | no | session | `core/executive/lifecycle/contracts.py:43` |
| `SituationDisposition` | no | repository | `core/cognition/situation/enums.py:31` |
| `SituationNotFoundError` | no | request | `core/cognition/situation/errors.py:14` |
| `SituationProjector` | no | executive | `core/cognition/situation/contracts.py:33` |
| `SituationQuery` | no | repository | `core/cognition/situation/models.py:299` |
| `SituationRepository` | no | executive, repository | `core/cognition/situation/contracts.py:13` |
| `SituationRepositoryClosedError` | no | repository | `core/cognition/situation/errors.py:18` |
| `SituationSnapshot` | no | executive | `core/cognition/situation/models.py:152` |
| `SituationStatus` | no | executive | `core/cognition/situation/enums.py:8` |
| `SourceRegistryNotFoundError` | no | request | `knowledge_engine/source_registry/errors.py:16` |
| `StaticExecutiveProvider` | no | executive | `tests/test_genesis_vi_a1_executive_telemetry.py:23` |
| `StaticPublicSurfaceEvaluator` | no | repository | `core/engineering/public_surface.py:22` |
| `StatusState` | no | executive | `core/executive/operations_center/models.py:39` |
| `StoragePathError` | no | request | `core/executive/persistence/storage.py:23` |
| `SubmitDirector` | no | director | `tests/test_genesis_ix_a4_4_runtime_integration.py:15` |
| `TerminalReasoningSessionError` | no | session | `core/reasoning/session/errors.py:14` |
| `TestGenesis3A2PersistentWorkspaceRepository` | no | repository | `tests/test_genesis_3a2_persistent_workspace_repository.py:16` |
| `TimelineInterprocessLock` | no | repository | `core/executive/timeline/locking.py:13` |
| `TimelineQueryEngine` | no | repository | `core/executive/timeline/query_engine.py:138` |
| `TimelineRepositoryConflictError` | no | repository | `core/executive/timeline/repository_contracts.py:34` |
| `TimelineRepositoryError` | no | repository | `core/executive/timeline/repository_contracts.py:26` |
| `TimelineRepositoryIndexes` | no | repository | `core/executive/timeline/indexes.py:14` |
| `TimelineRepositoryIntegrityError` | no | repository | `core/executive/timeline/repository_contracts.py:38` |
| `TimelineRepositoryIntegrityReport` | no | repository | `core/executive/timeline/repository_contracts.py:99` |
| `TimelineRepositoryStatistics` | no | repository | `core/executive/timeline/repository_contracts.py:48` |
| `TimelineRepositoryStorageError` | no | repository | `core/executive/timeline/repository_contracts.py:30` |
| `ToolPlanner` | no | planner, request | `core/src/planner/tool_planner.py:6` |
| `TraceabilityRecord` | no | trace | `core/governance/constitution/ratification/models.py:64` |
| `VerificationTests` | no | repository | `tests/test_genesis_vii_c0_pack1b.py:111` |
| `WorkingMemory` | no | executive | `core/cognition/working_memory.py:55` |
| `WorkingMemory` | no | executive | `genesis_vi_a2_working_memory/core/cognition/working_memory.py:55` |
| `WorkingMemorySnapshot` | no | executive | `core/cognition/working_memory.py:17` |
| `WorkingMemorySnapshot` | no | executive | `genesis_vi_a2_working_memory/core/cognition/working_memory.py:17` |
| `WorkspaceConversationRequest` | no | conversation, request | `core/executive/conversation/contracts.py:15` |
| `WorkspaceConversationResponse` | no | conversation, response | `core/executive/conversation/contracts.py:44` |
| `WorkspaceIntegrationPipeline` | no | request | `core/cognition/integration/pipeline.py:17` |
| `WorkspaceIntegrationRequest` | no | request | `core/cognition/integration/contracts.py:80` |
| `_PrefixRepository` | no | repository | `core/executive/persistence/recovery.py:152` |
