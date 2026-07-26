# JARVIS Genesis IV-B1 — Executive Integration and Visibility Fabric

Genesis IV-B1 provides the canonical integration layer that exposes Executive
capabilities, runtime health, knowledge readiness, integration wiring, mission
state, execution state, and UI-ready projections without collapsing the
certified boundaries of Genesis IV-A1 through IV-A9.

It provides a canonical capability registry, repository integration audit,
knowledge-readiness projection, API-ready envelopes, Mission Control projections,
tests, documentation, ADR, installer, and verifier.

## Install

```bash
unzip genesis_iv_b1_executive_integration_visibility_fabric.zip
chmod +x genesis_iv_b1/dev/install_genesis_iv_b1.sh
./genesis_iv_b1/dev/install_genesis_iv_b1.sh
```

## Verify

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_genesis_4b1.sh
```

## Generate the integration audit

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
-m core.integration.cli audit \
--repository-root . \
--output docs/audits/genesis_iv_b1_integration_audit.json
```
