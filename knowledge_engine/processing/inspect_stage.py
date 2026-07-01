import json

from knowledge_engine.inspectors import InspectorRegistry


class InspectStage:
    def __init__(self, inspection_store):
        self.registry = InspectorRegistry()
        self.inspection_store = inspection_store

    def run(self, paths: list) -> dict:
        inspected = 0
        unsupported = 0
        errors = []

        for path in paths:
            inspector = self.registry.get(path)

            if inspector is None:
                unsupported += 1
                continue

            try:
                metadata = inspector.inspect(path)

                self.inspection_store.upsert(
                    document_path=str(path.resolve()),
                    inspector=inspector.__class__.__name__,
                    status="INSPECTED",
                    metadata_json=json.dumps(metadata, default=str),
                )

                inspected += 1

            except Exception as exc:
                self.inspection_store.upsert(
                    document_path=str(path.resolve()),
                    inspector=inspector.__class__.__name__,
                    status="ERROR",
                    error=str(exc),
                )

                errors.append((str(path), str(exc)))

        return {
            "inspected": inspected,
            "unsupported": unsupported,
            "inspection_errors": errors,
        }
