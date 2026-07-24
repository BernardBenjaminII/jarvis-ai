# JARVIS Genesis UI-A4.1 — Knowledge Inventory Projection

UI-A4.1 is the first certified installment of the Executive Knowledge Projection
program.

It adds a canonical `knowledge` projection that answers:

- Is the configured knowledge root available?
- Which SQLite knowledge stores exist?
- Which tables exist in each store?
- How many rows are visible in each table?
- How many files and bytes are present under the knowledge root?
- Which top-level knowledge areas consume the most storage?
- Is the projection fresh, cached, degraded, or unavailable?

UI-A4.1 is deliberately read-only. It does not mutate the knowledge catalog,
run ingestion, or create research tasks.

## Install

From the JARVIS repository root:

```bash
unzip genesis_ui_a41_knowledge_inventory_projection.zip \
    -d /tmp/genesis-ui-a41

cp -R /tmp/genesis-ui-a41/* .

chmod +x \
    dev/install_genesis_ui_a41_knowledge_inventory_projection.sh \
    dev/verify_genesis_ui_a41_knowledge_inventory_projection.sh \
    dev/verification/verify_genesis_ui_a41_knowledge_inventory_projection.py
```

Run:

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/install_genesis_ui_a41_knowledge_inventory_projection.sh
```

## Configuration

The default knowledge root is:

```text
/media/abdullah/JARVISDATA/Knowledge
```

Override it with:

```bash
export JARVIS_KNOWLEDGE_ROOT="/path/to/Knowledge"
```

Optional controls:

```bash
export JARVIS_KNOWLEDGE_PROJECTION_TTL_SECONDS=30
export JARVIS_KNOWLEDGE_SCAN_MAX_FILES=250000
```

## Runtime verification

Restart JARVIS, then run:

```bash
curl -s http://127.0.0.1:8000/operations/projections/knowledge \
    | python -m json.tool
```

Check the aggregate plane:

```bash
curl -s http://127.0.0.1:8000/operations/projections \
    | python -c '
import json, sys
data = json.load(sys.stdin)
print("providers:", data["provider_count"])
print("knowledge:", data["projections"]["knowledge"]["health"]["status"])
'
```
