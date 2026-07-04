from __future__ import annotations

import hashlib
import math
import re


class LocalHashEmbeddingProvider:
    provider_name = "local_hash"
    model_name = "hashing_vector_v1"

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions

        tokens = self._tokens(text)

        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        return self._normalize(vector)

    def _tokens(self, text: str) -> list[str]:
        return re.findall(r"[A-Za-z0-9_]+", text.lower())

    def _normalize(self, vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(x * x for x in vector))

        if norm == 0:
            return vector

        return [x / norm for x in vector]
