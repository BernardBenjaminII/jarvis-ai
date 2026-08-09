from __future__ import annotations
from typing import Any
from core.knowledge_catalog.qualified_search import get_last_qualification_result
from .contracts import GroundedAnswerExecutionRequest, GroundedAnswerRuntimeContext
from .service import GroundedAnswerRuntimeService
from .telemetry import publish_grounded_answer_telemetry

def ensure_grounded_answer_service(orchestrator: Any):
    service=getattr(orchestrator,"grounded_answer_service",None)
    if isinstance(service,GroundedAnswerRuntimeService): return service
    service=GroundedAnswerRuntimeService.create_default()
    setattr(orchestrator,"grounded_answer_service",service)
    return service

def build_runtime_request(context: Any, qualification: Any):
    metadata=dict(getattr(context,"metadata",{}) or {})
    return GroundedAnswerExecutionRequest(
        context=GroundedAnswerRuntimeContext(
            request_id=str(metadata.get("request_id") or metadata.get("correlation_id") or "executive-request"),
            session_id=str(metadata.get("session_id") or getattr(context,"session_id","") or "executive-session"),
            operator_input=str(getattr(context,"operator_input","") or ""),
            mode=str(getattr(context,"mode","full") or "full"),
            channel=str(getattr(context,"channel","text") or "text"),
            metadata=metadata),
        qualification=qualification)

def augment_synthesis_input(orchestrator: Any, context: Any, synthesis_input: str) -> str:
    qualification=get_last_qualification_result()
    if qualification is None: return synthesis_input
    service=ensure_grounded_answer_service(orchestrator)
    request=build_runtime_request(context,qualification)
    response=service.plan(request)
    setattr(orchestrator,"_last_grounded_answer_plan",response.plan)
    setattr(orchestrator,"_last_grounded_answer_response",response)
    telemetry=publish_grounded_answer_telemetry(runtime_request=request,qualification=qualification,response=response)
    setattr(orchestrator,"_last_grounded_answer_telemetry",telemetry)
    contract=response.plan.synthesis_prompt.strip()
    if not contract or "JARVIS GROUNDED ANSWER CONTRACT:" in synthesis_input:
        return synthesis_input
    return synthesis_input.rstrip()+"\n\n"+contract+"\n"

def get_last_grounded_answer_plan(orchestrator): return getattr(orchestrator,"_last_grounded_answer_plan",None)
def get_last_grounded_answer_response(orchestrator): return getattr(orchestrator,"_last_grounded_answer_response",None)
def get_last_grounded_answer_telemetry(orchestrator): return getattr(orchestrator,"_last_grounded_answer_telemetry",None)
