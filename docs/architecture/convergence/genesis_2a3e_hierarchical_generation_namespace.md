# Genesis II-A3E — Hierarchical Generation Namespace

**Status:** Implemented
**Predecessor:** Genesis II-A3D

## Decision

Extend the production Genesis manifest grammar to recognize canonical Roman
generation namespaces:

```text
dev/verify_genesis_vii_b0.sh
dev/verify_genesis_viii_a1.sh
dev/verify_genesis_xii_c4a2.sh
```

Roman generations are converted to integer identities for deterministic
ordering while retaining Roman public labels.

## Compatibility

Existing numeric names remain unchanged:

```text
2a3b   -> 2-A3B
4a6a1  -> 4-A6.A.1
4a62   -> 4-A62
```

Roman names render canonically:

```text
vii_b0     -> VII-B0
xii_c4a2   -> XII-C4.A.2
```

The top-level ordinal may be zero so foundational phases such as `B0` are legal.
Nested numeric hierarchy values remain positive.

## Guarantees

1. II-A3B legacy labels remain unchanged.
2. II-A3C hierarchical numeric parsing remains unchanged.
3. II-A3D compatibility behavior remains unchanged.
4. Roman numerals must be canonical and lowercase in filenames.
5. Numeric and Roman namespaces share one deterministic phase identity.
6. The current VII-B0 verifier becomes manifest-valid.
