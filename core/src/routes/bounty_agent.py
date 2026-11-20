from __future__ import annotations

import hmac
import os
from fastapi import APIRouter, HTTPException, Query, Depends, Header
from fastapi.responses import Response
from core.bounty_agent.report_export import export_json, export_markdown
from pydantic import BaseModel, Field
from core.bootstrap.discovery.platform import detect_platform_details

from core.bounty_agent import BountyAgent
from core.bounty_agent.operations_status import build_operations_status

router = APIRouter(prefix="/api/bounty-agent", tags=["Bounty Agent"])


class CreateRequest(BaseModel):
    authorization_id: str = Field(min_length=1, max_length=200)
    root_target: str = Field(min_length=1, max_length=253)
    budget: int = Field(default=100, ge=1, le=1000)


class DecisionRequest(BaseModel):
    decision: str
    reviewer: str = Field(min_length=1, max_length=200)


class CapabilityPolicyReviewRequest(BaseModel):
    reviewer: str = Field(
        min_length=1,
        max_length=200,
    )
    decision: str
    policy_source: str = Field(
        min_length=1,
        max_length=1000,
    )
    policy_evidence: str = Field(
        min_length=1,
        max_length=10000,
    )
    constraints: list[str] = []


class ValidationAuthorizationProposalRequest(BaseModel):
    reviewer: str = Field(
        min_length=1,
        max_length=200,
    )
    request_budget: int = Field(
        default=10,
        ge=1,
        le=25,
    )
    ttl: int = Field(
        default=1800,
        ge=60,
        le=3600,
    )


class HypothesisDecisionRequest(BaseModel):
    decision: str
    reviewer: str = Field(
        min_length=1,
        max_length=200,
    )


class EvidenceReviewRequest(BaseModel):
    reviewer: str = Field(
        min_length=1,
        max_length=200,
    )


class ActionProposalRequest(BaseModel):
    reviewer: str = Field(
        min_length=1,
        max_length=200,
    )


class ActionDecisionRequest(BaseModel):
    decision: str
    reviewer: str = Field(
        min_length=1,
        max_length=200,
    )


def _agent():
    return BountyAgent()


@router.get("/sessions")
def sessions(limit: int = Query(50, ge=1, le=200)):
    return {"sessions": _agent().list_sessions(limit)}


@router.post("/sessions")
def create_session(request: CreateRequest):
    raise HTTPException(
        status_code=403,
        detail=(
            "Direct session creation disabled: "
            "durable human approval and coordinated "
            "mission creation are required"
        ),
    )


@router.post("/sessions/{session_id}/run")
def run_session(session_id: str):
    raise HTTPException(
        status_code=403,
        detail=(
            "Recon execution disabled pending "
            "execution-time authorization enforcement"
        ),
    )



@router.get("/sessions/{session_id}/operations-status")
def session_operations_status(session_id: str):
    try:
        return build_operations_status(
            _agent(),
            session_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail="Operations status unavailable",
        ) from exc


@router.get("/sessions/{session_id}")
def report_session(session_id: str):
    try:
        return _agent().report(session_id)
    except Exception as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/options/{option_id}/decision")
def decide_option(option_id: str, request: DecisionRequest):
    try:
        return _agent().decide(option_id, request.decision, request.reviewer)
    except Exception as exc:
        raise HTTPException(409, str(exc)) from exc

@router.post(
    "/investigation-plans/{plan_id}"
    "/actions/{action_id}"
    "/hypotheses/{hypothesis_id}"
    "/capability-policy-review"
)
def review_hypothesis_capability_policy(
    plan_id: str,
    action_id: str,
    hypothesis_id: str,
    request: CapabilityPolicyReviewRequest,
):
    try:
        return _agent().review_validation_capability_policy(
            plan_id,
            action_id,
            hypothesis_id,
            request.reviewer,
            decision=request.decision,
            policy_source=request.policy_source,
            policy_evidence=request.policy_evidence,
            constraints=request.constraints,
        )
    except Exception as exc:
        raise HTTPException(
            409,
            str(exc),
        ) from exc


@router.post(
    "/investigation-plans/{plan_id}"
    "/actions/{action_id}"
    "/hypotheses/{hypothesis_id}"
    "/validation-authorization-proposal"
)
def propose_hypothesis_validation_authorization(
    plan_id: str,
    action_id: str,
    hypothesis_id: str,
    request: ValidationAuthorizationProposalRequest,
):
    try:
        return _agent().propose_validation_authorization(
            plan_id,
            action_id,
            hypothesis_id,
            request.reviewer,
            request_budget=request.request_budget,
            ttl=request.ttl,
        )
    except Exception as exc:
        raise HTTPException(
            409,
            str(exc),
        ) from exc


@router.post(
    "/investigation-plans/{plan_id}"
    "/actions/{action_id}"
    "/hypotheses/{hypothesis_id}/decision"
)
def decide_investigation_hypothesis(
    plan_id: str,
    action_id: str,
    hypothesis_id: str,
    request: HypothesisDecisionRequest,
):
    try:
        return _agent().decide_evidence_hypothesis(
            plan_id,
            action_id,
            hypothesis_id,
            request.decision,
            request.reviewer,
        )
    except Exception as exc:
        raise HTTPException(
            409,
            str(exc),
        ) from exc


@router.post(
    "/investigation-plans/{plan_id}"
    "/actions/{action_id}/evidence-review"
)
def review_investigation_action_evidence(
    plan_id: str,
    action_id: str,
    request: EvidenceReviewRequest,
):
    try:
        return _agent().review_plan_action_evidence(
            plan_id,
            action_id,
            request.reviewer,
        )
    except Exception as exc:
        raise HTTPException(
            409,
            str(exc),
        ) from exc


