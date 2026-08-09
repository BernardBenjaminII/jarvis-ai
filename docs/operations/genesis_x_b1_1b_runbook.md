# Genesis X-B1.1b Runbook

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python

"$PYTHON_BIN" -m dev.run_genesis_x_b1_1b audit

"$PYTHON_BIN" -m dev.run_genesis_x_b1_1b prepare \
  --limit 100 \
  --target-chars 2200 \
  --overlap-chars 220

"$PYTHON_BIN" -m dev.run_genesis_x_b1_1b status

time "$PYTHON_BIN" -m dev.run_genesis_x_b1_1b embed \
  --limit 200 \
  --batch-size 8

"$PYTHON_BIN" -m dev.run_genesis_x_b1_1b certify
```
