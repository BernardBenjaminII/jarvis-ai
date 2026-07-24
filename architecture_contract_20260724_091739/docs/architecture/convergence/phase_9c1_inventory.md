# Phase IX-C1 Cognitive Architecture Inventory

## Audit metadata

- Schema version: `1.0`
- Generated: `2026-07-18T17:39:34.723475+00:00`
- Branch: `feature/cognitive-architecture-convergence`
- Project root: `/media/abdullah/JARVISDATA/Projects/jarvis-ai`

## Executive package summary

- Python files: `23`
- Public duplicate symbol names: `2`

| File | Lines | Syntax | Public symbols | SHA-256 |
| --- | --- | --- | --- | --- |
| core/executive/__init__.py | 53 | yes | — | 8aafcaed00ff |
| core/executive/capabilities.py | 94 | yes | DirectorReadiness, Capability, DirectorDescriptor, RoutingCandidate, RoutingDecision, normalize_capability, normalize_director_name | b9d1310cb3be |
| core/executive/cli.py | 121 | yes | default_database_path, parse_context, build_parser, print_json, main | e92c7330c115 |
| core/executive/contracts.py | 34 | yes | DirectorHandler, ExecutiveError, DirectorNotRegisteredError, MissionNotFoundError, InvalidMissionPlanError | 57145ed7f886 |
| core/executive/director.py | 166 | yes | ExecutiveDirector | bbaf03d4e410 |
| core/executive/engine.py | 247 | yes | MissionEngine | eb4e58e459b4 |
| core/executive/handlers.py | 136 | yes | executive_handler, placeholder_system_handler, KnowledgeHandler | 03fc15edc392 |
| core/executive/models.py | 108 | yes | utc_now, MissionStatus, TaskStatus, MissionTask, Mission, TaskExecutionResult | 992f7eac520e |
| core/executive/planner.py | 121 | yes | CapabilityRule, MissionPlanner | 9705d970028d |
| core/executive/planning/__init__.py | 102 | yes | — | a8af70d67d9a |
| core/executive/planning/dependencies.py | 218 | yes | collect_plan_element_ids, DependencyGraph, build_dependency_graph | d144bf37b52b |
| core/executive/planning/enums.py | 128 | yes | PlanState, MissionPriority, AuthorizationMode, RiskLevel, RiskStatus, ConstraintKind, DependencyType, ResourceKind, PlanElementKind | 22eda203587c |
| core/executive/planning/errors.py | 55 | yes | PlanningError, PlanningValidationError, DependencyGraphError, DependencyCycleError, MissingPlanElementError, DuplicatePlanElementError, InvalidPlanTransitionError, PlanNotFoundError, PlanVersionConflictError, ImmutablePlanVersionError | a448da389a9c |
| core/executive/planning/models.py | 551 | yes | new_identifier, utc_now, AuthorizationRequirement, EvidenceReference, Assumption, Constraint, ResourceRequirement, Risk, Dependency, Command, Activity, Task, Objective, Mission, PlanVersion, MissionPlan, create_plan_version | a8f872035e72 |
| core/executive/planning/repository.py | 131 | yes | PlanRepository, InMemoryPlanRepository | 87920c44327b |
| core/executive/planning/service.py | 211 | yes | PlanningService | 52884c1f12ea |
| core/executive/planning/validation.py | 194 | yes | ValidationReport, PlanValidator | 9d5b27bc24b5 |
| core/executive/planning_engine/__init__.py | 66 | yes | — | 8c9335b28b3c |
| core/executive/planning_engine/enums.py | 91 | yes | WorkItemKind, WorkItemState, ReadinessState, BlockerType, RecommendationType, ConfidenceBand, TraceSeverity, PlanningPolicy | 14dd3b690300 |
| core/executive/planning_engine/errors.py | 35 | yes | PlanningEngineError, InvalidExecutionSnapshotError, PlanningGraphError, DuplicateWorkItemError, UnknownWorkItemError, UnknownDependencyReferenceError, PlanningCycleError, UnsupportedPlanningPolicyError | ae07f8e24405 |
| core/executive/planning_engine/models.py | 531 | yes | utc_now, canonical_fingerprint, WorkItem, ExecutionRecord, ExecutionSnapshot, Blocker, ReadinessResult, DecisionTrace, Recommendation, PlanningAssessment | 5aadd0905432 |
| core/executive/registry.py | 196 | yes | DirectorRegistry | dc2ee435ec4f |
| core/executive/store.py | 185 | yes | MissionStore | ecc233ecf397 |

