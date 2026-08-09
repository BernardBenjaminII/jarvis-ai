# Genesis X-B1.1b — Embedding Context Adaptation & Semantic Fragmentation

Canonical `runtime_chunks` remain immutable.

Context-overflow chunks are represented by deterministic semantic fragments.
Fragments carry parent runtime chunk ID, fragment index, offsets, SHA-256, text,
stage, attempts, and detail. Vectors are stored separately in
`semantic_fragment_vectors`.

A parent becomes `FRAGMENTED`, then `COMPLETE_FRAGMENTED` when all fragments
have semantic vectors.

Final certification requires zero remaining context-length rejections and no
incomplete semantic fragments.
