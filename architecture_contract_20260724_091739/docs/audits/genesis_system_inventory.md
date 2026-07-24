# JARVIS Genesis System Inventory

**Generated:** 2026-07-21T16:45:05.465032+00:00  
**Branch:** `feature/genesis-iv-r3-evidence-engine`  
**HEAD:** `95e508406d4aec9b0e86ba1e82c944f78a5a3003`  
**Architecture fingerprint:** `c54d96b19d584731580d8e526401406c95083caacd4bd10ac51f54249e65456a`  
**Working tree:** contains changes

## 1. Scope

This inventory is derived from the repository itself. It excludes Git internals,
migration backups, virtual environments, caches, build outputs, and external
runtime or knowledge volumes.

## 2. Repository Summary

| Measure | Count |
| --- | ---: |
| Production Python modules | 269 |
| Production Python lines | 23932 |
| Test files | 32 |
| Development scripts | 247 |
| Documentation files | 183 |

## 3. Production Package Inventory

| Package | Modules | Lines | Public classes | __all__ exports |
| --- | --- | --- | --- | --- |
| core | 1 | 0 | 0 | 0 |
| core.bootstrap | 36 | 931 | 10 | 0 |
| core.capabilities | 9 | 365 | 8 | 8 |
| core.capability_runtime_cli | 1 | 92 | 0 | 0 |
| core.cognition | 55 | 7096 | 104 | 156 |
| core.config | 1 | 10 | 0 | 0 |
| core.discovery | 1 | 0 | 0 | 0 |
| core.evidence | 4 | 947 | 41 | 44 |
| core.executive | 19 | 3030 | 61 | 57 |
| core.gmail_archive_candidates | 1 | 90 | 0 | 0 |
| core.gmail_cleanup_report | 1 | 105 | 0 | 0 |
| core.gmail_reader_test | 1 | 14 | 0 | 0 |
| core.gmail_test | 1 | 13 | 0 | 0 |
| core.knowledge_catalog | 21 | 1837 | 7 | 0 |
| core.knowledge_graph | 8 | 338 | 2 | 0 |
| core.knowledge_mapper | 7 | 127 | 0 | 0 |
| core.knowledge_system | 1 | 0 | 0 | 0 |
| core.reasoning | 26 | 4170 | 77 | 91 |
| core.representation | 7 | 1887 | 42 | 19 |
| core.semantic_digest | 7 | 356 | 1 | 0 |
| core.src | 60 | 2524 | 13 | 0 |
| core.utils | 1 | 0 | 0 | 0 |

## 4. Cognitive Subsystem Presence

| Subsystem | Observed modules |
| --- | ---: |
| Evidence | 4 |
| Observation | 16 |
| Reasoning | 27 |
| Executive | 19 |

## 5. Evidence Engine Inventory

