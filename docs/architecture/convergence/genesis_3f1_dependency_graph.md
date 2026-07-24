# Genesis III-F1 Dependency Graph

**Architecture fingerprint:** `fb9cb5790cfb3cec743f391e8c392dcf255093e26df42624cd250f838723a433`

## Certified direction

```text
core.cognition.workspace
        ↓
core.cognition.integration
        ↓
future executive consumers
```

## Internal import edges

- `core.cognition.workspace` → `core.cognition.workspace.core.cognition.workspace.catalog`
- `core.cognition.workspace` → `core.cognition.workspace.core.cognition.workspace.enums`
- `core.cognition.workspace` → `core.cognition.workspace.core.cognition.workspace.errors`
- `core.cognition.workspace` → `core.cognition.workspace.core.cognition.workspace.models`
- `core.cognition.workspace` → `core.cognition.workspace.core.cognition.workspace.repository`
- `core.cognition.workspace` → `core.cognition.workspace.core.cognition.workspace.service`
- `core.cognition.workspace.catalog` → `core.cognition.workspace.__future__`
- `core.cognition.workspace.catalog` → `core.cognition.workspace.core.cognition.workspace.enums`
- `core.cognition.workspace.catalog` → `core.cognition.workspace.core.cognition.workspace.models`
- `core.cognition.workspace.catalog` → `core.cognition.workspace.core.cognition.workspace.repository`
- `core.cognition.workspace.catalog` → `core.cognition.workspace.dataclasses`
- `core.cognition.workspace.catalog` → `core.cognition.workspace.datetime`
- `core.cognition.workspace.catalog` → `core.cognition.workspace.enum`
- `core.cognition.workspace.catalog` → `core.cognition.workspace.typing`
- `core.cognition.workspace.enums` → `core.cognition.workspace.__future__`
- `core.cognition.workspace.enums` → `core.cognition.workspace.enum`
- `core.cognition.workspace.models` → `core.cognition.workspace.__future__`
- `core.cognition.workspace.models` → `core.cognition.workspace.core.cognition.workspace.enums`
- `core.cognition.workspace.models` → `core.cognition.workspace.core.cognition.workspace.errors`
- `core.cognition.workspace.models` → `core.cognition.workspace.dataclasses`
- `core.cognition.workspace.models` → `core.cognition.workspace.datetime`
- `core.cognition.workspace.models` → `core.cognition.workspace.hashlib`
- `core.cognition.workspace.models` → `core.cognition.workspace.typing`
- `core.cognition.workspace.models` → `core.cognition.workspace.uuid`
- `core.cognition.workspace.repository` → `core.cognition.workspace.__future__`
- `core.cognition.workspace.repository` → `core.cognition.workspace.core.cognition.workspace.enums`
- `core.cognition.workspace.repository` → `core.cognition.workspace.core.cognition.workspace.errors`
- `core.cognition.workspace.repository` → `core.cognition.workspace.core.cognition.workspace.models`
- `core.cognition.workspace.repository` → `core.cognition.workspace.dataclasses`
- `core.cognition.workspace.repository` → `core.cognition.workspace.datetime`
- `core.cognition.workspace.repository` → `core.cognition.workspace.pathlib`
- `core.cognition.workspace.repository` → `core.cognition.workspace.typing`
- `core.cognition.workspace.service` → `core.cognition.workspace.__future__`
- `core.cognition.workspace.service` → `core.cognition.workspace.core.cognition.workspace.enums`
- `core.cognition.workspace.service` → `core.cognition.workspace.core.cognition.workspace.errors`
- `core.cognition.workspace.service` → `core.cognition.workspace.core.cognition.workspace.models`
- `core.cognition.workspace.service` → `core.cognition.workspace.dataclasses`
- `core.cognition.integration` → `core.cognition.integration.contracts`
- `core.cognition.integration` → `core.cognition.integration.director`
- `core.cognition.integration` → `core.cognition.integration.errors`
- `core.cognition.integration` → `core.cognition.integration.models`
- `core.cognition.integration` → `core.cognition.integration.pipeline`
- `core.cognition.integration` → `core.cognition.integration.service`
- `core.cognition.integration.contracts` → `core.cognition.integration.__future__`
- `core.cognition.integration.contracts` → `core.cognition.integration.dataclasses`
- `core.cognition.integration.contracts` → `core.cognition.integration.hashlib`
- `core.cognition.integration.director` → `core.cognition.integration.__future__`
- `core.cognition.integration.director` → `core.cognition.integration.core.cognition.integration.contracts`
- `core.cognition.integration.director` → `core.cognition.integration.core.cognition.integration.models`
- `core.cognition.integration.director` → `core.cognition.integration.core.cognition.integration.service`
- `core.cognition.integration.models` → `core.cognition.integration.__future__`
- `core.cognition.integration.models` → `core.cognition.integration.core.cognition.workspace`
- `core.cognition.integration.models` → `core.cognition.integration.dataclasses`
- `core.cognition.integration.pipeline` → `core.cognition.integration.__future__`
- `core.cognition.integration.pipeline` → `core.cognition.integration.core.cognition.integration.contracts`
- `core.cognition.integration.pipeline` → `core.cognition.integration.core.cognition.integration.models`
- `core.cognition.integration.pipeline` → `core.cognition.integration.core.cognition.workspace`
- `core.cognition.integration.service` → `core.cognition.integration.__future__`
- `core.cognition.integration.service` → `core.cognition.integration.core.cognition.integration.contracts`
- `core.cognition.integration.service` → `core.cognition.integration.core.cognition.integration.models`
- `core.cognition.integration.service` → `core.cognition.integration.core.cognition.integration.pipeline`
- `core.cognition.integration.service` → `core.cognition.integration.core.cognition.workspace`
- `core.cognition.integration.service` → `core.cognition.integration.dataclasses`

**Forbidden dependency violations:** 0