@router.post(
    "/investigation-plans/{plan_id}"
    "/actions/{action_id}/proposal"
)
def propose_investigation_action(
    plan_id: str,
    action_id: str,
    request: ActionProposalRequest,
):
    try:
        return _agent().propose_plan_action(
            plan_id,
            action_id,
            request.reviewer,
        )
    except Exception as exc:
        raise HTTPException(
            409,
            str(exc),
        ) from exc


@router.post(
    "/investigation-plans/{plan_id}"
    "/actions/{action_id}/decision"
)
def decide_investigation_action(
    plan_id: str,
    action_id: str,
    request: ActionDecisionRequest,
):
    try:
        return _agent().decide_plan_action(
            plan_id,
            action_id,
            request.decision,
            request.reviewer,
        )
    except Exception as exc:
        raise HTTPException(
            409,
            str(exc),
        ) from exc



def require_bounty_export_access(
    export_token: str | None = Header(
        default=None,
        alias="X-JARVIS-Export-Token",
    ),
):
    """Fail-closed authentication for investigation exports."""
    expected = os.environ.get(
        "JARVIS_BOUNTY_EXPORT_TOKEN", ""
    )

    if len(expected) < 32:
        raise HTTPException(
            503, "Report export is not configured"
        )

    if not export_token or not hmac.compare_digest(
        export_token, expected
    ):
        raise HTTPException(
            401, "Report export authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/sessions/{session_id}/export/json", dependencies=[Depends(require_bounty_export_access)])
def export_session_json(session_id: str):
    try:
        report = _agent().report(session_id)
        content = export_json(report)
    except Exception as exc:
        raise HTTPException(404, "Report unavailable") from exc

    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition":
                'attachment; filename="jarvis-bounty-report.json"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/sessions/{session_id}/export/markdown", dependencies=[Depends(require_bounty_export_access)])
def export_session_markdown(session_id: str):
    try:
        report = _agent().report(session_id)
        content = export_markdown(report)
    except Exception as exc:
        raise HTTPException(404, "Report unavailable") from exc

    return Response(
        content=content,
        media_type="text/markdown",
        headers={
            "Content-Disposition":
                'attachment; filename="jarvis-bounty-report.md"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/platform")
def bounty_agent_platform() -> dict:
    details = detect_platform_details()
    environment = str(details.get("environment") or "unknown").lower()
    return {
        "environment": environment,
        "pretty_name": details.get("pretty_name") or details.get("name") or environment,
        "version": details.get("version") or details.get("version_id"),
        "live_bounty_enabled": environment == "kali",
        "workspace": "kali-security" if environment == "kali" else "shared-review",
    }


# JARVIS_R920B_WORKSTATION_ADVISORY
@router.get("/workstation-advisory")
def get_workstation_advisory():
    """Return advisory tool mappings; never execute tools."""

    from core.bootstrap.discovery.platform import detect_platform
    from core.bounty_agent.autonomy.workstation_advisory_r920a import (
        workstation_advisory,
    )

    if detect_platform() != "kali":
        raise HTTPException(
            status_code=404,
            detail="Kali workstation advisory unavailable",
        )

    result = workstation_advisory()

    if (
        result.get("execution_authorized") is not False
        or result.get("submission_authorized") is not False
        or result.get("mode") != "advisory_only"
        or any(
            entry.get("execution_allowed") is not False
            or entry.get("human_review_required") is not True
            for entry in result.get("activities", {}).values()
        )
        or any(
            entry.get("execution_allowed") is not False
            for entry in result.get(
                "legacy_lab_experiments", {}
            ).values()
        )
    ):
        raise HTTPException(
            status_code=500,
            detail="Invalid workstation advisory safety flags",
        )

    return result


# JARVIS_R920E_SESSION_ADVISORY
@router.get("/sessions/{session_id}/mission-advisory")
def get_session_mission_advisory(session_id: str):
    """Inspect an existing session; no execution or mutation."""

    from core.bootstrap.discovery.platform import detect_platform
    from core.bounty_agent.autonomy.session_advisory_r920e import (
        SessionAdvisoryError,
        build_session_advisory,
    )
    from core.bounty_agent.autonomy.recon_planner import (
        ReconPlanningError,
    )
    from core.bounty_authorization import AuthorizationDenied

    if detect_platform() != "kali":
        raise HTTPException(status_code=404)

    try:
        result = build_session_advisory(
            _agent(),
            session_id,
        )
    except SessionAdvisoryError as exc:
        raise HTTPException(
            status_code=404,
            detail="Session advisory unavailable",
        ) from exc
    except (ReconPlanningError, AuthorizationDenied, ValueError) as exc:
        raise HTTPException(
            status_code=409,
            detail="Mission is not eligible for advisory planning",
        ) from exc

    if (
        result.get("execution_authorized") is not False
        or result.get("automatic_execution_allowed") is not False
        or result.get("execution_started") is not False
        or result.get("submission_authorized") is not False
        or result.get("human_review_required") is not True
    ):
        raise HTTPException(
            status_code=500,
            detail="Invalid advisory safety contract",
        )

    return result


# JARVIS_R921D2_SCOPE_API
# Inherits authentication from the parent Bounty router in main.py.
# Contains no execution, reviewer-approval, or session routes.
from core.src.routes.program_scopes_r921d import (
    router as program_scopes_router,
)

router.include_router(program_scopes_router)

# JARVIS_R922D1_OPPORTUNITY_INTELLIGENCE
from core.src.routes.bounty_opportunities_r922d1 import (
    router as opportunity_router_r922d1,
)
router.include_router(opportunity_router_r922d1)
