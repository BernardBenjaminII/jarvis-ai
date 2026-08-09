# Genesis II-A3G — Manifest Evolution for Runtime Campaigns

**Status:** Implemented
**Predecessor:** Genesis II-A3F

## Objective

Admit Roman runtime campaign verifier identities that intentionally omit the
alphabetic stream token, including:

```text
dev/verify_genesis_ix_0.sh
```

## Runtime Campaign Grammar

```text
verify_genesis_<roman-generation>_<runtime-body>.sh
```

Supported examples:

```text
verify_genesis_ix_0.sh
verify_genesis_x_1.sh
verify_genesis_xi_2a.sh
verify_genesis_xii_10_3.sh
```

Runtime campaigns use the reserved internal stream `z` for deterministic
ordering. Existing numeric phases, Roman stream phases, Roman hierarchical
subphases, and legacy labels remain unchanged.

## Root Regression Resolved

II-A3G removes the manifest failure caused by:

```text
GenesisManifestError:
unrecognized Genesis verifier path:
dev/verify_genesis_ix_0.sh
```
