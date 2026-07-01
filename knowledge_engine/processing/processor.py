from pathlib import Path

from knowledge_engine.storage.database import KnowledgeDatabase
from knowledge_engine.storage.catalog_store import CatalogStore
from knowledge_engine.storage.inspection_store import InspectionStore
from knowledge_engine.storage.structure_store import StructureStore

from knowledge_engine.processing.catalog_stage import CatalogStage
from knowledge_engine.processing.inspect_stage import InspectStage
from knowledge_engine.processing.structure_stage import StructureStage

from knowledge_engine.index import KnowledgeIndexBuilder
from knowledge_engine.index import KnowledgeIndexStore


class ProcessingEngine:
    def __init__(self, db_path: Path):
        self.db = KnowledgeDatabase(db_path)
        self.db.initialize()

        self.catalog_store = CatalogStore(self.db)
        self.inspection_store = InspectionStore(self.db)
        self.structure_store = StructureStore(self.db)
        self.index_store = KnowledgeIndexStore(self.db)

    def run_foundation(self, root: Path) -> dict:
        root = root.expanduser().resolve()

        catalog_result = CatalogStage(self.catalog_store).run(root)
        paths = catalog_result["paths"]

        inspection_result = InspectStage(self.inspection_store).run(paths)
        structure_result = StructureStage(self.structure_store).run(paths)

        index_result = KnowledgeIndexBuilder(
            self.db,
            self.index_store,
        ).build()

        summary = self.catalog_store.summary()

        return {
            **summary,
            **catalog_result,
            **inspection_result,
            **structure_result,
            **index_result,
            **self.index_store.summary(),
        }
