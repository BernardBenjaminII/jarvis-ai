"""Read-only report: python -m core.src.cognition.platform_status"""
import json
from .context_builder import build_context


def snapshot():
    # Reporting platform state must not probe the network or invoke the LLM.
    return build_context(check_network=False)


if __name__ == "__main__":
    print(json.dumps(snapshot(), indent=2))
