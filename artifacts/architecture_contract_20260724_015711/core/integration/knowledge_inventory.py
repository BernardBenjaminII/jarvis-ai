"""Read-only inventory service for the JARVIS knowledge estate."""

from __future__ import annotations

import hashlib
import os
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_KNOWLEDGE_ROOT = Path("/media/abdullah/JARVISDATA/Knowledge")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class KnowledgeInventoryConfig:
    root: Path
    ttl_seconds: float = 30.0
    max_files: int = 250_000

    @classmethod
    def from_environment(cls) -> "KnowledgeInventoryConfig":
        root = Path(
            os.getenv(
                "JARVIS_KNOWLEDGE_ROOT",
                str(DEFAULT_KNOWLEDGE_ROOT),
            )
        ).expanduser()

        ttl_raw = os.getenv(
            "JARVIS_KNOWLEDGE_PROJECTION_TTL_SECONDS",
            "30",
        )
        max_files_raw = os.getenv(
            "JARVIS_KNOWLEDGE_SCAN_MAX_FILES",
            "250000",
        )

        try:
            ttl_seconds = max(0.0, float(ttl_raw))
        except ValueError:
            ttl_seconds = 30.0

        try:
            max_files = max(1, int(max_files_raw))
        except ValueError:
            max_files = 250_000

        return cls(
            root=root,
            ttl_seconds=ttl_seconds,
            max_files=max_files,
        )


