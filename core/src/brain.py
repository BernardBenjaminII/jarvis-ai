import os

from .cognition.intent_classifier import classify_intent


def _debug(message: str) -> None:
    if os.getenv("JARVIS_DEBUG", "").strip().casefold() in {"1", "true", "yes", "on"}:
        print(message)

from .cognition.response_planner import build_response_plan

from .services.model_router import choose_model

from .cognition.context_builder import build_context
from .cognition.prompt_builder import build_prompt, build_system_prompt

from .services.llm_service import query_llm

from .agents.recon_agent import handle_recon

from .planner.tool_planner import planner
from .runtime.executor import executor


def _present_tool_result(value):
    """Return a concise human-facing description of a deterministic tool result.

    The original result is preserved separately by route_question() as
    technical_details. This function never destroys or mutates tool output.
    """
    if not isinstance(value, dict):
        return str(value)

    success = value.get("success")
    tool = str(value.get("tool") or "").strip()
    action = str(value.get("action") or "").strip()
    result = value.get("result")

    if success is False:
        error = (
            value.get("error")
            or value.get("message")
            or value.get("detail")
            or "The operation did not complete successfully."
        )
        return f"The {tool or 'requested'} operation failed: {error}"

    # --------------------------------------------------------------
    # Filesystem directory listing
    # --------------------------------------------------------------
    if tool == "filesystem" and action in {"ls", "list", "list_directory"}:
        if isinstance(result, dict):
            directories = result.get("directories") or []
            files = result.get("files") or []

            directory_names = [
                str(item.get("name"))
                for item in directories
                if isinstance(item, dict) and item.get("name")
            ]
            file_names = [
                str(item.get("name"))
                for item in files
                if isinstance(item, dict) and item.get("name")
            ]

            count = result.get("count")
            if count is None:
                count = len(directory_names) + len(file_names)

            path = value.get("path")
            lines = []

            if path:
                lines.append(
                    f"{path} contains {len(directory_names)} "
                    f"{'directory' if len(directory_names) == 1 else 'directories'} "
                    f"and {len(file_names)} "
                    f"{'file' if len(file_names) == 1 else 'files'}."
                )
            else:
                lines.append(
                    f"The location contains {len(directory_names)} "
                    f"{'directory' if len(directory_names) == 1 else 'directories'} "
                    f"and {len(file_names)} "
                    f"{'file' if len(file_names) == 1 else 'files'}."
                )

            if directory_names:
                lines.append("")
                lines.append("Directories:")
                lines.append(", ".join(directory_names))

            if file_names:
                lines.append("")
                lines.append("Files:")
                lines.append(", ".join(file_names))

            lines.append("")
            lines.append(f"{count} items total.")

            return "\n".join(lines)

    # --------------------------------------------------------------
    # Generic deterministic tool result
    # --------------------------------------------------------------
    if success is True:
        label = " ".join(part for part in (tool, action) if part).strip()

        if isinstance(result, str) and result.strip():
            return result.strip()

        if isinstance(result, dict):
            for key in ("answer", "message", "summary", "output", "text"):
                candidate = result.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()

        if label:
            return f"The {label} operation completed successfully."

        return "The requested operation completed successfully."

    # Non-standard result envelope. Keep output useful without pretending
    # that the structure is prose.
    for key in ("answer", "message", "summary", "output", "text"):
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()

    return "The requested operation completed. Open Technical details to inspect the result."


def synthesize_grounded_answer(synthesis_prompt: str):
    """
    Synthesize an Executive Conversation response from an already-grounded
    synthesis prompt.

    TRUST BOUNDARY:
    Retrieved evidence, catalog metadata, awareness state, and grounded-answer
    instructions are DATA. They must never be reinterpreted as fresh operator
    tool instructions.

    Tool planning therefore belongs only to the initial operator-input routing
    path (route_question), never to this synthesis path.
    """

    context = build_context()

    #
    # The synthesis prompt already contains the original operator question,
    # grounded evidence, knowledge state, and grounded-answer contract.
    #
    # Do NOT call planner.plan() here.
    # Do NOT execute tools here.
    # Do NOT dispatch recon here.
    #

    # Classify the operator's request, not the evidence-enriched synthesis
    # payload. Evidence may contain words such as strategy, planning, or steps
    # that describe source content rather than operator intent.
    operator_input = synthesis_prompt.split(
        "\n\nJARVIS KNOWLEDGE GROUNDING:",
        1,
    )[0].strip()
    classification = classify_intent(operator_input)

    intent = classification["intent"]

    model = choose_model(intent)

    plan = build_response_plan(
        classification,
        synthesis_prompt,
    )

    _debug(
        f"[DEBUG] SYNTHESIS "
        f"ENV={context['environment']} | "
        f"INTENT={intent} | "
        f"MODEL={model}"
    )

    response = query_llm(
        prompt=build_prompt(
            context,
            synthesis_prompt,
            intent,
        ),
        model=model,
        max_tokens=plan["max_tokens"],
        temperature=plan["temperature"],
        system=build_system_prompt(intent),
    )

    return (
        f"[JARVIS/"
        f"{context['environment']}/"
        f"{model}] "
        f"{response}"
    )


def route_question(question: str):

    #
    # Build runtime context
    #

    context = build_context()

    #
    # Intent classification
    #

    classification = classify_intent(question)

    intent = classification["intent"]
    task_type = classification["task_type"]

    #
    # Tool planning
    #

    execution_plan = planner.plan(question)

    if execution_plan is not None:
        tool_result = executor.execute(execution_plan)
        return {
            "answer": _present_tool_result(tool_result),
            "technical_details": tool_result,
        }

    #
    # JARVIS-specific intent overrides
    #

    q = question.lower().strip()

    if (
        "project status" in q
        or "status of my project" in q
        or "jarvis roadmap" in q
        or "current priorities" in q
        or "architecture" in q
        or "jarvis architecture" in q
        or "roadmap" in q
        or "project roadmap" in q
    ):
        intent = "planning"

    #
    # Debug
    #

    print(
        f"[DEBUG] "
        f"ENV={context['environment']} | "
        f"ROLE={context['role']} | "
        f"INTENT={intent} | "
        f"TASK={task_type}"
    )

    #
    # Tool routing
    #

    if intent == "recon":
        return handle_recon(question)

    #
    # Model routing
    #

    model = choose_model(intent)

    #
    # Response planning
    #

    plan = build_response_plan(
        classification,
        question,
    )

    print(f"[DEBUG] MODEL={model}")
    print(f"[DEBUG] CLASSIFICATION={classification}")
    print(f"[DEBUG] RESPONSE PLAN={plan}")

    #
    # Prompt generation
    #

    prompt = build_prompt(
        context,
        question,
        intent,
    )

    #
    # LLM call
    #

    response = query_llm(
        prompt=prompt,
        model=model,
        max_tokens=plan["max_tokens"],
        temperature=plan["temperature"],
        system=build_system_prompt(intent),
    )

    #
    # Final response
    #

    return (
        f"[JARVIS/"
        f"{context['environment']}/"
        f"{model}] "
        f"{response}"
    )
