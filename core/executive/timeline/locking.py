"""Portable interprocess locking for the Executive Timeline repository."""
from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import time
from typing import Iterator

from .repository_contracts import TimelineRepositoryStorageError


class TimelineInterprocessLock:
    """Exclusive lock backed by a repository-local lock file."""

    def __init__(
        self,
        path: str | Path,
        *,
        timeout_seconds: float = 30.0,
        poll_interval_seconds: float = 0.05,
    ) -> None:
        self.path = Path(path).expanduser().resolve()
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds

    @contextmanager
    def acquire(self) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+b")
        started = time.monotonic()

        try:
            while True:
                try:
                    self._lock(handle)
                    break
                except (BlockingIOError, OSError) as exc:
                    if time.monotonic() - started >= self.timeout_seconds:
                        raise TimelineRepositoryStorageError(
                            "Timed out acquiring Executive Timeline lock: "
                            f"{self.path}"
                        ) from exc
                    time.sleep(self.poll_interval_seconds)

            yield
        finally:
            try:
                self._unlock(handle)
            finally:
                handle.close()

    @staticmethod
    def _lock(handle) -> None:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            return

        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    @staticmethod
    def _unlock(handle) -> None:
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
            return

        import fcntl

        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
