"""Evolutionary Genesis verification-manifest validation.

Genesis II-A3B replaces a fixed, exact manifest ceiling with a constitutional
ordering model.

The certified baseline remains mandatory and immutable. Later Genesis
verifiers may be appended when their phase identities are valid and strictly
ordered.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from typing import Iterable, Sequence


GENESIS_MANIFEST_PATH = Path(
    "dev/verification/manifests/genesis.manifest"
)

CERTIFIED_BASELINE: tuple[str, ...] = (
    "dev/verify_genesis_1a1.sh",
    "dev/verify_genesis_1a2.sh",
    "dev/verify_genesis_1a3.sh",
    "dev/verify_genesis_2a1.sh",
    "dev/verify_genesis_2a2.sh",
    "dev/verify_reasoning_fixtures.sh",
    "dev/verify_genesis_2a3.sh",
    "dev/verify_genesis_2a3a.sh",
)

_SPECIAL_PHASES: dict[str, tuple[int, str, int, str]] = {
    "dev/verify_reasoning_fixtures.sh": (2, "a", 2, "r"),
}

_GENESIS_PATTERN = re.compile(
    r"^dev/verify_genesis_"
    r"(?P<generation>[1-9][0-9]*)"
    r"(?P<stream>[a-z])"
    r"(?P<ordinal>[1-9][0-9]*)"
    r"(?P<suffix>[a-z]*)"
    r"\.sh$"
)


class GenesisManifestError(ValueError):
    """Raised when the Genesis manifest violates constitutional rules."""


@dataclass(frozen=True, slots=True, order=True)
class GenesisPhaseKey:
    """Sortable constitutional identity of one Genesis verifier."""

    generation: int
    stream: str
    ordinal: int
    suffix: tuple[int, ...]

    @classmethod
    def create(
        cls,
        *,
        generation: int,
        stream: str,
        ordinal: int,
        suffix: str = "",
    ) -> "GenesisPhaseKey":
        """Create a normalized sortable phase key."""

        if generation < 1:
            raise GenesisManifestError(
                "generation must be greater than zero"
            )

        if len(stream) != 1 or not stream.islower():
            raise GenesisManifestError(
                "stream must be one lowercase letter"
            )

        if ordinal < 1:
            raise GenesisManifestError(
                "ordinal must be greater than zero"
            )

        if suffix and (
            not suffix.isalpha()
            or not suffix.islower()
        ):
            raise GenesisManifestError(
                "suffix must contain lowercase letters only"
            )

        return cls(
            generation=generation,
            stream=stream,
            ordinal=ordinal,
            suffix=tuple(
                ord(character) - ord("a") + 1
                for character in suffix
            ),
        )

    @property
    def label(self) -> str:
        """Return a human-readable constitutional phase label."""

        suffix = "".join(
            chr(value + ord("a") - 1)
            for value in self.suffix
        )

        return (
            f"{self.generation}-"
            f"{self.stream.upper()}"
            f"{self.ordinal}"
            f"{suffix.upper()}"
        )


@dataclass(frozen=True, slots=True)
class GenesisManifestEntry:
    """One parsed Genesis verifier entry."""

    path: str
    phase: GenesisPhaseKey


@dataclass(frozen=True, slots=True)
class GenesisManifestReport:
    """Immutable result of successful manifest certification."""

    manifest_path: str
    entries: tuple[GenesisManifestEntry, ...]
    fingerprint: str

    @property
    def suite_count(self) -> int:
        """Return the number of certified Genesis suites."""

        return len(self.entries)

    @property
    def extension_count(self) -> int:
        """Return suites added after the certified baseline."""

        return len(self.entries) - len(CERTIFIED_BASELINE)


def read_manifest_entries(
    manifest_path: Path | str = GENESIS_MANIFEST_PATH,
) -> tuple[str, ...]:
    """Read non-comment manifest entries without changing their order."""

    path = Path(manifest_path)

    if not path.is_file():
        raise GenesisManifestError(
            f"Genesis manifest does not exist: {path}"
        )

    entries = tuple(
        line.strip()
        for line in path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
        and not line.strip().startswith("#")
    )

    if not entries:
        raise GenesisManifestError(
            f"Genesis manifest is empty: {path}"
        )

    return entries


def parse_phase(path: str) -> GenesisPhaseKey:
    """Parse a Genesis verifier path into a sortable phase identity."""

    if path in _SPECIAL_PHASES:
        generation, stream, ordinal, suffix = _SPECIAL_PHASES[path]

        return GenesisPhaseKey.create(
            generation=generation,
            stream=stream,
            ordinal=ordinal,
            suffix=suffix,
        )

    match = _GENESIS_PATTERN.fullmatch(path)

    if match is None:
        raise GenesisManifestError(
            "unrecognized Genesis verifier path: "
            f"{path}"
        )

    return GenesisPhaseKey.create(
        generation=int(match.group("generation")),
        stream=match.group("stream"),
        ordinal=int(match.group("ordinal")),
        suffix=match.group("suffix"),
    )


def _validate_repository_relative_path(path: str) -> None:
    """Validate one repository-relative verifier path."""

    if not isinstance(path, str):
        raise GenesisManifestError(
            "manifest entries must be strings"
        )

    if not path:
        raise GenesisManifestError(
            "manifest entries must not be empty"
        )

    candidate = Path(path)

    if candidate.is_absolute():
        raise GenesisManifestError(
            f"absolute path is forbidden: {path}"
        )

    if ".." in candidate.parts:
        raise GenesisManifestError(
            f"path traversal is forbidden: {path}"
        )

    if candidate.suffix != ".sh":
        raise GenesisManifestError(
            f"Genesis verifier must be a shell script: {path}"
        )

    if not path.startswith("dev/"):
        raise GenesisManifestError(
            f"Genesis verifier must be under dev/: {path}"
        )


def _manifest_fingerprint(entries: Sequence[str]) -> str:
    """Produce a deterministic fingerprint for an ordered manifest."""

    payload = "\n".join(entries) + "\n"

    return sha256(
        payload.encode("utf-8")
    ).hexdigest()


def validate_entries(
    entries: Iterable[str],
    *,
    manifest_path: str = str(GENESIS_MANIFEST_PATH),
) -> GenesisManifestReport:
    """Certify Genesis manifest entries.

    Constitutional rules:

    1. Paths are repository-relative and unique.
    2. The complete II-A3A certified baseline remains the exact prefix.
    3. Every later verifier has a parseable Genesis phase identity.
    4. Phase identities are strictly increasing.
    5. No later verifier may collide with an existing phase identity.
    """

    normalized_entries = tuple(entries)

    if not normalized_entries:
        raise GenesisManifestError(
            "Genesis manifest must contain at least one verifier"
        )

    for entry in normalized_entries:
        _validate_repository_relative_path(entry)

    if len(normalized_entries) != len(set(normalized_entries)):
        raise GenesisManifestError(
            "Genesis manifest contains duplicate verifier paths"
        )

    baseline_length = len(CERTIFIED_BASELINE)

    if len(normalized_entries) < baseline_length:
        raise GenesisManifestError(
            "Genesis manifest is missing one or more "
            "certified baseline verifiers"
        )

    actual_baseline = normalized_entries[:baseline_length]

    if actual_baseline != CERTIFIED_BASELINE:
        raise GenesisManifestError(
            "Genesis certified baseline was modified or reordered"
        )

    parsed_entries = tuple(
        GenesisManifestEntry(
            path=entry,
            phase=parse_phase(entry),
        )
        for entry in normalized_entries
    )

    phases = tuple(
        entry.phase
        for entry in parsed_entries
    )

    if len(phases) != len(set(phases)):
        raise GenesisManifestError(
            "Genesis manifest contains duplicate phase identities"
        )

    for previous, current in zip(
        parsed_entries,
        parsed_entries[1:],
        strict=False,
    ):
        if current.phase <= previous.phase:
            raise GenesisManifestError(
                "Genesis constitutional order violation: "
                f"{current.path} ({current.phase.label}) "
                "must follow "
                f"{previous.path} ({previous.phase.label})"
            )

    return GenesisManifestReport(
        manifest_path=manifest_path,
        entries=parsed_entries,
        fingerprint=_manifest_fingerprint(
            normalized_entries
        ),
    )


def validate_manifest(
    manifest_path: Path | str = GENESIS_MANIFEST_PATH,
) -> GenesisManifestReport:
    """Read and certify a Genesis manifest file."""

    path = Path(manifest_path)

    return validate_entries(
        read_manifest_entries(path),
        manifest_path=path.as_posix(),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Certify the evolutionary Genesis "
            "verification manifest."
        )
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate the configured Genesis manifest.",
    )
    parser.add_argument(
        "--manifest",
        default=str(GENESIS_MANIFEST_PATH),
        help="Path to the Genesis manifest.",
    )

    return parser


def main() -> int:
    """Command-line entry point."""

    parser = _build_parser()
    arguments = parser.parse_args()

    if not arguments.check:
        parser.error("--check is required")

    try:
        report = validate_manifest(
            arguments.manifest
        )
    except GenesisManifestError as error:
        print(f"[FAIL] {error}")
        return 1

    print(
        "[PASS] Genesis manifest constitutional order"
    )
    print(
        f"[INFO] Manifest: {report.manifest_path}"
    )
    print(
        f"[INFO] Suites: {report.suite_count}"
    )
    print(
        f"[INFO] Evolutionary extensions: "
        f"{report.extension_count}"
    )
    print(
        f"[INFO] Fingerprint: {report.fingerprint}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
