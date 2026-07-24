"""Repository boundary for immutable executive checkpoints."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
from typing import Any, Mapping, Protocol, runtime_checkable

from .checkpoint import (
    CheckpointIntegrityError,
    CheckpointSequenceError,
    CheckpointStatus,
    CheckpointSummary,
    ExecutiveCheckpoint,
    ZERO_DIGEST,
    create_checkpoint,
    decode_checkpoint,
    encode_checkpoint,
)
from .storage import AtomicFileStorage, StorageError, StoragePolicy


_SESSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_CHECKPOINT_FILENAME_PATTERN = re.compile(r"^(?P<sequence>[0-9]{8})\.chk$")


class CheckpointRepositoryError(RuntimeError):
    """Base error for checkpoint repository operations."""


class CheckpointNotFoundError(CheckpointRepositoryError):
    """Raised when a requested checkpoint does not exist."""


class CheckpointConflictError(CheckpointRepositoryError):
    """Raised when immutable checkpoint history would be overwritten."""


class CheckpointHistoryError(CheckpointRepositoryError):
    """Raised when a session's checkpoint chain is inconsistent."""


@dataclass(frozen=True, slots=True)
class RepositoryPolicy:
    checkpoint_suffix: str = ".chk"
    sequence_width: int = 8

    def __post_init__(self) -> None:
        if self.checkpoint_suffix != ".chk":
            raise ValueError("Genesis VI-A6.3 requires the .chk suffix")
        if self.sequence_width != 8:
            raise ValueError("Genesis VI-A6.3 requires eight-digit sequences")


@runtime_checkable
class CheckpointRepository(Protocol):
    def save(
        self,
        *,
        session_id: str,
        payload: bytes,
        schema_name: str,
        schema_version: int,
        mission_id: str | None = None,
        metadata: Mapping[str, str] | None = None,
        created_at: datetime | None = None,
    ) -> ExecutiveCheckpoint: ...

    def load(self, session_id: str, sequence: int) -> ExecutiveCheckpoint: ...

    def latest(self, session_id: str) -> ExecutiveCheckpoint | None: ...

    def history(self, session_id: str) -> tuple[CheckpointSummary, ...]: ...

    def verify(self, session_id: str, sequence: int) -> CheckpointSummary: ...

    def archive(self, session_id: str) -> Path: ...


