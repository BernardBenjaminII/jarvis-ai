# Genesis II-A3 — Constitutional Reasoning Context

**Document ID:** `GENESIS-II-A3`  
**Version:** `1.0.0`  
**Status:** Implementation Candidate  
**Subsystem:** Reasoning Engine  
**Depends On:** Genesis II-A1, II-A2, II-A2R  
**Successor:** Genesis II-A4 Evidence Collection

## 1. Purpose

Genesis II-A3 introduces the immutable constitutional state within which
reasoning occurs.

A reasoning session establishes identity and lifecycle. A reasoning context
establishes the question, scope, constraints, assumptions, decision criteria,
and unresolved questions that govern the work performed inside that session.

II-A3 does not perform inference, collect evidence, rank alternatives, or
form decisions.

## 2. Constitutional Boundary

II-A3 owns:

- reasoning-context identity;
- linkage to a certified reasoning session;
- the primary reasoning question;
- optional purpose and operational linkage;
- explicit constraints;
- explicit assumptions;
- weighted decision criteria;
- unresolved questions;
- deterministic extension attributes;
- immutable revisioned context snapshots; and
- deterministic context update operations.

II-A3 does not own:

- evidence records;
- evidence provenance;
- model execution;
- prompts;
- deliberation traces;
- alternative generation;
- scoring;
- recommendation formation;
- decisions; or
- execution.

These belong to later Genesis phases.

## 3. Context Model

```text
ReasoningSession
        │
        ▼
ReasoningContext
├── context identity
├── session identity
├── primary question
├── purpose
├── mission/objective linkage
├── constraints
├── assumptions
├── decision criteria
├── open questions
├── attributes
├── revision
└── schema version
```

## 4. Determinism

All keyed collections are:

- immutable tuples;
- normalized through their constitutional contracts;
- rejected when duplicate keys are present; and
- sorted lexicographically by normalized key.

Equivalent valid inputs therefore produce equivalent context snapshots.

## 5. Revision Law

A newly constructed reasoning context begins at revision zero.

Each accepted immutable operation produces a new snapshot and increments the
revision by exactly one.

The original snapshot remains unchanged.

## 6. Identity Law

`ReasoningContextId` is UUID-backed and may be:

- constructed from an existing UUID value; or
- deterministically derived using UUIDv5.

A reasoning context is permanently linked to one
`ReasoningSessionId`.

II-A3 operations must not alter either identity.

## 7. Contract Inventory

### `ReasoningConstraint`

A binding condition limiting acceptable reasoning or decisions.

### `ReasoningAssumption`

An explicit proposition currently treated as true.

### `DecisionCriterion`

A weighted standard used later to assess candidate decisions. Weight is an
integer from 1 through 100.

### `OpenReasoningQuestion`

An unresolved question with an integer priority from 1 through 100.

### `ReasoningContextAttribute`

A deterministic extension key/value pair.

### `ReasoningContext`

The complete immutable constitutional frame.

## 8. Manager Operations

`ReasoningContextManager` provides deterministic immutable operations:

- replace the primary question;
- add a constraint;
- add an assumption;
- add a decision criterion;
- add an open question; and
- add an extension attribute.

Duplicate keyed values are rejected rather than silently replaced.

Explicit replacement and removal semantics are deferred until a later
context-governance phase requires them.

## 9. Fixture Compliance

ADR-0018 applies.

II-A3 extends the canonical reasoning fixture library with:

```python
make_context_identifier(...)
make_reasoning_context(...)
```

All II-A3 tests construct constitutional context objects through these
fixtures unless the constructor itself is under direct test.

## 10. Certification Conditions

II-A3 is certified only when:

- all public contracts are immutable;
- all public imports are stable;
- context identifiers are valid and deterministic;
- keyed collections are deterministically ordered;
- duplicate keys are rejected;
- invalid weights and priorities are rejected;
- context revision begins at zero;
- every manager operation returns a new snapshot;
- every manager operation increments revision exactly once;
- context and session identities remain unchanged;
- canonical context fixtures pass certification;
- II-A1, II-A2, and II-A2R regressions pass;
- no private session module is imported; and
- no runtime, persistence, network, or model dependency enters the package.

## 11. Architectural Result

After II-A3, JARVIS possesses:

```text
Reasoning identity
        ↓
Reasoning lifecycle
        ↓
Canonical construction
        ↓
Constitutional reasoning context
```

Genesis II-A4 may now introduce evidence records without allowing evidence
collection to redefine the question, assumptions, constraints, or decision
criteria it is intended to serve.

## 12. Constitutional Principle

> Reasoning without context is inference without governance.

The context defines what JARVIS is trying to determine, what it must respect,
what it currently assumes, and how eventual decisions will be judged.
