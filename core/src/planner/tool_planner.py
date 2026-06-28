from __future__ import annotations

from ..runtime.execution_plan import ExecutionPlan


class ToolPlanner:
    """
    Converts natural-language requests into execution plans.

    This class NEVER executes anything.
    It only decides what should happen.
    """

    def plan(self, question: str) -> ExecutionPlan | None:

        q = question.lower().strip()

        # -------------------------------------------------
        # Filesystem
        # -------------------------------------------------

        if (
            "runtime" in q
            and any(
                word in q
                for word in (
                    "list",
                    "show",
                    "contents",
                    "inside",
                )
            )
        ):
            return ExecutionPlan(
                type="tool",
                tool="filesystem",
                action="ls",
                args={
                    "path": "runtime",
                },
            )

        if (
            "knowledge" in q
            and "exist" in q
        ):
            return ExecutionPlan(
                type="tool",
                tool="filesystem",
                action="exists",
                args={
                    "path": "knowledge",
                },
            )

        if any(
            phrase in q
            for phrase in (
                "disk usage",
                "free space",
                "space left",
            )
        ):
            return ExecutionPlan(
                type="tool",
                tool="filesystem",
                action="disk_usage",
                args={
                    "path": "runtime",
                },
            )

        if (
            "find" in q
            and "launcher.py" in q
        ):
            return ExecutionPlan(
                type="tool",
                tool="filesystem",
                action="find",
                args={
                    "path": "project",
                    "pattern": "launcher.py",
                },
            )

        # -------------------------------------------------
        # Nothing matched
        # -------------------------------------------------

        return None


planner = ToolPlanner()
