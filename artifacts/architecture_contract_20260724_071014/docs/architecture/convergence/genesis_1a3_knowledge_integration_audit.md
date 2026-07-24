# Genesis I-A3 — Knowledge Integration Audit

**Status:** Architecture baseline  
**Production code modified:** No  
**Audited modules:**

- `core/reasoning/knowledge.py`
- `core/reasoning/pipeline.py`

## Purpose

This audit records the existing boundary between retrieved knowledge and deterministic reasoning. It establishes the baseline that future Reasoning Session and evidence-provenance work must preserve.

## Executive Finding

JARVIS already has a distinct knowledge-adaptation boundary and a composition pipeline. Genesis should preserve both. Future changes should add session context and richer provenance around these components rather than moving their responsibilities into a new parallel architecture.

## Integration Flow

```text
External knowledge or ranked retrieval results
        ↓
KnowledgeEvidenceAdapter
        ↓
AdaptedEvidenceBatch
        ↓
Canonical EvidenceItem contracts
        ↓
DeterministicHypothesisGenerator
        ↓
ReasoningRequest
        ↓
ReasoningEngine
        ↓
ReasoningResult
        ↓
KnowledgeReasoningOutcome
```

## Module Inventory

| Module | Lines | Classes | Top-level functions |
|---|---:|---:|---:|
| `core/reasoning/knowledge.py` | 148 | 3 | 6 |
| `core/reasoning/pipeline.py` | 81 | 2 | 1 |

## Knowledge Adapter

### `KnowledgeEvidenceAdapterError`

Raised when knowledge output cannot be adapted.

- Dataclass: No
- Frozen: No
- Slotted: No

### `AdaptedEvidenceBatch`

_No class docstring._

- Dataclass: Yes
- Frozen: Yes
- Slotted: Yes

Fields:

- `query`
- `evidence`
- `rejected_count`
- `source_count`

### `KnowledgeEvidenceAdapter`

Accept production SearchResult objects or ranked dictionaries.

- Dataclass: No
- Frozen: No
- Slotted: No

Methods:

- `adapt(self, query, results, stance, minimum_text_length) -> AdaptedEvidenceBatch`

## Knowledge Reasoning Pipeline

### `KnowledgeReasoningOutcome`

_No class docstring._

- Dataclass: Yes
- Frozen: Yes
- Slotted: Yes

Fields:

- `evidence_batch`
- `generation`
- `reasoning`

### `KnowledgeReasoningPipeline`

Join an injected Knowledge search callable to reasoning.

- Dataclass: No
- Frozen: No
- Slotted: No

Methods:

- `__init__(self, search, adapter, generator, engine) -> None`
- `reason(self, goal, query, limit, constraints, context) -> KnowledgeReasoningOutcome`

## Public Integration Interfaces

### `KnowledgeEvidenceAdapter`

- `adapt()`

### `KnowledgeReasoningPipeline`

- `reason()`

## Structural Conclusions

- **Knowledge adapter present:** Yes
- **Adapted batch contract present:** Yes
- **Knowledge pipeline present:** Yes
- **Pipeline outcome contract present:** Yes
- **Canonical evidence dependency present:** Yes
- **Canonical reasoning request dependency present:** Yes
- **Canonical reasoning result dependency present:** Yes
- **Reasoning engine dependency present:** Yes
- **Hypothesis generator dependency present:** Yes
- **Expected knowledge classes present:** Yes
- **Expected pipeline classes present:** Yes

## Architectural Findings

- Knowledge adaptation is already separated from core inference and reasoning orchestration.
- The adapter is the canonical anti-corruption boundary between retrieval-shaped data and immutable reasoning evidence.
- The pipeline coordinates existing subsystems instead of duplicating their internal responsibilities.
- The pipeline should remain a composition layer and must not become the owner of evidence scoring, inference, or executive policy.
- Future ReasoningSession support should wrap or contextualize this pipeline rather than replace the adapter and engine boundaries.
- Evidence provenance evolution should begin at the adapter boundary because that is where external source metadata becomes canonical reasoning evidence.

## Migration Constraints

- Preserve KnowledgeEvidenceAdapter as the single conversion boundary for retrieval results entering reasoning.
- Preserve EvidenceItem as the canonical evidence contract until an explicit compatible migration is approved.
- Preserve deterministic identifiers generated from stable source content and references.
- Do not allow the integration pipeline to retrieve knowledge directly unless retrieval is explicitly delegated through an injected dependency.
- Do not introduce executive governance into the adapter; governance belongs to a future ReasoningSession or Executive integration layer.
- Do not permit pipeline orchestration to mutate knowledge, evidence, hypotheses, or reasoning results.

## Architectural Decision

`KnowledgeEvidenceAdapter` remains the canonical boundary where external retrieval data becomes immutable reasoning evidence.

`KnowledgeReasoningPipeline` remains a composition layer. It may coordinate adaptation, hypothesis generation, and reasoning, but it must not absorb the responsibilities of those components.

The future `ReasoningSession` will provide execution context, governance, budgets, and lifecycle state around this existing pipeline.

## Next Genesis Step

**Genesis I-A4 — Canonical Reasoning Architecture Baseline**

I-A4 will consolidate the contract, service, knowledge-adapter, and pipeline findings into one authoritative architecture map before the Reasoning Session model is introduced.
