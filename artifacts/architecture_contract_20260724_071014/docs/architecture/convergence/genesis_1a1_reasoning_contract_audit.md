# Genesis I-A1 — Reasoning Contract Audit

**Status:** Architecture baseline  
**Scope:** `core/reasoning/models.py`  
**Production code modified:** No

## Purpose

This audit records the canonical contract architecture that existed before Genesis evidence-model evolution began. It is a deterministic baseline, not a redesign.

## Executive Finding

The Reasoning Engine already contains a coherent immutable contract model. Genesis must evolve these contracts deliberately rather than introducing a parallel evidence or session architecture.

## Contract Inventory

| Contract | Fields | Frozen | Slotted | `to_dict()` | `__post_init__()` |
|---|---:|:---:|:---:|:---:|:---:|
| `EvidenceItem` | 8 | Yes | Yes | Yes | Yes |
| `Hypothesis` | 7 | Yes | Yes | Yes | Yes |
| `ReasoningRequest` | 6 | Yes | Yes | Yes | Yes |
| `HypothesisAssessment` | 10 | Yes | Yes | Yes | No |
| `ReasoningTraceStep` | 5 | Yes | Yes | Yes | No |
| `PlanningRecommendation` | 6 | Yes | Yes | Yes | No |
| `ReasoningResult` | 11 | Yes | Yes | Yes | No |

## Detailed Contracts

### `EvidenceItem`

One explicit piece of evidence available to a reasoning session.

**Fields**

- `evidence_id: str`
- `proposition: str`
- `stance: EvidenceStance`
- `source_ref: str`
- `kind: EvidenceKind` — defaulted
- `reliability: float` — defaulted
- `confidence: float` — defaulted
- `metadata: Mapping[str, Any]` — defaulted

**Methods:** `__post_init__()`, `to_dict()`

**Properties:** `weight`

### `Hypothesis`

One candidate explanation or course of action to assess.

**Fields**

- `hypothesis_id: str`
- `statement: str`
- `supporting_evidence_ids: tuple[str, ...]` — defaulted
- `contradicting_evidence_ids: tuple[str, ...]` — defaulted
- `assumptions: tuple[str, ...]` — defaulted
- `proposed_actions: tuple[str, ...]` — defaulted
- `metadata: Mapping[str, Any]` — defaulted

**Methods:** `__post_init__()`, `to_dict()`

**Properties:** None

### `ReasoningRequest`

Complete deterministic input to the Reasoning Engine.

**Fields**

- `request_id: str`
- `goal: str`
- `evidence: tuple[EvidenceItem, ...]`
- `hypotheses: tuple[Hypothesis, ...]`
- `constraints: tuple[str, ...]` — defaulted
- `context: Mapping[str, Any]` — defaulted

**Methods:** `__post_init__()`, `to_dict()`

**Properties:** `fingerprint`

### `HypothesisAssessment`

Auditable scoring result for one hypothesis.

**Fields**

- `hypothesis_id: str`
- `statement: str`
- `support_score: float`
- `contradiction_score: float`
- `confidence: float`
- `disposition: HypothesisDisposition`
- `supporting_evidence_ids: tuple[str, ...]`
- `contradicting_evidence_ids: tuple[str, ...]`
- `assumptions: tuple[str, ...]`
- `rationale: tuple[str, ...]`

**Methods:** `to_dict()`

**Properties:** None

### `ReasoningTraceStep`

One deterministic, inspectable reasoning operation.

**Fields**

- `sequence: int`
- `operation: str`
- `inputs: tuple[str, ...]`
- `output: str`
- `explanation: str`

**Methods:** `to_dict()`

**Properties:** None

### `PlanningRecommendation`

Structured bridge from reasoning into future planning.

**Fields**

- `objective: str`
- `rationale: str`
- `recommended_actions: tuple[str, ...]`
- `assumptions: tuple[str, ...]`
- `constraints: tuple[str, ...]`
- `risks: tuple[str, ...]`

**Methods:** `to_dict()`

**Properties:** None

### `ReasoningResult`

Complete output of one deterministic reasoning session.

**Fields**

- `session_id: str`
- `request_id: str`
- `request_fingerprint: str`
- `status: ReasoningStatus`
- `assessments: tuple[HypothesisAssessment, ...]`
- `selected_hypothesis_id: str | None`
- `missing_information: tuple[str, ...]`
- `contradictions: tuple[str, ...]`
- `planning_recommendation: PlanningRecommendation | None`
- `trace: tuple[ReasoningTraceStep, ...]`
- `fingerprint: str`

**Methods:** `to_dict()`

**Properties:** None

## Canonical Infrastructure

Top-level model helpers:

- `_require_text()`
- `_require_probability()`
- `canonicalize()`
- `canonical_fingerprint()`

Imported reasoning enumerations:

- `EvidenceKind`
- `EvidenceStance`
- `HypothesisDisposition`
- `ReasoningStatus`

## Structural Conclusions

- **Canonical contract module present:** Yes
- **Expected contracts present:** Yes
- **All contracts frozen and slotted:** Yes
- **All contracts serializable:** Yes
- **Canonical serialization present:** Yes
- **Evidence weight present:** Yes
- **Request fingerprint present:** Yes
- **Evidence model is embedded in models module:** Yes
- **Reasoning session input present:** Yes
- **Reasoning session output present:** Yes
- **Planning bridge present:** Yes

## Genesis Migration Observations

- EvidenceItem is already the canonical evidence contract; Genesis must evolve it rather than introduce a competing evidence model.
- ReasoningRequest already represents a deterministic session input and includes a canonical fingerprint.
- ReasoningResult already represents a complete reasoning-session output, including traceability and a planning bridge.
- All current contracts use frozen, slotted dataclasses and should retain those immutability guarantees.
- Canonical serialization and SHA-256 fingerprinting are established cross-contract infrastructure and should remain backward compatible.
- Future evidence provenance, admission, and assessment contracts should integrate with EvidenceItem through deliberate migration.

## Architectural Decision

`core/reasoning/models.py` remains the canonical reasoning-contract module during the first Genesis increment. No competing `core/reasoning/evidence/` package will be introduced until a specific migration requirement justifies it.

The next audit increment should inspect orchestration in `core/reasoning/service.py` and determine how the existing contracts participate in a complete reasoning session.
