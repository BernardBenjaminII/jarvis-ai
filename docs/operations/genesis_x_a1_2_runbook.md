# Genesis X-A1.2 Runbook

Qualification:

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python

"$PYTHON_BIN" -m dev.run_genesis_x_a1_2 execute   --workers 6   --batch-size 1000   --max-in-flight 24   --artifact-queue-size 32   --writer-batch-size 20
```

Production after qualification:

```bash
"$PYTHON_BIN" -m dev.run_genesis_x_a1_2 execute   --workers 6   --batch-size 5000   --max-in-flight 24   --artifact-queue-size 32   --writer-batch-size 20
```

Only try 8 workers if the artifact queue remains mostly empty.
