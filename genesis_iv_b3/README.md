# Genesis IV-B3 — Canonical Observation Convergence

Install:

```bash
chmod +x genesis_iv_b3/dev/install_genesis_iv_b3.sh
./genesis_iv_b3/dev/install_genesis_iv_b3.sh
```

Verify:

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_genesis_4b3.sh
```

This phase is non-destructive: it establishes `core.observation` as the canonical
contract and retains existing cognition and Observation Bus implementations behind
explicit compatibility adapters.
