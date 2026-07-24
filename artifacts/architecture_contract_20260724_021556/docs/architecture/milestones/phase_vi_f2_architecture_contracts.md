# JARVIS Gen 2 Phase VI-F2

## Architecture Contracts and Repository Layer

### Status

Complete after focused and master verification pass.

### Purpose

Phase VI-F2 makes the Assimilation Core architecture executable and
self-enforcing.

The phase protects:

- dependency direction
- service isolation
- handler boundaries
- Director boundaries
- Runner delegation
- SQL ownership
- public service APIs
- repository APIs
- immutable result models

### Architectural correction

Architecture contracts detected that SourceCollectionHandler directly queried
knowledge_registry.

The SQL was moved into:

```text
KnowledgeRegistryRepository
