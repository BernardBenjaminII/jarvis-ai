"""
JARVIS Gen 2 Phase VII-A1 Acquisition Foundation verification.

All discovery occurs inside temporary directories.
"""

from __future__ import annotations

import hashlib
import tempfile
from dataclasses import FrozenInstanceError
from pathlib import Path

from knowledge_engine.acquisition import (
    AcquisitionProviderRegistry,
    AcquisitionRequest,
    FilesystemAcquisitionProvider,
    KnowledgeAcquisitionDirector,
    build_default_provider_registry,
)


def assert_frozen(
    instance: object,
    attribute_name: str,
    replacement: object,
) -> None:
    try:
        setattr(
            instance,
            attribute_name,
            replacement,
        )
    except FrozenInstanceError:
        return

    raise AssertionError(
        f"{type(instance).__name__} must remain immutable"
    )


def create_fixture(root: Path) -> None:
    (root / "alpha.txt").write_text(
        "Alpha knowledge",
        encoding="utf-8",
    )

    (root / "bravo.md").write_text(
        "# Bravo",
        encoding="utf-8",
    )

    (root / "charlie.py").write_text(
        "print('Charlie')\n",
        encoding="utf-8",
    )

    (root / "delta.bin").write_bytes(
        b"\x00\x01\x02\x03"
    )

    (root / ".hidden.txt").write_text(
        "hidden",
        encoding="utf-8",
    )

    nested = root / "nested"
    nested.mkdir()

    (nested / "echo.pdf").write_bytes(
        b"%PDF-1.4\nEcho"
    )


def verify_registry() -> None:
    registry = build_default_provider_registry()

    assert registry.provider_ids() == (
        "filesystem",
    )
    assert registry.supports("filesystem")
    assert isinstance(
        registry.get("filesystem"),
        FilesystemAcquisitionProvider,
    )

    try:
        registry.register(
            FilesystemAcquisitionProvider()
        )
    except ValueError as exc:
        assert "already registered" in str(exc)
    else:
        raise AssertionError(
            "Duplicate provider registration was accepted"
        )

    try:
        registry.get("missing")
    except LookupError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError(
            "Unknown provider lookup was accepted"
        )


def verify_deterministic_discovery(
    root: Path,
) -> None:
    registry = build_default_provider_registry()
    director = KnowledgeAcquisitionDirector(
        registry
    )

    request = AcquisitionRequest(
        request_id="filesystem-test",
        roots=(str(root),),
        recursive=True,
        include_hidden=False,
        max_files=100,
    )

    first = director.plan(
        provider_id="filesystem",
        request=request,
    )

    second = director.plan(
        provider_id="filesystem",
        request=request,
    )

    assert first == second
    assert first.fingerprint == second.fingerprint
    assert first.candidate_count == 5
    assert first.truncated is False

    paths = [
        candidate.local_path
        for candidate in first.candidates
    ]

    assert paths == sorted(paths)
    assert not any(
        ".hidden.txt" in path
        for path in paths
    )

    types = {
        candidate.filename: candidate.candidate_type
        for candidate in first.candidates
    }

    assert types["alpha.txt"] == "document"
    assert types["bravo.md"] == "document"
    assert types["charlie.py"] == "source_code"
    assert types["delta.bin"] == "generic_file"
    assert types["echo.pdf"] == "document"

    alpha = next(
        candidate
        for candidate in first.candidates
        if candidate.filename == "alpha.txt"
    )

    expected_checksum = hashlib.sha256(
        b"Alpha knowledge"
    ).hexdigest()

    assert alpha.checksum_sha256 == expected_checksum
    assert alpha.source_uri.startswith("file://")
    assert first.total_bytes > 0

    assert_frozen(
        first,
        "truncated",
        True,
    )

    assert_frozen(
        alpha,
        "filename",
        "changed.txt",
    )


def verify_filters_and_bounds(
    root: Path,
) -> None:
    provider = FilesystemAcquisitionProvider()

    filtered = provider.discover(
        request=AcquisitionRequest(
            request_id="filtered",
            roots=(str(root),),
            allowed_extensions=(
                "txt",
                ".md",
            ),
            max_files=100,
        )
    )

    assert [
        candidate.filename
        for candidate in filtered.candidates
    ] == [
        "alpha.txt",
        "bravo.md",
    ]

    bounded = provider.discover(
        request=AcquisitionRequest(
            request_id="bounded",
            roots=(str(root),),
            include_hidden=True,
            max_files=2,
        )
    )

    assert bounded.candidate_count == 2
    assert bounded.truncated is True

    nonrecursive = provider.discover(
        request=AcquisitionRequest(
            request_id="nonrecursive",
            roots=(str(root),),
            recursive=False,
            max_files=100,
        )
    )

    assert "echo.pdf" not in {
        candidate.filename
        for candidate in nonrecursive.candidates
    }


def verify_missing_root() -> None:
    provider = FilesystemAcquisitionProvider()

    plan = provider.discover(
        request=AcquisitionRequest(
            request_id="missing-root",
            roots=(
                "/definitely/not/a/real/jarvis/path",
            ),
        )
    )

    assert plan.candidate_count == 0
    assert plan.skipped_count == 1


def verify_request_validation() -> None:
    try:
        AcquisitionRequest(
            request_id="",
            roots=("/tmp",),
        )
    except ValueError as exc:
        assert "request_id" in str(exc)
    else:
        raise AssertionError(
            "Blank request_id was accepted"
        )

    try:
        AcquisitionRequest(
            request_id="test",
            roots=(),
        )
    except ValueError as exc:
        assert "roots" in str(exc)
    else:
        raise AssertionError(
            "Empty roots were accepted"
        )

    try:
        AcquisitionRequest(
            request_id="test",
            roots=("/tmp",),
            max_files=0,
        )
    except ValueError as exc:
        assert "max_files" in str(exc)
    else:
        raise AssertionError(
            "Invalid max_files was accepted"
        )


def main() -> None:
    verify_registry()
    verify_request_validation()
    verify_missing_root()

    with tempfile.TemporaryDirectory(
        prefix="jarvis-phase-7a1-"
    ) as temporary:
        root = Path(temporary)
        create_fixture(root)

        verify_deterministic_discovery(root)
        verify_filters_and_bounds(root)

    print("[PASS] Acquisition provider registry")
    print("[PASS] Duplicate and unknown provider handling")
    print("[PASS] Acquisition request validation")
    print("[PASS] Read-only filesystem discovery")
    print("[PASS] Deterministic candidate ordering")
    print("[PASS] Stable acquisition-plan fingerprint")
    print("[PASS] Hidden-file exclusion")
    print("[PASS] Extension filtering")
    print("[PASS] Recursive and nonrecursive discovery")
    print("[PASS] Bounded candidate results")
    print("[PASS] Candidate classification")
    print("[PASS] SHA-256 provenance checksum")
    print("[PASS] Missing-root handling")
    print("[PASS] Immutable acquisition contracts")
    print("----------------------------------------------------------------------")
    print("[PASS] Phase VII-A1 acquisition foundation verified")


if __name__ == "__main__":
    main()
