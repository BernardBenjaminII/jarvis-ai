from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class LocalEmbeddingProvider:
    """
    Local sentence-transformers embedding provider.

    Default model:
    sentence-transformers/all-MiniLM-L6-v2

    Output:
    list[list[float]]
    """

    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    def __post_init__(self) -> None:
        self.model = SentenceTransformer(self.model_name)

    def embed_text(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text.")

        vector = self.model.encode(text, normalize_embeddings=True)

        if isinstance(vector, np.ndarray):
            return vector.astype(float).tolist()

        return list(vector)

    def embed_batch(self, texts: Iterable[str]) -> List[list[float]]:
        cleaned = [t for t in texts if t and t.strip()]

        if not cleaned:
            raise ValueError("Cannot embed empty batch.")

        vectors = self.model.encode(cleaned, normalize_embeddings=True)

        return [
            v.astype(float).tolist() if isinstance(v, np.ndarray) else list(v)
            for v in vectors
        ]
