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

