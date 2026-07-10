"""Deterministic Phase V-C query analyzer."""

from __future__ import annotations

import re
from collections import Counter

from knowledge_engine.query_understanding.lexicon import (
    DESIRED_OUTPUT_BY_TASK,
    DOMAIN_TERMS,
    SPECIALISTS_BY_DOMAIN,
    STOPWORDS,
    TASK_PATTERNS,
)
from knowledge_engine.query_understanding.models import QueryUnderstanding


TOKEN_PATTERN = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9_+#.-]*"
)

ENTITY_PATTERN = re.compile(
    r"\b(?:"
    r"SQLite|PostgreSQL|Postgres|MySQL|Oracle|Python|Java|"
    r"JavaScript|Linux|Ubuntu|Windows|macOS|Kali|"
    r"JARVIS|Ollama|BM25|SQL|LLM|AI|UH-60|Blackhawk"
    r")\b",
    re.IGNORECASE,
)


class QueryAnalyzer:
    """Convert raw search text into a structured interpretation."""

    def analyze(self, query: str) -> QueryUnderstanding:
        """Analyze and normalize a knowledge query."""

        original = query or ""
        normalized = self._normalize_text(original)

        if not normalized:
            raise ValueError("query must not be empty")

        task = self._detect_task(normalized)
        tokens = self._tokens(normalized)
        domains = self._detect_domains(normalized, tokens)
        entities = self._extract_entities(original)
        keywords = self._extract_keywords(tokens)
        specialists = self._specialists(domains)
        desired_output = DESIRED_OUTPUT_BY_TASK[task]

        retrieval_query = self._build_retrieval_query(
            normalized_query=normalized,
            task=task,
            entities=entities,
            keywords=keywords,
        )

        confidence = self._confidence(
            task=task,
            domains=domains,
            entities=entities,
            keywords=keywords,
        )

        explanation = self._explanation(
            task=task,
            domains=domains,
            entities=entities,
            specialists=specialists,
        )

        return QueryUnderstanding(
            original_query=original.strip(),
            normalized_query=normalized,
            retrieval_query=retrieval_query,
            task=task,
            domains=domains,
            entities=entities,
            keywords=keywords,
            desired_output=desired_output,
            specialists=specialists,
            confidence=confidence,
            explanation=explanation,
        )

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.strip().split())

    @staticmethod
    def _tokens(value: str) -> tuple[str, ...]:
        return tuple(
            token.lower()
            for token in TOKEN_PATTERN.findall(value)
        )

    @staticmethod
    def _detect_task(normalized_query: str) -> str:
        lowered = f" {normalized_query.lower()} "

        for task, patterns in TASK_PATTERNS:
            if any(pattern in lowered for pattern in patterns):
                return task

        return "research"

    @staticmethod
    def _detect_domains(
        normalized_query: str,
        tokens: tuple[str, ...],
    ) -> tuple[str, ...]:
        lowered = normalized_query.lower()
        token_set = set(tokens)
        scored: list[tuple[str, int]] = []

        for domain, terms in DOMAIN_TERMS.items():
            score = 0

            for term in terms:
                if " " in term:
                    if term in lowered:
                        score += 2
                elif term in token_set:
                    score += 1

            if score:
                scored.append((domain, score))

        scored.sort(
            key=lambda item: (-item[1], item[0])
        )

        return tuple(
            domain
            for domain, _ in scored[:3]
        )

    @staticmethod
    def _extract_entities(
        original_query: str,
    ) -> tuple[str, ...]:
        found: list[str] = []
        seen: set[str] = set()

        for match in ENTITY_PATTERN.finditer(original_query):
            entity = match.group(0)
            identity = entity.lower()

            if identity in seen:
                continue

            seen.add(identity)
            found.append(entity)

        return tuple(found)

    @staticmethod
    def _extract_keywords(
        tokens: tuple[str, ...],
    ) -> tuple[str, ...]:
        meaningful = [
            token
            for token in tokens
            if token not in STOPWORDS
            and len(token) > 1
        ]

        counts = Counter(meaningful)

        ordered = sorted(
            counts,
            key=lambda token: (
                -counts[token],
                meaningful.index(token),
            ),
        )

        return tuple(ordered[:12])

    @staticmethod
    def _specialists(
        domains: tuple[str, ...],
    ) -> tuple[str, ...]:
        specialists: list[str] = []

        for domain in domains:
            for specialist in SPECIALISTS_BY_DOMAIN.get(
                domain,
                (),
            ):
                if specialist not in specialists:
                    specialists.append(specialist)

        if not specialists:
            specialists.append("general_knowledge")

        return tuple(specialists)

    @staticmethod
    def _build_retrieval_query(
        *,
        normalized_query: str,
        task: str,
        entities: tuple[str, ...],
        keywords: tuple[str, ...],
    ) -> str:
        """Construct the query sent to Retrieval Intelligence.

        Instruction words (explain, compare, find, etc.) are removed so the
        retrieval engine focuses on subject matter rather than user intent.
        """

        del normalized_query

        task_words = {
            "explain",
            "compare",
            "find",
            "search",
            "show",
            "give",
            "list",
            "describe",
            "define",
            "tell",
            "locate",
            "instructions",
            "instruction",
            "procedure",
            "steps",
            "how",
            "what",
            "why",
        }

        terms: list[str] = []
        seen: set[str] = set()

        for value in (*entities, *keywords):

            cleaned = value.strip()

            if not cleaned:
                continue

            lowered = cleaned.lower()

            if lowered in task_words:
                continue

            if lowered in seen:
                continue

            seen.add(lowered)
            terms.append(cleaned)

        if not terms:
            return ""

        del task

        return " ".join(terms)

    @staticmethod
    def _confidence(
        *,
        task: str,
        domains: tuple[str, ...],
        entities: tuple[str, ...],
        keywords: tuple[str, ...],
    ) -> float:
        score = 0.40

        if task != "research":
            score += 0.15

        if domains:
            score += min(0.20, len(domains) * 0.10)

        if entities:
            score += min(0.15, len(entities) * 0.075)

        if len(keywords) >= 2:
            score += 0.10

        return min(1.0, score)

    @staticmethod
    def _explanation(
        *,
        task: str,
        domains: tuple[str, ...],
        entities: tuple[str, ...],
        specialists: tuple[str, ...],
    ) -> str:
        domain_text = (
            ", ".join(domains)
            if domains
            else "general knowledge"
        )

        entity_text = (
            ", ".join(entities)
            if entities
            else "no explicit named entities"
        )

        specialist_text = ", ".join(specialists)

        return (
            f"Classified as {task}; domains: {domain_text}; "
            f"entities: {entity_text}; suggested specialists: "
            f"{specialist_text}."
        )
