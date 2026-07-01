from pathlib import Path

from knowledge_engine.storage.database import KnowledgeDatabase
from knowledge_engine.storage.catalog_store import CatalogStore
from knowledge_engine.storage.inspection_store import InspectionStore
from knowledge_engine.storage.structure_store import StructureStore

from knowledge_engine.processing.catalog_stage import CatalogStage
from knowledge_engine.processing.inspect_stage import InspectStage
from knowledge_engine.processing.structure_stage import StructureStage


class ProcessingEngine:
    """
    Runs the staged document processing pipeline.

    Current stages:
    1. Catalog files
    2. Inspect supported formats
    3. Extract document structure

    Future stages:
    4. Extract text
    5. Chunk text
    6. Extract concepts
    7. Build retrieval indexes
    """

    def __init__(self, db_path: Path):
        self.db = KnowledgeDatabase(db_path)
        self.db.initialize()

        self.catalog_store = CatalogStore(self.db)
        self.inspection_store = InspectionStore(self.db)
        self.structure_store = StructureStore(self.db)

    def run_foundation(self, root: Path) -> dict:
        root = root.expanduser().resolve()

        catalog_result = CatalogStage(self.catalog_store).run(root)
        paths = catalog_result["paths"]

        inspection_result = InspectStage(self.inspection_store).run(paths)
        structure_result = StructureStage(self.structure_store).run(paths)

        summary = self.catalog_store.summary()

        return {
            **summary,
            **catalog_result,
            **inspection_result,
            **structure_result,
        }
