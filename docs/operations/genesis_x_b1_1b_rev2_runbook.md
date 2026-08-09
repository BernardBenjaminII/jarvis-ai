# Runbook

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python
"$PYTHON_BIN" -m dev.run_genesis_x_b1_1b_rev2 audit
"$PYTHON_BIN" -m dev.run_genesis_x_b1_1b_rev2 adapt --limit 20 --fallback-target-chars 1400 --fallback-overlap-chars 140
"$PYTHON_BIN" -m dev.run_genesis_x_b1_1b_rev2 status
time "$PYTHON_BIN" -m dev.run_genesis_x_b1_1b_rev2 embed --limit 50 --batch-size 1
"$PYTHON_BIN" -m dev.run_genesis_x_b1_1b_rev2 certify
```
