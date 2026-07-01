# ADR-0006: Bootstrap Architecture

**Status:** Accepted

**Date:** 2026-07-01

---

# Context

As JARVIS has evolved from a simple FastAPI application into a portable, multi-platform AI system, the startup process has accumulated significant responsibilities.

The launcher is currently responsible for:

- Detecting the operating system
- Locating the JARVIS runtime
- Selecting the appropriate virtual environment
- Creating the virtual environment if necessary
- Installing Python dependencies
- Verifying runtime storage
- Configuring environment variables
- Starting Ollama
- Verifying installed models
- Detecting system capabilities
- Launching the FastAPI server

This has resulted in a launcher that mixes platform discovery, dependency management, verification, and application startup into a single module.

As additional startup responsibilities are introduced—including knowledge initialization, plugin discovery, database migrations, and service verification—the launcher would become increasingly difficult to maintain.

---

# Decision

Introduce a dedicated Bootstrap subsystem.

The launcher becomes a thin entry point whose only responsibility is to invoke the bootstrap process.
