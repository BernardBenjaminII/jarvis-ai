# JARVIS Genesis IV-A8 — Executive Mission Compiler

Genesis IV-A8 compiles an approved Executive Decision into an immutable,
deterministic Mission Plan containing objectives, tasks, activities, and a
validated directed acyclic execution graph.

It does not execute the plan.

## Install

Run from the JARVIS repository root:

```bash
unzip genesis_iv_a8_executive_mission_compiler.zip
chmod +x genesis_iv_a8/dev/install_genesis_iv_a8.sh
./genesis_iv_a8/dev/install_genesis_iv_a8.sh
```

## Verify

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_genesis_4a8.sh
```
