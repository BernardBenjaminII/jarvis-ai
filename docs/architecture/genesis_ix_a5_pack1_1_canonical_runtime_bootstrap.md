# Genesis IX-A5 Pack 1.1 — Canonical Runtime Bootstrap Repair

## Mission

Establish one certified startup path for Genesis engineering tools and repair
the IX-A5 Pack 1 audit runner so it can execute from any working directory.

## Runtime Flow

```text
Executable
    ↓
bootstrap_runtime()
    ↓
locate_project_root()
    ↓
ensure_repository_layout()
    ↓
deduplicate and insert project root into sys.path
    ↓
construct immutable RuntimeContext
    ↓
import core.*
    ↓
execute tool
```

## Runtime Context

The immutable context records:

- project root;
- Python executable;
- Python version;
- working directory;
- platform;
- repository verification state;
- Genesis version when available.

## Error Hierarchy

- `GenesisRuntimeError`
- `GenesisRepositoryNotFoundError`
- `GenesisRepositoryValidationError`
- `GenesisEnvironmentError`
- `GenesisBootstrapError`

## Production Repair

This pack canonically replaces:

```text
dev/run_genesis_ix_a5_pack1_audit.py
```

The runner now bootstraps the repository before importing `core`, and its
default output path is anchored to the canonical project root.

## Scope

Pack 1.1 establishes the shared runtime package and migrates the defective IX-A5
Pack 1 executable. It does not blindly rewrite all historical Genesis scripts.
Future packs should adopt `dev.runtime.bootstrap_runtime()` as their startup
contract.
