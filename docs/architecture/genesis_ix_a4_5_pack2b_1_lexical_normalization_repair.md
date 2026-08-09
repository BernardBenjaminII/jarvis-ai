# Genesis IX-A4.5 Pack 2B.1 — Lexical Qualification Normalization Repair

## Mission

Repair technical-identifier matching inside the lexical qualification layer
without changing evaluator thresholds or downstream runtime behavior.

## Canonical Equivalence

```text
SHA-256            SHA256            SHA 256            (SHA)-256
AES-256            AES256            AES 256
RFC-9110           RFC9110           RFC 9110
CVE-2025-12345     CVE202512345      CVE 2025 12345
_BitInt(32)        BitInt32
```

`C++` and `C#` are preserved.

## Scope

Only `core/retrieval/qualification/lexical.py` is replaced.

The evaluator, thresholds, phrase analysis, subject analysis, retrieval,
orchestrator, grounded-answer engine, and telemetry remain unchanged.
