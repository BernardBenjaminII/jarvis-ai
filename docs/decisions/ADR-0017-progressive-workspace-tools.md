# ADR-0017

# Progressive Workspace Tools

Status

Accepted

---

## Context

Mission Control contains capabilities used by operators, engineers,
researchers, and administrators.

Some capabilities are required continuously.

Others are specialized.

Making every capability permanently visible increases cognitive load and
reduces Mission focus.

---

## Decision

Mission Control adopts Progressive Workspace Tools.

Capabilities remain available at all times.

Capabilities are not permanently visible.

Specialized tools appear only when required.

Mission Workspace remains focused upon the active Mission.

---

## Examples

Mission Tools include:

• Operations Console

• Knowledge Inspector

• Evidence Viewer

• Log Viewer

• Performance Monitor

Future Mission Tools follow the same architectural model.

---

## Consequences

Advantages

• Reduced cognitive load

• Cleaner workspace

• Better Mission focus

• Cross-platform consistency

• Easier future expansion

Tradeoffs

• One additional action may be required to open specialized tools.

This tradeoff is accepted.

---

## Architectural Principle

Every capability is always available.

Not every capability is always visible.

