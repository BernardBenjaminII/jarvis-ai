# Genesis X-B2.4A-1 Runbook

Run verification, then execute the live acceptance query:

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python
./dev/verify_genesis_x_b2_4a_1.sh

time "$PYTHON_BIN" -m dev.run_genesis_x_b2_4a_1 quality \
  --query "How do C++ iterators work?" \
  --top-k 8 --candidate-pool 60 --scan-limit 25000
```

Acceptance target: `query_intent=mechanism`, direct iterator/STL evidence becomes C1, synthesis utility is visible separately from retrieval score, and provenance is unchanged.
