from .cognition.context_builder import build_context
from .cognition.model_selector import select_model
from .cognition.prompt_builder import build_prompt

from .services.llm_service import query_llm

from .agents.recon_agent import handle_recon


def classify_intent(question: str):

    q = question.lower()

    recon_words = [
        "recon",
        "subdomain",
        "enumerate",
        "scan",
        "bug bounty",
        "target",
	"network",
	"map network", 
	"discover hosts",
	"host discovery",
	"nmap", 
	"ports", 
	"port scan", 
	"wifi scan", 
    ]

    if any(word in q for word in recon_words):
        return "recon"

    return "general"


def route_question(question: str):

    context = build_context()

    intent = classify_intent(question)

    print(
        f"[DEBUG] "
        f"ENV={context['environment']} | "
        f"ROLE={context['role']} | "
        f"INTENT={intent}"
    )

    if intent == "recon":
        return handle_recon(question)

    model = select_model(context, intent)

    prompt = build_prompt(context, question)

    response = query_llm(prompt, model=model)

    return f"[JARVIS/{context['environment']}/{model}] {response}"
