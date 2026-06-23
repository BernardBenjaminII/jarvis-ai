from .response_profiles import RESPONSE_PROFILES


def build_response_plan(
    classification,
    question=""
):

    intent = classification["intent"]

    profile = RESPONSE_PROFILES.get(
        intent,
        RESPONSE_PROFILES["assistant"]
    )

    max_tokens = profile["max_tokens"]

    question = question.lower()

    #
    # Dynamic response expansion
    #

    if "project status" in question:
        max_tokens = 4000

    elif "status of my project" in question:
        max_tokens = 4000

    elif "roadmap" in question:
        max_tokens = 5000

    elif "deep dive" in question:
        max_tokens = 6000

    elif "compare" in question:
        max_tokens = 4000

    elif "architecture" in question:
        max_tokens = 4000

    return {
        "intent": intent,
        "max_tokens": max_tokens,
        "temperature": profile["temperature"],
    }