from .cognition.intent_classifier import classify_intent
from .cognition.response_planner import build_response_plan

from .services.model_router import choose_model

from .cognition.context_builder import build_context
from .cognition.prompt_builder import build_prompt

from .services.llm_service import query_llm

from .agents.recon_agent import handle_recon

from .planner.tool_planner import planner
from .runtime.executor import executor

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
        return executor.execute(execution_plan)

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
