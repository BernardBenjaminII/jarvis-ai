"""
JARVIS Gen 2

Phase VI-F3

Runner Composition Contracts
"""

from __future__ import annotations

import inspect

from knowledge_engine.assimilation.runner import (
    AssimilationRunner,
    ClaimedDocument,
)

from knowledge_engine.assimilation.services.state import (
    AssimilationStateService,
)

from knowledge_engine.assimilation.services.persistence import (
    DocumentPersistenceService,
)

from knowledge_engine.assimilation.services.attempts import (
    AttemptJournalService,
)

from knowledge_engine.assimilation.services.extraction import (
    ExtractionService,
)


def banner(title: str):
    print(f"[PASS] {title}")


def verify_handler_name():
    assert AssimilationRunner.HANDLER_NAME == "document_assimilation"
    banner("Runner handler identity")


def verify_constructor_signature():
    sig = inspect.signature(AssimilationRunner.__init__)

    expected = [
        "self",
        "db",
        "default_max_attempts",
        "state_service",
        "persistence_service",
        "attempt_service",
        "extraction_service",
    ]

    assert list(sig.parameters.keys()) == expected

    banner("Constructor signature")


def verify_retry_validation():

    class DummyDB:
        pass

    try:
        AssimilationRunner(
            DummyDB(),
            default_max_attempts=0,
        )
    except ValueError:
        banner("Retry validation")
        return

    raise AssertionError(
        "default_max_attempts must reject zero"
    )


def verify_dependency_injection():

    class DummyDB:
        pass

    state = AssimilationStateService()
    persistence = DocumentPersistenceService()
    attempts = AttemptJournalService()
    extraction = ExtractionService()

    runner = AssimilationRunner(
        DummyDB(),
        state_service=state,
        persistence_service=persistence,
        attempt_service=attempts,
        extraction_service=extraction,
    )

    assert runner.state_service is state
    assert runner.persistence_service is persistence
    assert runner.attempt_service is attempts
    assert runner.extraction_service is extraction

    banner("Dependency injection")


def verify_default_services():

    class DummyDB:
        pass

    runner = AssimilationRunner(DummyDB())

    assert isinstance(
        runner.state_service,
        AssimilationStateService,
    )

    assert isinstance(
        runner.persistence_service,
        DocumentPersistenceService,
    )

    assert isinstance(
        runner.attempt_service,
        AttemptJournalService,
    )

    assert isinstance(
        runner.extraction_service,
        ExtractionService,
    )

    banner("Default composition")


def verify_public_methods():

    methods = {
        name
        for name, value in inspect.getmembers(
            AssimilationRunner,
            inspect.isfunction,
        )
        if not name.startswith("_")
    }

    expected = {
        "run_one_single_document",
        "recover_stale_processing",
        "requeue_failed_documents",
    }

    assert methods == expected

    banner("Public Runner API")


def verify_claim_document_contract():

    fields = list(
        ClaimedDocument.__dataclass_fields__.keys()
    )

    expected = [
        "object_uuid",
        "object_path",
        "object_type",
        "attempt_number",
        "max_attempts",
        "attempt_id",
    ]

    assert fields == expected
    assert ClaimedDocument.__dataclass_params__.frozen

    banner("ClaimedDocument contract")


def main():

    verify_handler_name()

    verify_constructor_signature()

    verify_retry_validation()

    verify_dependency_injection()

    verify_default_services()

    verify_public_methods()

    verify_claim_document_contract()

    print("-" * 70)

    print("[PASS] Runner composition contracts verified")


if __name__ == "__main__":
    main()
