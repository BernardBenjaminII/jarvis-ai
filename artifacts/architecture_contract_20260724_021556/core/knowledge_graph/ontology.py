from pathlib import Path
from dataclasses import dataclass
import yaml

ROOT = Path("knowledge/ontology")


def _load_yaml(name: str):
    with open(ROOT / f"{name}.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class KnowledgeOntology:

    domains: dict
    relationships: dict
    campaigns: dict
    concepts: dict
    prerequisites: dict


def load_ontology() -> KnowledgeOntology:

    return KnowledgeOntology(
        domains=_load_yaml("domains"),
        relationships=_load_yaml("relationships"),
        campaigns=_load_yaml("campaigns"),
        concepts=_load_yaml("concepts"),
        prerequisites=_load_yaml("prerequisites"),
    )
