from __future__ import annotations

from typing import Any

from tools.dispatcher import dispatch

from .execution_plan import ExecutionPlan


class Executor:
    """
    Executes an ExecutionPlan.

    The planner decides WHAT should happen.
    The executor decides HOW to make it happen.
    """

    def execute(self, plan: ExecutionPlan | None) -> Any:

        if plan is None:
            return None

        # -------------------------------------------------
        # Tool execution
        # -------------------------------------------------

        if plan.type == "tool":

            return dispatch(
                tool=plan.tool,
                action=plan.action,
                **plan.args,
            )

        # -------------------------------------------------
        # LLM execution
        # -------------------------------------------------

        if plan.type == "llm":

            raise NotImplementedError(
                "LLM execution has not been implemented yet."
            )

        # -------------------------------------------------
        # Agent execution
        # -------------------------------------------------

        if plan.type == "agent":

            raise NotImplementedError(
                "Agent execution has not been implemented yet."
            )

        # -------------------------------------------------
        # Unknown plan
        # -------------------------------------------------

        raise ValueError(
            f"Unknown execution type: {plan.type}"
        )


executor = Executor()
