# Genesis II-A3D — Legacy Label Compatibility

**Status:** Implemented
**Domain:** Constitutional verification architecture
**Predecessor:** Genesis II-A3C

## Decision

Restore the II-A3B public label contract without changing II-A3C parsing,
identity, ordering, or manifest validation.

Legacy labels remain compact:

```text
4a5                 -> 4-A5
2a3b                -> 2-A3B
reasoning_fixtures  -> 2-A2R
```

Genuinely nested labels remain hierarchical:

```text
4a6a1      -> 4-A6.A.1
10c3a4b2   -> 10-C3.A.4.B.2
```

## Certification

II-A3D requires:

1. package compilation,
2. dedicated compatibility tests,
3. unchanged II-A3B regression success,
4. unchanged II-A3C regression success, and
5. current manifest validation.
