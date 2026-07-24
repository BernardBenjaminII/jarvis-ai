# JARVIS Gen 2 Phase VII-B1

## Deterministic Source Admission

This document describes the architecture for the Phase VII-B1
acquisition-control layer.

### Purpose

The acquisition-control package sits in front of the frozen acquisition
package and performs deterministic source admission.

### Responsibilities

-   Validate source proposals
-   Normalize HTTPS URLs and local paths
-   Produce deterministic fingerprints
-   Apply immutable admission policy
-   Return Accepted / Review Required / Rejected decisions

### Non-responsibilities

-   No networking
-   No crawling
-   No downloading
-   No catalog writes
-   No mission creation

### Dependency Direction

future orchestration → acquisition_control

The frozen `knowledge_engine.acquisition` package must not depend on
`knowledge_engine.acquisition_control`.

### Completion Criteria

-   Immutable contracts
-   Deterministic normalization
-   Deterministic fingerprints
-   Policy enforcement
-   No side effects
-   VII-A8 regression remains green
