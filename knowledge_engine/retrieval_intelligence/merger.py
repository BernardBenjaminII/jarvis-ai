"""Candidate merging for Retrieval Intelligence."""

from __future__ import annotations

from collections.abc import Iterable

from knowledge_engine.retrieval_intelligence.models import RetrievalCandidate


class CandidateMerger:
    """Merge provider results while preserving the strongest candidate."""

    def merge(
        self,
        groups: Iterable[Iterable[RetrievalCandidate]],
    ) -> list[RetrievalCandidate]:
        merged: dict[tuple[str, int], RetrievalCandidate] = {}

        for group in groups:
            for candidate in group:
                identity = candidate.identity()
                current = merged.get(identity)

                if current is None:
                    merged[identity] = candidate
                    continue

                if candidate.normalized_score > current.normalized_score:
                    winner = candidate
                    loser = current
                else:
                    winner = current
                    loser = candidate

                providers = set(
                    winner.metadata.get(
                        "retrieval_providers",
                        [winner.provider],
                    )
                )
                providers.add(loser.provider)

                winner.metadata["retrieval_providers"] = sorted(providers)

                merged[identity] = winner

        return sorted(
            merged.values(),
            key=lambda item: item.normalized_score,
            reverse=True,
        )
