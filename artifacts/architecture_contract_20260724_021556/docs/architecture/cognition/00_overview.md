# Cognition Subsystem Overview

**Architecture:** Genesis IV  
**Consolidation phase:** Genesis IV-R0  
**Package:** R0-A Repository Skeleton  
**Status:** Active

---

# 1. Purpose

The cognition subsystem transforms normalized representations into auditable
cognitive objects suitable for interpretation, reasoning, and justification.

It does not own:

- knowledge acquisition;
- source-file storage;
- user-interface behavior;
- executive authority;
- mission execution;
- transport APIs.

---

# 2. Permanent Package Topology

core/cognition/
├── __init__.py
├── common/
├── observation/
├── evidence/
├── claims/
├── relationships/
├── hypotheses/
├── interpretation/
├── justification/
└── reasoning/

During Genesis IV-R0, existing flat modules are migrated incrementally into
these packages.

The facade at core/cognition/__init__.py remains the stable public API.

---

# 3. Layer Responsibilities
Common

Shared contracts, normalization, serialization, errors, common enums, and
cross-layer validation primitives.

Common may not import any higher cognition layer.

Observation

Explicit extracted or sensed information with source references, normalized
values, and confidence.

Observation may depend only on common infrastructure and approved
representation contracts.

Evidence

Provenance, evidence records, direction, quality, evidence chains, evidence
association, and evidence validation.

Evidence may depend on common and observation.

Claims

Normalized evidence-grounded propositions, claim construction, claim
classification, status, polarity, scope, and validation.

Claims may depend on common, observation, and evidence.

Relationships

Explicit relationships among claims or other approved cognitive objects.

Relationships may depend on claims and all lower cognition layers.

Hypotheses

Possible explanations or predictions built from claims and relationships.

Hypotheses may depend on relationships and all lower cognition layers.

Interpretation

Contextual meaning produced from hypotheses and supporting cognitive state.

Interpretation may depend on hypotheses and lower cognition layers.

Reasoning

Defined reasoning operations applied to interpretations and lower cognitive
objects.

Reasoning may not assume planning or executive authority.

Justification

Auditable explanation structures that connect conclusions to reasoning,
hypotheses, claims, evidence, observations, assumptions, and policies.

---

# 4. Migration Strategy

Genesis IV-R0 uses incremental migration.

R0-A

Create package topology, architectural constitution, and topology
verification. No production implementation moves.

R0-B

Migrate shared infrastructure into common/ while preserving compatibility.

R0-C

Migrate observation implementation.

R0-D

Migrate evidence implementation.

R0-E

Migrate claim implementation.

R0-F

Stabilize the facade, enforce the import DAG, and certify the reorganized
subsystem.

R0-G

Consolidate permanent subsystem documentation and complete final
certification.

Every migration must leave all existing public imports and behavioral tests
green.

---

# 5. Public API

Consumers use:

from core.cognition import Observation
from core.cognition import EvidenceRecord
from core.cognition import ClaimRecord

Internal package paths are implementation details unless explicitly documented
otherwise.

---

# 6. Transitional Rule

During R0 migration, flat modules and new package directories will temporarily
coexist.

New packages must not shadow or replace existing public objects until their
dedicated migration package:

moves the implementation;
updates imports;
provides compatibility re-exports where necessary;
passes regression verification.

The coexistence is deliberate and temporary.

---

# 7. Certification Requirement

R0-A is complete only when verification confirms:

every permanent package exists;
every package is importable;
the existing cognition facade remains importable;
the existing facade export set is unchanged;
placeholder packages export no accidental production symbols;
production modules remain in their current locations;
the architecture constitution exists;
the cognition overview exists;
ADR-0020 exists;
all pre-existing Genesis IV tests remain green.
