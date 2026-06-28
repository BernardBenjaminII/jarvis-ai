# JARVIS Design Principles

** Knowledge is permanent. Intelligence is upgradable **

Version: 1.0
Status: Living Document

---

# Purpose

This document defines the engineering principles that govern every subsystem in JARVIS.

These principles take precedence over implementation convenience.

---

# Principle 1

Repository contains behavior.

Runtime contains state.

Repository:

- source code
- configuration templates
- documentation
- tests
- interfaces

Runtime:

- logs
- memory
- knowledge
- databases
- indexes
- embeddings
- caches
- generated artifacts

---

# Principle 2

Interfaces before implementations.

Every subsystem begins with an interface.

Examples:

- KnowledgeProvider
- KnowledgeService
- MemoryService
- RuntimeManager

Implementation details remain hidden.

---

# Principle 3

Data is permanent.

Models are replaceable.

JARVIS should never become dependent on:

- a specific LLM
- a specific embedding model
- a specific vector database
- a specific framework

Knowledge must survive technology changes.

---

# Principle 4

Every subsystem owns one responsibility.

Examples:

Runtime Engine
    discovers runtime

Knowledge Engine
    manages knowledge

Memory Engine
    manages memory

Tool Engine
    executes tools

Model Engine
    routes AI models

Launcher
    starts the system

---

# Principle 5

Cross-platform is a first-class requirement.

Linux

Windows

macOS

Future operating systems should require minimal changes.

---

# Principle 6

Offline-first whenever practical.

Cloud services are enhancements.

Local functionality is the baseline.

---

# Principle 7

Configuration over hardcoding.

Paths

Models

Collections

Providers

Capabilities

should all be configurable.

---

# Principle 8

Everything is modular.

Subsystems communicate through interfaces.

Subsystems should not directly manipulate each other's internal state.

---

# Principle 9

Knowledge is provider-based.

Every knowledge source is represented by a provider.

Providers produce KnowledgeAssets.

---

# Principle 10

Architecture before implementation.

Every major subsystem should have:

Architecture

Design

Implementation

Testing

Documentation

in that order.

---

# Principle 11

Code should explain how.

Architecture explains why.

The why belongs in documentation.

The how belongs in source code.

---

# Principle 12

Future Abdullah is a first-class user.

Every architectural decision should optimize maintainability for future development.
