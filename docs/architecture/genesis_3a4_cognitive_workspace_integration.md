# Genesis III-A4 — Cognitive Workspace Integration Engine

## Purpose

Genesis III-A4 establishes the Cognitive Workspace as the canonical integration substrate for inspectable reasoning state. It translates immutable integration requests into canonical hypotheses, evidence references, assumptions, and open questions, then persists the resulting workspace through the certified Genesis III-A2 repository boundary.

## Boundaries

A4 assembles and persists cognitive state. It does not perform inference, choose a winning hypothesis, issue recommendations, execute plans, call networks, or acquire knowledge.

## Flow

`WorkspaceIntegrationRequest -> WorkspaceIntegrationPipeline -> CognitiveWorkspaceService -> CognitiveWorkspaceRepository -> WorkspaceIntegrationResult`

The pipeline is deterministic with respect to identities and idempotent when the same request is applied to the same workspace. Existing Genesis III-A1 through A3 contracts remain canonical and unchanged.

## Transparency

Every result contains the complete immutable workspace and its snapshot, plus counters describing which objects were newly applied. This gives later Executive and UI layers a stable surface for displaying hypotheses, evidence, assumptions, unresolved questions, revision, and confidence.
