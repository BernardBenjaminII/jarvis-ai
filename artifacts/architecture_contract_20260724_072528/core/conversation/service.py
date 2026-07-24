"""Canonical Executive Conversation Service."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from core.conversation.compiler import ExecutiveRequestCompiler
from core.conversation.contracts import (
    ConversationMessage,
    ConversationRole,
    ConversationState,
    ConversationTraceEvent,
    ExecutiveConversationResponse,
    ExecutiveRequestContext,
)
from core.conversation.repository import ConversationRepository


AnswerHandler = Callable[[str], Any]


class ExecutiveConversationService:
    """Own the operator-to-JARVIS conversation boundary.

    C-1 deliberately adapts the current brain entry point rather than replacing it.
    Later packs can inject a director orchestrator through ``answer_handler`` without
    changing the HTTP or UI contracts introduced here.
    """

    def __init__(
        self,
        *,
        database_path: str | Path,
        answer_handler: AnswerHandler,
        compiler: ExecutiveRequestCompiler | None = None,
    ) -> None:
        self.repository = ConversationRepository(database_path)
        self.answer_handler = answer_handler
        self.compiler = compiler or ExecutiveRequestCompiler()

    def ask(
        self,
        operator_input: str,
        *,
        session_id: str | None = None,
        mode: str = "full",
        channel: str = "text",
        metadata: dict[str, Any] | None = None,
    ) -> ExecutiveConversationResponse:
        objectives = self.compiler.compile(operator_input)
        context = ExecutiveRequestContext.create(
            operator_input=operator_input,
            session_id=session_id,
            mode=mode,
            channel=channel,
            metadata=metadata,
            objectives=objectives,
        )
        trace: list[ConversationTraceEvent] = [
            ConversationTraceEvent(
                stage="request.accepted",
                status="completed",
                detail="Executive conversation request accepted.",
            ),
            ConversationTraceEvent(
                stage="request.compiled",
                status="completed",
                detail=f"Compiled {len(objectives)} objective(s).",
                data={"routing_hints": sorted({hint for item in objectives for hint in item.routing_hints})},
            ),
        ]

        self.repository.append(
            ConversationMessage.create(
                session_id=context.session_id,
                role=ConversationRole.OPERATOR,
                content=context.operator_input,
                request_id=context.request_id,
                metadata={"mode": mode, "channel": channel},
            )
        )

        try:
            trace.append(
                ConversationTraceEvent(
                    stage="executive.dispatch",
                    status="processing",
                    detail="Dispatching request through the current JARVIS brain boundary.",
                )
            )
            raw_answer = self.answer_handler(context.operator_input)
            answer = self._normalize_answer(raw_answer)
            trace.append(
                ConversationTraceEvent(
                    stage="executive.response",
                    status="completed",
                    detail="JARVIS response completed.",
                )
            )
            response = ExecutiveConversationResponse(
                request_id=context.request_id,
                session_id=context.session_id,
                state=ConversationState.COMPLETED,
                answer=answer,
                objectives=objectives,
                trace=tuple(trace),
                metadata={"mode": mode, "channel": channel, "adapter": "core.src.brain.route_question"},
            )
        except Exception as exc:
            trace.append(
                ConversationTraceEvent(
                    stage="executive.response",
                    status="failed",
                    detail="JARVIS could not complete the request.",
                    data={"exception_type": type(exc).__name__},
                )
            )
            response = ExecutiveConversationResponse(
                request_id=context.request_id,
                session_id=context.session_id,
                state=ConversationState.FAILED,
                answer="JARVIS was unable to complete this request.",
                objectives=objectives,
                trace=tuple(trace),
                error=str(exc),
                metadata={"mode": mode, "channel": channel},
            )

        self.repository.append(
            ConversationMessage.create(
                session_id=context.session_id,
                role=ConversationRole.JARVIS,
                content=response.answer,
                request_id=context.request_id,
                metadata={
                    "state": response.state.value,
                    "error": response.error,
                    "trace": [item.to_dict() for item in response.trace],
                },
            )
        )
        return response

    def history(self, session_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
        return [message.to_dict() for message in self.repository.messages(session_id, limit=limit)]

    @staticmethod
    def _normalize_answer(value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            for key in ("answer", "response", "message", "output"):
                if key in value:
                    return str(value[key])
        return str(value)
