# Genesis VII-C4.1 Pack 1 — Constitutional Certification Framework

## Install

From the JARVIS repository root:

```bash
unzip -o ~/Downloads/genesis_vii_c4_1_pack1_certification_framework.zip -d .
```

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/install_genesis_vii_c4_1_pack1.sh
```

## Independent verification

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_genesis_vii_c4_1_pack1.sh
```

## Prerequisite

Genesis VII-C4 must have produced:

```text
artifacts/audit/km0000-c4/constitutional_compliance.json
```

## Scope

Pack 1 certifies the framework only. All eight scenarios are deliberately recorded as `skipped` until Pack 2 provides deterministic live scenario generation and execution.
