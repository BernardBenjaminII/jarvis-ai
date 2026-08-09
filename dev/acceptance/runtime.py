from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Protocol

class RuntimeAdapter(Protocol):
    def execute(self, prompt: str, *, mode: str, metadata: dict[str, Any]) -> str: ...
    def telemetry(self) -> dict[str, Any]: ...

@dataclass(slots=True)
class CallableRuntimeAdapter:
    ask_handler: Callable[..., Any]
    telemetry_handler: Callable[[], dict[str, Any]] | None = None

    def execute(self, prompt, *, mode, metadata):
        response = self.ask_handler(prompt, mode=mode, metadata=metadata)
        if isinstance(response, str):
            return response
        if isinstance(response, dict):
            for key in ("answer", "response", "text", "content"):
                if key in response:
                    return str(response[key])
        for key in ("answer", "response", "text", "content"):
            if hasattr(response, key):
                return str(getattr(response, key))
        return str(response)

    def telemetry(self):
        return {} if self.telemetry_handler is None else dict(self.telemetry_handler() or {})

def create_live_runtime_adapter():
    from core.src.routes.api import conversation_service
    from core.conversation.grounded_answer.telemetry import get_grounded_answer_telemetry_store
    return CallableRuntimeAdapter(
        conversation_service.ask,
        get_grounded_answer_telemetry_store().projection,
    )
