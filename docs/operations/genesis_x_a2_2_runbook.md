# Genesis X-A2.2 Runbook

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python

"$PYTHON_BIN" -m dev.run_genesis_x_a2_2 audit
"$PYTHON_BIN" -m dev.run_genesis_x_a2_2 apply-hygiene --yes
"$PYTHON_BIN" -m dev.run_genesis_x_a2_2 certify

"$PYTHON_BIN" -m dev.run_genesis_x_a2_2 recover-final --yes

"$PYTHON_BIN" -m dev.run_genesis_x_a2_2 status
"$PYTHON_BIN" -m dev.run_genesis_x_a2_2 certify
```

Final `EXCELLENT` requires zero `FAILED` candidates plus runtime integrity,
chunk/FTS parity, no duplicate runtime paths, no orphan chunks, and no
intermediate materialization stages.