| File | Classes | Functions | Declared exports |
| --- | --- | --- | --- |
| core/evidence/__init__.py | — | — | SCHEMA_VERSION, AdmissibilityDecision, AdmissibilityReason, AdmissibilityStatus, AssessmentMethod, EvidenceAdmissibilityError, EvidenceAggregationError, EvidenceAssessment, EvidenceConflictError, EvidenceConstructionError, EvidenceDirection, EvidenceDirectness, EvidenceError, EvidenceFingerprintError, EvidenceGap, EvidenceGapType, EvidenceIntegrityError, EvidenceNotFoundError, EvidencePolicyError, EvidenceRecord, EvidenceRelationship, EvidenceRelationshipError, EvidenceRelationshipType, EvidenceSerializationError, EvidenceSet, EvidenceStateTransitionError, EvidenceStatus, EvidenceSufficiencyStatus, EvidenceValidationError, IntegrityStatus, ObservationReferenceError, Proposition, PropositionError, PropositionModality, PropositionNotFoundError, PropositionStatus, PropositionValidationError, SerializableContract, SourceReliabilityClass, StableStringEnum, UnsupportedObservationError, WeightBreakdown, utc_now |
| core/evidence/contracts.py | SerializableContract, Proposition, WeightBreakdown, AdmissibilityDecision, EvidenceAssessment, EvidenceRecord, EvidenceRelationship, EvidenceGap, EvidenceSet | utc_now, _require_text, _normalize_optional_text, _require_score, _freeze_value, _freeze_mapping, _canonical_serialize | SCHEMA_VERSION, AdmissibilityDecision, EvidenceAssessment, EvidenceGap, EvidenceRecord, EvidenceRelationship, EvidenceSet, JSONValue, Proposition, SerializableContract, WeightBreakdown, utc_now |
| core/evidence/enums.py | StableStringEnum, EvidenceDirection, EvidenceStatus, AdmissibilityStatus, AdmissibilityReason, EvidenceRelationshipType, EvidenceDirectness, SourceReliabilityClass, EvidenceGapType, EvidenceSufficiencyStatus, PropositionStatus, PropositionModality, AssessmentMethod, IntegrityStatus | — | AdmissibilityReason, AdmissibilityStatus, AssessmentMethod, EvidenceDirection, EvidenceDirectness, EvidenceGapType, EvidenceRelationshipType, EvidenceStatus, EvidenceSufficiencyStatus, IntegrityStatus, PropositionModality, PropositionStatus, SourceReliabilityClass, StableStringEnum |
| core/evidence/errors.py | EvidenceError, EvidenceValidationError, EvidenceAdmissibilityError, EvidenceConstructionError, EvidenceIntegrityError, EvidenceConflictError, EvidenceRelationshipError, EvidenceAggregationError, EvidenceFingerprintError, EvidenceSerializationError, EvidenceStateTransitionError, PropositionError, PropositionValidationError, PropositionNotFoundError, EvidenceNotFoundError, ObservationReferenceError, UnsupportedObservationError, EvidencePolicyError | — | EvidenceAdmissibilityError, EvidenceAggregationError, EvidenceConflictError, EvidenceConstructionError, EvidenceError, EvidenceFingerprintError, EvidenceIntegrityError, EvidenceNotFoundError, EvidencePolicyError, EvidenceRelationshipError, EvidenceSerializationError, EvidenceStateTransitionError, EvidenceValidationError, ObservationReferenceError, PropositionError, PropositionNotFoundError, PropositionValidationError, UnsupportedObservationError |

### Files absent from the proposed next pack

- `core/evidence/policy.py`
- `core/evidence/rules.py`
- `core/evidence/evaluator.py`
- `core/evidence/admissibility.py`

## 6. Internal Dependency Edges

| Source package | Target package | Import statements |
| --- | --- | --- |
| core.bootstrap | core.src | 2 |
| core.capability_runtime_cli | core.capabilities | 2 |
| core.cognition | core.claim | 1 |
| core.cognition | core.claim_construction | 1 |
| core.cognition | core.claim_validation | 1 |
| core.cognition | core.confidence | 1 |
| core.cognition | core.contracts | 1 |
| core.cognition | core.enums | 1 |
| core.cognition | core.errors | 1 |
| core.cognition | core.evidence | 1 |
| core.cognition | core.evidence_chain | 1 |
| core.cognition | core.evidence_validation | 1 |
| core.cognition | core.extraction | 1 |
| core.cognition | core.identifiers | 1 |
| core.cognition | core.normalization | 1 |
| core.cognition | core.observation | 1 |
| core.cognition | core.provenance | 1 |
| core.cognition | core.serialization | 1 |
| core.cognition | core.validation | 1 |
| core.evidence | core.contracts | 1 |
| core.evidence | core.enums | 1 |
| core.evidence | core.errors | 1 |
| core.knowledge_catalog | core.knowledge_mapper | 1 |
| core.knowledge_catalog | core.semantic_digest | 1 |
| core.knowledge_graph | core.knowledge_catalog | 1 |
| core.representation | core.contracts | 1 |
| core.representation | core.segmentation | 1 |
| core.semantic_digest | core.knowledge_catalog | 1 |

## 7. Duplicate Public Symbols

