# ADR-0019 — Adopt a Canonical Evidence Model

**Status:** Accepted  
**Date:** 2026-07-20  
**Decision Domain:** Genesis / Reasoning Architecture  
**Related Architecture:** GENESIS-II-A4  
**Supersedes:** None  

---

## Context

JARVIS currently possesses certified reasoning-session contracts, session
lifecycle governance, canonical reasoning fixtures, constitutional reasoning
contexts, and domain-based verification architecture.

Future reasoning phases require a stable representation for information that
participates in reasoning.

Without a canonical model, individual subsystems may independently represent
evidence as:

- search results;
- document excerpts;
- user statements;
- memory records;
- observations;
- confidence-bearing strings;
- tool outputs;
- inferred facts.

These representations would create incompatible semantics, duplicate
confidence models, incomplete provenance, and weak explainability.

The architecture must also remain compatible with multiple reasoning
approaches, including probabilistic inference, belief functions, formal
argumentation, truth maintenance, belief revision, causal reasoning, and
decision theory.

---

## Decision

JARVIS will adopt a Canonical Evidence Model as a constitutional component of
the Genesis reasoning architecture.

Evidence will be defined as:

> A traceable information-bearing record offered for reasoning.

The model will distinguish Evidence from:

- information;
- claims;
- arguments;
- beliefs;
- hypotheses;
- decisions;
- missions.

Canonical Evidence Records will be:

- immutable;
- deterministically identifiable;
- provenance-bearing;
- temporally scoped;
- modality-aware;
- uncertainty-aware;
- relationship-capable;
- supersedable without destructive mutation.

Context-dependent evaluations will be represented separately as Evidence
Assessments.

The architecture will not impose one universal reasoning or uncertainty
algorithm.

---

## Decision Details

### Evidence Records

Evidence Records will preserve historical reasoning inputs.

They will not contain final belief, decision, or hypothesis ranking.

### Evidence Assessments

Assessments will capture contextual judgments such as:

- source reliability;
- content credibility;
- relevance;
- freshness;
- independence;
- diagnosticity;
- decision impact.

Assessments will not mutate Evidence Records.

### Evidence Relationships

Relationships will be typed and directional.

The initial model is expected to support concepts such as:

- derivation;
- corroboration;
- contradiction;
- duplication;
- qualification;
- dependency;
- supersession;
- shared origin.

### Uncertainty

Uncertainty will use an explicit type discriminator.

The canonical model will permit different representations rather than reduce
all uncertainty to a generic floating-point confidence value.

### Modality

The architecture will distinguish observational, inferential, causal,
interventional, counterfactual, predictive, normative, and procedural
assertions.

### Algorithmic Neutrality

The Evidence Model will standardize reasoning inputs without requiring all
reasoning systems to use the same algorithm.

---

## Alternatives Considered

### Alternative 1 — Use Search Results as Evidence

Rejected.

Search results are retrieval artifacts and do not provide a complete,
universal reasoning representation.

### Alternative 2 — Store a Statement and Confidence Score

Rejected.

A statement plus a generic confidence value conflates source reliability,
content credibility, uncertainty, diagnosticity, and belief.

### Alternative 3 — Make Everything Evidence

Rejected.

Claims, arguments, beliefs, hypotheses, and decisions have distinct cognitive
responsibilities and lifecycle rules.

### Alternative 4 — Select One Universal Reasoning Calculus

Rejected.

Bayesian, belief-function, argumentation, causal, and decision-theoretic
methods solve different classes of problems.

The constitutional model must permit their coexistence.

### Alternative 5 — Allow Mutable Evidence Records

Rejected.

Mutable historical records would weaken provenance, auditability, belief
revision, and deterministic explanation.

Corrections will occur through append-only relationships and replacement
records.

---

## Consequences

### Positive

- All reasoning subsystems gain a shared cognitive language.
- Evidence provenance becomes auditable.
- Future decisions can expose their supporting basis.
- Belief revision can preserve historical reasoning.
- Duplicate sources can be distinguished from independent corroboration.
- Multiple uncertainty and reasoning algorithms remain possible.
- Knowledge, Memory, Reasoning, and Executive subsystems can interoperate
  without redefining evidence semantics.

### Negative

- More contracts and identifiers are required.
- Contextual assessment becomes a separate architectural concern.
- Evidence ingestion will require normalization.
- Existing search and memory results will eventually need adapters.
- Reasoning implementation will initially be more deliberate than direct
  prompt-to-answer processing.

### Risks

- The model could become overly broad.
- Future phases could improperly place Claim or Belief behavior inside the
  Evidence package.
- Typed vocabularies could expand without governance.
- Source-dependence analysis could be ignored by downstream consumers.

These risks will be controlled through strict package boundaries,
constitutional verification, and independent future Genesis phases.

---

## Implementation Constraints

The future Evidence package must:

- use immutable public contracts;
- generate deterministic identities;
- expose stable public imports;
- avoid inference-engine implementation;
- avoid persistence implementation;
- avoid network and process execution;
- depend only on certified lower-level Genesis contracts;
- provide deterministic canonical fixtures;
- participate in Genesis domain verification.

---

## Validation

This decision will be validated through:

```text
dev/verify_genesis_2a4.sh
dev/verify_genesis_all.sh
dev/verify_all.sh
```

Certification must cover the requirements specified in:

```text
docs/architecture/genesis/reasoning/
GENESIS_II_A4_CANONICAL_EVIDENCE_MODEL.md
```

---

## Result

The Canonical Evidence Model becomes the first formal reasoning substrate
above the certified Reasoning Context.

Future Claims, Arguments, Beliefs, Hypotheses, Situation Models, Decisions,
and Executive Recommendations will reference this model rather than invent
independent evidence representations.
