from ..cognition.model_map import MODEL_MAP


def choose_model(intent: str) -> str:
    return MODEL_MAP.get(intent, "mistral")