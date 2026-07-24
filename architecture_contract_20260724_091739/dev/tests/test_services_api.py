"""
JARVIS Gen 2 assimilation-service API contract verification.

This suite protects the stable public interfaces of:

- ExtractionService
- DocumentPersistenceService
- AttemptJournalService
- AssimilationStateService

It verifies:

- required public methods
- exact parameter names
- keyword-only argument contracts
- default values
- result-model structure
- result-model immutability
- result properties
- constructor validation
- public-method input validation
- deterministic utility behavior

This test intentionally performs no persistent database writes.
Database behavior is covered by the phase-specific integration suites.
"""

from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError
from inspect import Parameter
from typing import Any, Callable

from knowledge_engine.assimilation.services.attempts import (
    AttemptJournalService,
    AttemptStartResult,
    AttemptUpdateResult,
)
from knowledge_engine.assimilation.services.extraction import (
    ExtractionResult,
    ExtractionService,
)
from knowledge_engine.assimilation.services.persistence import (
    DocumentPersistenceResult,
    DocumentPersistenceService,
)
from knowledge_engine.assimilation.services.state import (
    AssimilationStateService,
    StateTransitionResult,
)


EMPTY = inspect.Signature.empty


def assert_public_callable(
    instance: object,
    method_name: str,
) -> Callable[..., Any]:
    """Verify that one expected public method exists and is callable."""

    assert hasattr(instance, method_name), (
        f"{type(instance).__name__} is missing public method "
        f"{method_name!r}"
    )

    method = getattr(instance, method_name)

    assert callable(method), (
        f"{type(instance).__name__}.{method_name} is not callable"
    )

    return method


def assert_signature(
    method: Callable[..., Any],
    *,
    expected_parameters: list[
        tuple[str, inspect._ParameterKind, Any]
    ],
) -> None:
    """
    Verify exact public parameter names, kinds, order, and defaults.

    Bound methods do not expose ``self`` in inspect.signature().
    """

    signature = inspect.signature(method)
    actual = list(signature.parameters.values())

    assert len(actual) == len(expected_parameters), (
        f"Unexpected signature for {method.__qualname__}: "
        f"{signature}. Expected {len(expected_parameters)} parameters, "
        f"found {len(actual)}."
    )

    for parameter, expected in zip(
        actual,
        expected_parameters,
        strict=True,
    ):
        expected_name, expected_kind, expected_default = expected

        assert parameter.name == expected_name, (
            f"{method.__qualname__}: expected parameter "
            f"{expected_name!r}, found {parameter.name!r}"
        )

        assert parameter.kind == expected_kind, (
            f"{method.__qualname__}.{parameter.name}: expected kind "
            f"{expected_kind}, found {parameter.kind}"
        )

        if expected_default is EMPTY:
            assert parameter.default is EMPTY, (
                f"{method.__qualname__}.{parameter.name}: expected a "
                "required parameter"
            )
        else:
            assert parameter.default == expected_default, (
                f"{method.__qualname__}.{parameter.name}: expected default "
                f"{expected_default!r}, found {parameter.default!r}"
            )


def assert_frozen(
    instance: object,
    attribute_name: str,
    replacement: object,
) -> None:
    """Verify that a result dataclass cannot be mutated."""

    try:
        setattr(instance, attribute_name, replacement)
    except FrozenInstanceError:
        return

    raise AssertionError(
        f"{type(instance).__name__} must remain immutable"
    )


def assert_raises(
    exception_type: type[BaseException],
    callable_object: Callable[[], Any],
    *,
    message_fragment: str | None = None,
) -> None:
    """Verify an expected validation exception and optional message."""

    try:
        callable_object()
    except exception_type as exc:
        if message_fragment is not None:
            assert message_fragment in str(exc), (
                f"Expected {message_fragment!r} in exception message, "
                f"received {str(exc)!r}"
            )
        return

    raise AssertionError(
        f"Expected {exception_type.__name__} was not raised"
    )


