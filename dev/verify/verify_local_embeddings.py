from knowledge_engine.embeddings.local_provider import LocalEmbeddingProvider


def main() -> None:
    provider = LocalEmbeddingProvider()

    sample = "JARVIS is building a local knowledge engine."

    vector = provider.embed_text(sample)

    print("Embedding provider: OK")
    print(f"Vector dimensions: {len(vector)}")
    print(f"First 5 values: {vector[:5]}")

    batch = provider.embed_batch([
        "PDF ingestion works.",
        "Local embeddings are required for semantic search.",
        "JARVIS Academy will use indexed knowledge."
    ])

    print(f"Batch size: {len(batch)}")
    print(f"Batch vector dimensions: {[len(v) for v in batch]}")

    assert len(vector) > 0
    assert len(batch) == 3
    assert all(len(v) == len(vector) for v in batch)

    print("Milestone 3A verification: PASS")


if __name__ == "__main__":
    main()
