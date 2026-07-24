# Bootstrap Canonical Architecture

## Purpose

This document defines the canonical bootstrap sequence for JARVIS.

---

# Canonical Entry Point

The official bootstrap entry point is:

```text
core/bootstrap/main.py
```

Launch sequence:

```text
main.py
    ↓
BootstrapRunner.run()
    ↓
preflight
    ↓
startup
    ↓
postflight
```

---

# Bootstrap Runner

BootstrapRunner is responsible for executing lifecycle stages.

Responsibilities:

- execute preflight checks
- initialize runtime
- start services
- perform postflight tasks

---

# Lifecycle

Lifecycle stages reside in:

```text
core/bootstrap/lifecycle/
```

Current stages:

- preflight.py
- startup.py
- postflight.py

---

# Legacy Bootstrap

The following file represents the previous bootstrap architecture:

```text
core/bootstrap/bootstrap.py
```

It manually initializes bootstrap services such as:

- RuntimeBootstrap
- DependencyBootstrap
- CapabilityBootstrap
- ApiBootstrap
- ModelBootstrap
- OllamaBootstrap

This implementation is retained temporarily for compatibility but is no longer considered the canonical execution path.

Future work will migrate any remaining functionality into BootstrapRunner before retiring this file.

---

# Runtime Check

The runtime check module is a launcher wrapper.

```text
runtime_check.py
```

Its responsibility is to invoke the canonical bootstrap sequence.

---

# Goal

Future development should extend:

```text
main.py
BootstrapRunner
lifecycle/
```

rather than introducing additional bootstrap entry points.