def verify_extraction_service_api() -> None:
    service = ExtractionService()

    extract = assert_public_callable(service, "extract")
    normalize_text = assert_public_callable(
        service,
        "normalize_text",
    )

    assert_signature(
        extract,
        expected_parameters=[
            (
                "document_path",
                Parameter.KEYWORD_ONLY,
                EMPTY,
            ),
        ],
    )

    assert_signature(
        normalize_text,
        expected_parameters=[
            (
                "text",
                Parameter.POSITIONAL_OR_KEYWORD,
                EMPTY,
            ),
        ],
    )

    assert service.chunk_size == 2000
    assert service.chunk_overlap == 200
    assert (
        service.extractor_name
        == ExtractionService.DEFAULT_EXTRACTOR
    )

    normalized = service.normalize_text(
        "\n\n  JARVIS extraction test  \n\n"
    )

    assert normalized == "JARVIS extraction test"

    assert_raises(
        ValueError,
        lambda: ExtractionService(chunk_size=0),
        message_fragment="chunk_size",
    )

    assert_raises(
        ValueError,
        lambda: ExtractionService(chunk_overlap=-1),
        message_fragment="chunk_overlap",
    )

    assert_raises(
        ValueError,
        lambda: ExtractionService(
            chunk_size=100,
            chunk_overlap=100,
        ),
        message_fragment="smaller than chunk_size",
    )

    assert_raises(
        ValueError,
        lambda: ExtractionService(extractor_name="   "),
        message_fragment="extractor_name",
    )

    result = ExtractionResult(
        document_path="/tmp/example.txt",
        extractor="test_extractor",
        normalized_text="Alpha Bravo",
        checksum="abc123",
        chunks=("Alpha", "Bravo"),
    )

    assert result.document_path == "/tmp/example.txt"
    assert result.extractor == "test_extractor"
    assert result.normalized_text == "Alpha Bravo"
    assert result.checksum == "abc123"
    assert result.chunks == ("Alpha", "Bravo")
    assert result.text_chars == len("Alpha Bravo")
    assert result.chunk_count == 2
    assert result.usable is True

    assert_frozen(
        result,
        "checksum",
        "modified",
    )

    unusable = ExtractionResult(
        document_path="/tmp/empty.txt",
        extractor="test_extractor",
        normalized_text="",
        checksum="empty",
        chunks=(),
    )

    assert unusable.text_chars == 0
    assert unusable.chunk_count == 0
    assert unusable.usable is False

    print("[PASS] ExtractionService public methods")
    print("[PASS] ExtractionService exact signatures")
    print("[PASS] ExtractionService constructor validation")
    print("[PASS] ExtractionResult immutable contract")


