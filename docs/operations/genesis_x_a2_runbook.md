# Genesis X-A2 Runbook

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python

"$PYTHON_BIN" -m dev.run_genesis_x_a2 audit
"$PYTHON_BIN" -m dev.run_genesis_x_a2 recover --dry-run
"$PYTHON_BIN" -m dev.run_genesis_x_a2 recover --limit 10
"$PYTHON_BIN" -m dev.run_genesis_x_a2 status
"$PYTHON_BIN" -m dev.run_genesis_x_a2 certify
"$PYTHON_BIN" -m dev.run_genesis_x_a2 recover
```
