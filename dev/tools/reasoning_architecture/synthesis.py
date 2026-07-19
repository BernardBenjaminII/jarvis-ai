from __future__ import annotations

from typing import Any

from .constitution import extension_points, invariants
from .loader import fingerprint
from .models import Component

BASELINE_ID = "GENESIS-I-A4"
BASELINE_VERSION = "1.0.0"


def components() -> tuple[Component, ...]:
    return (
        Component("EvidenceItem", "Canonical Contracts", "Represent one immutable attributable item of evidence.", ("Evidence identity", "Proposition", "Stance", "Source reference", "Reliability", "Confidence", "Metadata"), ("Knowledge retrieval", "Hypothesis assessment", "Runtime mutation"), ("core/reasoning/models.py",), "Constitutionally stable", "Extend compatibly through structured provenance."),
        Component("Hypothesis", "Canonical Contracts", "Represent one immutable candidate explanation.", ("Identity", "Statement", "Evidence relationships", "Assumptions", "Proposed actions"), ("Confidence calculation", "Evidence retrieval", "Conclusion selection"), ("core/reasoning/models.py",), "Constitutionally stable", "Keep inference results separate from the hypothesis contract."),
        Component("ReasoningRequest", "Canonical Contracts", "Define the immutable deterministic input to one reasoning execution.", ("Request identity", "Goal", "Evidence", "Hypotheses", "Constraints", "Context"), ("Mutable session lifecycle", "Executive state", "Search execution"), ("core/reasoning/models.py",), "Constitutionally stable", "A future ReasoningSession may create requests but must not replace them."),
        Component("KnowledgeEvidenceAdapter", "Knowledge Boundary", "Normalize external knowledge results into canonical EvidenceItem objects.", ("Input normalization", "Identifier derivation", "Score normalization", "Rejected-result accounting", "Source metadata capture"), ("Knowledge retrieval", "Inference", "Executive governance"), ("core/reasoning/knowledge.py",), "Stable extension boundary", "Future provenance enrichment enters through this boundary."),
        Component("DeterministicHypothesisGenerator", "Hypothesis Generation", "Generate candidate hypotheses deterministically from goal and evidence.", ("Generation strategy", "Candidate construction", "Generation result"), ("Evidence retrieval", "Final assessment", "Executive authorization"), ("core/reasoning/generation.py",), "Stable replaceable strategy", "Alternative generators must preserve explicit outputs and traceability."),
        Component("ReasoningEngine", "Inference and Orchestration", "Validate requests, assess hypotheses, rank conclusions, identify gaps, and produce auditable results.", ("Validation", "Assessment orchestration", "Stable ranking", "Conclusion selection", "Contradiction detection", "Missing-information detection", "Trace construction", "Result fingerprinting"), ("Knowledge retrieval", "Tool execution", "Mission mutation", "Persistent session lifecycle"), ("core/reasoning/service.py", "core/reasoning/inference.py", "core/reasoning/confidence.py"), "Constitutionally stable core", "New context wraps the engine; determinism and explicit inputs remain intact."),
        Component("PlanningRecommendation", "Planning Bridge", "Translate the selected conclusion into an immutable advisory planning recommendation.", ("Objective", "Rationale", "Recommended actions", "Assumptions", "Constraints", "Risks"), ("Plan execution", "Mission creation", "Authorization"), ("core/reasoning/models.py",), "Constitutionally stable bridge", "Planning consumes but does not mutate reasoning output."),
        Component("ReasoningResult", "Canonical Contracts", "Represent the immutable fingerprinted result of one reasoning execution.", ("Status", "Assessments", "Selected hypothesis", "Missing information", "Contradictions", "Planning recommendation", "Trace", "Fingerprint"), ("Mutable runtime state", "Mission execution", "Knowledge acquisition"), ("core/reasoning/models.py",), "Constitutionally stable", "Compatibility-affecting additions require versioned migration."),
        Component("KnowledgeReasoningPipeline", "Composition", "Coordinate injected search, adaptation, generation, request construction, and reasoning.", ("Composition order", "Dependency injection", "Query normalization", "Context enrichment", "Outcome construction"), ("Search implementation", "Inference algorithms", "Executive policy", "Persistent session state"), ("core/reasoning/pipeline.py",), "Stable composition boundary", "A future session layer may wrap it; it must remain thin."),
    )


