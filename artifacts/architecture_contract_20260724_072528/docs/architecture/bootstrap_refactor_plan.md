Current State

launcher.py
        │
        ▼
BootstrapRunner
        │
        ├── Lifecycle execution
        └── API startup

runner.py
        │
        ▼
Preflight validation

Future State

BootstrapOrchestrator
        │
        ├── PreflightRunner
        ├── LifecycleRunner
        └── API Launcher

Benefits

• One public bootstrap interface
• Clear separation of responsibilities
• Easier testing
• Cleaner Doctor integration