def verify_persistence_service_api() -> None:
    service = DocumentPersistenceService()

    persist_document = assert_public_callable(
        service,
        "persist_document",
    )
    upsert_document_text = assert_public_callable(
        service,
        "upsert_document_text",
    )
    replace_chunks = assert_public_callable(
        service,
        "replace_chunks",
    )

    assert_signature(
        persist_document,
        expected_parameters=[
            ("conn", Parameter.KEYWORD_ONLY, EMPTY),
            ("document_path", Parameter.KEYWORD_ONLY, EMPTY),
            ("text", Parameter.KEYWORD_ONLY, EMPTY),
            ("checksum", Parameter.KEYWORD_ONLY, EMPTY),
            ("chunks", Parameter.KEYWORD_ONLY, EMPTY),
            (
                "extractor",
                Parameter.KEYWORD_ONLY,
                DocumentPersistenceService.DEFAULT_EXTRACTOR,
            ),
        ],
    )

    assert_signature(
        upsert_document_text,
        expected_parameters=[
            ("conn", Parameter.KEYWORD_ONLY, EMPTY),
            ("document_path", Parameter.KEYWORD_ONLY, EMPTY),
            ("text", Parameter.KEYWORD_ONLY, EMPTY),
            ("checksum", Parameter.KEYWORD_ONLY, EMPTY),
            ("extractor", Parameter.KEYWORD_ONLY, EMPTY),
        ],
    )

    assert_signature(
        replace_chunks,
        expected_parameters=[
            ("conn", Parameter.KEYWORD_ONLY, EMPTY),
            ("document_path", Parameter.KEYWORD_ONLY, EMPTY),
            ("chunks", Parameter.KEYWORD_ONLY, EMPTY),
        ],
    )

    assert_raises(
        ValueError,
        lambda: service.persist_document(
            conn=None,  # Validation occurs before DB access.
            document_path="/tmp/example.txt",
            text="   ",
            checksum="abc123",
            chunks=["Alpha"],
        ),
        message_fragment="text",
    )

    assert_raises(
        ValueError,
        lambda: service.persist_document(
            conn=None,
            document_path="/tmp/example.txt",
            text="Alpha",
            checksum="abc123",
            chunks=[],
        ),
        message_fragment="chunks",
    )

    assert_raises(
        ValueError,
        lambda: service.persist_document(
            conn=None,
            document_path="   ",
            text="Alpha",
            checksum="abc123",
            chunks=["Alpha"],
        ),
        message_fragment="document_path",
    )

    assert_raises(
        ValueError,
        lambda: service.persist_document(
            conn=None,
            document_path="/tmp/example.txt",
            text="Alpha",
            checksum="   ",
            chunks=["Alpha"],
        ),
        message_fragment="checksum",
    )

    assert_raises(
        ValueError,
        lambda: service.persist_document(
            conn=None,
            document_path="/tmp/example.txt",
            text="Alpha",
            checksum="abc123",
            chunks=["Alpha"],
            extractor="   ",
        ),
        message_fragment="extractor",
    )

    result = DocumentPersistenceResult(
        document_path="/tmp/example.txt",
        text_chars=100,
        chunk_count=4,
        checksum="abc123",
        extractor="test_extractor",
    )

    assert result.persisted is True
    assert result.document_path == "/tmp/example.txt"
    assert result.text_chars == 100
    assert result.chunk_count == 4
    assert result.checksum == "abc123"
    assert result.extractor == "test_extractor"

    assert_frozen(
        result,
        "chunk_count",
        99,
    )

    empty_result = DocumentPersistenceResult(
        document_path="/tmp/empty.txt",
        text_chars=0,
        chunk_count=0,
        checksum="empty",
        extractor="test_extractor",
    )

    assert empty_result.persisted is False

    print("[PASS] DocumentPersistenceService public methods")
    print("[PASS] DocumentPersistenceService exact signatures")
    print("[PASS] DocumentPersistenceService input validation")
    print("[PASS] DocumentPersistenceResult immutable contract")


