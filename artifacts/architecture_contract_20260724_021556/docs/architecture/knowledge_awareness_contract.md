# Knowledge Awareness Contract

## Objective

JARVIS must know what it knows, what it does not know, and what evidence supports its conclusions.

## Required knowledge states

- discovered
- catalogued
- classified
- validated
- extracted
- chunked
- embedded
- indexed
- retrievable
- reasoning-ready
- stale
- failed
- quarantined

## Coverage model

Coverage must be reported by:

- domain
- topic
- source class
- authority level
- freshness
- language
- representation readiness
- retrieval readiness

## Knowledge gap record

```json
{
  "gap_id": "stable-id",
  "domain": "cybersecurity",
  "topic": "cloud incident response",
  "reason": "insufficient authoritative coverage",
  "severity": "high",
  "confidence": 0.82,
  "detected_at": "RFC3339",
  "supporting_evidence": [],
  "recommended_sources": [],
  "research_status": "proposed|approved|acquiring|ingesting|resolved|deferred"
}
```

## Required UI surfaces

Knowledge Overview:
- total catalog objects
- objects by lifecycle state
- chunks
- embeddings
- graph nodes/edges
- index health
- retrieval health
- recent ingestion

Coverage:
- known domains
- sparse domains
- stale domains
- unsupported domains
- confidence and basis

Research Queue:
- detected gap
- why it matters
- recommended source type
- acquisition status
- validation outcome
- ingestion result

Answer transparency:
- retrieved sources
- confidence
- contradictions
- unsupported claims
- missing evidence
