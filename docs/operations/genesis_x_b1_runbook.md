# Genesis X-B1 Runbook

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python

"$PYTHON_BIN" -m dev.run_genesis_x_b1 audit

"$PYTHON_BIN" -m dev.run_genesis_x_b1 compare

"$PYTHON_BIN" -m dev.run_genesis_x_b1 query   --query "NIST incident response"   --limit 10

"$PYTHON_BIN" -m dev.run_genesis_x_b1 certify
```

Do not build or mutate embeddings until the semantic audit tells us whether the
existing `chunk_embeddings` table is usable.
