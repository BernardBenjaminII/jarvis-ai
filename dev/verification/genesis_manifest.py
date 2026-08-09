"""Evolutionary and hierarchical Genesis verification-manifest validation.

Genesis II-A3G extends the certified Genesis namespace with Roman runtime
campaign identities such as ``ix_0`` while preserving numeric phases, Roman
stream phases, hierarchical Roman subphases, legacy labels, constitutional
ordering, and the certified baseline.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from functools import total_ordering
from hashlib import sha256
from pathlib import Path
import re
from typing import Iterable, Sequence


GENESIS_MANIFEST_PATH = Path("dev/verification/manifests/genesis.manifest")

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

_SPECIAL_PHASES: dict[str, tuple[int, str, tuple[tuple[int, int], ...]]] = {
    "dev/verify_reasoning_fixtures.sh": (2, "a", ((0, 2), (1, 18))),
}

_NUMERIC_GENESIS_PATTERN = re.compile(
    r"^dev/verify_genesis_"
    r"(?P<generation>[1-9][0-9]*)"
    r"(?P<stream>[a-z])"
    r"(?P<body>[1-9][0-9]*(?:[a-z](?:[1-9][0-9]*)?)*)"
    r"\.sh$"
)

_ROMAN_GENESIS_PATTERN = re.compile(
    r"^dev/verify_genesis_"
    r"(?P<generation>[ivxlcdm]+)_"
    r"(?P<stream>[a-z])"
    r"(?P<body>[0-9]+(?:[a-z](?:[0-9]+)?)*)"
    r"(?P<subphases>(?:_[0-9]+(?:[a-z](?:[0-9]+)?)*)*)"
    r"\.sh$"
)


_RUNTIME_CAMPAIGN_PATTERN = re.compile(
    r"^dev/verify_genesis_"
    r"(?P<generation>[ivxlcdm]+)_"
    r"(?P<body>[0-9]+(?:[a-z](?:[0-9]+)?)*)"
    r"(?P<subphases>(?:_[0-9]+(?:[a-z](?:[0-9]+)?)*)*)"
    r"\.sh$"
)

_BODY_TOKEN_PATTERN = re.compile(r"[0-9]+|[a-z]")


_ROMAN_VALUES = {
    "i": 1,
    "v": 5,
    "x": 10,
    "l": 50,
    "c": 100,
    "d": 500,
    "m": 1000,
}


def _roman_to_integer(token: str) -> int:
    value = 0
    previous = 0
    for character in reversed(token):
        current = _ROMAN_VALUES[character]
        if current < previous:
            value -= current
        else:
            value += current
            previous = current
    if value < 1 or _integer_to_roman(value).lower() != token:
        raise GenesisManifestError(f"invalid Roman Genesis generation: {token}")
    return value


def _integer_to_roman(value: int) -> str:
    if value < 1 or value > 3999:
        raise GenesisManifestError("Roman Genesis generation must be between 1 and 3999")
    table = (
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    )
    remainder = value
    result: list[str] = []
    for integer, numeral in table:
        while remainder >= integer:
            result.append(numeral)
            remainder -= integer
    return "".join(result)


class GenesisManifestError(ValueError):
    """Raised when the Genesis manifest violates constitutional rules."""


@total_ordering
@dataclass(frozen=True, slots=True)
class GenesisPhaseKey:
    """Sortable constitutional identity of one Genesis verifier."""

    generation: int
    stream: str
    hierarchy: tuple[tuple[int, int], ...]
    namespace: str = field(default="numeric", compare=False)
    phase_kind: str = field(default="branch", compare=False)

    @classmethod
    def create(
        cls,
        *,
        generation: int,
        stream: str,
        hierarchy: Sequence[tuple[int, int]],
        namespace: str = "numeric",
        phase_kind: str = "branch",
    ) -> "GenesisPhaseKey":
        if generation < 1:
            raise GenesisManifestError("generation must be greater than zero")
        if len(stream) != 1 or not stream.islower() or not stream.isalpha():
            raise GenesisManifestError("stream must be one lowercase letter")

        if namespace not in {"numeric", "roman"}:
            raise GenesisManifestError("namespace must be numeric or roman")
        if phase_kind not in {"root", "branch"}:
            raise GenesisManifestError("phase_kind must be root or branch")

        normalized = tuple(hierarchy)
        if not normalized:
            raise GenesisManifestError("phase hierarchy must not be empty")
        if normalized[0][0] != 0:
            raise GenesisManifestError("phase hierarchy must begin with a numeric ordinal")

        for index, (tag, value) in enumerate(normalized):
            if tag not in (0, 1):
                raise GenesisManifestError("hierarchy tags must be numeric or alphabetic")
            minimum = 0 if index == 0 and tag == 0 else 1
            if value < minimum:
                raise GenesisManifestError(
                    "top-level ordinal may be zero; nested hierarchy values must be positive"
                )
            if tag == 1 and value > 26:
                raise GenesisManifestError("alphabetic hierarchy value exceeds z")

        return cls(
            generation=generation,
            stream=stream,
            hierarchy=normalized,
            namespace=namespace,
            phase_kind=phase_kind,
        )

    def _constitutional_order_key(self) -> tuple:
        """Return ordering independent of compatibility display labels."""

        phase_rank = 0 if self.phase_kind == "root" else 1
        stream_rank = "" if self.phase_kind == "root" else self.stream
        return (
            self.generation,
            phase_rank,
            stream_rank,
            self.hierarchy,
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, GenesisPhaseKey):
            return NotImplemented
        return self._constitutional_order_key() < other._constitutional_order_key()

    @property
    def ordinal(self) -> int:
        """Return the top-level ordinal for backward-compatible callers."""

        return self.hierarchy[0][1]

    @property
    def suffix(self) -> tuple[int, ...]:
        """Return alphabetic hierarchy values for backward-compatible callers."""

        return tuple(value for tag, value in self.hierarchy[1:] if tag == 1)

    @property
    def label(self) -> str:
        """Return a backward-compatible public phase label."""

        generation = (
            _integer_to_roman(self.generation)
            if self.namespace == "roman"
            else str(self.generation)
        )
        prefix = f"{generation}-{self.stream.upper()}"

        if len(self.hierarchy) == 1:
            return f"{prefix}{self.hierarchy[0][1]}"

        if (
            len(self.hierarchy) == 2
            and self.hierarchy[0][0] == 0
            and self.hierarchy[1][0] == 1
        ):
            ordinal = self.hierarchy[0][1]
            suffix = chr(ord("A") + self.hierarchy[1][1] - 1)
            return f"{prefix}{ordinal}{suffix}"

        components: list[str] = []
        for tag, value in self.hierarchy:
            components.append(
                str(value) if tag == 0 else chr(ord("A") + value - 1)
            )
        return f"{prefix}{'.'.join(components)}"


@dataclass(frozen=True, slots=True)
class GenesisManifestEntry:
    path: str
    phase: GenesisPhaseKey


@dataclass(frozen=True, slots=True)
class GenesisManifestReport:
    manifest_path: str
    entries: tuple[GenesisManifestEntry, ...]
    fingerprint: str

    @property
    def suite_count(self) -> int:
        return len(self.entries)

    @property
    def extension_count(self) -> int:
        return len(self.entries) - len(CERTIFIED_BASELINE)


def read_manifest_entries(
    manifest_path: Path | str = GENESIS_MANIFEST_PATH,
) -> tuple[str, ...]:
    path = Path(manifest_path)
    if not path.is_file():
        raise GenesisManifestError(f"Genesis manifest does not exist: {path}")

    entries = tuple(
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    )
    if not entries:
        raise GenesisManifestError(f"Genesis manifest is empty: {path}")
    return entries


def _parse_body(body: str) -> tuple[tuple[int, int], ...]:
    tokens = _BODY_TOKEN_PATTERN.findall(body)
    if "".join(tokens) != body:
        raise GenesisManifestError(f"invalid hierarchical Genesis phase body: {body}")

    hierarchy: list[tuple[int, int]] = []
    expected_numeric = True

    for token in tokens:
        is_numeric = token[0].isdigit()
        if is_numeric != expected_numeric:
            expected = "numeric" if expected_numeric else "alphabetic"
            raise GenesisManifestError(
                f"hierarchical Genesis phase expected {expected} component: {body}"
            )

        if is_numeric:
            if len(token) > 1 and token.startswith("0"):
                raise GenesisManifestError(
                    f"numeric hierarchy component has a leading zero: {body}"
                )
            hierarchy.append((0, int(token)))
        else:
            hierarchy.append((1, ord(token) - ord("a") + 1))
        expected_numeric = not expected_numeric

    return tuple(hierarchy)


def _parse_roman_hierarchy(
    body: str,
    subphases: str,
) -> tuple[tuple[int, int], ...]:
    """Parse one Roman-generation body plus underscore-delimited subphases."""

    segments = (body, *subphases.lstrip("_").split("_")) if subphases else (body,)
    hierarchy: list[tuple[int, int]] = []

    for index, segment in enumerate(segments):
        if not segment:
            raise GenesisManifestError("Roman subphase segments must not be empty")

        parsed = _parse_body(segment)
        if index > 0 and parsed[0][0] != 0:
            raise GenesisManifestError(
                f"Roman subphase must begin with a numeric component: {segment}"
            )
        hierarchy.extend(parsed)

    return tuple(hierarchy)


def parse_phase(path: str) -> GenesisPhaseKey:
    if path in _SPECIAL_PHASES:
        generation, stream, hierarchy = _SPECIAL_PHASES[path]
        return GenesisPhaseKey.create(
            generation=generation,
            stream=stream,
            hierarchy=hierarchy,
        )

    numeric_match = _NUMERIC_GENESIS_PATTERN.fullmatch(path)
    if numeric_match is not None:
        return GenesisPhaseKey.create(
            generation=int(numeric_match.group("generation")),
            stream=numeric_match.group("stream"),
            hierarchy=_parse_body(numeric_match.group("body")),
            namespace="numeric",
        )

    roman_match = _ROMAN_GENESIS_PATTERN.fullmatch(path)
    if roman_match is not None:
        return GenesisPhaseKey.create(
            generation=_roman_to_integer(roman_match.group("generation")),
            stream=roman_match.group("stream"),
            hierarchy=_parse_roman_hierarchy(
                roman_match.group("body"),
                roman_match.group("subphases"),
            ),
            namespace="roman",
        )

    runtime_match = _RUNTIME_CAMPAIGN_PATTERN.fullmatch(path)
    if runtime_match is not None:
        return GenesisPhaseKey.create(
            generation=_roman_to_integer(runtime_match.group("generation")),
            stream="z",
            hierarchy=_parse_roman_hierarchy(
                runtime_match.group("body"),
                runtime_match.group("subphases"),
            ),
            namespace="roman",
            phase_kind="root",
        )

    raise GenesisManifestError(f"unrecognized Genesis verifier path: {path}")


def _validate_repository_relative_path(path: str) -> None:
    if not isinstance(path, str):
        raise GenesisManifestError("manifest entries must be strings")
    if not path:
        raise GenesisManifestError("manifest entries must not be empty")

    candidate = Path(path)
    if candidate.is_absolute():
        raise GenesisManifestError(f"absolute path is forbidden: {path}")
    if ".." in candidate.parts:
        raise GenesisManifestError(f"path traversal is forbidden: {path}")
    if candidate.suffix != ".sh":
        raise GenesisManifestError(f"Genesis verifier must be a shell script: {path}")
    if not path.startswith("dev/"):
        raise GenesisManifestError(f"Genesis verifier must be under dev/: {path}")


def _manifest_fingerprint(entries: Sequence[str]) -> str:
    return sha256(("\n".join(entries) + "\n").encode("utf-8")).hexdigest()


def validate_entries(
    entries: Iterable[str],
    *,
    manifest_path: str = str(GENESIS_MANIFEST_PATH),
) -> GenesisManifestReport:
    normalized_entries = tuple(entries)
    if not normalized_entries:
        raise GenesisManifestError("Genesis manifest must contain at least one verifier")

    for entry in normalized_entries:
        _validate_repository_relative_path(entry)

    if len(normalized_entries) != len(set(normalized_entries)):
        raise GenesisManifestError("Genesis manifest contains duplicate verifier paths")

    baseline_length = len(CERTIFIED_BASELINE)
    if len(normalized_entries) < baseline_length:
        raise GenesisManifestError(
            "Genesis manifest is missing one or more certified baseline verifiers"
        )
    if normalized_entries[:baseline_length] != CERTIFIED_BASELINE:
        raise GenesisManifestError("Genesis certified baseline was modified or reordered")

    parsed_entries = tuple(
        GenesisManifestEntry(path=entry, phase=parse_phase(entry))
        for entry in normalized_entries
    )
    phases = tuple(entry.phase for entry in parsed_entries)

    if len(phases) != len(set(phases)):
        raise GenesisManifestError("Genesis manifest contains duplicate phase identities")

    for previous, current in zip(parsed_entries, parsed_entries[1:], strict=False):
        if current.phase <= previous.phase:
            raise GenesisManifestError(
                "Genesis constitutional order violation: "
                f"{current.path} ({current.phase.label}) must follow "
                f"{previous.path} ({previous.phase.label})"
            )

    return GenesisManifestReport(
        manifest_path=manifest_path,
        entries=parsed_entries,
        fingerprint=_manifest_fingerprint(normalized_entries),
    )


def validate_manifest(
    manifest_path: Path | str = GENESIS_MANIFEST_PATH,
) -> GenesisManifestReport:
    path = Path(manifest_path)
    return validate_entries(
        read_manifest_entries(path),
        manifest_path=path.as_posix(),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Certify the hierarchical Genesis verification manifest."
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--manifest", default=str(GENESIS_MANIFEST_PATH))
    return parser


def main() -> int:
    parser = _build_parser()
    arguments = parser.parse_args()

    if not arguments.check:
        parser.error("--check is required")

    try:
        report = validate_manifest(arguments.manifest)
    except GenesisManifestError as error:
        print(f"[FAIL] {error}")
        return 1

    print("[PASS] Genesis manifest constitutional order")
    print(f"[INFO] Manifest: {report.manifest_path}")
    print(f"[INFO] Suites: {report.suite_count}")
    print(f"[INFO] Evolutionary extensions: {report.extension_count}")
    print(f"[INFO] Fingerprint: {report.fingerprint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
