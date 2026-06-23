from .model_map import MODEL_MAP


def required_models():
    return sorted(set(MODEL_MAP.values()))