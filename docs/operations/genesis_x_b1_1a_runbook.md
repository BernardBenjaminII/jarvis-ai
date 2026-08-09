# X-B1.1a Runbook

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python

"$PYTHON_BIN" -m dev.run_genesis_x_b1_1a audit

time "$PYTHON_BIN" -m dev.run_genesis_x_b1_1a embed   --limit 100   --batch-size 8

"$PYTHON_BIN" -m dev.run_genesis_x_b1_1a status
"$PYTHON_BIN" -m dev.run_genesis_x_b1_1a certify
```

Do not begin the full corpus campaign until the 100-item reliability canary is clean.
