from __future__ import annotations

from pathlib import Path

from knowledge_engine.director.router.models import RoutedIntent


class IntentRouter:
    """
    Deterministic intent router.

    Converts natural-ish user requests into Director intents.

    This is intentionally rule-based for Phase IV-D.
    LLM-assisted routing can be added later.
    """

    SEARCH_KEYWORDS = {
        "search",
        "find",
        "look up",
        "lookup",
        "retrieve",
        "show me",
        "what do i know",
        "where is",
    }

    INGEST_KEYWORDS = {
        "ingest",
        "import",
        "process",
        "learn",
        "add file",
        "add document",
        "read file",
    }

    def route(
        self,
        text: str,
        *,
        source_path: str | Path | None = None,
        limit: int = 5,
    ) -> RoutedIntent:
        original = text or ""
        normalized = original.strip().lower()

        path = Path(source_path) if source_path else None

        if path is not None:
            return RoutedIntent(
                intent="ingest_fixture",
                confidence=0.95,
                reason="source_path provided",
                source_path=path,
                query=original.strip(),
                metadata={"limit": limit},
            )

        if not normalized:
            return RoutedIntent(
                intent="unknown",
                confidence=0.0,
                reason="empty request",
                metadata={"limit": limit},
            )

        if self._contains_any(normalized, self.INGEST_KEYWORDS):
            return RoutedIntent(
                intent="ingest_fixture",
                confidence=0.80,
                reason="matched ingest keyword",
                query=original.strip(),
                metadata={"limit": limit},
            )

        if self._contains_any(normalized, self.SEARCH_KEYWORDS):
            query = self._strip_search_prefix(original.strip())

            return RoutedIntent(
                intent="search",
                confidence=0.85,
                reason="matched search keyword",
                query=query,
                metadata={"limit": limit},
            )

        return RoutedIntent(
            intent="search",
            confidence=0.60,
            reason="default to search",
            query=original.strip(),
            metadata={"limit": limit},
        )

    def _contains_any(self, text: str, keywords: set[str]) -> bool:
        return any(keyword in text for keyword in keywords)

    def _strip_search_prefix(self, text: str) -> str:
        prefixes = [
            "search for ",
            "search ",
            "find ",
            "find me ",
            "look up ",
            "lookup ",
            "retrieve ",
            "show me ",
        ]

        lowered = text.lower()

        for prefix in prefixes:
            if lowered.startswith(prefix):
                return text[len(prefix):].strip()

        return text
