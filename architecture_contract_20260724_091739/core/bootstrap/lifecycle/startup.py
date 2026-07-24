from core.bootstrap.services.models import ensure_models
from core.bootstrap.services.ollama import ensure_ollama


def run(paths):
    """
    Execute startup services.
    """

    ensure_ollama(paths)

    ensure_models()
