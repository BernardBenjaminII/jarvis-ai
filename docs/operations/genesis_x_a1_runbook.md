# Genesis X-A1 Runbook

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python
```

Prepare:

```bash
"$PYTHON_BIN" -m dev.run_genesis_x_a1 prepare
```

Status:

```bash
"$PYTHON_BIN" -m dev.run_genesis_x_a1 status
```

Dry-run 25:

```bash
"$PYTHON_BIN" -m dev.run_genesis_x_a1 dry-run --workers 4 --batch-size 25
```

First production canary:

```bash
"$PYTHON_BIN" -m dev.run_genesis_x_a1 execute --workers 2 --batch-size 10 --stop-on-error
```

Review:

```bash
cat docs/audits/genesis_x_a1/execution_report.md
```

Scale gradually: 10, 25, 100, 500, then 1,000 documents per invocation.
