# Executive Runtime Callable Surface

| Owner | Method | Public | Signature | Source |
|---|---|---|---|---|
| `conversation_service` | `ask` | True | `(operator_input: 'str', *, session_id: 'str | None' = None, mode: 'str' = 'full', channel: 'str' = 'text', metadata: 'dict[str, Any] | None' = None) -> 'ExecutiveConversationResponse'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/service.py:42` |
| `conversation_service` | `history` | True | `(session_id: 'str', *, limit: 'int' = 100) -> 'list[dict[str, Any]]'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/service.py:168` |
| `conversation_service` | `_normalize_answer` | False | `(value: 'Any') -> 'str'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/service.py:171` |
| `orchestrator` | `execute` | True | `(context: 'ExecutiveRequestContext') -> 'OrchestrationResult'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/orchestrator.py:87` |
| `orchestrator` | `synthesis_handler` | True | `(question: str)` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/src/brain.py:16` |
| `orchestrator` | `_assignment` | False | `(objective_id: 'str', mission: 'Mission') -> 'DirectorAssignment'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/orchestrator.py:205` |
| `orchestrator` | `_normalize_answer` | False | `(value: 'Any') -> 'str'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/orchestrator.py:229` |
| `director` | `create_mission` | True | `(objective: 'str', *, context: 'dict[str, Any] | None' = None) -> 'Mission'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/executive/director.py:88` |
| `director` | `director_catalog` | True | `() -> 'list[dict[str, Any]]'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/executive/director.py:165` |
| `director` | `execute_mission` | True | `(mission_id: 'str') -> 'Mission'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/executive/director.py:142` |
| `director` | `get_mission` | True | `(mission_id: 'str') -> 'Mission'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/executive/director.py:150` |
| `director` | `list_missions` | True | `(*, status: 'str | None' = None, limit: 'int' = 50) -> 'list[Mission]'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/executive/director.py:153` |
| `director` | `mission_events` | True | `(mission_id: 'str') -> 'list[dict[str, Any]]'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/executive/director.py:161` |
| `director` | `plan_mission` | True | `(mission: 'Mission') -> 'Mission'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/executive/director.py:106` |
| `director` | `submit` | True | `(objective: 'str', *, context: 'dict[str, Any] | None' = None, execute: 'bool' = True) -> 'Mission'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/executive/director.py:129` |
| `grounding_service` | `ground` | True | `(context: 'ExecutiveRequestContext') -> 'GroundingResult'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/grounding.py:152` |
| `grounding_service` | `search_for_director` | True | `(objective: 'str', context: 'dict[str, Any]') -> 'dict[str, Any]'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/grounding.py:161` |
| `grounding_service` | `search_handler` | True | `(query: 'str', limit: 'int') -> 'Iterable[Mapping[str, Any]]'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/grounding.py:148` |
| `grounding_service` | `_ground_objective` | False | `(objective: 'CompiledObjective') -> 'ObjectiveGrounding'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/grounding.py:178` |
| `grounding_service` | `_search_catalog` | False | `(query: 'str', limit: 'int') -> 'Iterable[Mapping[str, Any]]'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/grounding.py:148` |
| `awareness_service` | `assess` | True | `(grounding: 'GroundingResult') -> 'ExecutiveKnowledgeState'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/knowledge_awareness/service.py:20` |
| `awareness_service` | `_answerability` | False | `(score: 'float') -> 'str'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/knowledge_awareness/service.py:97` |
| `awareness_service` | `_evidence` | False | `(objective: 'ObjectiveGrounding') -> 'tuple[EvidenceItem, ...]'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/knowledge_awareness/service.py:81` |
| `awareness_service` | `_maturity` | False | `(score: 'float') -> 'str'` | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/knowledge_awareness/service.py:94` |
