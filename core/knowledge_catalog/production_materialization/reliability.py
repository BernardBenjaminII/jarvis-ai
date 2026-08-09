from __future__ import annotations

import random
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, TypeVar


T = TypeVar("T")


TRANSIENT_LOCK_MARKERS = (
    "database is locked",
    "database table is locked",
    "database schema is locked",
    "busy",
)


def is_transient_lock_error(exc: BaseException) -> bool:
    if not isinstance(exc, sqlite3.OperationalError):
        return False

    message = str(exc).casefold()
    return any(marker in message for marker in TRANSIENT_LOCK_MARKERS)


@dataclass(frozen=True, slots=True)
class SQLiteReliabilityPolicy:
    connect_timeout_seconds: float = 30.0
    busy_timeout_ms: int = 30_000
    retry_attempts: int = 6
    initial_backoff_seconds: float = 0.10
    maximum_backoff_seconds: float = 5.0
    jitter_fraction: float = 0.10
    journal_mode: str = "WAL"
    synchronous: str = "NORMAL"

    def validate(self) -> "SQLiteReliabilityPolicy":
        if self.connect_timeout_seconds <= 0:
            raise ValueError("connect_timeout_seconds must be positive")
        if self.busy_timeout_ms < 0:
            raise ValueError("busy_timeout_ms cannot be negative")
        if self.retry_attempts < 1:
            raise ValueError("retry_attempts must be at least one")
        if self.initial_backoff_seconds < 0:
            raise ValueError("initial_backoff_seconds cannot be negative")
        if self.maximum_backoff_seconds < self.initial_backoff_seconds:
            raise ValueError("maximum_backoff_seconds is too small")
        if not 0.0 <= self.jitter_fraction <= 1.0:
            raise ValueError("jitter_fraction must be between zero and one")
        return self


class ReliableSQLite:
    def __init__(
        self,
        database_path: Path,
        policy: SQLiteReliabilityPolicy,
    ) -> None:
        self.database_path = Path(database_path)
        self.policy = policy.validate()

    def connect(
        self,
        *,
        read_only: bool = False,
    ) -> sqlite3.Connection:
        if read_only:
            connection = sqlite3.connect(
                f"file:{self.database_path.resolve()}?mode=ro",
                uri=True,
                timeout=self.policy.connect_timeout_seconds,
            )
        else:
            connection = sqlite3.connect(
                self.database_path,
                timeout=self.policy.connect_timeout_seconds,
            )

        connection.row_factory = sqlite3.Row
        connection.execute(
            f"PRAGMA busy_timeout={int(self.policy.busy_timeout_ms)}"
        )
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def configure_runtime_database(self) -> dict[str, str | int]:
        connection = self.connect()
        try:
            journal_mode = str(
                connection.execute(
                    f"PRAGMA journal_mode={self.policy.journal_mode}"
                ).fetchone()[0]
            )
            connection.execute(
                f"PRAGMA synchronous={self.policy.synchronous}"
            )
            connection.commit()

            busy_timeout = int(
                connection.execute("PRAGMA busy_timeout").fetchone()[0]
            )
            synchronous = int(
                connection.execute("PRAGMA synchronous").fetchone()[0]
            )

            return {
                "journal_mode": journal_mode,
                "busy_timeout_ms": busy_timeout,
                "synchronous": synchronous,
            }
        finally:
            connection.close()

    def run_with_retry(
        self,
        operation: Callable[[], T],
        *,
        on_retry: Callable[[int, float, BaseException], None] | None = None,
    ) -> T:
        last_error: BaseException | None = None

        for attempt in range(1, self.policy.retry_attempts + 1):
            try:
                return operation()
            except BaseException as exc:
                if not is_transient_lock_error(exc):
                    raise

                last_error = exc

                if attempt >= self.policy.retry_attempts:
                    raise

                base_delay = min(
                    self.policy.maximum_backoff_seconds,
                    self.policy.initial_backoff_seconds * (2 ** (attempt - 1)),
                )
                jitter = base_delay * self.policy.jitter_fraction
                delay = max(
                    0.0,
                    base_delay + random.uniform(-jitter, jitter),
                )

                if on_retry is not None:
                    on_retry(attempt, delay, exc)

                time.sleep(delay)

        assert last_error is not None
        raise last_error
