from ..services.model_router import choose_model


def select_model(context, intent):
    return choose_model(intent)