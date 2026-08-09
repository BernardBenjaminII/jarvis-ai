# Genesis IX-A4.1A — Executive & Conversation Inventory

**Generated:** 2026-08-04T22:13:10.553888+00:00
**Repository:** `/media/abdullah/JARVISDATA/Projects/jarvis-ai`
**Fingerprint:** `cb56c393401cdcf946766a752962e8a71a00fb73fb6f88ed32be1d0c61fcedbb`

## Executive Summary

- Executive/conversation symbols: **2003**
- Import edges: **803**
- Static call edges: **2414**
- API routes: **24**
- Mission Control consumers: **3**
- Duplicate candidate groups: **8**

## Live Runtime Composition

```json
{
  "ask_signature": "(operator_input: 'str', *, session_id: 'str | None' = None, mode: 'str' = 'full', channel: 'str' = 'text', metadata: 'dict[str, Any] | None' = None) -> 'ExecutiveConversationResponse'",
  "conversation_service": {
    "answer_handler": null,
    "compiler": {
      "module": "core.conversation.compiler",
      "type": "ExecutiveRequestCompiler"
    },
    "module": "core.conversation.service",
    "orchestrator": {
      "module": "core.conversation.orchestrator",
      "type": "ExecutiveConversationOrchestrator"
    },
    "repository": {
      "module": "core.conversation.repository",
      "type": "ConversationRepository"
    },
    "type": "ExecutiveConversationService"
  },
  "orchestrator": {
    "awareness_service": {
      "module": "core.knowledge_awareness.service",
      "type": "ExecutiveKnowledgeAwarenessService"
    },
    "director": {
      "module": "core.executive.director",
      "type": "ExecutiveDirector"
    },
    "grounding_service": {
      "module": "core.conversation.grounding",
      "type": "CatalogGroundingService"
    },
    "module": "core.conversation.orchestrator",
    "observability_service": null,
    "synthesis_handler": {
      "module": "builtins",
      "type": "function"
    },
    "type": "ExecutiveConversationOrchestrator"
  }
}
```

## API Inventory

| Method | Route | Function | Response model | Source |
|---|---|---|---|---|
| POST | `/api/conversation/query` | `conversation_query` | `` | `core/src/routes/api.py:82` |
| GET | `/api/conversation/sessions/{session_id}` | `conversation_session` | `` | `core/src/routes/api.py:93` |
| GET | `/api/conversation/sessions/{session_id}/messages` | `conversation_messages` | `` | `core/src/routes/api.py:101` |
| POST | `/ask` | `ask` | `` | `core/src/routes/api.py:74` |
| GET | `/bridge` | `commanders_bridge` | `` | `core/src/routes/mission_control.py:13` |
| GET | `/bridge` | `executive_bridge_snapshot` | `` | `core/src/routes/operations.py:161` |
| GET | `/bridge/manifest` | `executive_bridge_manifest` | `` | `core/src/routes/operations.py:171` |
| GET | `/bridge/projections/{projection_id}` | `executive_bridge_projection` | `` | `core/src/routes/operations.py:176` |
| GET | `/bridge/readiness` | `executive_bridge_readiness` | `` | `core/src/routes/operations.py:166` |
| GET | `/capabilities` | `operations_capabilities` | `` | `core/src/routes/operations.py:133` |
| GET | `/capabilities/{capability_name}` | `operations_capability` | `` | `core/src/routes/operations.py:140` |
| POST | `/conversation` | `knowledge_workspace_conversation` | `` | `core/src/routes/knowledge_workspace.py:27` |
| GET | `/event-runtime` | `executive_event_runtime_status` | `` | `core/src/routes/executive_event_runtime.py:27` |
| GET | `/events` | `operations_events` | `` | `core/src/routes/operations.py:95` |
| GET | `/executive` | `operations_executive` | `` | `core/src/routes/operations.py:48` |
| GET | `/health` | `operations_health` | `` | `core/src/routes/operations.py:55` |
| GET | `/mission-control` | `commanders_bridge` | `` | `core/src/routes/mission_control.py:14` |
| GET | `/missions` | `operations_missions` | `` | `core/src/routes/operations.py:60` |
| GET | `/projections` | `operations_projections` | `` | `core/src/routes/operations.py:109` |
| GET | `/projections/{projection_id}` | `operations_projection` | `` | `core/src/routes/operations.py:120` |
| GET | `/resources` | `operations_resources` | `` | `core/src/routes/operations.py:68` |
| GET | `/status` | `operations_status` | `` | `core/src/routes/operations.py:43` |
| GET | `/timeline` | `operations_timeline` | `` | `core/src/routes/operations.py:73` |
| GET | `/transparency` | `operations_transparency` | `` | `core/src/routes/operations.py:82` |

