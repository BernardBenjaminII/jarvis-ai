# Genesis VII-C4 — Constitutional Compliance Engine

## Install

From the JARVIS repository root:

```bash
unzip -o ~/Downloads/genesis_vii_c4_constitutional_compliance_engine.zip -d .
```

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/install_genesis_vii_c4.sh
```

## Independent verification

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_genesis_vii_c4.sh
```

## Prerequisite

Genesis VII-C3 must already have generated:

```text
artifacts/audit/km0000-c3/constitutional_ratification.json
artifacts/audit/km0000-c3/constitutional_registry.json
```

The verifier creates a deterministic self-assessment subject at:

```text
artifacts/audit/km0000-c4/compliance_subjects.json
```
