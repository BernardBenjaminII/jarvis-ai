# Executive Integration Audit

**Repository:** `/media/abdullah/JARVISDATA/Projects/jarvis-ai`

## Summary

- Subsystems audited: 7
- Route files discovered: 3
- UI files discovered: 0
- Capability files discovered: 12
- Test files discovered: 61
- Verification files discovered: 340

## Matrix

| Subsystem | Classification | Packages | Routes | UI | Capabilities | Tests | Verification | Placeholder hits |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| executive | api_only | 2 | 1 | 0 | 1 | 29 | 76 | 0 |
| capabilities | api_only | 1 | 1 | 0 | 10 | 5 | 29 | 0 |
| knowledge | backend_only | 3 | 0 | 0 | 0 | 10 | 139 | 0 |
| reasoning | backend_only | 3 | 0 | 0 | 0 | 24 | 65 | 0 |
| acquisition | backend_only | 2 | 0 | 0 | 0 | 3 | 39 | 0 |
| runtime | api_only | 2 | 1 | 0 | 4 | 8 | 80 | 0 |
| timeline | api_only | 1 | 1 | 0 | 1 | 8 | 18 | 0 |

## Detailed findings

### executive

**Classification:** `api_only`

**Packages:** core/executive, core/operations

**Routes:** core/src/routes/operations.py

**UI files:** None detected

**Capability files:** core/capabilities/operations.py

**Placeholder indicators:** None detected

### capabilities

**Classification:** `api_only`

**Packages:** core/capabilities

**Routes:** core/src/routes/operations.py

**UI files:** None detected

**Capability files:** core/capabilities/__init__.py, core/capabilities/adapters/__init__.py, core/capabilities/adapters/builder.py, core/capabilities/base.py, core/capabilities/discovery.py, core/capabilities/loader.py, core/capabilities/operations.py, core/capabilities/registry.py, core/capabilities/report.py, core/capabilities/runner.py

**Placeholder indicators:** None detected

### knowledge

**Classification:** `backend_only`

**Packages:** core/knowledge_catalog, core/knowledge_graph, knowledge_engine

**Routes:** None detected

**UI files:** None detected

**Capability files:** None detected

**Placeholder indicators:** None detected

### reasoning

**Classification:** `backend_only`

**Packages:** core/reasoning, core/cognition, core/representation

**Routes:** None detected

**UI files:** None detected

**Capability files:** None detected

**Placeholder indicators:** None detected

### acquisition

**Classification:** `backend_only`

**Packages:** core/acquisition, knowledge_engine

**Routes:** None detected

**UI files:** None detected

**Capability files:** None detected

**Placeholder indicators:** None detected

### runtime

**Classification:** `api_only`

**Packages:** core/bootstrap, core/runtime

**Routes:** core/src/routes/operations.py

**UI files:** None detected

**Capability files:** core/capabilities/metadata.py, core/capabilities/models.py, core/capabilities/operations.py, core/capabilities/registry.py

**Placeholder indicators:** None detected

### timeline

**Classification:** `api_only`

**Packages:** core/executive

**Routes:** core/src/routes/operations.py

**UI files:** None detected

**Capability files:** core/capabilities/operations.py

**Placeholder indicators:** None detected
