# JARVIS Evidence Engine

**Status:** Canonical subsystem specification  
**Canonical package:** `core.evidence`  
**Architecture release:** Genesis IV-R3A Pack 3

## 1. Mission

The Evidence Engine transforms validated observations into deterministic,
explainable, auditable evidence suitable for reasoning and executive decisions.

It answers five distinct questions:

1. Is the source observation admissible?
2. What evidence record should be constructed?
3. How does that record relate to other evidence?
4. Is the available body of evidence sufficient?
5. What stable evidence input may reasoning consume?

## 2. Design Principles

The Evidence Engine is:

- deterministic;
- immutable at its contract boundaries;
- provenance preserving;
- policy driven;
- explainable;
- auditable;
- serialization stable;
- side-effect free in its domain evaluation layers;
- isolated from reasoning algorithms.

## 3. Canonical Pipeline

```text
Observation
    |
    v
Validation
    |
    v
Admissibility Evaluation
    |
    +--> Rejected / Deferred
    |
    v
Evidence Construction
    |
    v
Relationship Analysis
    |
    v
Aggregation and Sufficiency
    |
    v
Reasoning Input
```

## 4. Architectural Layers

### 4.1 Foundation

Current canonical files:

- `core/evidence/enums.py`
- `core/evidence/errors.py`
- `core/evidence/contracts.py`
- `core/evidence/__init__.py`

Responsibilities:

- stable vocabulary;
- immutable contracts;
- validation invariants;
- deterministic canonical serialization;
- public API exports.

### 4.2 Admissibility

Planned canonical files:

- `core/evidence/policy.py`
- `core/evidence/rules.py`
- `core/evidence/evaluator.py`
- `core/evidence/admissibility.py`

Responsibilities:

- immutable policy definition;
- deterministic rule evaluation;
- reason-coded outcomes;
- evaluation traces;
- no persistence;
- no evidence construction.

### 4.3 Construction

Planned responsibility:

- produce an `EvidenceRecord` from an admitted observation and decision;
- preserve provenance and policy identifiers;
- calculate deterministic identifiers and fingerprints;
- perform no relationship or sufficiency analysis.

### 4.4 Relationships

Planned responsibility:

- represent support, contradiction, corroboration, duplication, and dependency;
- remain deterministic and explainable;
- avoid mutating evidence records.

### 4.5 Aggregation and Sufficiency

Planned responsibility:

- assemble evidence sets;
- calculate policy-defined sufficiency;
- identify gaps and conflicts;
- expose reasoning-ready evidence without performing reasoning.

### 4.6 Runtime Integration

Planned responsibility:

- orchestrate domain components;
- connect registries or persistence;
- expose stable application services;
- preserve domain-layer independence.

## 5. Dependency Direction

```text
enums/errors
     |
     v
contracts
     |
     v
policy/rules
     |
     v
evaluator/admissibility
     |
     v
construction
     |
     v
relationships
     |
     v
aggregation
     |
     v
runtime service
     |
     v
reasoning consumer
```

Dependencies must not point from Evidence into Reasoning or Executive.

## 6. Admissibility Boundary

The admissibility layer consumes observation references or observation-domain
contracts and produces an `AdmissibilityDecision`.

It does not:

- create an `EvidenceRecord`;
- write to a registry;
- discover relationships;
- aggregate evidence;
- calculate reasoning confidence;
- issue recommendations.

## 7. Policy Families

The architecture reserves the following policy families:

- observation completeness;
- provenance completeness;
- source reliability;
- integrity status;
- temporal validity and freshness;
- duplication indicators;
- chain-of-custody requirements;
- supported observation type;
- policy-version compatibility.

Each rule must emit a stable rule identifier and an explainable result.

## 8. Public Compatibility

The stable public API is defined through `core.evidence.__all__`.

Future releases may add exports. Existing certified exports may only be removed
through an explicit compatibility-breaking decision and migration.

## 9. Certification and Compatibility

Certification proves a pack satisfies the specification in force when released.

Compatibility verification proves later packs preserve promised public behavior
while allowing intentional architectural evolution.

Historical certification tests are not permanent prohibitions against adding
new capabilities.

## 10. Release Sequence

- **Genesis IV-R3A** — Evidence foundation and deterministic contracts.
- **Genesis IV-R3B** — Admissibility policy foundation.
- **Genesis IV-R3C** — Evidence construction.
- **Genesis IV-R3D** — Evidence relationships.
- **Genesis IV-R3E** — Aggregation and sufficiency.
- **Genesis IV-R3F** — Runtime integration.
- **Genesis IV-R3G** — Evidence subsystem freeze.