## Planning implementation locations

### `core/executive/planner.py`

- Files: `1`
- Symbols: `2`

- `core/executive/planner.py`

### `core/executive/planning`

- Files: `8`
- Symbols: `45`

- `core/executive/planning/__init__.py`
- `core/executive/planning/dependencies.py`
- `core/executive/planning/enums.py`
- `core/executive/planning/errors.py`
- `core/executive/planning/models.py`
- `core/executive/planning/repository.py`
- `core/executive/planning/service.py`
- `core/executive/planning/validation.py`

### `core/executive/planning_engine`

- Files: `4`
- Symbols: `28`

- `core/executive/planning_engine/__init__.py`
- `core/executive/planning_engine/enums.py`
- `core/executive/planning_engine/errors.py`
- `core/executive/planning_engine/models.py`

## Duplicate public symbols

### `Mission`

- `core/executive/models.py:68 (class)`
- `core/executive/planning/models.py:369 (class)`

### `utc_now`

- `core/executive/models.py:12 (function)`
- `core/executive/planning/models.py:35 (function)`
- `core/executive/planning_engine/models.py:24 (function)`

## Root-level whitepaper disposition

| Source | Proposed destination | Relationship | Source hash | Destination hash |
| --- | --- | --- | --- | --- |
| WP-0001-executive-cognitive-architecture.md | docs/whitepapers/WP-0001-executive-cognitive-architecture.md | destination_missing | 949e842bb948 | — |
| WP-0002-knowledge-engine.md | docs/whitepapers/WP-0002-knowledge-engine.md | destination_missing | 63508e50764e | — |
| WP-0003-reasoning-engine.md | docs/whitepapers/WP-0003-reasoning-engine.md | destination_missing | 089385afe5ec | — |
| WP-0004-executive-engine.md | docs/whitepapers/WP-0004-executive-engine.md | destination_missing | 6803f8f98d84 | — |
| WP-0005-planning-engine.md | docs/whitepapers/WP-0005-planning-engine.md | destination_missing | 0a828938ac57 | — |
| WP-0006-execution-engine.md | docs/whitepapers/WP-0006-execution-engine.md | destination_missing | 69d0a3c3fe1d | — |
| WP-0007-outcome-assessment.md | docs/whitepapers/WP-0007-outcome-assessment.md | destination_missing | 4dbbe80aae55 | — |
| WP-0008-experience-engine.md | docs/whitepapers/WP-0008-experience-engine.md | destination_missing | 2af5bd44be24 | — |
| WP-0009-memory-engine.md | docs/whitepapers/WP-0009-memory-engine.md | destination_missing | 1e4b2f836ae7 | — |
| WP-0010-engine-communication.md | docs/whitepapers/WP-0010-engine-communication.md | destination_missing | 8543c032812d | — |

## Findings

- Multiple planning implementations are present: core/executive/planner.py, core/executive/planning, core/executive/planning_engine
- 2 public symbol names appear in more than one Executive module.
- Root-level whitepapers do not yet have canonical destination files: WP-0001-executive-cognitive-architecture.md, WP-0002-knowledge-engine.md, WP-0003-reasoning-engine.md, WP-0004-executive-engine.md, WP-0005-planning-engine.md, WP-0006-execution-engine.md, WP-0007-outcome-assessment.md, WP-0008-experience-engine.md, WP-0009-memory-engine.md, WP-0010-engine-communication.md

## Recommendations

- Do not remove planner.py, planning/, or planning_engine/ until Phase IX-C2 assigns canonical ownership.
- Treat core/executive/planning/ as the leading canonical candidate because it already contains service, repository, validation, dependency, model, enum, and error layers.
- Compare planning_engine models and enums against planning/ before merging their contracts.
- Keep the Executive package responsible for orchestration, not detailed planning algorithms.
- Reconcile root-level whitepapers by content and hash rather than filename alone.
- Introduce the reasoning engine only after canonical planning contracts and Executive public exports are stable.

## IX-C1 decision

This report is an inventory only. No implementation is declared canonical by IX-C1.

Canonical ownership, file migration, compatibility adapters, and deletion decisions belong to Phase IX-C2.
