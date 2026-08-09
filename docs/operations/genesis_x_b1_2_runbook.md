# Genesis X-B1.2 Runbook

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python

"$PYTHON_BIN" -m dev.run_genesis_x_b1_2 audit

time "$PYTHON_BIN" -m dev.run_genesis_x_b1_2 execute   --limit 1000   --batch-size 8   --report-every 100   --max-load1 4.0   --min-mem-gib 4

"$PYTHON_BIN" -m dev.run_genesis_x_b1_2 status
"$PYTHON_BIN" -m dev.run_genesis_x_b1_2 certify
```

If the 1,000-item canary is clean, escalate to 5,000 rather than launching the
entire corpus immediately.
