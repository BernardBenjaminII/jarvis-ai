# Genesis IX-A4.1A — Executive & Conversation Inventory

## Mission

Discover, classify, and document every Executive and Conversation component
present in the repository and active in the runtime.

IX-A4.1A introduces no new Executive behavior.

## Deliverables

```text
docs/audits/genesis_ix_a4_1a/
    executive_inventory.md
    conversation_inventory.md
    executive_dependency_graph.md
    executive_runtime_inventory.json
    executive_call_graph.md
    executive_component_matrix.md
    executive_duplicate_report.md
```

## Audit Domains

- Executive services and directors
- Conversation requests, responses, repositories, sessions, and traces
- Objective compilers
- Orchestrators and dispatch paths
- Grounding and awareness dependencies
- HTTP routes
- Mission Control HTTP and WebSocket consumers
- Static imports and call edges
- Live dependency composition
- Duplicate candidates
- KEEP, MERGE, REMOVE, RENAME, and UNKNOWN decisions

## Rule

> Static existence does not prove runtime ownership.

The inventory combines source inspection with live composition probing.

## Follow-on

IX-A4.1B must attach every retrieval and runtime component to the certified
Executive call graph produced here.
