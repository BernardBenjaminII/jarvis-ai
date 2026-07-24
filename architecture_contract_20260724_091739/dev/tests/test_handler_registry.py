from knowledge_engine.assimilation.handler_registry import HandlerRegistry
from knowledge_engine.assimilation.registry_builder import (
    build_handler_registry,
)
from knowledge_engine.assimilation.runner import AssimilationRunner
from knowledge_engine.storage.database import KnowledgeDatabase

db = KnowledgeDatabase(":memory:")

runner = AssimilationRunner(db)

registry = build_handler_registry(runner)

assert isinstance(registry, HandlerRegistry)

# ------------------------------------------------------------------
# Registry contents
# ------------------------------------------------------------------

assert registry.supports("single_document")
assert registry.supports("source_collection")

document = registry.get("single_document")
collection = registry.get("source_collection")

assert document.object_type == "single_document"
assert collection.object_type == "source_collection"

assert registry.object_types() == [
    "single_document",
    "source_collection",
]

print("[PASS] Registry construction")
print("[PASS] Document handler registration")
print("[PASS] Source collection registration")
print("[PASS] Registry object-type enumeration")
