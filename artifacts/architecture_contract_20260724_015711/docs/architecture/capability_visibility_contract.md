# Capability Visibility Contract

## Principle

The capability registry is the canonical source for what JARVIS can and cannot do.

## Required descriptor

```json
{
  "id": "filesystem.read",
  "name": "Read Files",
  "subsystem": "operations",
  "description": "Read authorized local files.",
  "status": "operational",
  "availability": "available",
  "health": "healthy",
  "operations": [
    {
      "name": "read",
      "method": "POST",
      "path": "/operations/capabilities/filesystem.read/commands",
      "destructive": false,
      "supports_dry_run": false
    }
  ],
  "inputs": {},
  "outputs": {},
  "permissions": ["operator"],
  "ui": {
    "section": "Operations",
    "group": "Filesystem",
    "visibility": "primary"
  },
  "provenance": {
    "provider": "core.capabilities.registry",
    "implementation": "module.symbol"
  },
  "degradation": null
}
```

## UI behavior

The UI must:

- show operational, degraded, unavailable, and not-configured capabilities;
- explain why a capability is unavailable;
- hide no capability merely because it is not currently usable;
- show the exact operation invoked;
- show dry-run support;
- show the latest execution result;
- link results to timeline and audit records.

## API behavior

```text
GET  /operations/capabilities
GET  /operations/capabilities/{capability_id}
POST /operations/capabilities/{capability_id}/commands
GET  /operations/commands/{command_id}
```

## Completion rule

A backend module is not a UI capability until a registry descriptor, projection, command path, test, and visible UI surface exist.
