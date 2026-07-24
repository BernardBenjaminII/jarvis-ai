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
from core.conversation.orchestrator import ExecutiveConversationOrchestrator
from core.conversation.repository import ConversationRepository


AnswerHandler = Callable[[str], Any]


class ExecutiveConversationService:
    """Own the operator-to-JARVIS boundary and activate the Executive organization."""

    def __init__(
        self,
        *,
        database_path: str | Path,
        answer_handler: AnswerHandler | None = None,
        orchestrator: ExecutiveConversationOrchestrator | None = None,
        compiler: ExecutiveRequestCompiler | None = None,
    ) -> None:
        if answer_handler is None and orchestrator is None:
            raise ValueError("An answer_handler or orchestrator is required")
        self.repository = ConversationRepository(database_path)
        self.answer_handler = answer_handler
        self.orchestrator = orchestrator
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
            if self.orchestrator is not None:
                trace.append(
                    ConversationTraceEvent(
                        stage="executive.dispatch",
                        status="processing",
                        detail="Dispatching compiled objectives to the Executive Director.",
                    )
                )
                result = self.orchestrator.execute(context)
                answer = result.answer
                trace.extend(result.trace)
                response_metadata = {
                    "mode": mode,
                    "channel": channel,
                    **result.metadata(),
                }
            else:
                trace.append(
                    ConversationTraceEvent(
                        stage="executive.dispatch",
                        status="processing",
                        detail="Dispatching request through the legacy JARVIS brain adapter.",
                    )
                )
                answer = self._normalize_answer(self.answer_handler(context.operator_input))
                response_metadata = {
                    "mode": mode,
                    "channel": channel,
                    "adapter": "legacy_answer_handler",
                }

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
                metadata=response_metadata,
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
                    **dict(response.metadata),
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
