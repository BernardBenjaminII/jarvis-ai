# Genesis VII-C4.2 — Repository-Wide Constitutional Audit

## Install

From the JARVIS repository root:

```bash
unzip -o ~/Downloads/genesis_vii_c4_2_repository_constitutional_audit.zip -d .
```

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/install_genesis_vii_c4_2.sh
```

## Independent verification

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_genesis_vii_c4_2.sh
```

## Prerequisites

- Genesis VII-C3 ratification artifacts
- Genesis VII-C4 compliance engine and audit artifact
- Genesis VII-C4.1 Pack 2 certification artifact

## Output

```text
artifacts/audit/km0000-c4_2/
```

The default policy audits documents and configuration while excluding source code. Source-code auditing can be enabled later through `default_repository_audit_policy(include_source_code=True)`.