def verify_attempt_service_api() -> None:
    service = AttemptJournalService()

    start_attempt = assert_public_callable(
        service,
        "start_attempt",
    )
    complete_attempt = assert_public_callable(
        service,
        "complete_attempt",
    )
    fail_attempt = assert_public_callable(
        service,
        "fail_attempt",
    )
    abandon_attempts = assert_public_callable(
        service,
        "abandon_processing_attempts",
    )
    fail_stale_attempts = assert_public_callable(
        service,
        "fail_stale_exhausted_attempts",
    )

    assert_signature(
        start_attempt,
        expected_parameters=[
            ("conn", Parameter.KEYWORD_ONLY, EMPTY),
            ("object_uuid", Parameter.KEYWORD_ONLY, EMPTY),
            ("object_path", Parameter.KEYWORD_ONLY, EMPTY),
            ("object_type", Parameter.KEYWORD_ONLY, EMPTY),
            ("handler_name", Parameter.KEYWORD_ONLY, EMPTY),
            ("attempt_number", Parameter.KEYWORD_ONLY, EMPTY),
        ],
    )

    assert_signature(
        complete_attempt,
        expected_parameters=[
            ("conn", Parameter.KEYWORD_ONLY, EMPTY),
            ("attempt_id", Parameter.KEYWORD_ONLY, EMPTY),
            ("text_chars", Parameter.KEYWORD_ONLY, EMPTY),
            ("chunk_count", Parameter.KEYWORD_ONLY, EMPTY),
            ("checksum", Parameter.KEYWORD_ONLY, EMPTY),
        ],
    )

    assert_signature(
        fail_attempt,
        expected_parameters=[
            ("conn", Parameter.KEYWORD_ONLY, EMPTY),
            ("attempt_id", Parameter.KEYWORD_ONLY, EMPTY),
            ("error_type", Parameter.KEYWORD_ONLY, EMPTY),
            ("error_message", Parameter.KEYWORD_ONLY, EMPTY),
        ],
    )

    assert_signature(
        abandon_attempts,
        expected_parameters=[
            ("conn", Parameter.KEYWORD_ONLY, EMPTY),
            ("object_uuid", Parameter.KEYWORD_ONLY, EMPTY),
            (
                "reason",
                Parameter.KEYWORD_ONLY,
                "Recovered stale processing claim",
            ),
        ],
    )

    assert_signature(
        fail_stale_attempts,
        expected_parameters=[
            ("conn", Parameter.KEYWORD_ONLY, EMPTY),
            ("object_uuid", Parameter.KEYWORD_ONLY, EMPTY),
            (
                "reason",
                Parameter.KEYWORD_ONLY,
                "Stale processing claim exhausted retry limit",
            ),
        ],
    )

    assert_raises(
        ValueError,
        lambda: service.start_attempt(
            conn=None,
            object_uuid="",
            object_path="/tmp/example.txt",
            object_type="single_document",
            handler_name="test",
            attempt_number=1,
        ),
        message_fragment="object_uuid",
    )

    assert_raises(
        ValueError,
        lambda: service.start_attempt(
            conn=None,
            object_uuid="object-001",
            object_path="",
            object_type="single_document",
            handler_name="test",
            attempt_number=1,
        ),
        message_fragment="object_path",
    )

    assert_raises(
        ValueError,
        lambda: service.start_attempt(
            conn=None,
            object_uuid="object-001",
            object_path="/tmp/example.txt",
            object_type="",
            handler_name="test",
            attempt_number=1,
        ),
        message_fragment="object_type",
    )

    assert_raises(
        ValueError,
        lambda: service.start_attempt(
            conn=None,
            object_uuid="object-001",
            object_path="/tmp/example.txt",
            object_type="single_document",
            handler_name="",
            attempt_number=1,
        ),
        message_fragment="handler_name",
    )

    assert_raises(
        ValueError,
        lambda: service.start_attempt(
            conn=None,
            object_uuid="object-001",
            object_path="/tmp/example.txt",
            object_type="single_document",
            handler_name="test",
            attempt_number=0,
        ),
        message_fragment="attempt_number",
    )

    assert_raises(
        ValueError,
        lambda: service.complete_attempt(
            conn=None,
            attempt_id=0,
            text_chars=100,
            chunk_count=2,
            checksum="abc123",
        ),
        message_fragment="attempt_id",
    )

    assert_raises(
        ValueError,
        lambda: service.complete_attempt(
            conn=None,
            attempt_id=1,
            text_chars=0,
            chunk_count=2,
            checksum="abc123",
        ),
        message_fragment="text_chars",
    )

    assert_raises(
        ValueError,
        lambda: service.complete_attempt(
            conn=None,
            attempt_id=1,
            text_chars=100,
            chunk_count=0,
            checksum="abc123",
        ),
        message_fragment="chunk_count",
    )

    assert_raises(
        ValueError,
        lambda: service.complete_attempt(
            conn=None,
            attempt_id=1,
            text_chars=100,
            chunk_count=2,
            checksum="",
        ),
        message_fragment="checksum",
    )

    assert_raises(
        ValueError,
        lambda: service.fail_attempt(
            conn=None,
            attempt_id=0,
            error_type="RuntimeError",
            error_message="failure",
        ),
        message_fragment="attempt_id",
    )

    assert_raises(
        ValueError,
        lambda: service.fail_attempt(
            conn=None,
            attempt_id=1,
            error_type="",
            error_message="failure",
        ),
        message_fragment="error_type",
    )

    assert_raises(
        ValueError,
        lambda: service.fail_attempt(
            conn=None,
            attempt_id=1,
            error_type="RuntimeError",
            error_message="",
        ),
        message_fragment="error_message",
    )

    start_result = AttemptStartResult(
        attempt_id=10,
        object_uuid="object-001",
        attempt_number=2,
    )

    assert start_result.attempt_id == 10
    assert start_result.object_uuid == "object-001"
    assert start_result.attempt_number == 2
    assert start_result.attempt_state == "processing"

    assert_frozen(
        start_result,
        "attempt_id",
        99,
    )

    update_result = AttemptUpdateResult(
        rows_updated=1,
        attempt_state="completed",
    )

    assert update_result.rows_updated == 1
    assert update_result.attempt_state == "completed"
    assert update_result.applied is True

    empty_update = AttemptUpdateResult(
        rows_updated=0,
        attempt_state="completed",
    )

    assert empty_update.applied is False

    assert_frozen(
        update_result,
        "rows_updated",
        99,
    )

    print("[PASS] AttemptJournalService public methods")
    print("[PASS] AttemptJournalService exact signatures")
    print("[PASS] AttemptJournalService input validation")
    print("[PASS] Attempt result immutable contracts")


