from pathlib import Path

from core.knowledge_mapper.rules import load_rules

RULES = load_rules()


def map_path(path: str):

    p = Path(path)

    pieces = list(p.parts)

    try:
        i = pieces.index("Knowledge")
        relative = "/".join(x.lower() for x in pieces[i+1:])
    except ValueError:
        relative = "/".join(x.lower() for x in pieces)

    for rule, mapping in RULES.items():
        if relative.startswith(rule):
            return mapping

    return {
        "subject": "unknown"
    }
