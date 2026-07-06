from __future__ import annotations

import os
from functools import cached_property
from pathlib import Path

from sentence_transformers import SentenceTransformer


RUNTIME_MODEL_DIR = Path(
    os.environ.get(
        "JARVIS_EMBEDDING_CACHE",
        "/media/abdullah/JARVIS_RUNTIME_L/models/embeddings",
    )
)


class LocalEmbeddingProvider:
    provider_name = "sentence_transformers"
    model_name = "all-MiniLM-L6-v2"

    @cached_property
    def model(self) -> SentenceTransformer:
        RUNTIME_MODEL_DIR.mkdir(parents=True, exist_ok=True)

        return SentenceTransformer(
            self.model_name,
            cache_folder=str(RUNTIME_MODEL_DIR),
        )

    @property
    def dimensions(self) -> int:
        return self.model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> list[float]:
        vector = self.model.encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        return vector.tolist()
