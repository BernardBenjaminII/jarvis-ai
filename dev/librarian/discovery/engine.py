from __future__ import annotations

import json
import re
from pathlib import Path

from dev.librarian.discovery.models import DiscoveryCandidate, TrustedSource, utc_now


DEFAULT_SOURCE_REGISTRY = Path(__file__).parent / "sources" / "trusted_sources.json"
DEFAULT_DISCOVERY_ROOT = Path(
    "/media/abdullah/JARVISDATA/Jarvis_Downloaded_Knowledge/discovery"
)


TOPIC_ALIASES = {
    "cs": "computer_science",
    "computer science": "computer_science",
    "ai": "ai",
    "artificial intelligence": "ai",
    "ml": "machine_learning",
    "machine learning": "machine_learning",
    "field medicine": "field_medicine",
    "emergency medicine": "emergency_medicine",
    "public health": "public_health",
    "infectious disease": "infectious_disease",
    "linear algebra": "linear_algebra",
    "control systems": "control_systems",
    "systems engineering": "systems_engineering",
}


RELATED_TOPICS = {
    "field_medicine": ["medicine", "emergency_medicine", "trauma", "public_health", "surgery"],
    "emergency_medicine": ["medicine", "trauma", "surgery", "public_health"],
    "trauma": ["medicine", "surgery", "emergency_medicine", "field_medicine"],
    "linear_algebra": ["mathematics", "computer_science", "ai", "engineering"],
    "machine_learning": ["computer_science", "ai", "mathematics", "statistics"],
    "ai": ["computer_science", "mathematics", "engineering"],
    "cybersecurity": ["computer_science", "standards", "cryptography"],
    "aerospace": ["engineering", "aviation", "systems_engineering"],
    "rotorcraft": ["aviation", "aerospace", "engineering"],
    "control_systems": ["engineering", "robotics", "electrical_engineering", "mechanical_engineering"],
}


def normalize_topic(topic: str) -> str:
    t = topic.strip().lower().replace("-", " ")
    return TOPIC_ALIASES.get(t, t.replace(" ", "_"))


def human_topic(topic: str) -> str:
    return topic.replace("_", " ")


def slugify(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", text.strip().lower()).strip("_")


def load_sources(path: Path = DEFAULT_SOURCE_REGISTRY) -> list[TrustedSource]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [TrustedSource(**item) for item in data]


def source_matches_topic(source: TrustedSource, topic: str) -> bool:
    expanded = {topic, *RELATED_TOPICS.get(topic, [])}
    source_topics = set(source.topics)
    return bool(expanded & source_topics)


def score_candidate(source: TrustedSource, topic: str) -> int:
    score = source.trust_score
    if topic in source.topics:
        score += 15
    if source.method in {"mit_ocw_course_package", "open_textbook"}:
        score += 5
    return min(score, 100)


def discover(topic: str, max_candidates: int = 50) -> list[DiscoveryCandidate]:
    topic = normalize_topic(topic)
    sources = load_sources()
    candidates: list[DiscoveryCandidate] = []

    for source in sources:
        if not source_matches_topic(source, topic):
            continue

        priority = score_candidate(source, topic)

        for template in source.query_templates:
            query = template.format(topic=human_topic(topic))
            candidates.append(
                DiscoveryCandidate(
                    topic=topic,
                    source_name=source.name,
                    trust_score=source.trust_score,
                    method=source.method,
                    base_url=source.base_url,
                    query=query,
                    priority=priority,
                    reason=f"{source.name} covers {topic} via {source.method}",
                    created_at=utc_now(),
                )
            )

    candidates.sort(key=lambda c: (c.priority, c.trust_score), reverse=True)
    return candidates[:max_candidates]


def write_discovery_plan(topic: str, candidates: list[DiscoveryCandidate], out_root: Path = DEFAULT_DISCOVERY_ROOT) -> Path:
    topic = normalize_topic(topic)
    out_root.mkdir(parents=True, exist_ok=True)
    path = out_root / f"{slugify(topic)}_discovery_plan.json"

    payload = {
        "topic": topic,
        "created_at": utc_now(),
        "candidate_count": len(candidates),
        "candidates": [c.to_dict() for c in candidates],
    }

    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