def verify_state_service_api() -> None:
    service = AssimilationStateService()

    claim_document = assert_public_callable(
        service,
        "claim_document",
    )
    mark_ready = assert_public_callable(
        service,
        "mark_document_ready_for_embedding",
    )
    mark_failure = assert_public_callable(
        service,
        "mark_document_failure",
    )
    recover_stale = assert_public_callable(
        service,
        "recover_stale_document",
    )
    fail_stale = assert_public_callable(
        service,
        "fail_stale_exhausted_document",
    )
    requeue_failed = assert_public_callable(
        service,
        "requeue_failed_document",
    )

    assert_signature(
        claim_document,
        expected_parameters=[
            ("conn", Parameter.KEYWORD_ONLY, EMPTY),
            ("object_uuid", Parameter.KEYWORD_ONLY, EMPTY),
            ("attempt_number", Parameter.KEYWORD_ONLY, EMPTY),
            ("max_attempts", Parameter.KEYWORD_ONLY, EMPTY),
        ],
    )

    assert_signature(
        mark_ready,
        expected_parameters=[
            ("conn", Parameter.KEYWORD_ONLY, EMPTY),
            ("object_uuid", Parameter.KEYWORD_ONLY, EMPTY),
        ],
    )

    assert_signature(
        mark_failure,
        expected_parameters=[
            ("conn", Parameter.KEYWORD_ONLY, EMPTY),
            ("object_uuid", Parameter.KEYWORD_ONLY, EMPTY),
            ("error_text", Parameter.KEYWORD_ONLY, EMPTY),
            ("retry_exhausted", Parameter.KEYWORD_ONLY, EMPTY),
        ],
    )

    assert_signature(
        recover_stale,
        expected_parameters=[
            ("conn", Parameter.KEYWORD_ONLY, EMPTY),
            ("object_uuid", Parameter.KEYWORD_ONLY, EMPTY),
        ],
    )

    assert_signature(
        fail_stale,
        expected_parameters=[
            ("conn", Parameter.KEYWORD_ONLY, EMPTY),
            ("object_uuid", Parameter.KEYWORD_ONLY, EMPTY),
        ],
    )

    assert_signature(
        requeue_failed,
        expected_parameters=[
            ("conn", Parameter.KEYWORD_ONLY, EMPTY),
            ("object_uuid", Parameter.KEYWORD_ONLY, EMPTY),
            ("reset_attempts", Parameter.KEYWORD_ONLY, EMPTY),
        ],
    )

    applied = StateTransitionResult(
        registry_rows=1,
        queue_rows=1,
    )

    assert applied.registry_rows == 1
    assert applied.queue_rows == 1
    assert applied.applied is True

    incomplete_registry = StateTransitionResult(
        registry_rows=0,
        queue_rows=1,
    )

    incomplete_queue = StateTransitionResult(
        registry_rows=1,
        queue_rows=0,
    )

    excessive_rows = StateTransitionResult(
        registry_rows=2,
        queue_rows=1,
    )

    assert incomplete_registry.applied is False
    assert incomplete_queue.applied is False
    assert excessive_rows.applied is False

    assert_frozen(
        applied,
        "registry_rows",
        99,
    )

    print("[PASS] AssimilationStateService public methods")
    print("[PASS] AssimilationStateService exact signatures")
    print("[PASS] StateTransitionResult exact application rules")
    print("[PASS] StateTransitionResult immutable contract")


def main() -> None:
    verify_extraction_service_api()
    verify_persistence_service_api()
    verify_attempt_service_api()
    verify_state_service_api()

    print("----------------------------------------------------------------------")
    print("[PASS] All assimilation service API contracts verified")


if __name__ == "__main__":
    main()
