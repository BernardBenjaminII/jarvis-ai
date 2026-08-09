# Genesis II-A3F — Hierarchical Roman Subphase Parser

**Status:** Implemented
**Predecessor:** Genesis II-A3E
**Purpose:** Admit underscore-delimited subphases beneath Roman-generation
identities without renaming existing verifiers.

## Problem

II-A3E recognized Roman-generation verifier identities such as:

```text
dev/verify_genesis_vii_b0.sh
```

It did not recognize the Government Framework verifier:

```text
dev/verify_genesis_viii_a0_1.sh
```

The VIII-A0-1 verifier itself certified successfully, but the Genesis manifest
validator rejected its identity before execution.

## Decision

Roman-generation verifier names may now contain one or more underscore-delimited
numeric subphase segments:

```text
viii_a0_1       -> VIII-A0.1
ix_c2_14_3      -> IX-C2.14.3
xii_f1_4c       -> XII-F1.4.C
```

Each underscore-delimited subphase must:

1. begin with a positive numeric component;
2. contain no leading zero;
3. contain no empty segment;
4. follow the existing alpha-numeric hierarchy grammar.

## Compatibility Guarantees

- II-A3B legacy labels remain unchanged.
- II-A3C numeric hierarchy remains unchanged.
- II-A3D compact legacy formatting remains unchanged.
- II-A3E Roman generation names remain unchanged.
- `dev/verify_genesis_viii_a0_1.sh` remains unrenamed.
- Manifest ordering and duplicate-identity protections remain active.
