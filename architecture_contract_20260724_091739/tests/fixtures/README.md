# Canonical Constitutional Test Fixtures

This directory contains the canonical construction helpers required by
ADR-0018.

Fixtures in this directory:

- derive directly from certified public contracts;
- invoke normal constitutional validation;
- use deterministic defaults;
- support explicit overrides;
- do not duplicate production validation logic; and
- must be certified before dependent Genesis tests run.

Tests must use these fixtures whenever a canonical fixture exists. They must
not independently reconstruct the same constitutional objects.