class FileCheckpointRepository:
    """Filesystem-backed immutable checkpoint repository.

    Layout:
        <root>/sessions/<session-id>/00000001.chk
        <root>/sessions/<session-id>/index.json
        <root>/archive/<session-id>/
        <root>/locks/<session-id>.lock
    """

    def __init__(
        self,
        root: str | Path,
        *,
        storage_policy: StoragePolicy | None = None,
        repository_policy: RepositoryPolicy | None = None,
    ) -> None:
        self._storage = AtomicFileStorage(root, policy=storage_policy)
        self._policy = repository_policy or RepositoryPolicy()

    @property
    def root(self) -> Path:
        return self._storage.root

    def save(
        self,
        *,
        session_id: str,
        payload: bytes,
        schema_name: str,
        schema_version: int,
        mission_id: str | None = None,
        metadata: Mapping[str, str] | None = None,
        created_at: datetime | None = None,
    ) -> ExecutiveCheckpoint:
        self._validate_session_id(session_id)
        lock_path = self._lock_path(session_id)

        with self._storage.advisory_lock(lock_path):
            current = self.latest(session_id)
            sequence = 1 if current is None else current.sequence + 1
            parent_digest = (
                ZERO_DIGEST if current is None else current.checkpoint_sha256
            )

            checkpoint = create_checkpoint(
                session_id=session_id,
                mission_id=mission_id,
                sequence=sequence,
                created_at=created_at,
                schema_name=schema_name,
                schema_version=schema_version,
                payload=payload,
                parent_checkpoint_sha256=parent_digest,
                metadata=metadata,
            )
            relative_path = self._checkpoint_path(session_id, sequence)
            try:
                self._storage.atomic_write_bytes(
                    relative_path,
                    encode_checkpoint(checkpoint),
                    replace=False,
                )
            except FileExistsError as exc:
                raise CheckpointConflictError(
                    f"checkpoint already exists: {checkpoint.checkpoint_id}"
                ) from exc

            self._write_index(session_id)
            return checkpoint

    def load(self, session_id: str, sequence: int) -> ExecutiveCheckpoint:
        self._validate_session_id(session_id)
        self._validate_sequence(sequence)
        relative_path = self._checkpoint_path(session_id, sequence)
        try:
            checkpoint = decode_checkpoint(self._storage.read_bytes(relative_path))
        except FileNotFoundError as exc:
            raise CheckpointNotFoundError(
                f"checkpoint not found: {session_id}:{sequence:08d}"
            ) from exc
        except CheckpointIntegrityError:
            raise
        except Exception as exc:
            raise CheckpointRepositoryError(
                f"cannot load checkpoint: {session_id}:{sequence:08d}"
            ) from exc

        if checkpoint.session_id != session_id or checkpoint.sequence != sequence:
            raise CheckpointHistoryError(
                f"checkpoint path identity mismatch: {session_id}:{sequence:08d}"
            )
        return checkpoint

    def latest(self, session_id: str) -> ExecutiveCheckpoint | None:
        sequences = self._sequences(session_id)
        if not sequences:
            return None
        return self.load(session_id, sequences[-1])

    def history(self, session_id: str) -> tuple[CheckpointSummary, ...]:
        sequences = self._sequences(session_id)
        checkpoints = tuple(self.load(session_id, sequence) for sequence in sequences)
        self._verify_chain(checkpoints)
        return tuple(CheckpointSummary.from_checkpoint(item) for item in checkpoints)

    def verify(self, session_id: str, sequence: int) -> CheckpointSummary:
        checkpoint = self.load(session_id, sequence)
        checkpoint.verify()

        if sequence == 1:
            if checkpoint.parent_checkpoint_sha256 != ZERO_DIGEST:
                raise CheckpointHistoryError(
                    "first checkpoint must use the zero parent digest"
                )
        else:
            previous = self.load(session_id, sequence - 1)
            if checkpoint.parent_checkpoint_sha256 != previous.checkpoint_sha256:
                raise CheckpointHistoryError(
                    f"parent linkage mismatch at {checkpoint.checkpoint_id}"
                )

        return CheckpointSummary.from_checkpoint(checkpoint)

    def archive(self, session_id: str) -> Path:
        self._validate_session_id(session_id)
        lock_path = self._lock_path(session_id)

        with self._storage.advisory_lock(lock_path):
            session_directory = self._storage.resolve(self._session_directory(session_id))
            if not session_directory.exists():
                raise CheckpointNotFoundError(
                    f"session checkpoint history not found: {session_id}"
                )
            self.history(session_id)

            archive_directory = self._storage.resolve(
                Path("archive") / session_id
            )
            if archive_directory.exists():
                raise CheckpointConflictError(
                    f"archive already exists for session: {session_id}"
                )
            archive_directory.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.move(str(session_directory), str(archive_directory))
            except OSError as exc:
                raise CheckpointRepositoryError(
                    f"cannot archive session: {session_id}"
                ) from exc
            return archive_directory

    def session_ids(self) -> tuple[str, ...]:
        sessions_root = self._storage.resolve("sessions")
        if not sessions_root.exists():
            return ()
        return tuple(
            sorted(
                entry.name
                for entry in sessions_root.iterdir()
                if entry.is_dir() and _SESSION_PATTERN.fullmatch(entry.name)
            )
        )

    def _sequences(self, session_id: str) -> tuple[int, ...]:
        self._validate_session_id(session_id)
        files = self._storage.list_files(
            self._session_directory(session_id),
            suffix=self._policy.checkpoint_suffix,
        )
        sequences: list[int] = []
        for path in files:
            match = _CHECKPOINT_FILENAME_PATTERN.fullmatch(path.name)
            if match is None:
                continue
            sequences.append(int(match.group("sequence")))

        sequences.sort()
        if sequences and sequences != list(range(1, sequences[-1] + 1)):
            raise CheckpointHistoryError(
                f"checkpoint sequence contains gaps for session {session_id}"
            )
        return tuple(sequences)

    def _write_index(self, session_id: str) -> None:
        summaries = self.history(session_id)
        document = {
            "format": "jarvis.executive.checkpoint-index",
            "format_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(
                timespec="microseconds"
            ).replace("+00:00", "Z"),
            "session_id": session_id,
            "checkpoints": [
                {
                    "checkpoint_id": item.checkpoint_id,
                    "checkpoint_sha256": item.checkpoint_sha256,
                    "created_at": item.created_at.isoformat(
                        timespec="microseconds"
                    ).replace("+00:00", "Z"),
                    "parent_checkpoint_sha256": item.parent_checkpoint_sha256,
                    "payload_sha256": item.payload_sha256,
                    "payload_size": item.payload_size,
                    "sequence": item.sequence,
                    "status": item.status.value,
                }
                for item in summaries
            ],
        }
        data = json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        self._storage.atomic_write_bytes(
            Path(self._session_directory(session_id)) / "index.json",
            data,
            replace=True,
        )

    @staticmethod
    def _verify_chain(checkpoints: tuple[ExecutiveCheckpoint, ...]) -> None:
        expected_parent = ZERO_DIGEST
        expected_sequence = 1
        for checkpoint in checkpoints:
            checkpoint.verify()
            if checkpoint.sequence != expected_sequence:
                raise CheckpointSequenceError(
                    f"expected sequence {expected_sequence}; "
                    f"got {checkpoint.sequence}"
                )
            if checkpoint.parent_checkpoint_sha256 != expected_parent:
                raise CheckpointHistoryError(
                    f"invalid parent linkage at {checkpoint.checkpoint_id}"
                )
            expected_parent = checkpoint.checkpoint_sha256
            expected_sequence += 1

    @staticmethod
    def _validate_session_id(session_id: str) -> None:
        if not isinstance(session_id, str) or not _SESSION_PATTERN.fullmatch(session_id):
            raise ValueError("invalid session_id")

    @staticmethod
    def _validate_sequence(sequence: int) -> None:
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
            raise ValueError("sequence must be a positive integer")

    @staticmethod
    def _session_directory(session_id: str) -> Path:
        return Path("sessions") / session_id

    @classmethod
    def _checkpoint_path(cls, session_id: str, sequence: int) -> Path:
        return cls._session_directory(session_id) / f"{sequence:08d}.chk"

    @staticmethod
    def _lock_path(session_id: str) -> Path:
        return Path("locks") / f"{session_id}.lock"
