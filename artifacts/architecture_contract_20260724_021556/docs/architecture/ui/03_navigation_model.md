# JARVIS Mission Control Navigation Model

**Document ID:** UI-0003
**Status:** Draft
**Version:** 1.0
**Phase:** VIII-A2

---

# 1. Purpose

This document defines the canonical navigation architecture for the JARVIS
Mission Control interface.

Navigation exists to support missions—not conversations.

Users should always know:

- where they are,
- what mission is active,
- what JARVIS is doing,
- what requires attention,
- what action comes next.

---

# 2. Design Principles

Mission-first navigation.

Capability-oriented workspaces.

Stable navigation.

Progressive disclosure.

Predictable locations.

Minimal cognitive load.

Navigation shall never become a list of individual features.

---

# 3. Primary Navigation

The permanent navigation hierarchy is:

1. Mission
2. Knowledge
3. Research
4. Development
5. Security
6. Devices
7. Settings

These represent operational domains.

New top-level navigation entries require an Architecture Decision Record.

---

# 4. Mission

Mission is the primary workspace.

Mission contains:

- Mission Control
- Mission Console
- Mission Timeline
- Mission Journal
- Tasks
- Approvals
- Recommendations

Mission Control is the default destination after startup.

The Mission Console is a tool inside Mission.

It is not the application itself.

---

# 5. Knowledge

Knowledge represents every knowledge-related capability.

Examples include:

- Search
- Registry
- Sources
- Acquisition
- Admission
- Extraction
- Assimilation
- Chunking
- Embeddings
- Integrity
- Ontology
- Coverage
- Knowledge Gaps

The default Knowledge view is Overview.

---

# 6. Research

Research is responsible for discovering new knowledge.

Secondary views may include:

- Active Research
- Research Queue
- Candidate Sources
- Verification
- Completed Research
- Journals

Research distinguishes discovery from verified knowledge.

---

# 7. Development

Development summarizes engineering activity.

Examples:

- Repository
- Branches
- Verification
- Tests
- Builds
- Architecture
- Releases

Development coordinates engineering work.

It does not replace IDEs.

---

# 8. Security

Security contains authorized security operations.

Potential areas:

- Security Posture
- Reconnaissance
- Device Inventory
- Findings
- Policies
- Audits

Unavailable capabilities must never appear operational.

---

# 9. Devices

Devices represents every body JARVIS occupies.

Examples:

- Desktop
- Laptop
- Raspberry Pi
- Mobile
- Meta Quest

The workspace summarizes:

- Health
- Synchronization
- Runtime
- Connectivity
- Available Sensors

---

# 10. Settings

Settings are grouped by operational domain.

Examples:

- Identity
- Security
- Models
- Knowledge
- Missions
- Devices
- Integrations
- Accessibility

---

# 11. Mission Continuity

Changing workspaces does not terminate the current mission.

The active mission remains visible regardless of workspace.

The user can always return to Mission Control in one action.

---

# 12. SITREP

The Situation Report remains available from every workspace.

The collapsed drawer displays:

- Critical items
- Attention items
- Recent operational updates

Expanding the drawer reveals additional operational detail.

The SITREP never becomes the primary workspace.

---

# 13. Commander Brief

The Commander Brief is available:

- at startup,
- from Mission Control,
- from the Mission Journal.

Every recommendation links directly to the relevant operational workspace.

---

# 14. Keyboard Navigation

The desktop interface should support keyboard-first operation.

Recommended shortcuts:

Ctrl+K
Open Command Palette

Ctrl+`
Mission Console

Ctrl+Shift+B
Commander Brief

Ctrl+Shift+S
Situation Report

Alt+1
Mission

Alt+2
Knowledge

Alt+3
Research

Alt+4
Development

Alt+5
Security

Alt+6
Devices

Alt+7
Settings

---

# 15. Device Adaptation

Navigation semantics remain identical across:

- Desktop
- Laptop
- Tablet
- Mobile
- Raspberry Pi
- Meta Quest

Presentation changes.

Meaning does not.

---

# 16. Navigation Ownership

Backend owns:

- Mission State
- Health State
- Capability State
- Authorization
- Operational Truth

Frontend owns:

- Selected Workspace
- Expanded Panels
- Window Layout
- Local Filters

The frontend must never redefine backend operational state.

---

# 17. Acceptance Criteria

The navigation model is considered complete when:

✓ Mission is always identifiable.

✓ Mission Control is one action away.

✓ Conversation remains inside Mission.

✓ Workspaces remain stable.

✓ Navigation scales to future Directors.

✓ Navigation adapts to every supported device.

✓ The interface reduces cognitive load.

✓ Mission remains the organizing principle of JARVIS.

---

# 18. Architectural Summary

Mission Control navigation is organized around operational capability rather
than individual tools.

The navigation model supports long-term continuity, multiple execution
platforms, and future expansion while preserving a consistent user experience.

This document is the canonical navigation specification for the Mission
Control interface.
