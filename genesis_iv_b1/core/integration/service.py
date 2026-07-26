from pathlib import Path
from .audit import RepositoryIntegrationAuditor
from .catalog import build_genesis_iv_capability_registry
from .knowledge import build_knowledge_readiness
from .projections import build_mission_control_projection
class ExecutiveIntegrationService:
    def __init__(self, repository_root: Path): self._root=repository_root.resolve(); self._registry=build_genesis_iv_capability_registry(); self._auditor=RepositoryIntegrationAuditor()
    def integration_health(self): return self._auditor.audit(self._root,self._registry)
    def knowledge_readiness(self,query,**kwargs): return build_knowledge_readiness(query=query,**kwargs)
    def mission_control(self,**kwargs): return build_mission_control_projection(self.integration_health(),**kwargs)
