from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from core.bootstrap.discovery.platform import detect_platform_details

from core.bounty_agent import BountyAgent

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
    try:
        return {"session_id": _agent().create(request.authorization_id, request.root_target, budget=request.budget)}
    except Exception as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/sessions/{session_id}/run")
def run_session(session_id: str):
    try:
        return _agent().run_recon(session_id)
    except Exception as exc:
        raise HTTPException(409, str(exc)) from exc


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
