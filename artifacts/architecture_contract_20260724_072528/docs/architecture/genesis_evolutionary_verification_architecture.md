# Genesis II-A3B — Evolutionary Verification Architecture

## Purpose

Genesis II-A3B removes the fixed manifest ceiling introduced by Genesis II-A3A
without weakening the certified Genesis baseline.

The original II-A3A verifier required the complete Genesis manifest to equal one
hard-coded list. That successfully froze the certified suites at the time, but
it also prevented any later Genesis milestone from being registered.

II-A3B separates two constitutional concerns:

1. **Baseline immutability** — previously certified suites must remain present,
   unchanged, and in their original order.
2. **Evolutionary extensibility** — future suites may be appended when their
   phase identities are valid, unique, and strictly ordered.

## Constitutional rules

The Genesis manifest must satisfy all of the following:

- Every path is repository-relative and points under `dev/`.
- Every verifier path is unique.
- The II-A3A certified baseline remains the exact manifest prefix.
- Every verifier has a parseable Genesis phase identity.
- Phase identities are unique.
- Phase identities are strictly increasing.
- The ordered manifest produces a deterministic SHA-256 fingerprint.

## Certified baseline

The immutable baseline is:

```text
dev/verify_genesis_1a1.sh
dev/verify_genesis_1a2.sh
dev/verify_genesis_1a3.sh
dev/verify_genesis_2a1.sh
dev/verify_genesis_2a2.sh
dev/verify_reasoning_fixtures.sh
dev/verify_genesis_2a3.sh
dev/verify_genesis_2a3a.sh
```

`dev/verify_reasoning_fixtures.sh` is a canonical compatibility suite associated
with Genesis II-A2R and is assigned that constitutional phase identity by the
manifest parser.

## Architectural effect

II-A3A continues to certify the baseline and verification architecture.

II-A3B certifies the rule by which Genesis may evolve beyond that baseline.

Future Genesis phases can therefore be added without modifying II-A3A or II-A3B,
provided their verifier names preserve constitutional ordering.
