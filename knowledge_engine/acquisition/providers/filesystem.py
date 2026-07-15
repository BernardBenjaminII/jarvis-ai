"""
Read-only filesystem acquisition provider.

The provider discovers regular local files and produces immutable source
candidates. It never modifies, moves, deletes, or assimilates source files.
"""

from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path

from knowledge_engine.acquisition.models import (
    AcquisitionPlan,
    AcquisitionRequest,
    SourceCandidate,
)
from knowledge_engine.acquisition.providers.base import (
    AcquisitionProvider,
)


DOCUMENT_EXTENSIONS = {
    ".csv",
    ".epub",
    ".htm",
    ".html",
    ".json",
    ".md",
    ".pdf",
    ".rst",
    ".rtf",
    ".tex",
    ".tsv",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

IMAGE_EXTENSIONS = {
    ".bmp",
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}

SOURCE_CODE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".kt",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".sql",
    ".swift",
    ".ts",
}


class FilesystemAcquisitionProvider(AcquisitionProvider):
    """Discover deterministic local-file candidates."""

    provider_id = "filesystem"

    def discover(
        self,
        *,
        request: AcquisitionRequest,
    ) -> AcquisitionPlan:
        paths: dict[str, Path] = {}
        skipped_count = 0

        resolved_roots = tuple(
            sorted({
                str(
                    Path(root)
                    .expanduser()
                    .resolve()
                )
                for root in request.roots
            })
        )

        for root_text in resolved_roots:
            root = Path(root_text)

            if not root.exists():
                skipped_count += 1
                continue

            if root.is_file():
                candidates = (root,)
            elif root.is_dir():
                iterator = (
                    root.rglob("*")
                    if request.recursive
                    else root.glob("*")
                )

                candidates = tuple(iterator)
            else:
                skipped_count += 1
                continue

            for path in candidates:
                try:
                    if path.is_symlink() and not request.follow_symlinks:
                        skipped_count += 1
                        continue

                    if not path.is_file():
                        continue

                    resolved = path.resolve()

                    if (
                        not request.include_hidden
                        and self._is_hidden(
                            resolved,
                            root=root,
                        )
                    ):
                        skipped_count += 1
                        continue

                    extension = resolved.suffix.lower()

                    if (
                        request.allowed_extensions
                        and extension
                        not in request.allowed_extensions
                    ):
                        skipped_count += 1
                        continue

                    paths[str(resolved)] = resolved

                except OSError:
                    skipped_count += 1

        ordered_paths = [
            paths[path]
            for path in sorted(paths)
        ]

        truncated = (
            len(ordered_paths)
            > request.max_files
        )

        ordered_paths = ordered_paths[
            :request.max_files
        ]

        candidates = tuple(
            self._candidate(path)
            for path in ordered_paths
        )

        return AcquisitionPlan(
            request_id=request.request_id,
            provider_id=self.provider_id,
            candidates=candidates,
            roots_scanned=resolved_roots,
            skipped_count=skipped_count,
            truncated=truncated,
        )

    @staticmethod
    def _is_hidden(
        path: Path,
        *,
        root: Path,
    ) -> bool:
        try:
            relative = path.relative_to(
                root if root.is_dir() else root.parent
            )
        except ValueError:
            relative = path

        return any(
            part.startswith(".")
            for part in relative.parts
            if part not in {
                ".",
                "..",
            }
        )

    def _candidate(
        self,
        path: Path,
    ) -> SourceCandidate:
        extension = path.suffix.lower()

        media_type = (
            mimetypes.guess_type(path.name)[0]
            or "application/octet-stream"
        )

        return SourceCandidate(
            provider_id=self.provider_id,
            source_uri=path.as_uri(),
            local_path=str(path),
            filename=path.name,
            extension=extension,
            media_type=media_type,
            candidate_type=self._candidate_type(
                extension
            ),
            size_bytes=path.stat().st_size,
            checksum_sha256=self._checksum(path),
        )

    @staticmethod
    def _candidate_type(
        extension: str,
    ) -> str:
        if extension in DOCUMENT_EXTENSIONS:
            return "document"

        if extension in IMAGE_EXTENSIONS:
            return "image"

        if extension in SOURCE_CODE_EXTENSIONS:
            return "source_code"

        return "generic_file"

    @staticmethod
    def _checksum(
        path: Path,
    ) -> str:
        digest = hashlib.sha256()

        with path.open("rb") as stream:
            while True:
                block = stream.read(
                    1024 * 1024
                )

                if not block:
                    break

                digest.update(block)

        return digest.hexdigest()
