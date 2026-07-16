# JARVIS Mission Control Screen Architecture

## 1. Canonical desktop layout

The primary desktop interface consists of four permanent regions:

1. Title and global status bar
2. Mission navigation
3. Main workspace
4. Collapsible SITREP drawer

```text
+------------------------------------------------------------------+
| JARVIS | Current Mission | System Health | Device | User         |
+-------------+----------------------------------------------------+
|             |                                                    |
| Mission     |                                                    |
| Knowledge   |                                                    |
| Research    |                Main Workspace                      |
| Development |                                                    |
| Security    |                                                    |
| Devices     |                                                    |
| Settings    |                                                    |
|             |                                                    |
+-------------+----------------------------------------------------+
| SITREP | Critical: 0 | Attention: 2 | Recent: 5 | Expand        |
+------------------------------------------------------------------+


---

# Mission Tools

Mission Tools extend Mission Control without permanently occupying the
Mission Workspace.

Mission Tools are hidden by default.

Mission Tools appear only when requested by:

• the operator,

• the Executive Director,

• keyboard shortcut,

• voice command,

• Command Bar,

• Mission recommendation.

Mission Tools preserve the calm, mission-oriented character of Mission
Control by remaining available without continuously consuming screen space.

Examples include:

• Operations Console

• Knowledge Inspector

• Evidence Viewer

• Log Viewer

• Performance Monitor

Closing a Mission Tool immediately returns focus to the Mission Workspace.

Mission Tools never redefine the Mission Workspace.