| Symbol | Locations |
| --- | --- |
| AssessmentMethod | core/evidence/enums.py<br>core/reasoning/evidence/enums.py |
| Assumption | core/cognition/workspace/models.py<br>core/executive/planning/models.py |
| BootstrapRunner | core/bootstrap/lifecycle_runner.py<br>core/bootstrap/preflight_runner.py<br>core/bootstrap/runner.py |
| Capability | core/capabilities/base.py<br>core/executive/capabilities.py |
| CognitiveObject | core/cognition/common/object_model.py<br>core/representation/contracts.py |
| CognitiveObjectKind | core/cognition/common/object_model.py<br>core/cognition/enums.py |
| EvidenceAssessment | core/evidence/contracts.py<br>core/reasoning/evidence/contracts.py |
| EvidenceDirection | core/cognition/evidence.py<br>core/evidence/enums.py |
| EvidenceError | core/evidence/errors.py<br>core/reasoning/evidence/errors.py |
| EvidenceKind | core/cognition/evidence.py<br>core/reasoning/enums.py |
| EvidenceRecord | core/cognition/evidence.py<br>core/evidence/contracts.py<br>core/reasoning/evidence/contracts.py |
| EvidenceReference | core/cognition/workspace/models.py<br>core/executive/planning/models.py |
| EvidenceRelationship | core/evidence/contracts.py<br>core/reasoning/evidence/contracts.py |
| EvidenceRelationshipError | core/evidence/errors.py<br>core/reasoning/evidence/errors.py |
| EvidenceRelationshipType | core/evidence/enums.py<br>core/reasoning/evidence/enums.py |
| EvidenceSerializationError | core/evidence/errors.py<br>core/reasoning/evidence/errors.py |
| EvidenceStatus | core/evidence/enums.py<br>core/reasoning/evidence/enums.py |
| EvidenceValidationError | core/evidence/errors.py<br>core/reasoning/evidence/errors.py |
| ExecutionPlan | core/src/planner/execution_plan.py<br>core/src/runtime/execution_plan.py |
| Hypothesis | core/cognition/workspace/models.py<br>core/reasoning/models.py |
| Mission | core/executive/models.py<br>core/executive/planning/models.py |
| Observation | core/cognition/common/contracts.py<br>core/representation/contracts.py |
| Proposition | core/evidence/contracts.py<br>core/representation/contracts.py |
| RuntimeLocator | core/bootstrap/discovery/locator.py<br>core/src/discovery/runtime_locator.py |
| RuntimePaths | core/src/discovery/runtime_context.py<br>core/src/runtime/runtime_models.py |
| StableStringEnum | core/evidence/enums.py<br>core/reasoning/evidence/enums.py |
| canonical_fingerprint | core/cognition/common/serialization.py<br>core/reasoning/models.py |
| canonical_json | core/cognition/common/serialization.py<br>core/reasoning/evidence/serialization.py |
| canonicalize | core/cognition/common/serialization.py<br>core/reasoning/models.py |
| detect_capabilities | core/src/cognition/capability_registry.py<br>core/src/utils/capabilities.py |
| infer_collection_id | core/knowledge_catalog/assimilation/engine.py<br>core/knowledge_catalog/registrar.py |
| launch_api | core/bootstrap/services/api.py<br>core/bootstrap/services/venv.py |
| load_keyword_rules | core/knowledge_catalog/classifiers/keyword_classifier.py<br>core/knowledge_catalog/digest.py |
| load_rules | core/knowledge_catalog/assimilation/engine.py<br>core/knowledge_mapper/rules.py<br>core/semantic_digest/analyzer.py |
| main | core/bootstrap/main.py<br>core/capability_runtime_cli.py<br>core/executive/cli.py<br>core/gmail_archive_candidates.py<br>core/gmail_cleanup_report.py<br>core/knowledge_catalog/assimilation/cli.py<br>core/knowledge_catalog/backfill.py<br>core/knowledge_catalog/cli.py<br>core/knowledge_graph/cli.py<br>core/semantic_digest/cli.py |
| migrate | core/knowledge_catalog/assimilation/engine.py<br>core/knowledge_catalog/database.py |
| normalize | core/knowledge_catalog/assimilation/engine.py<br>core/semantic_digest/analyzer.py |
| normalize_optional_text | core/reasoning/context/validators.py<br>core/reasoning/evidence/validation.py |
| normalize_text | core/knowledge_catalog/digest.py<br>core/reasoning/evidence/validation.py |
| register_file | core/knowledge_catalog/registrar.py<br>core/knowledge_catalog/service.py |
| run | core/bootstrap/lifecycle/postflight.py<br>core/bootstrap/lifecycle/preflight.py<br>core/bootstrap/lifecycle/startup.py |
| sha256_file | core/knowledge_catalog/assimilation/engine.py<br>core/knowledge_catalog/digest.py |
| utc_now | core/cognition/common/object_model.py<br>core/cognition/layers/observation/models.py<br>core/cognition/workspace/models.py<br>core/evidence/contracts.py<br>core/executive/models.py<br>core/executive/planning/models.py<br>core/knowledge_catalog/assimilation/engine.py<br>core/knowledge_catalog/collections.py<br>core/knowledge_catalog/models.py<br>core/knowledge_catalog/registrar.py |

