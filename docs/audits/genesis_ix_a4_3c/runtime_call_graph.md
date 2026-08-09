# Executive Runtime Call Graph

| Source | Target | Relation | Evidence |
|---|---|---|---|
| `conversation_service` | `orchestrator` | owns | `conversation_service.orchestrator` |
| `orchestrator` | `director` | owns | `orchestrator.director` |
| `orchestrator` | `grounding_service` | owns | `orchestrator.grounding_service` |
| `orchestrator` | `awareness_service` | owns | `orchestrator.awareness_service` |
| `orchestrator` | `synthesis_handler` | owns | `orchestrator.synthesis_handler` |
| `orchestrator.execute` | `self.grounding_service.ground` | source_call | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/orchestrator.py:99` |
| `orchestrator.execute` | `self.director.submit` | source_call | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/orchestrator.py:136` |
| `orchestrator.execute` | `grounding.synthesis_input` | source_call | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/orchestrator.py:175` |
| `orchestrator.execute` | `knowledge_state.synthesis_input` | source_call | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/orchestrator.py:177` |
| `orchestrator.execute` | `self.synthesis_handler` | source_call | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/orchestrator.py:178` |
| `orchestrator.execute` | `self.awareness_service.assess` | source_call | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/orchestrator.py:118` |
| `orchestrator.execute` | `grounding.for_objective` | source_call | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/orchestrator.py:135` |
| `orchestrator.execute` | `objective_grounding.to_dict` | source_call | `/media/abdullah/JARVISDATA/Projects/jarvis-ai/core/conversation/orchestrator.py:146` |