def synthesize(source_reports: list[dict[str, str]]) -> dict[str, Any]:
    comps = [item.to_dict() for item in components()]
    baseline: dict[str, Any] = {
        "baseline_id": BASELINE_ID,
        "baseline_version": BASELINE_VERSION,
        "title": "Canonical Reasoning Architecture Baseline",
        "status": "Foundational architecture baseline",
        "production_code_modified": False,
        "purpose": "Define the canonical architecture, constitutional invariants, approved extension points, and controlled evolution path for the JARVIS Reasoning Engine.",
        "executive_summary": "The existing Reasoning Engine is a coherent deterministic subsystem. Genesis will evolve it through a ReasoningSession envelope, structured provenance, executive governance, adaptive reasoning, calibration, and governed learning while preserving canonical contracts and authority boundaries.",
        "source_reports": source_reports,
        "canonical_components": comps,
        "responsibility_matrix": [{"component": c["name"], "layer": c["layer"], "primary_responsibility": c["responsibility"], "stability": c["stability"]} for c in comps],
        "current_processing_flow": ["Injected Knowledge Search", "KnowledgeEvidenceAdapter", "EvidenceItem", "DeterministicHypothesisGenerator", "ReasoningRequest", "ReasoningEngine", "PlanningRecommendation", "ReasoningResult", "KnowledgeReasoningOutcome"],
        "constitutional_invariants": [item.to_dict() for item in invariants()],
        "approved_extension_points": [item.to_dict() for item in extension_points()],
        "architectural_decisions": [
            {"decision": "Evolve the existing Reasoning Engine rather than replace it.", "basis": "The audited subsystem already has immutable contracts, deterministic orchestration, explicit knowledge adaptation, and stable fingerprints."},
            {"decision": "Introduce ReasoningSession as an execution envelope.", "basis": "Lifecycle, budgets, history, review state, and executive directives naturally surround current deterministic execution."},
            {"decision": "Preserve KnowledgeEvidenceAdapter as the provenance ingress.", "basis": "It is already the anti-corruption boundary between retrieval data and canonical evidence."},
            {"decision": "Keep KnowledgeReasoningPipeline thin.", "basis": "Its architectural value is dependency-injected composition."},
        ],
        "target_generation_2_flow": ["Executive Director", "ExecutiveReasoningGovernance", "ReasoningSession", "KnowledgeReasoningPipeline", "KnowledgeEvidenceAdapter", "DeterministicHypothesisGenerator", "ReasoningEngine", "ReasoningResult", "OutcomeCalibration", "LearningFeedback"],
        "evolution_sequence": [
            {"phase": "Genesis II", "capability": "Reasoning Session"},
            {"phase": "Genesis III", "capability": "Evidence Provenance"},
            {"phase": "Genesis IV", "capability": "Executive Governance"},
            {"phase": "Genesis V", "capability": "Competing Hypotheses"},
            {"phase": "Genesis VI", "capability": "Adaptive Reasoning"},
            {"phase": "Genesis VII", "capability": "Outcome Calibration"},
            {"phase": "Genesis VIII", "capability": "Governed Learning"},
        ],
        "change_governance": {
            "required_for_contract_changes": ["Explicit architecture decision", "Version update", "Migration plan", "Backward-compatibility assessment", "Deterministic regression fixtures"],
            "prohibited_without_architecture_revision": ["Hidden knowledge retrieval inside ReasoningEngine", "Mission execution inside core/reasoning", "Mutable canonical reasoning records", "Unversioned fingerprint-semantic changes", "Self-modifying learning behavior"],
        },
        "next_step": {"phase": "Genesis I-A4 Phase 2", "deliverable": "Constitutional verification suite", "then": "Genesis II — Reasoning Session Foundation"},
    }
    baseline["baseline_fingerprint"] = fingerprint(baseline)
    return baseline