## Mission Control Consumers

| Method | Endpoint | Transport | Source |
|---|---|---|---|
| POST | `/api/conversation/query` | http | `core/src/static/mission_control/knowledge_workspace.js:140` |
| POST | `/api/knowledge/conversation` | http | `core/src/static/mission_control/knowledge_workspace.js:133` |
| POST | `/ask` | http | `core/src/static/mission_control/knowledge_workspace.js:142` |

## Canonicalization

| Component | Decision | Rationale |
|---|---|---|
| `CatalogGroundingService` | **KEEP** | Active in the live runtime composition. |
| `ConversationRepository` | **KEEP** | Active in the live runtime composition. |
| `ConversationTraceEvent` | **KEEP** | Matches an established Executive or Conversation contract. |
| `ExecutiveConversationAdapter` | **KEEP** | Compatibility adapter; preserve until consumers are migrated. |
| `ExecutiveConversationOrchestrator` | **KEEP** | Active in the live runtime composition. |
| `ExecutiveConversationResponse` | **KEEP** | Matches an established Executive or Conversation contract. |
| `ExecutiveConversationService` | **KEEP** | Active in the live runtime composition. |
| `ExecutiveDirector` | **KEEP** | Active in the live runtime composition. |
| `ExecutiveKnowledgeAwarenessService` | **KEEP** | Active in the live runtime composition. |
| `ExecutiveRequestCompiler` | **KEEP** | Active in the live runtime composition. |
| `ExecutiveRequestContext` | **KEEP** | Matches an established Executive or Conversation contract. |
| `ExecutiveTelemetryAdapter` | **KEEP** | Compatibility adapter; preserve until consumers are migrated. |
| `AcademyContractValidationError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `AcademyDormantError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `AcquisitionMissionRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `AcquisitionRequest` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `AdmissionDirector` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `AssessmentDisposition` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `AssessmentNotFoundError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `AssessmentQuery` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `AssessmentRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `AssessmentRepositoryClosedError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `AssignmentRequest` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `AssimilationDirector` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `AssimilationDispatchRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `AssimilationDispatchResult` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `AssimilationHandler` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `AssimilationHandoffRecord` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `AssimilationHandoffRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `AssimilationPlanner` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `AttentionCandidate` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `AttentionReason` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `BootstrapRunner` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CanonicalAssimilationDispatcher` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CanonicalSnapshotSerializer` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CapabilityEventPublisher` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CapabilityOrchestrator` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `CapabilityPlanner` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CapabilityRegistry` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CatalogRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `CheckpointConflictError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CheckpointDescriptor` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CheckpointHistoryError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CheckpointNotFoundError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CheckpointReason` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CheckpointRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `CheckpointRepositoryError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `CheckpointRepositoryProtocol` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `CognitionCycleController` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CognitiveCycleStatus` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CognitiveEvent` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CognitiveEventKind` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CognitiveState` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CognitiveStateMachine` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CognitiveWorkspaceCatalog` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CognitiveWorkspaceConflictError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CognitiveWorkspaceIntegrationDirector` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CognitiveWorkspaceNotFoundError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CognitiveWorkspaceRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `CognitiveWorkspaceRepositoryError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `CollectionExpansionPlanner` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ConstitutionalDirectorateFoundationEngine` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ConstitutionalDirectorateGraph` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ConstitutionalDirectorateProjectionEngine` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ConstitutionalDirectorateProjectionReporter` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ConstitutionalDirectorateQueryService` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ConstitutionalExtractionEngine` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ConstitutionalRepositoryProjection` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ConstitutionalRepositoryProjectionEngine` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ConstitutionalRepositoryProjectionReporter` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ConstitutionalRepositoryQueryService` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ConversationHTTPContractTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ConversationMessage` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ConversationQuery` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ConversationRole` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ConversationState` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CourseOfActionError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `CourseOfActionRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `DecisionNotApprovedError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DecisionNotFoundError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DecisionPolicyError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DecisionRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `DecisionRepositoryClosedError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `DecisionRepositoryDisposition` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `DecisionRequest` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `DecisionTrace` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `DefaultExecutiveProvider` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DemoRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `DeterministicExecutiveReasoner` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectiveRequest` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `Director` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorActivationHttpTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorActivationTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorAssignment` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorDescriptor` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorDispatchError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorEventPublisher` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorHandler` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorNotRegisteredError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorReadiness` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorRegistry` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorRequest` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `DirectorResponse` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `Directorate` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorateAssignmentRule` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorateAuthorityResolver` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorateCapabilityResolver` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorateEdge` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorateEdgeKind` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorateFoundationAssessment` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorateFoundationTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorateImpactAnalyzer` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorateImpactAssessment` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorateNode` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorateNodeKind` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorateProjectionIntegrity` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorateProjectionTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `DirectorateReviewEngine` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `Dispatcher` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `EmptyMissionProvider` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `EndToEndRetrievalTracer` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `EvidenceClass` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `EvidenceItem` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `EvidenceNotFoundError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `EvidenceStateTransitionError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecuteOnlyDirector` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutionApprovalRequiredError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutionOrchestratorError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ExecutionPlan` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveAcademyBaseline` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveAcademyError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveAlternativeGenerationService` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveApiEnvelope` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveApiTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveCheckpoint` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveContext` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveConversationServiceTests` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ExecutiveDashboardService` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveDecision` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveDecisionEngine` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveDecisionError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveDecisionService` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveDirectorTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveEventBus` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveEventRuntime` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveEventRuntimeSnapshot` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveEventRuntimeState` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveEventSubscriber` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveEvidenceCorrelator` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveEvidenceService` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveExecutionOrchestrator` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ExecutiveGovernanceService` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveGovernmentProvider` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveGovernmentSnapshot` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveGovernmentView` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveHealth` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveHealthService` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveHypothesisGenerator` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveHypothesisService` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveIntegrationContractTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveIntegrationProvider` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveIntegrationRuntime` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveIntegrationService` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveIntegrityEngine` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveKnowledgeState` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveLifecycleManager` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveLifecycleState` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveLiveBroker` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveLiveBrokerTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveLiveEnvelope` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveLiveEventBridge` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveMetric` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveMetrics` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveMetricsService` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveMissionCompiler` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ExecutiveObservabilityService` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveObservationBus` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveObservationService` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveOffice` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveOperationsRuntime` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveProjection` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveProjectionBus` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveProjectionFrameworkTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveProjectionService` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveProvider` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutivePublication` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutivePublisher` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveReadiness` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveReasoner` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveReasoningError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveReasoningResult` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveReasoningService` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveRecommendation` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveRecommendationProvider` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveRecoveryEngine` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveRequestCompilerTests` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ExecutiveRuntime` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveRuntimeCallGraphReconstructor` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveSession` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ExecutiveSessionEvent` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ExecutiveSessionSnapshot` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ExecutiveSessionStatus` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ExecutiveSessionTests` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ExecutiveSituationProjector` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveSituationService` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveSnapshot` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveSnapshotProvider` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveSnapshotPublisher` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveState` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveStatus` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveStatusService` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveSubscriberFailure` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveSubscription` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveTimelineEngine` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveTimelineNode` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutiveTimelineRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `Executor` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ExecutorUnavailableError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `FailingExecutiveProvider` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `FileCheckpointRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `FilesystemTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `FreezeAuditError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `GenesisIVR0ARepositorySkeletonTests` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `GenesisVIA1ExecutiveTelemetryTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `GenesisVIA2ExecutiveMissionControlTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `GovernmentSnapshotRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `Grounding` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `GroundingEvidence` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `GroundingResult` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `HealthEventPublisher` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `Hypothesis` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `HypothesisDisposition` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `HypothesisGenerator` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `HypothesisNotFoundError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `HypothesisQuery` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `HypothesisRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `HypothesisRepositoryClosedError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `HypothesisStatus` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `IllegalExecutionTransitionError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `InMemoryAssessmentRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `InMemoryCourseOfActionRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `InMemoryDecisionRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `InMemoryHypothesisRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `InMemoryObservationRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `InMemoryPlanRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `InMemoryReasoningRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `InMemorySituationRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `IntegrationError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `IntentRouter` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `InvalidCognitiveContextError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `InvalidDecisionInputError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `InvalidDecisionRecordError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `InvalidExecutionPlanError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `InvalidLifecycleTransitionError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `InvalidMissionPlanError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `InvalidMissionSpecificationError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `InvalidPlanTransitionError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `InvalidReasoningInputError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `InvalidReasoningRequestError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `InvalidReasoningResultError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `InvalidReasoningSessionTransitionError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `InvalidStateTransitionError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `InventoryTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `KnowledgeAcquisitionDirector` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `KnowledgeDirector` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `KnowledgeDirectorCheck` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `KnowledgeGapPropagationTracer` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `KnowledgeGroundingTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `KnowledgeHandler` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `KnowledgeRegistryRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `LifecycleError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `MarkdownParserTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `MemoryEntry` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `MemoryEntryKind` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `MetricState` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `Mission` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `MissionCompilationRequest` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `MissionCompilerError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `MissionDependencyCycleError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `MissionEventPublisher` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `MissionExecutionRequest` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `MissionNotFoundError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `MissionPlanner` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `MissionPriority` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `MissionProvider` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `MissionStore` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `MissionTrace` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `NoAdmissibleCourseOfActionError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `NoDirectorMethods` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ObjectRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ObjectiveGrounding` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ObservationDirector` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ObservationDirectorTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ObservationRepositoryClosedError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `OrganizationalSupervisor` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `OrphanPlanNodeError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `PersistenceRecordKind` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `PlanNotFoundError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `PlanRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ProjectionProviderNotFoundError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ProjectionRegistry` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `PromotionPlanner` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `PropositionNotFoundError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ProvenanceRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `PythonParserTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `QueryUnderstanding` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ReasoningDisposition` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ReasoningPolicy` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ReasoningQuery` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ReasoningRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ReasoningRepositoryClosedError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ReasoningRepositoryDisposition` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ReasoningRequest` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ReasoningResult` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ReasoningResultNotFoundError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ReasoningSession` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ReasoningSessionContractError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ReasoningSessionId` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ReasoningSessionLifecycle` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ReasoningSessionLifecycleError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ReasoningSessionMetadata` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ReasoningSessionState` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ReasoningTraceStep` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RecoveryRequest` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RegistryCounter` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `RelationshipRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `Repository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryAccessError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryArtifact` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryArtifactAssessment` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryAuditAssessment` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryAuditDiscoveryError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryAuditFixture` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryAuditManifest` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryAuditPolicy` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryAuditStatistics` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryConstitutionalAuditEngine` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryConstitutionalAuditReporter` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryConstitutionalAuditTests` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryCoverageStatus` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryEdge` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryEdgeKind` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryFile` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryHealth` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryIntegrationAuditor` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryIntegrityStatus` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryInventory` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryInventoryBuilder` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryInventoryVerifier` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryLifecycleState` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryNode` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryNodeKind` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryNotFoundError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryPolicy` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryProjectionAssessment` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryProjectionIntegrity` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryProjectionMetrics` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryProjectionTests` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryRealityModelingTests` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryStatistics` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepositoryVerificationReport` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepresentationDirector` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `RepresentationRequest` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `RepresentationResult` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `ResolvedDirectorDispatch` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `RetrievalDirector` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `RetrievalDirectorTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `RuntimeLocator` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `SQLiteCognitiveWorkspaceRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `SQLiteSourceRegistryRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `SafeCommitError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `SearchResponse` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `SegmentationRequest` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `SelectionTrace` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `SessionAlreadyActiveError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `SessionAttribute` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `SessionNotActiveError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `SituationDisposition` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `SituationNotFoundError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `SituationProjector` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `SituationQuery` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `SituationRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `SituationRepositoryClosedError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `SituationSnapshot` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `SituationStatus` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `SourceRegistryNotFoundError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `StaticExecutiveProvider` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `StaticPublicSurfaceEvaluator` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `StatusState` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `StoragePathError` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `SubmitDirector` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `TerminalReasoningSessionError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `TestGenesis3A2PersistentWorkspaceRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `TimelineInterprocessLock` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `TimelineQueryEngine` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `TimelineRepositoryConflictError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `TimelineRepositoryError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `TimelineRepositoryIndexes` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `TimelineRepositoryIntegrityError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `TimelineRepositoryIntegrityReport` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `TimelineRepositoryStatistics` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `TimelineRepositoryStorageError` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `ToolPlanner` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `TraceabilityRecord` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `VerificationTests` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `WorkingMemory` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `WorkingMemorySnapshot` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `WorkspaceConversationRequest` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `WorkspaceConversationResponse` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `WorkspaceIntegrationPipeline` | **UNKNOWN** | Static existence found, but canonical runtime ownership is unproven. |
| `WorkspaceIntegrationRequest` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |
| `_PrefixRepository` | **UNKNOWN** | Potential overlap requires consumer and runtime verification. |

## Follow-on

1. Verify duplicate candidates against actual consumers.
2. Certify one canonical service, orchestrator, compiler, repository, request model, response model, and trace model.
3. Preserve compatibility adapters until every consumer has migrated.
4. Attach IX-A4.1B retrieval inventory to this certified Executive call graph.
