# JARVIS Gen 2 Phase II-A — Capability-Based Director Routing

## Purpose

Phase II-A separates task capability inference from director selection.

The planner determines what a task requires. The Director Registry chooses the
best available director using capability coverage, readiness, and priority.

## Director readiness

- `ready`
- `degraded`
- `unavailable`

Unavailable directors cannot be selected.

## Routing evidence

Each delegated task stores:

- Required capabilities
- Selected director
- Ranked candidates
- Matched capabilities
- Missing capabilities
- Scores
- Readiness state
- Selection reason

## Current directors

### Executive

- `mission_analysis`
- `mission_synthesis`
- `general_reasoning`

### Knowledge

- `knowledge_search`
- `knowledge_retrieval`
- `knowledge_summarization`

The Knowledge Director is degraded while using the placeholder bridge and ready
when supplied with a live search callable.

### System

- `system_assessment`
- `platform_analysis`

The System Director remains assessment-only and degraded.

## Next phase

Phase II-B will connect the existing Knowledge Director through a concrete
adapter and add a health probe that updates readiness automatically.
