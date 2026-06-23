from .cognition.intent_classifier import classify_intent
from .services.model_router import choose_model
from .cognition.context_builder import build_context
from .cognition.model_selector import select_model
from .cognition.prompt_builder import build_prompt

from .services.llm_service import query_llm

from .agents.recon_agent import handle_recon


def route_question(question: str):

    context = build_context()

    classification = classify_intent(question)

    intent = classification["intent"]
    task_type = classification["task_type"]

    print(
        f"[DEBUG] "
        f"ENV={context['environment']} | "
        f"ROLE={context['role']} | "
        f"INTENT={intent} | "
        f"TASK={task_type}"
    )

    if intent == "recon":
        return handle_recon(question)

    model = choose_model(intent)

    print(f"[DEBUG] MODEL={model}")
    print(f"[DEBUG] CLASSIFICATION={classification}")

    prompt = build_prompt(context, question, intent)

    response = query_llm(prompt, model=model)

    return f"[JARVIS/{context['environment']}/{model}] {response}"

