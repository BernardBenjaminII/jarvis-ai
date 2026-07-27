# Genesis VII-C0 Pack 1B-R1 — Evidence Classification

**Inventory schema:** `1.1.0`  
**Audit engine:** `GENESIS-VII-C0-P1B-R1`

## Decision

Repository source integrity and generated artifact correctness are separate certification concerns.

- `SOURCE` files are immutable evidence during a verification run and receive presence and SHA-256 checks.
- `GENERATED` files are operational outputs. They are excluded from the canonical source inventory by default and, when explicitly inventoried, are not subject to source immutability checks.
- `EXTERNAL` files identify third-party or imported material and are not treated as native repository source evidence.

The default scan policy excludes `artifacts`, `reports`, `logs`, `coverage`, `htmlcov`, `dist`, and `build`. This prevents audit products from recursively changing the repository fingerprint that produced them.

Generated certification artifacts are validated independently for presence, JSON syntax, and repository-fingerprint consistency.
