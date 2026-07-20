# Genesis II-A3A — Verification Architecture

**Document ID:** `GENESIS-II-A3A`  
**Status:** Implementation Candidate  
**Depends On:** Genesis II-A3  
**Purpose:** Establish scalable, deterministic verification-domain orchestration.

## Decision

`dev/verify_all.sh` remains the permanent public entry point for complete
repository verification.

The master verifier delegates to domain orchestrators:

```text
dev/verify_all.sh
├── dev/verify_knowledge_all.sh
└── dev/verify_genesis_all.sh
```

Each domain orchestrator delegates to the shared deterministic manifest runner:

```text
dev/run_verification_manifest.sh
```

Domain ordering is stored as data under:

```text
dev/verification/manifests/
├── knowledge.manifest
└── genesis.manifest
```

## Existing Python Package

`dev/verification/` already contains the project's Python verification
framework. II-A3A preserves that package.

Only declarative manifest files are added beneath
`dev/verification/manifests/`. Shell orchestration remains in `dev/`.

## Laws

1. `dev/verify_all.sh` is the stable public verification command.
2. Domain orchestrators contain no phase-specific verifier list.
3. Manifest entries are repository-relative.
4. Manifest order is authoritative.
5. Missing or non-executable verifiers are failures, never skips.
6. Blank lines and comments are permitted.
7. Duplicate manifest entries are forbidden.
8. Domain failures are aggregated by the master verifier.
9. Existing certified verification order must be preserved during migration.
10. A domain may be added without restructuring existing domain manifests.

## Current Domains

### Knowledge

Contains the Phase VI and Phase VII suites previously embedded directly in
`dev/verify_all.sh`.

### Genesis

Contains Genesis I-A1 through II-A3A in constitutional dependency order.

## Extension Procedure

To add a future Genesis certification suite:

1. create the verifier under `dev/`;
2. make it executable;
3. add its repository-relative path to
   `dev/verification/manifests/genesis.manifest`;
4. extend II-A3A certification expectations when the architectural baseline
   changes; and
5. run `./dev/verify_all.sh`.

## Result

Verification becomes an architectural subsystem rather than a growing list
inside one shell script.

The public command remains stable while internal verification domains can
expand independently.
