# JARVIS Convergence C-4A — Knowledge Compatibility Repair

This focused repair pack:

- removes the obsolete hard dependency on `STRUCTURE_SQL`;
- preserves mandatory Knowledge Catalog migrations;
- keeps migrations idempotent;
- updates C-1 and C-2 HTTP contracts for C-4 grounding enrichment;
- leaves production Director orchestration and grounding untouched.

## Install

```bash
cd /media/abdullah/JARVISDATA/Projects/jarvis-ai

PROJECT_ROOT=/media/abdullah/JARVISDATA/Projects/jarvis-ai \
bash jarvis_convergence_c4a/install.sh
```

## Verify

```bash
cd /media/abdullah/JARVISDATA/Projects/jarvis-ai

PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_convergence_c4a.sh
```
