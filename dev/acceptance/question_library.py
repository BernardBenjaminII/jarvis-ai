from .classification import FailureClassification, FailureSeverity
from .test_case import AcceptanceTestCase, ExpectedOutcome

def smoke_questions():
    return (
        AcceptanceTestCase(
            "SMOKE-KNOWN-SHA256", "Retrieval", "Known SHA-256 question",
            "What is SHA-256?",
            ExpectedOutcome(
                minimum_accepted_evidence=1,
                forbidden_phrases=("i don't have access to your knowledge base",),
            ),
            classification_on_failure=FailureClassification.RETRIEVAL,
            severity_on_failure=FailureSeverity.S3,
        ),
        AcceptanceTestCase(
            "SMOKE-UNKNOWN-WARP-CORE", "Gap Detection", "Fabricated gap question",
            "Explain the internal architecture of the Quantum Banana Warp Core Mk XII.",
            ExpectedOutcome(
                expected_state="unknown", maximum_accepted_evidence=0,
                require_recommendation=True, require_citations=False,
            ),
            classification_on_failure=FailureClassification.GROUNDING,
            severity_on_failure=FailureSeverity.S4,
        ),
    )
