# Genesis X-B1.2a Runbook

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python

"$PYTHON_BIN" -m dev.run_genesis_x_b1_2a audit

# Recover the existing 751 context-overflow rows first.
time "$PYTHON_BIN" -m dev.run_genesis_x_b1_2a recover   --limit 1000

"$PYTHON_BIN" -m dev.run_genesis_x_b1_2a status
"$PYTHON_BIN" -m dev.run_genesis_x_b1_2a certify

# Then run a fresh 1,000-item production canary.
time "$PYTHON_BIN" -m dev.run_genesis_x_b1_2a execute   --limit 1000   --batch-size 8   --report-every 100   --max-load1 4.0   --min-mem-gib 4

"$PYTHON_BIN" -m dev.run_genesis_x_b1_2a certify
```
