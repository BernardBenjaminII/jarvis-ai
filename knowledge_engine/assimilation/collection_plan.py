"""
Read-only expansion planning for JARVIS source collections.

Phase VI-D2 inspects exactly one directory level. It does not:

- recurse into child directories
- create registry objects
- queue child objects
- modify source files
- execute child handlers
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from knowledge_engine.assimilation.dispatch import get_handler_spec


CURRENT_DOCUMENT_EXTENSIONS = {
    ".csv",
    ".htm",
    ".html",
    ".json",
    ".md",
    ".pdf",
    ".txt",
    ".xml",
}

IMAGE_EXTENSIONS = {
    ".avif",
    ".bmp",
    ".gif",
    ".heic",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}


@dataclass(frozen=True)
class CollectionChildPlan:
    """Read-only classification of one direct collection child."""

    sequence: int
    name: str
    path: str
    object_type: str
    entry_kind: str
    size_bytes: int | None

    handler_name: str
    handler_kind: str
    handler_readiness: str
    handler_executable: bool

    supported: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CollectionExpansionPlan:
    """Deterministic, read-only plan for one source collection."""

    object_uuid: str
    collection_path: str
    children: list[CollectionChildPlan] = field(default_factory=list)
    skipped_entries: list[dict[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def total_children(self) -> int:
        return len(self.children)

    @property
    def supported_children(self) -> int:
        return sum(child.supported for child in self.children)

    @property
    def unsupported_children(self) -> int:
        return self.total_children - self.supported_children

    @property
    def object_type_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}

        for child in self.children:
            counts[child.object_type] = (
                counts.get(child.object_type, 0) + 1
            )

        return dict(sorted(counts.items()))

    @property
    def handler_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}

        for child in self.children:
            counts[child.handler_name] = (
                counts.get(child.handler_name, 0) + 1
            )

        return dict(sorted(counts.items()))

    @property
    def fingerprint(self) -> str:
        """
        Stable fingerprint of the collection expansion plan.

        The fingerprint changes when the ordered direct-child inventory
        changes.
        """

        payload = {
            "object_uuid": self.object_uuid,
            "collection_path": self.collection_path,
            "children": [
                {
                    "sequence": child.sequence,
                    "name": child.name,
                    "path": child.path,
                    "object_type": child.object_type,
                    "entry_kind": child.entry_kind,
                    "size_bytes": child.size_bytes,
                    "handler_name": child.handler_name,
                }
                for child in self.children
            ],
            "skipped_entries": self.skipped_entries,
        }

        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_uuid": self.object_uuid,
            "collection_path": self.collection_path,
            "fingerprint": self.fingerprint,
            "summary": {
                "total_children": self.total_children,
                "supported_children": self.supported_children,
                "unsupported_children": self.unsupported_children,
                "skipped_entries": len(self.skipped_entries),
                "object_type_counts": self.object_type_counts,
                "handler_counts": self.handler_counts,
            },
            "warnings": list(self.warnings),
            "skipped_entries": list(self.skipped_entries),
            "children": [
                child.to_dict()
                for child in self.children
            ],
        }


class CollectionExpansionPlanner:
    """Create deterministic plans for direct collection children."""

    def plan(
        self,
        *,
        object_uuid: str,
        collection_path: str | Path,
    ) -> CollectionExpansionPlan:
        root = Path(collection_path).expanduser().resolve()

        if not root.exists():
            raise FileNotFoundError(
                f"Source collection does not exist: {root}"
            )

        if not root.is_dir():
            raise NotADirectoryError(
                f"Source collection is not a directory: {root}"
            )

        plan = CollectionExpansionPlan(
            object_uuid=object_uuid,
            collection_path=str(root),
        )

        entries = sorted(
            root.iterdir(),
            key=lambda entry: (
                entry.name.casefold(),
                entry.name,
            ),
        )

        sequence = 0

        for entry in entries:
            if entry.name.startswith("."):
                plan.skipped_entries.append(
                    {
                        "path": str(entry),
                        "reason": "hidden entry",
                    }
                )
                continue

            if entry.is_symlink():
                plan.skipped_entries.append(
                    {
                        "path": str(entry),
                        "reason": "symbolic link",
                    }
                )
                continue

            sequence += 1

            plan.children.append(
                self._classify_child(
                    sequence=sequence,
                    entry=entry,
                )
            )

        if not plan.children:
            plan.warnings.append(
                "The collection contains no eligible direct children."
            )

        if plan.unsupported_children:
            plan.warnings.append(
                f"{plan.unsupported_children} direct child object(s) "
                "do not yet have production assimilation handlers."
            )

        if plan.skipped_entries:
            plan.warnings.append(
                f"{len(plan.skipped_entries)} hidden or linked "
                "entry/entries were skipped."
            )

        return plan

    @staticmethod
    def _classify_child(
        *,
        sequence: int,
        entry: Path,
    ) -> CollectionChildPlan:
        if entry.is_dir():
            object_type = "folder_collection"
            entry_kind = "directory"
            size_bytes = None
            reason = (
                "Direct child directory recognized; recursive expansion "
                "is deferred to Phase VI-E."
            )

        elif entry.is_file():
            entry_kind = "file"

            try:
                size_bytes = entry.stat().st_size
            except OSError:
                size_bytes = None

            extension = entry.suffix.lower()

            if extension in CURRENT_DOCUMENT_EXTENSIONS:
                object_type = "single_document"
                reason = (
                    "Supported by the current failure-safe document handler."
                )

            elif extension in IMAGE_EXTENSIONS:
                object_type = "single_image"
                reason = (
                    "Recognized image; image assimilation remains planned."
                )

            else:
                object_type = "single_file"
                reason = (
                    "Generic file classification; specialized routing "
                    "remains planned."
                )

        else:
            object_type = "single_file"
            entry_kind = "other"
            size_bytes = None
            reason = "Filesystem entry is neither a regular file nor directory."

        spec = get_handler_spec(object_type)

        supported = spec.readiness.value != "unsupported"

        return CollectionChildPlan(
            sequence=sequence,
            name=entry.name,
            path=str(entry.resolve()),
            object_type=object_type,
            entry_kind=entry_kind,
            size_bytes=size_bytes,
            handler_name=spec.handler_name,
            handler_kind=spec.handler_kind,
            handler_readiness=spec.readiness.value,
            handler_executable=spec.executable,
            supported=supported,
            reason=reason,
        )
