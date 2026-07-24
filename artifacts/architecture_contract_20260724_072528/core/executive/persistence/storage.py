"""Reliable filesystem primitives for executive persistence.

The storage layer knows nothing about executive sessions or checkpoints.
It provides deterministic paths, atomic replacement, bounded reads, and
cross-process advisory locking without introducing a database dependency.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import os
import tempfile
import time
from typing import Iterator


class StorageError(RuntimeError):
    """Base error for persistence storage failures."""


class StoragePathError(StorageError):
    """Raised when a requested path escapes the configured storage root."""


class StorageLockTimeoutError(StorageError):
    """Raised when an advisory lock cannot be acquired before its deadline."""


class StorageSizeLimitError(StorageError):
    """Raised when a file exceeds the configured maximum readable size."""


@dataclass(frozen=True, slots=True)
class StoragePolicy:
    """Filesystem safety and durability policy."""

    file_mode: int = 0o600
    directory_mode: int = 0o700
    lock_timeout_seconds: float = 10.0
    lock_poll_interval_seconds: float = 0.05
    maximum_read_bytes: int = 256 * 1024 * 1024
    fsync_directory: bool = True

    def __post_init__(self) -> None:
        if self.lock_timeout_seconds <= 0:
            raise ValueError("lock_timeout_seconds must be positive")
        if self.lock_poll_interval_seconds <= 0:
            raise ValueError("lock_poll_interval_seconds must be positive")
        if self.maximum_read_bytes <= 0:
            raise ValueError("maximum_read_bytes must be positive")


class AtomicFileStorage:
    """Atomic, root-confined binary file storage."""

    def __init__(
        self,
        root: str | os.PathLike[str],
        *,
        policy: StoragePolicy | None = None,
    ) -> None:
        self._root = Path(root).expanduser().resolve()
        self._policy = policy or StoragePolicy()
        self._root.mkdir(parents=True, exist_ok=True, mode=self._policy.directory_mode)

    @property
    def root(self) -> Path:
        return self._root

    @property
    def policy(self) -> StoragePolicy:
        return self._policy

    def resolve(self, relative_path: str | os.PathLike[str]) -> Path:
        candidate = (self._root / Path(relative_path)).resolve()
        try:
            candidate.relative_to(self._root)
        except ValueError as exc:
            raise StoragePathError(
                f"path escapes storage root: {relative_path!s}"
            ) from exc
        return candidate

    def exists(self, relative_path: str | os.PathLike[str]) -> bool:
        return self.resolve(relative_path).is_file()

    def read_bytes(self, relative_path: str | os.PathLike[str]) -> bytes:
        path = self.resolve(relative_path)
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            raise
        except OSError as exc:
            raise StorageError(f"cannot stat {path}") from exc

        if size > self._policy.maximum_read_bytes:
            raise StorageSizeLimitError(
                f"{path} is {size} bytes; limit is "
                f"{self._policy.maximum_read_bytes} bytes"
            )

        try:
            return path.read_bytes()
        except OSError as exc:
            raise StorageError(f"cannot read {path}") from exc

    def atomic_write_bytes(
        self,
        relative_path: str | os.PathLike[str],
        data: bytes,
        *,
        replace: bool = False,
    ) -> Path:
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")

        destination = self.resolve(relative_path)
        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
            mode=self._policy.directory_mode,
        )

        if destination.exists() and not replace:
            raise FileExistsError(destination)

        temporary_path: Path | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{destination.name}.",
                suffix=".tmp",
                dir=destination.parent,
            )
            temporary_path = Path(temporary_name)

            with os.fdopen(descriptor, "wb", closefd=True) as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())

            os.chmod(temporary_path, self._policy.file_mode)

            if destination.exists() and not replace:
                raise FileExistsError(destination)

            os.replace(temporary_path, destination)
            temporary_path = None

            if self._policy.fsync_directory:
                self._fsync_directory(destination.parent)

            return destination
        except (FileExistsError, StorageError):
            raise
        except OSError as exc:
            raise StorageError(f"cannot atomically write {destination}") from exc
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def unlink(self, relative_path: str | os.PathLike[str]) -> None:
        path = self.resolve(relative_path)
        try:
            path.unlink()
            if self._policy.fsync_directory:
                self._fsync_directory(path.parent)
        except FileNotFoundError:
            raise
        except OSError as exc:
            raise StorageError(f"cannot remove {path}") from exc

    def list_files(
        self,
        relative_directory: str | os.PathLike[str] = ".",
        *,
        suffix: str | None = None,
    ) -> tuple[Path, ...]:
        directory = self.resolve(relative_directory)
        if not directory.exists():
            return ()
        if not directory.is_dir():
            raise StorageError(f"not a directory: {directory}")

        files = [
            item
            for item in directory.iterdir()
            if item.is_file() and (suffix is None or item.name.endswith(suffix))
        ]
        return tuple(sorted(files, key=lambda item: item.name))

    @contextmanager
    def advisory_lock(
        self,
        relative_path: str | os.PathLike[str],
    ) -> Iterator[Path]:
        """Acquire a portable exclusive lock using atomic file creation."""

        lock_path = self.resolve(relative_path)
        lock_path.parent.mkdir(
            parents=True,
            exist_ok=True,
            mode=self._policy.directory_mode,
        )
        deadline = time.monotonic() + self._policy.lock_timeout_seconds
        descriptor: int | None = None

        while descriptor is None:
            try:
                descriptor = os.open(
                    lock_path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    self._policy.file_mode,
                )
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise StorageLockTimeoutError(
                        f"timed out acquiring lock: {lock_path}"
                    )
                time.sleep(self._policy.lock_poll_interval_seconds)
            except OSError as exc:
                raise StorageError(f"cannot acquire lock: {lock_path}") from exc

        try:
            lock_record = (
                f"pid={os.getpid()}\n"
                f"created_ns={time.time_ns()}\n"
            ).encode("ascii")
            os.write(descriptor, lock_record)
            os.fsync(descriptor)
            yield lock_path
        finally:
            if descriptor is not None:
                os.close(descriptor)
            try:
                lock_path.unlink(missing_ok=True)
            except OSError as exc:
                raise StorageError(f"cannot release lock: {lock_path}") from exc

    @staticmethod
    def _fsync_directory(directory: Path) -> None:
        if os.name == "nt":
            return
        try:
            descriptor = os.open(directory, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
