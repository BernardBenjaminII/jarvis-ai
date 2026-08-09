# Genesis X-A2.1 Runbook

Set Python:

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python
```

Audit the remaining failures and OCR environment:

```bash
"$PYTHON_BIN" -m dev.run_genesis_x_a2_1 audit
```

Dry run 10 candidates:

```bash
"$PYTHON_BIN" -m dev.run_genesis_x_a2_1 recover --dry-run --limit 10
```

Production canary:

```bash
"$PYTHON_BIN" -m dev.run_genesis_x_a2_1 recover --limit 5
```

Status and certification:

```bash
"$PYTHON_BIN" -m dev.run_genesis_x_a2_1 status
"$PYTHON_BIN" -m dev.run_genesis_x_a2_1 certify
```

Full bounded recovery:

```bash
"$PYTHON_BIN" -m dev.run_genesis_x_a2_1 recover
```

For Arabic + English OCR, only use this after confirming Tesseract reports both
language packs:

```bash
"$PYTHON_BIN" -m dev.run_genesis_x_a2_1 audit --languages eng+ara
```

Then:

```bash
"$PYTHON_BIN" -m dev.run_genesis_x_a2_1 recover --languages eng+ara
```
