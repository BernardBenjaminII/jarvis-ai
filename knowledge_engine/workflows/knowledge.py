from knowledge_engine.workflow.registry import WorkflowRegistry

from knowledge_engine.capabilities.receiving import ReceivingCapability
from knowledge_engine.capabilities.discovery import DiscoveryCapability
from knowledge_engine.capabilities.objects import ObjectCapability
from knowledge_engine.capabilities.registry import RegistryCapability
from knowledge_engine.capabilities.validation import ValidationCapability
from knowledge_engine.capabilities.inspection import InspectionCapability
from knowledge_engine.capabilities.librarian import LibrarianCapability
from knowledge_engine.capabilities.enrichment import EnrichmentCapability
from knowledge_engine.capabilities.chunking import ChunkingCapability
from knowledge_engine.capabilities.embeddings import EmbeddingCapability
from knowledge_engine.capabilities.faiss import FAISSCapability
from knowledge_engine.capabilities.graph import GraphCapability
from knowledge_engine.capabilities.doctor import DoctorCapability


def build():

    registry = WorkflowRegistry()

    registry.register(ReceivingCapability())

    registry.register(DiscoveryCapability())

    registry.register(ObjectCapability())

    registry.register(RegistryCapability())

    registry.register(ValidationCapability())

    registry.register(InspectionCapability())

    registry.register(LibrarianCapability())

    registry.register(EnrichmentCapability())

    registry.register(ChunkingCapability())

    registry.register(EmbeddingCapability())

    registry.register(FAISSCapability())

    registry.register(GraphCapability())

    registry.register(DoctorCapability())

    return registry
