# Executive Director Inspection

| Owner | Method | Public | Signature | Source |
|---|---|---|---|---|
| `director` | `create_mission` | True | `(objective: 'str', *, context: 'dict[str, Any] | None' = None) -> 'Mission'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/executive/director.py:88` |
| `director` | `director_catalog` | True | `() -> 'list[dict[str, Any]]'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/executive/director.py:165` |
| `director` | `execute_mission` | True | `(mission_id: 'str') -> 'Mission'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/executive/director.py:142` |
| `director` | `get_mission` | True | `(mission_id: 'str') -> 'Mission'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/executive/director.py:150` |
| `director` | `list_missions` | True | `(*, status: 'str | None' = None, limit: 'int' = 50) -> 'list[Mission]'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/executive/director.py:153` |
| `director` | `mission_events` | True | `(mission_id: 'str') -> 'list[dict[str, Any]]'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/executive/director.py:161` |
| `director` | `plan_mission` | True | `(mission: 'Mission') -> 'Mission'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/executive/director.py:106` |
| `director` | `submit` | True | `(objective: 'str', *, context: 'dict[str, Any] | None' = None, execute: 'bool' = True) -> 'Mission'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/executive/director.py:129` |

```json
{
  "candidates": [
    {
      "method": "submit",
      "reasons": [
        "referenced by orchestrator",
        "accepts runtime input"
      ],
      "score": 60
    },
    {
      "method": "plan_mission",
      "reasons": [
        "accepts runtime input"
      ],
      "score": 10
    },
    {
      "method": "mission_events",
      "reasons": [
        "accepts runtime input"
      ],
      "score": 10
    },
    {
      "method": "list_missions",
      "reasons": [
        "accepts runtime input"
      ],
      "score": 10
    },
    {
      "method": "get_mission",
      "reasons": [
        "accepts runtime input"
      ],
      "score": 10
    },
    {
      "method": "execute_mission",
      "reasons": [
        "accepts runtime input"
      ],
      "score": 10
    },
    {
      "method": "director_catalog",
      "reasons": [
        "accepts runtime input"
      ],
      "score": 10
    },
    {
      "method": "create_mission",
      "reasons": [
        "accepts runtime input"
      ],
      "score": 10
    }
  ],
  "method": "submit",
  "module": "core.executive.director",
  "qualified_name": "ExecutiveDirector.submit",
  "reasons": [
    "referenced by orchestrator",
    "accepts runtime input"
  ],
  "score": 60,
  "signature": "(objective: 'str', *, context: 'dict[str, Any] | None' = None, execute: 'bool' = True) -> 'Mission'",
  "source_file": "/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/executive/director.py",
  "source_line": 129,
  "status": "resolved"
}
```
