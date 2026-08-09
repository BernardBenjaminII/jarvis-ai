# Genesis IX-A1 — Knowledge Workspace Mount

IX-A1 replaces the dead Knowledge placeholder with an operational workspace while preserving the mature Mission Control shell.

## Surgical scope

Adds only:

- `knowledge_workspace.js`
- `knowledge_workspace.css`
- IX-A1 tests and verifier

The installer performs a guarded insertion of those assets into the existing `index.html`. It does not replace `index.html`, `app.js`, `api.js`, `dashboard.js`, `health_projection.js`, or `timeline_projection.js`.

## Behavior

All existing Knowledge entry points mount the same workspace:

- `data-view="knowledge"`
- `data-open-view="knowledge"`
- `data-command="open-knowledge"`

The workspace submits first to `POST /api/conversation/query` and falls back to `POST /ask`. It displays the answer, latency, confidence when available, Executive activity, evidence, and sources.
