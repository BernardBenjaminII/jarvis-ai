from .contracts import CapabilityDefinition, VerificationReference
from .enums import CapabilityLifecycle as L, HealthStatus as H, VisibilitySurface as V
from .registry import CapabilityRegistry

def build_genesis_iv_capability_registry():
    data=(
      CapabilityDefinition('observation','Observation Foundation','Canonical observation intake.','core.observation',L.IMPLEMENTED,H.UNKNOWN,output_contracts=('Observation',),visibility=(V.RUNTIME,)),
      CapabilityDefinition('situation','Situation Assessment','Constructs operational situation models.','core.cognition',L.IMPLEMENTED,H.UNKNOWN,dependencies=('observation',),visibility=(V.RUNTIME,)),
      CapabilityDefinition('hypothesis','Hypothesis Generation','Generates candidate explanations.','core.cognition',L.IMPLEMENTED,H.UNKNOWN,dependencies=('situation',),visibility=(V.RUNTIME,)),
      CapabilityDefinition('evidence','Evidence Correlation','Correlates and assesses evidence.','core.evidence',L.IMPLEMENTED,H.UNKNOWN,dependencies=('hypothesis',),visibility=(V.RUNTIME,)),
      CapabilityDefinition('reasoning','Executive Reasoning','Produces justified recommendations.','core.reasoning',L.IMPLEMENTED,H.UNKNOWN,dependencies=('evidence',),visibility=(V.RUNTIME,)),
      CapabilityDefinition('decision','Executive Decision Engine','Selects one admissible COA.','core.cognition.executive_decision',L.IMPLEMENTED,H.UNKNOWN,dependencies=('reasoning',),visibility=(V.RUNTIME,)),
      CapabilityDefinition('mission_compiler','Executive Mission Compiler','Compiles decisions into missions.','core.cognition.mission_compiler',L.IMPLEMENTED,H.UNKNOWN,dependencies=('decision',),output_contracts=('MissionPlan',),visibility=(V.RUNTIME,),verification=VerificationReference('dev/verify_genesis_4a8.sh','3cdd6539c6594bc81e4888c9b7dfa62640a3f490971464bf17391cc2a70b59a8')),
      CapabilityDefinition('execution_orchestrator','Executive Execution Orchestrator','Coordinates controlled mission execution.','core.cognition.execution_orchestrator',L.IMPLEMENTED,H.UNKNOWN,dependencies=('mission_compiler',),output_contracts=('MissionExecutionSnapshot','ExecutionObservation'),visibility=(V.RUNTIME,V.TELEMETRY),verification=VerificationReference('dev/verify_genesis_4a9.sh','2ba5dcc7dc3d486ae40bb7b1c65c9e9d73848bccc755910c542c9f21376e9eca')),
      CapabilityDefinition('knowledge_catalog','Knowledge Catalog','Projects knowledge availability.','core.knowledge',L.IMPLEMENTED,H.UNKNOWN,visibility=(V.RUNTIME,V.KNOWLEDGE)),
      CapabilityDefinition('acquisition','Knowledge Acquisition','Queues governed source acquisition.','core.acquisition',L.IMPLEMENTED,H.UNKNOWN,dependencies=('knowledge_catalog',),visibility=(V.RUNTIME,V.KNOWLEDGE)),
      CapabilityDefinition('executive_api','Executive API','Projects Executive state over HTTP.','core.src.routes',L.NOT_CONNECTED,H.UNKNOWN,dependencies=('observation','decision','mission_compiler','execution_orchestrator','knowledge_catalog'),visibility=(V.API,)),
      CapabilityDefinition('mission_control_ui','Mission Control UI','Commander-visible operational projections.','ui',L.NOT_CONNECTED,H.UNKNOWN,dependencies=('executive_api',),visibility=(V.UI,)),
    )
    return CapabilityRegistry(data)
