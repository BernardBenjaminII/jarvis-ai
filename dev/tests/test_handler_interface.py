from knowledge_engine.assimilation.handlers import (
    SingleDocumentHandler,
    SourceCollectionHandler,
)
from knowledge_engine.assimilation.runner import (
    AssimilationRunner,
)
from knowledge_engine.storage.database import (
    KnowledgeDatabase,
)

db = KnowledgeDatabase(":memory:")

runner = AssimilationRunner(db)

document = SingleDocumentHandler(runner)

collection = SourceCollectionHandler(db)

for handler in (
    document,
    collection,
):

    assert callable(handler.plan)
    assert callable(handler.verify)
    assert callable(handler.execute)
    assert callable(handler.recover)
    assert callable(handler.report)

print("[PASS] Canonical handler lifecycle")
