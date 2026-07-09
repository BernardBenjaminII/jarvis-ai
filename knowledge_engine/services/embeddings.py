from __future__ import annotations

from typing import Iterable

from knowledge_engine.embeddings.local_provider import LocalEmbeddingProvider


class EmbeddingService:
    """
    Canonical public embedding service.

    Workflows, Doctor, Librarian and future agents
    should use this service.

    Background database embedding remains the
    responsibility of EmbeddingEngine.
    """

    def __init__(self):
        self.provider = LocalEmbeddingProvider()

    def embed(self, text: str) -> list[float]:
        return self.provider.embed(text)

    def embed_batch(
        self,
        texts: Iterable[str],
    ) -> list[list[float]]:
        return self.provider.embed_batch(texts)
