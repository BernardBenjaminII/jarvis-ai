# Genesis II-A3C — Hierarchical Manifest Parser

**Status:** Implemented
**Domain:** Constitutional verification architecture
**Predecessor:** Genesis II-A3B

## Problem

II-A3B represented only a top-level numeric ordinal and an alphabetic suffix.
It rejected valid nested identities such as:

```text
dev/verify_genesis_4a6a1.sh
```

## Decision

Genesis verifier bodies now follow:

```text
generation stream numeric-ordinal (alphabetic-level numeric-level?)*
```

Supported examples:

```text
2a3b      -> 2-A3.B
4a6a1     -> 4-A6.A.1
10c3a4b2  -> 10-C3.A.4.B.2
```

A contiguous numeric body remains one ordinal:

```text
4a62 -> 4-A62
```

This preserves existing filename meaning instead of guessing that `62` means
`6.2`.

## Guarantees

1. The II-A3A certified baseline remains the exact immutable prefix.
2. Existing numeric and alphabetic-leaf identifiers remain compatible.
3. Nested alpha-numeric identifiers are parsed natively.
4. Ordering remains deterministic.
5. Duplicate paths and phase identities remain forbidden.
6. Repository-relative path protections remain unchanged.
7. No wrapper or surrogate parser is used.

## Migration

The installer backs up all replaced files, removes the obsolete
`genesis_phase_extension.py` wrapper when present, registers II-A3C immediately
after II-A3B, and runs both II-A3C certification and the II-A3B regression.
