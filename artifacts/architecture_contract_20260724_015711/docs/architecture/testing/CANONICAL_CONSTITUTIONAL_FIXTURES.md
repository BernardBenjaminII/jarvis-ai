# Canonical Constitutional Test Fixtures

**Document ID:** `GENESIS-II-A2R`  
**Version:** `1.0.0`  
**Status:** Implementation Candidate  
**Authority:** ADR-0018  
**Subsystem:** Engineering Governance  
**Depends On:** Genesis II-A1 and Genesis II-A2

## Purpose

Genesis II-A2R establishes the canonical fixture framework required by
ADR-0018. It repairs the II-A2 certification path and prevents later Genesis
phases from guessing or duplicating constitutional constructors.

## Source-of-Truth Rule

Certified public contracts define constitutional reality.

Canonical fixtures construct valid deterministic examples exclusively through
those contracts. Fixtures do not reproduce validation rules and do not import
private implementation modules.

## Reasoning Fixture Surface

The canonical reasoning fixture module exposes:

```python
make_identifier(...)
make_metadata(...)
make_reasoning_session(...)
```

It also exposes deterministic defaults for namespace, identity material, and
the creating authority.

## Lifecycle Compatibility Repair

Genesis II-A1 constitutionally defines the initial session revision as zero.
Genesis II-A2R therefore confirms that the lifecycle accepts revision zero and
that the first legal transition advances revision from zero to one.

This is a compatibility correction, not a relaxation of lifecycle law.
Revisions remain non-negative integers and every accepted transition advances
the revision by exactly one.

## Verification Order

Dependent verification follows this order:

```text
Certified II-A1 contracts
        ↓
Canonical fixture certification
        ↓
II-A2 lifecycle certification
        ↓
Later Genesis phases
```

## Prohibitions

Once a canonical fixture exists, dependent tests shall not:

- guess constructor signatures;
- use reflection to invent required contract values;
- duplicate constitutional defaults;
- bypass public validation;
- import private contract implementation modules; or
- define competing local fixture constructors.

## Certification Requirements

II-A2R passes only when:

- fixture modules compile;
- public fixture imports succeed;
- identifiers are valid and deterministic;
- metadata follows certified normalization;
- sessions default to revision zero and `CREATED`;
- fixture objects remain immutable;
- explicit overrides work;
- invalid values continue to fail contract validation;
- II-A1 regression tests pass;
- II-A2 imports the canonical fixture;
- duplicated II-A2 fixture logic is absent; and
- ADR-0018 is present.

## Constitutional Declaration

Fixtures construct validity. Tests verify behavior. Contracts define reality.

**Build the Constitution once. Construct from it forever.**
