from __future__ import annotations

import json
import re
from pathlib import Path


STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "into", "onto",
    "your", "you", "are", "was", "were", "will", "shall", "may", "can",
    "pdf", "html", "docx", "txt", "epub", "files", "file", "book",
    "archive", "website", "document",
}


DOMAIN_ALIASES = {
    "afg war diary": [
        "afghanistan war diary",
        "afghan war diary",
        "wikileaks afghanistan",
        "afghanistan reports",
        "severity reports",
        "sigacts",
    ],
    "cmakelists": [
        "cmake",
        "cmake project",
        "build system",
        "c project",
    ],
    "quran": [
        "qur'an",
        "koran",
        "al quran",
        "quran translation",
        "arabic english quran",
    ],
}


ENTITY_RULES = {
    "Afghanistan": ["afghanistan", "afghan", "afg"],
    "WikiLeaks": ["wikileaks", "war diary"],
    "CMake": ["cmake", "cmakelists"],
    "C Programming": [" c ", "c language", "effective c"],
    "Quran": ["quran", "qur'an", "koran"],
    "Islam": ["islam", "deen", "hadith", "muslim"],
    "Security": ["hacking", "cyber", "security", "pentest"],
    "Aviation": ["aviation", "blackhawk", "uh-60", "faa"],
}


TOPIC_RULES = {
    "military_history": ["afghanistan", "war diary", "military", "sigacts"],
    "programming": ["programming", "cmake", "python", "java", "c++", "compiler"],
    "religion": ["quran", "islam", "deen", "hadith"],
    "cybersecurity": ["hacking", "security", "pentest", "kali"],
    "aviation": ["aviation", "blackhawk", "uh-60", "faa"],
}


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9_+-]{1,}", text.lower())


def important_terms(*texts: str | None, limit: int = 40) -> list[str]:
    counts: dict[str, int] = {}

    for text in texts:
        if not text:
            continue

        for token in tokenize(text):
            if token in STOPWORDS:
                continue
            if len(token) < 3:
                continue
            counts[token] = counts.get(token, 0) + 1

    return [
        term
        for term, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def detect_entities(haystack: str) -> list[str]:
    h = f" {haystack.lower()} "
    found = []

    for entity, needles in ENTITY_RULES.items():
        if any(needle in h for needle in needles):
            found.append(entity)

    return sorted(set(found))


def detect_topics(haystack: str) -> list[str]:
    h = haystack.lower()
    found = []

    for topic, needles in TOPIC_RULES.items():
        if any(needle in h for needle in needles):
            found.append(topic)

    return sorted(set(found))


def aliases_for(title: str | None, object_path: str | None) -> list[str]:
    title_norm = (title or "").lower().replace("_", " ").replace("-", " ").strip()
    path_norm = (object_path or "").lower().replace("_", " ").replace("-", " ")

    aliases: set[str] = set()

    if title:
        aliases.add(title)
        aliases.add(title_norm)

    for key, values in DOMAIN_ALIASES.items():
        if key in title_norm or key in path_norm:
            aliases.update(values)

    if object_path:
        stem = Path(object_path).stem.replace("_", " ").replace("-", " ").strip()
        if stem:
            aliases.add(stem)

    return sorted(a for a in aliases if a)


def enrich_row(row) -> dict:
    title = row["display_title"] or row["canonical_title"] or ""
    description = row["description"] or ""
    subject = row["subject"] or ""
    keywords = row["keywords"] or ""
    object_type = row["object_type"] or ""
    object_path = row["object_path"] or ""
    metadata_json = row["metadata_json"] or "{}"

    haystack = " ".join(
        [
            title,
            description,
            subject,
            keywords,
            object_type,
            object_path,
            metadata_json,
        ]
    )

    aliases = aliases_for(title, object_path)
    entities = detect_entities(haystack)
    topics = detect_topics(haystack)

    terms = important_terms(
        title,
        description,
        subject,
        keywords,
        object_type,
        object_path,
        metadata_json,
        " ".join(aliases),
        " ".join(entities),
        " ".join(topics),
    )

    data = {
        "aliases": aliases,
        "entities": entities,
        "topics": topics,
        "search_terms": terms,
    }

    return {
        "aliases": ", ".join(aliases),
        "entities": ", ".join(entities),
        "topics": ", ".join(topics),
        "search_terms": ", ".join(terms),
        "enrichment_json": json.dumps(data, ensure_ascii=False, sort_keys=True),
    }
