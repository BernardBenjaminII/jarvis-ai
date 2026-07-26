# JARVIS Genesis IV-A9 — Executive Execution Orchestrator

Genesis IV-A9 consumes an immutable Mission Plan and advances its activities
through a controlled execution lifecycle.

The orchestrator owns scheduling, dispatch coordination, state transitions,
retries, rollback requests, telemetry, and execution observations.

It does not provide unrestricted shell execution or bypass approval boundaries.

## Install

From the JARVIS repository root:

```bash
unzip genesis_iv_a9_executive_execution_orchestrator.zip
chmod +x genesis_iv_a9/dev/install_genesis_iv_a9.sh
./genesis_iv_a9/dev/install_genesis_iv_a9.sh
```

## Verify

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_genesis_4a9.sh
```
