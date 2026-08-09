# Genesis X-B1.1 Runbook

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python

"$PYTHON_BIN" -m dev.run_genesis_x_b1_1 audit

"$PYTHON_BIN" -m dev.run_genesis_x_b1_1 prepare

"$PYTHON_BIN" -m dev.run_genesis_x_b1_1 status

"$PYTHON_BIN" -m dev.run_genesis_x_b1_1 embed   --limit 100   --batch-size 8

"$PYTHON_BIN" -m dev.run_genesis_x_b1_1 query   --query "NIST incident response"   --limit 10

"$PYTHON_BIN" -m dev.run_genesis_x_b1_1 certify
```

Do not launch all 783K embeddings until the canary throughput, vector dimensions,
database growth, and local Ollama stability are measured.