class KnowledgeInventoryService:
    """Build and cache a deterministic, read-only knowledge inventory."""

    def __init__(
        self,
        config: KnowledgeInventoryConfig | None = None,
    ) -> None:
        self.config = config or KnowledgeInventoryConfig.from_environment()
        self._lock = threading.RLock()
        self._cached_at_monotonic: float | None = None
        self._cached_inventory: dict[str, Any] | None = None

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'

    @staticmethod
    def _database_files(root: Path) -> list[Path]:
        candidates: set[Path] = set()

        for pattern in ("*.sqlite", "*.sqlite3", "*.db"):
            candidates.update(
                path
                for path in root.glob(pattern)
                if path.is_file()
            )

        return sorted(candidates, key=lambda path: path.name.lower())

    def _inspect_database(self, path: Path) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": path.name,
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "tables": [],
            "table_count": 0,
            "total_rows": 0,
            "status": "available",
            "warnings": [],
            "errors": [],
        }

        uri = f"file:{path.resolve()}?mode=ro"

        try:
            with sqlite3.connect(
                uri,
                uri=True,
                timeout=2.0,
            ) as connection:
                rows = connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                      AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                    """
                ).fetchall()

                for (table_name,) in rows:
                    quoted = self._quote_identifier(str(table_name))
                    table_result = {
                        "name": str(table_name),
                        "row_count": None,
                        "status": "available",
                        "error": None,
                    }

                    try:
                        row_count = int(
                            connection.execute(
                                f"SELECT COUNT(*) FROM {quoted}"
                            ).fetchone()[0]
                        )
                        table_result["row_count"] = row_count
                        result["total_rows"] += row_count
                    except sqlite3.DatabaseError as exc:
                        table_result["status"] = "degraded"
                        table_result["error"] = str(exc)
                        result["warnings"].append(
                            f"{table_name}: {exc}"
                        )

                    result["tables"].append(table_result)

                result["table_count"] = len(result["tables"])

                if result["warnings"]:
                    result["status"] = "degraded"

        except (OSError, sqlite3.DatabaseError) as exc:
            result["status"] = "unavailable"
            result["errors"].append(str(exc))

        return result

    def _scan_filesystem(self, root: Path) -> dict[str, Any]:
        total_files = 0
        total_directories = 0
        total_bytes = 0
        truncated = False
        extension_counts: dict[str, int] = {}
        top_level: dict[str, dict[str, int]] = {}

        stack: list[tuple[Path, str]] = []

        try:
            entries = sorted(
                root.iterdir(),
                key=lambda item: item.name.lower(),
            )
        except OSError as exc:
            return {
                "total_files": 0,
                "total_directories": 0,
                "total_bytes": 0,
                "scan_truncated": False,
                "extensions": {},
                "top_level": [],
                "errors": [str(exc)],
            }

        for entry in entries:
            label = entry.name
            top_level[label] = {
                "files": 0,
                "directories": 0,
                "bytes": 0,
            }
            stack.append((entry, label))

        errors: list[str] = []

        while stack:
            path, label = stack.pop()

            try:
                if path.is_symlink():
                    continue

                if path.is_dir():
                    total_directories += 1
                    top_level[label]["directories"] += 1

                    for child in path.iterdir():
                        stack.append((child, label))
                    continue

                if not path.is_file():
                    continue

                total_files += 1
                top_level[label]["files"] += 1

                size = path.stat().st_size
                total_bytes += size
                top_level[label]["bytes"] += size

                extension = path.suffix.lower() or "[no extension]"
                extension_counts[extension] = (
                    extension_counts.get(extension, 0) + 1
                )

                if total_files >= self.config.max_files:
                    truncated = bool(stack)
                    break

            except OSError as exc:
                errors.append(f"{path}: {exc}")

        return {
            "total_files": total_files,
            "total_directories": total_directories,
            "total_bytes": total_bytes,
            "scan_truncated": truncated,
            "max_files": self.config.max_files,
            "extensions": dict(
                sorted(
                    extension_counts.items(),
                    key=lambda item: (-item[1], item[0]),
                )[:50]
            ),
            "top_level": [
                {
                    "name": name,
                    **metrics,
                }
                for name, metrics in sorted(
                    top_level.items(),
                    key=lambda item: (
                        -item[1]["bytes"],
                        item[0].lower(),
                    ),
                )
            ],
            "errors": errors,
        }

    @staticmethod
    def _fingerprint(payload: dict[str, Any]) -> str:
        stable_parts = [
            str(payload.get("root")),
            str(payload.get("database_count")),
            str(payload.get("database_total_rows")),
            str(payload.get("filesystem", {}).get("total_files")),
            str(payload.get("filesystem", {}).get("total_bytes")),
        ]

        for database in payload.get("databases", []):
            stable_parts.extend(
                [
                    str(database.get("name")),
                    str(database.get("size_bytes")),
                    str(database.get("table_count")),
                    str(database.get("total_rows")),
                    str(database.get("status")),
                ]
            )

        return hashlib.sha256(
            "|".join(stable_parts).encode("utf-8")
        ).hexdigest()

    def _build_inventory(self) -> dict[str, Any]:
        captured_at = utc_now()
        root = self.config.root

        if not root.exists():
            return {
                "root": str(root),
                "root_exists": False,
                "root_readable": False,
                "captured_at": iso_z(captured_at),
                "database_count": 0,
                "database_total_rows": 0,
                "databases": [],
                "filesystem": {
                    "total_files": 0,
                    "total_directories": 0,
                    "total_bytes": 0,
                    "scan_truncated": False,
                    "extensions": {},
                    "top_level": [],
                    "errors": [],
                },
                "warnings": [],
                "errors": [
                    f"Knowledge root does not exist: {root}"
                ],
                "fingerprint": None,
            }

        readable = os.access(root, os.R_OK)
        database_results = [
            self._inspect_database(path)
            for path in self._database_files(root)
        ]
        filesystem = self._scan_filesystem(root)

        warnings: list[str] = []
        errors: list[str] = list(filesystem.get("errors", []))

        for database in database_results:
            warnings.extend(
                f"{database['name']}: {warning}"
                for warning in database["warnings"]
            )
            errors.extend(
                f"{database['name']}: {error}"
                for error in database["errors"]
            )

        if filesystem.get("scan_truncated"):
            warnings.append(
                "Filesystem scan reached the configured file limit."
            )

        payload: dict[str, Any] = {
            "root": str(root),
            "root_exists": True,
            "root_readable": readable,
            "captured_at": iso_z(captured_at),
            "database_count": len(database_results),
            "database_total_rows": sum(
                int(database.get("total_rows", 0))
                for database in database_results
            ),
            "databases": database_results,
            "filesystem": filesystem,
            "warnings": warnings,
            "errors": errors,
        }
        payload["fingerprint"] = self._fingerprint(payload)
        return payload

    def inventory(self, *, force_refresh: bool = False) -> dict[str, Any]:
        now = time.monotonic()

        with self._lock:
            cache_is_fresh = (
                self._cached_inventory is not None
                and self._cached_at_monotonic is not None
                and (
                    now - self._cached_at_monotonic
                    < self.config.ttl_seconds
                )
            )

            if cache_is_fresh and not force_refresh:
                return dict(self._cached_inventory)

            inventory = self._build_inventory()
            self._cached_inventory = inventory
            self._cached_at_monotonic = now
            return dict(inventory)

    def invalidate(self) -> None:
        with self._lock:
            self._cached_inventory = None
            self._cached_at_monotonic = None
