# Genesis X-B2.4A-1 — Utility Propagation & Intent-Aware Focus

X-B2.4A-1 corrects two live-corpus defects: answer utility previously stopped at the focus layer, and term coverage could not distinguish concept mention from query-intent satisfaction.

The pack keeps `retrieval_score` as immutable retrieval provenance while propagating a separate `synthesis_utility_score` into `QualificationScore.final`. It also detects generic query intent (`definition`, `mechanism`, `causal`, `comparison`, `procedural`, `temporal`, `general`) and rewards passages that satisfy the requested explanatory form.

No catalog, semantic-index, vector, or provenance mutation is authorized.
