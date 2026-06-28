# JARVIS Storage Architecture

**Status:** Draft  
**Version:** 0.1  
**Purpose:** Define how JARVIS separates repository code, runtime state, structured data, unstructured data, indexes, caches, and generated artifacts.

---

## 1. Core Principle

Repository contains behavior.

Runtime contains state.

The repository should contain:

- source code
- configuration templates
- architecture documents
- tests
- static defaults

The runtime should contain:

- logs
- memory
- knowledge assets
- indexes
- embeddings
- SQLite databases
- caches
- generated files

---

## 2. Runtime Root

Example Linux runtime path:

```text
/media/abdullah/JARVIS_RUNTIME_L/
