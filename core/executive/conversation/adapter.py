from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from time import perf_counter
from typing import Any, Callable

from .contracts import WorkspaceConversationRequest, WorkspaceConversationResponse


def as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "to_dict") and callable(value.to_dict):
        result = value.to_dict()
        if isinstance(result, Mapping):
            return result
    if is_dataclass(value):
        return asdict(value)
    return {}


def first(data: Mapping[str, Any], *paths: str, default: Any = None) -> Any:
    for path in paths:
        current: Any = data
        for part in path.split("."):
            if not isinstance(current, Mapping) or part not in current:
                break
            current = current[part]
        else:
            if current is not None:
                return current
    return default


def items(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        return (value,)
    if isinstance(value, Mapping):
        return tuple(value.values())
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)


def normalized_item(value: Any, index: int, kind: str) -> dict[str, Any]:
    if isinstance(value, str):
        return {"title" if kind == "source" else "statement": value}
    data = as_mapping(value)
    if kind == "source":
        return {
            "title": str(first(data, "title", "name", "path", "id",
                               default=f"Source {index + 1}")),
            "reference": str(first(data, "reference", "document_id",
                                   "chunk_id", "path", default="")),
            "excerpt": str(first(data, "excerpt", "text", "content",
                                 "summary", default="")),
            "confidence": first(data, "confidence", "score", default=None),
        }
    return {
        "statement": str(first(data, "statement", "text", "content",
                               "excerpt", default=f"Evidence {index + 1}")),
        "source_reference": str(first(data, "source_reference", "document_id",
                                      "chunk_id", default="")),
        "confidence": first(data, "confidence", "score", default=None),
    }


class ExecutiveConversationAdapter:
    def __init__(self, conversation_call: Callable[..., Any]) -> None:
        if not callable(conversation_call):
            raise TypeError("conversation_call must be callable")
        self._conversation_call = conversation_call

    def execute(
        self,
        request: WorkspaceConversationRequest,
    ) -> WorkspaceConversationResponse:
        started = perf_counter()
        activity = [
            {"stage": "Executive", "status": "completed",
             "detail": "Executive conversation request accepted."},
            {"stage": "Knowledge Directorate", "status": "active",
             "detail": "Searching the canonical knowledge catalog."},
        ]
        try:
            raw = self._conversation_call(
                operator_input=request.question,
                session_id=request.session_id,
                mode=request.mode,
                channel="text",
                metadata={
                    "workspace": "knowledge",
                    **dict(request.context),
                },
            )
            data = as_mapping(raw)
            answer = str(first(
                data,
                "answer", "response", "message", "content",
                "result.answer", "assistant_message.content",
                default="",
            ) or "").strip()
            session = first(data, "session_id", "session.id",
                            "metadata.session_id", default=request.session_id)
            confidence = first(
                data,
                "confidence", "result.confidence", "metadata.confidence",
                "metadata.executive_knowledge_state.confidence",
                default=None,
            )
            sources_raw = items(first(
                data,
                "sources", "citations", "result.sources",
                "metadata.sources", "metadata.knowledge_grounding.sources",
                default=(),
            ))
            evidence_raw = items(first(
                data,
                "evidence", "result.evidence", "metadata.evidence",
                "metadata.knowledge_grounding.evidence",
                "metadata.knowledge_grounding.matches",
                default=(),
            ))
            technical_details = first(
                data,
                "technical_details",
                "metadata.technical_details",
                default=None,
            )
            activity.extend([
                {"stage": "Grounding", "status": "completed",
                 "detail": "Knowledge grounding completed."},
                {"stage": "Knowledge Awareness", "status": "completed",
                 "detail": "Coverage and confidence assessed."},
                {"stage": "Executive", "status": "completed",
                 "detail": "Executive response published."},
            ])
            return WorkspaceConversationResponse(
                status="completed",
                answer=answer or "The Executive returned no answer text.",
                session_id=str(session) if session else None,
                confidence=float(confidence) if confidence not in (None, "") else None,
                latency_ms=max(0, round((perf_counter() - started) * 1000)),
                sources=tuple(
                    normalized_item(value, index, "source")
                    for index, value in enumerate(sources_raw)
                ),
                evidence=tuple(
                    normalized_item(value, index, "evidence")
                    for index, value in enumerate(evidence_raw)
                ),
                activity=tuple(activity),
                technical_details=technical_details,
            )
        except Exception as exc:
            message = str(exc).splitlines()[0][:500] or "Conversation failed."
            code = (
                "conversation_timeout"
                if isinstance(exc, TimeoutError) or "timeout" in message.lower()
                else "conversation_error"
            )
            activity.append({
                "stage": "Executive",
                "status": "failed",
                "detail": "Conversation execution failed.",
            })
            return WorkspaceConversationResponse(
                status="failed",
                answer="",
                session_id=request.session_id,
                confidence=None,
                latency_ms=max(0, round((perf_counter() - started) * 1000)),
                activity=tuple(activity),
                error={"code": code, "message": message},
            )
