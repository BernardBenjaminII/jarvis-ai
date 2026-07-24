# JARVIS Architecture Blueprint

**Status:** Active  
**Phase:** Stabilization Phase II-A — Architecture Governance  
**Purpose:** Define the canonical architecture, subsystem ownership, and development rules for the JARVIS platform.

---

# 1. Architecture Rule

Before adding a new directory, package, service, or major module, every developer must answer:

1. Which subsystem owns this responsibility?
2. Does an existing subsystem already own it?
3. Is this a new capability or an extension of an existing capability?

If ownership is unclear, do not create the component until ownership has been established.

---

# 2. Architectural Principles

- Every subsystem has a single owner.
- Every subsystem has one primary responsibility.
- Prefer extension over duplication.
- Development tools must not contain production runtime logic.
- Production code should not depend on development utilities.
- Interfaces should be stable; implementations may evolve.

---

# 3. Top-Level Platform Layout

```text
JARVIS
├── Bootstrap
├── Runtime
├── Core Services
├── Capability Framework
├── Knowledge Engine
├── Librarian
├── Development Tools
├── Verification
└── Future Agent Framework
```

---

# 4. Bootstrap

**Canonical package**

```text
core/bootstrap/
```

**Canonical entry point**

```text
core/bootstrap/main.py
```

**Responsibilities**

- Platform discovery
- Runtime discovery
- Lifecycle execution
- Preflight
- Startup
- Service initialization
- Postflight

**Does not own**

- Knowledge ingestion
- Search
- Embeddings
- AI reasoning

---

# 5. Runtime

**Canonical locations**

```text
core/bootstrap/discovery/
core/bootstrap/services/runtime.py
```

**Responsibilities**

- Runtime paths
- Mounted runtime validation
- Virtual environment location
- Runtime configuration
- Platform assumptions

---

# 6. Core Services

**Canonical package**

```text
core/bootstrap/services/
```

**Responsibilities**

- API startup
- Ollama startup
- Runtime services
- Capability services
- Virtual environment services

---

# 7. Capability Framework

**Canonical package**

```text
knowledge_engine/capabilities/
```

**Responsibilities**

- Capability registration
- Capability metadata
- Capability discovery
- Capability loading

Capability modules register functionality. They do not implement the functionality.

---

# 8. Knowledge Engine

**Canonical package**

```text
knowledge_engine/
```

**Knowledge Lifecycle**

```text
Receiving
    ↓
Discovery
    ↓
Inspection
    ↓
Extraction
    ↓
Processing
    ↓
Chunking
    ↓
Embeddings
    ↓
Objects
    ↓
Registry
    ↓
Knowledge Graph
    ↓
Retrieval
```

---

# 9. Receiving

**Canonical package**

```text
knowledge_engine/receiving/
```

**Responsibilities**

- Intake
- Filtering
- Sanitization
- Intake reports

---

# 10. Discovery

**Canonical package**

```text
knowledge_engine/discovery/
```

**Responsibilities**

- Filesystem discovery
- Resource discovery
- Scanning
- Discovery services

---

# 11. Inspection

**Canonical packages**

```text
knowledge_engine/inspectors/
knowledge_engine/resource_inspection/
```

**Responsibilities**

- File inspection
- Metadata extraction
- Type identification
- Resource classification

---

# 12. Extraction

**Canonical package**

```text
knowledge_engine/extraction/
```

**Responsibilities**

- Content extraction
- Extractor interfaces
- Format-specific extraction

---

# 13. Processing

**Canonical package**

```text
knowledge_engine/processing/
```

**Responsibilities**

- Pipeline stages
- Stage coordination
- Pipeline execution

---

# 14. Processors

**Canonical package**

```text
knowledge_engine/processors/
```

**Responsibilities**

- Resource-specific processing
- Processor interfaces
- Processor registry

---

# 15. Chunking

**Canonical package**

```text
knowledge_engine/chunking/
```

**Responsibilities**

- Chunk generation
- Chunk persistence
- Chunk strategies

---

# 16. Embeddings

**Canonical package**

```text
knowledge_engine/embeddings/
```

**Responsibilities**

- Embedding generation
- Embedding providers
- Embedding persistence

---

# 17. Objects

**Canonical package**

```text
knowledge_engine/objects/
```

**Responsibilities**

- Object construction
- Object services
- Canonical representation

---

# 18. Registry

**Canonical package**

```text
knowledge_engine/registry/
```

**Responsibilities**

- Registry services
- Registry persistence
- Knowledge registration

---

# 19. Knowledge Graph

**Canonical package**

```text
knowledge_engine/knowledge_graph/
```

**Responsibilities**

- Graph extraction
- Graph construction
- Graph persistence

---

# 20. Retrieval

**Canonical packages**

```text
knowledge_engine/retrieval/
knowledge_engine/search/
knowledge_engine/hybrid_retrieval/
```

**Responsibilities**

- Vector retrieval
- Metadata retrieval
- Hybrid retrieval
- Query interfaces

---

# 21. Workflow

**Canonical package**

```text
knowledge_engine/workflow/
```

**Responsibilities**

- Workflow execution
- Runner
- Stage contracts
- Reporting

---

# 22. Workflows

**Canonical package**

```text
knowledge_engine/workflows/
```

**Responsibilities**

- Named workflows
- Business workflows
- Reusable pipelines

---

# 23. Orchestrator

**Canonical package**

```text
knowledge_engine/orchestrator/
```

**Responsibilities**

- Pipeline composition
- Stage sequencing
- Execution planning

---

# 24. Director

**Canonical package**

```text
knowledge_engine/director/
```

**Responsibilities**

- High-level coordination
- Execution decisions
- Workflow supervision

---

# 25. Librarian

**Current location**

```text
dev/librarian/
```

**Responsibilities**

- Acquisition experiments
- Staged intake
- Inventory
- Library organization

---

# 26. Development Tools

**Canonical package**

```text
dev/
```

**Responsibilities**

- Audits
- Consolidation tools
- Doctor tools
- Developer utilities

---

# 27. Verification

**Canonical package**

```text
dev/verify/
```

**Responsibilities**

- Smoke tests
- Capability verification
- Integration verification

---

# 28. Backup Policy

Archive temporary backup artifacts instead of leaving them in active source directories.

Examples:

```text
*.bak
*.resource_v1.bak
*.resource_working.bak
*.pre_resource_refactor.bak
*.monolith.bak
```

Archive location:

```text
archive/phase_ii_a_backups/
```

---

# 29. Architectural Anti-Patterns

Avoid:

- Duplicate subsystem ownership
- Duplicate runners
- Duplicate pipelines
- Production code in development tools
- Circular subsystem dependencies
- Orphan packages

---

# 30. Phase II-A Completion Criteria

Phase II-A is complete when:

- Bootstrap architecture is canonical.
- Runtime ownership is documented.
- Knowledge Engine ownership is documented.
- Subsystem ownership is documented.
- Backup artifacts are archived.
- Verification passes.
- Future development follows this blueprint.
