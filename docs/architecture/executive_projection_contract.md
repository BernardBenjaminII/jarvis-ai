# Executive Projection Contract

## Purpose

Define the stable read model consumed by Mission Control.

## Root endpoint

```http
GET /operations/executive
```

## Minimum response

```json
{
  "schema_version": "1.0",
  "generated_at": "RFC3339",
  "system": {
    "name": "JARVIS",
    "mode": "development|operational|degraded|maintenance",
    "health": "healthy|degraded|unhealthy|unknown"
  },
  "commander_brief": {
    "current_focus": null,
    "active_mission_id": null,
    "priority_items": [],
    "alerts": [],
    "recommendations": []
  },
  "missions": {
    "active": [],
    "queued": [],
    "recently_completed": []
  },
  "knowledge": {
    "catalog_health": "unknown",
    "objects": 0,
    "chunks": 0,
    "embeddings": 0,
    "coverage": [],
    "known_gaps": [],
    "research_queue": []
  },
  "reasoning": {
    "active_sessions": [],
    "open_hypotheses": [],
    "contradictions": [],
    "recommendations": []
  },
  "capabilities": {
    "total": 0,
    "available": 0,
    "degraded": 0,
    "unavailable": 0
  },
  "runtime": {
    "services": [],
    "workers": [],
    "models": [],
    "resources": {}
  },
  "timeline": [],
  "provenance": {
    "sources": [],
    "projection_build_id": "stable-id"
  },
  "warnings": []
}
```

## Projection rules

1. Every number must be derived from a real backing source.
2. Unknown values must remain `null`, `"unknown"`, or an explicitly empty collection.
3. Empty collections may not imply successful configuration.
4. Each subsection must expose its health or degradation state.
5. The projection should remain read-only and safe to call frequently.
6. Expensive calculations must be cached with visible timestamps.
7. The root projection may summarize; dedicated subsystem endpoints provide details.

## Dedicated endpoints

```text
GET /operations/executive
GET /operations/capabilities
GET /operations/knowledge
GET /operations/knowledge/gaps
GET /operations/knowledge/research-queue
GET /operations/reasoning
GET /operations/reasoning/sessions/{id}
GET /operations/missions
GET /operations/missions/{id}
GET /operations/acquisition
GET /operations/runtime
GET /operations/timeline
GET /operations/health
```