Duplicate names are review targets, not automatic defects. They may represent
bounded-context reuse, aliases, or competing canonical ownership.

## 8. Syntax Health

No syntax errors were detected in inventoried production modules.

## 9. Recent Repository History

- `95e5084 (HEAD -> feature/genesis-iv-r3-evidence-engine, tag: genesis-iv-r3a-pack2a, origin/feature/genesis-iv-r3-evidence-engine) Complete Genesis IV-R3A Pack 2A deterministic evidence contracts`
- `e3c4f45 (tag: genesis-iv-r2, tag: cognition-v1, origin/feature/genesis-iv-r0-cognition-consolidation, feature/genesis-iv-r0-cognition-consolidation) Complete Genesis IV-R2 Observation Engine`
- `10c3e0e (feature/genesis-iv-a1-observation-engine) Introduce Genesis IV evidence and claim cognition layers`
- `51a34f8 (tag: genesis-iv-a1, origin/feature/genesis-iv-a1-observation-engine) Introduce Genesis IV-A1 cognition foundation and deterministic observation engine`
- `f2ea552 (tag: genesis-v1.0, origin/stabilization/genesis-1.0, origin/feature/cognitive-representation-phase-xc2, stabilization/genesis-1.0, feature/genesis-iv-cognitive-interpretation, feature/cognitive-representation-phase-xc2) Remove temporary Genesis verifier backup`
- `f337e08 Complete Genesis III foundation and certify master architecture`
- `6db495f (feature/genesis-ii-a4-evidence-model) Stabilize repository artifact management`
- `72b6aa2 Add cognitive workspace catalog and search`
- `a752d77 Add persistent cognitive workspace repository`
- `b36aa61 Introduce Genesis cognitive workspace foundation`
- `3f0a8f3 Define Genesis II-A4 canonical evidence architecture`
- `aad481e (tag: genesis/ii-a3a-integrated, origin/feature/genesis-ii-a3a-verification-architecture, feature/genesis-ii-a3a-verification-architecture) Merge branch 'recovery/genesis-context' into feature/genesis-ii-a3a-verification-architecture`

## 10. Derived Next-Pack Boundary

The observed Evidence Engine currently provides domain vocabulary, errors, and
immutable contracts. The next pack should add deterministic admissibility policy
evaluation while deliberately excluding construction, persistence, relationship
analysis, aggregation, runtime orchestration, and reasoning integration.

### Recommended release

**Genesis IV-R3B Pack 1 — Admissibility Policy Foundation**

Proposed production files:

- `core/evidence/policy.py`
- `core/evidence/rules.py`
- `core/evidence/evaluator.py`
- `core/evidence/admissibility.py`

Proposed release assets:

- `docs/architecture/evidence_engine.md`
- `docs/decisions/ADR-00XX-certification-vs-compatibility.md`
- `tests/test_genesis_4r3b_pack1_admissibility_policy.py`
- `dev/verification/verify_genesis_4r3b_pack1.py`
- `dev/verify_genesis_4r3b_pack1.sh`

### Explicit exclusions

- Evidence record construction
- Registries or persistence
- Relationship graphs
- Aggregate sufficiency scoring
- Runtime service orchestration
- Direct reasoning-engine integration

## 11. Review Gate

Before implementation, inspect this report and its JSON companion for:

1. Existing observation contracts the evaluator must consume.
2. Existing modules that overlap the proposed policy boundary.
3. Dependency edges that could create upward or circular coupling.
4. Public enum values that constrain policy outcomes.
5. Stable exports that compatibility verification must preserve.
