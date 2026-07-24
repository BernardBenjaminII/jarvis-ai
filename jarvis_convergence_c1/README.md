# JARVIS Convergence Pack C-1

## Executive Conversation Activation

This pack establishes the canonical text-conversation entry point for JARVIS and activates it on Commander's Bridge.

It intentionally reuses the current `core.src.brain.route_question` execution path. It does not replace the knowledge, reasoning, planning, executive, or model-routing subsystems. Instead, it wraps them in a stable conversation contract that later convergence packs can enrich with director dispatch, catalog grounding, and live orchestration.

## Delivered

- `core/conversation/` public package
- structured request, response, trace, objective, and message contracts
- deterministic request compiler for compound commands
- SQLite-backed conversation session repository
- executive conversation service
- `/api/conversation/query`
- `/api/conversation/sessions/{session_id}`
- `/api/conversation/sessions/{session_id}/messages`
- Bridge chat interface with persistent browser session
- unit, route, and static-boundary tests
- certification verifier and wrapper

## Install

From the project root:

```bash
bash dev/install_convergence_c1_executive_conversation.sh
```

## Verify

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
./dev/verify_convergence_c1.sh
```

## Run

```bash
PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python
$PYTHON_BIN -m uvicorn core.src.main:app --host 127.0.0.1 --port 8000 --reload
```

Open:

```text
http://127.0.0.1:8000/bridge
```
