from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from core.retrieval.grounded_answer import GroundedAnswerEngine

from .contracts import (
    GroundedAnswerExecutionRequest,
    GroundedAnswerExecutionResponse,
)


SynthesisHandler = Callable[[str], str]


@dataclass(slots=True)
class GroundedAnswerRuntimeService:
    """
    Canonical adapter between the Executive conversation runtime and IX-A4.6.

    Pack 1 introduces the interface only. Callers must invoke `plan()` or
    `execute()` explicitly; no existing runtime path is modified.
    """

    engine: GroundedAnswerEngine

    @classmethod
    def create_default(cls) -> "GroundedAnswerRuntimeService":
        return cls(engine=GroundedAnswerEngine())

    def plan(
        self,
        request: GroundedAnswerExecutionRequest,
    ) -> GroundedAnswerExecutionResponse:
        plan = self.engine.plan(
            request.context.operator_input,
            request.qualification,
        )

        return GroundedAnswerExecutionResponse(
            plan=plan,
            answer=None,
            synthesis_invoked=False,
            metadata={
                "adapter": "grounded_answer_runtime_service",
                "mode": request.context.mode,
                "channel": request.context.channel,
                "request_id": request.context.request_id,
                "session_id": request.context.session_id,
                "behavior_change": False,
            },
        )

    def execute(
        self,
        request: GroundedAnswerExecutionRequest,
        synthesis_handler: SynthesisHandler,
    ) -> GroundedAnswerExecutionResponse:
        plan = self.engine.plan(
            request.context.operator_input,
            request.qualification,
        )
        answer = self.engine.answer(
            request.context.operator_input,
            request.qualification,
            synthesis_handler,
        )

        return GroundedAnswerExecutionResponse(
            plan=plan,
            answer=answer,
            synthesis_invoked=True,
            metadata={
                "adapter": "grounded_answer_runtime_service",
                "mode": request.context.mode,
                "channel": request.context.channel,
                "request_id": request.context.request_id,
                "session_id": request.context.session_id,
                "behavior_change": False,
            },
        )
