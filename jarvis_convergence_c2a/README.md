# JARVIS Convergence C-2A — Certification Repair

This pack repairs the stale C-1 HTTP contract exposed after C-2 activated the
Executive orchestration path. It does not modify production code.

## Install

```bash
cd /media/abdullah/JARVISDATA/Projects/jarvis-ai
PROJECT_ROOT=/media/abdullah/JARVISDATA/Projects/jarvis-ai \
  bash jarvis_convergence_c2a/install.sh
```

## Verify

```bash
cd /media/abdullah/JARVISDATA/Projects/jarvis-ai
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
  ./dev/verify_convergence_c2a.sh
```
