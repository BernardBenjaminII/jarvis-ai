from knowledge.structure import StructureRegistry


class StructureStage:
    def __init__(self, structure_store):
        self.registry = StructureRegistry()
        self.structure_store = structure_store

    def run(self, paths: list) -> dict:
        structured = 0
        errors = []

        for path in paths:
            extractor = self.registry.get(path)

            if extractor is None:
                continue

            try:
                nodes = extractor.extract(path)

                if nodes:
                    self.structure_store.replace(
                        document_path=str(path.resolve()),
                        nodes=nodes,
                    )
                    structured += 1

            except Exception as exc:
                errors.append((str(path), str(exc)))

        return {
            "structured": structured,
            "structure_errors": errors,
            "structure_summary": self.structure_store.summary(),
        }
