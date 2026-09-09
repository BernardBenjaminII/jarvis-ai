from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ObjectRole(str, Enum):
    DOCUMENT = "DOCUMENT"
    DATASET = "DATASET"
    SOURCE_CODE = "SOURCE_CODE"
    WEB_ARCHIVE = "WEB_ARCHIVE"
    MEDIA = "MEDIA"
    METADATA = "METADATA"
    INTERNAL = "INTERNAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RouteDecision:
    role: ObjectRole
    handler: str
    admissible_to_text_pipeline: bool
    reason: str


DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
    ".markdown",
    ".rst",
    ".docx",
    ".epub",
}


SOURCE_CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".css",
    ".scss",
    ".sql",
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".c",
    ".h",
    ".hpp",
    ".cpp",
    ".cc",
    ".java",
    ".go",
    ".rs",
}


WEB_EXTENSIONS = {
    ".html",
    ".htm",
}


WEB_ARCHIVE_EXTENSIONS = {
    ".zim",
    ".warc",
    ".warc.gz",
}


STRUCTURED_DATA_EXTENSIONS = {
    ".csv",
    ".tsv",
    ".jsonl",
    ".parquet",
    ".feather",
    ".arrow",
    ".sqlite",
    ".sqlite3",
    ".db",
}


AMBIGUOUS_STRUCTURED_EXTENSIONS = {
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".toml",
}


GEOSPATIAL_EXTENSIONS = {
    ".tif",
    ".tiff",
    ".geotiff",
    ".shp",
    ".shx",
    ".dbf",
    ".prj",
    ".geojson",
    ".gpkg",
    ".kml",
    ".kmz",
    ".dem",
    ".hgt",
    ".asc",
}


MEDIA_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".bmp",
    ".svg",
    ".mp3",
    ".wav",
    ".flac",
    ".m4a",
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
}


ARCHIVE_EXTENSIONS = {
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
}


INTERNAL_NAMES = {
    ".DS_Store",
    "Thumbs.db",
}


INTERNAL_DIRS = {
    ".jarvis",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
}


DATASET_PATH_MARKERS = {
    "geodata",
    "dataset",
    "datasets",
    "elevation",
    "raster",
    "rasters",
    "vector",
    "vectors",
    "dem",
    "gis",
}


METADATA_NAME_MARKERS = {
    "metadata",
    "manifest",
    "catalog",
    "index",
    "schema",
}


def _parts_lower(path: Path) -> tuple[str, ...]:
    return tuple(part.casefold() for part in path.parts)


def _name_lower(path: Path) -> str:
    return path.name.casefold()


def _suffix(path: Path) -> str:
    name = _name_lower(path)

    if name.endswith(".warc.gz"):
        return ".warc.gz"

    return path.suffix.casefold()


def _looks_internal(path: Path) -> bool:
    if path.name in INTERNAL_NAMES:
        return True

    parts = set(_parts_lower(path))

    return bool(
        parts.intersection(
            {item.casefold() for item in INTERNAL_DIRS}
        )
    )


def _looks_dataset_path(path: Path) -> bool:
    parts = set(_parts_lower(path))

    return bool(
        parts.intersection(DATASET_PATH_MARKERS)
    )


def _looks_metadata_name(path: Path) -> bool:
    stem = path.stem.casefold()

    return any(
        marker in stem
        for marker in METADATA_NAME_MARKERS
    )


def _is_copernicus_metadata(path: Path) -> bool:
    name = _name_lower(path)
    parts = _parts_lower(path)

    return (
        path.suffix.casefold() == ".xml"
        and "copernicus_dsm" in name
        and (
            "elevation" in parts
            or "geodata" in parts
        )
    )


def route_object(path: Path) -> RouteDecision:
    """
    Determine the corpus role of a physical object.

    Pack 1A is intentionally conservative:

    - DOCUMENT may enter normal textual assimilation.
    - SOURCE_CODE is routed to a code-aware handler.
    - WEB_ARCHIVE uses a provider/archive handler.
    - DATASET is registered as data, not blindly chunked.
    - METADATA attaches to another object/dataset.
    - MEDIA requires a specialized handler.
    - INTERNAL is excluded.
    - UNKNOWN requires review.

    No database mutation occurs here.
    """

    suffix = _suffix(path)

    if _looks_internal(path):
        return RouteDecision(
            role=ObjectRole.INTERNAL,
            handler="exclude",
            admissible_to_text_pipeline=False,
            reason=(
                "System/internal object; excluded from "
                "knowledge assimilation."
            ),
        )

    # --------------------------------------------------------
    # Explicit geospatial metadata rule.
    # This addresses the Copernicus XML objects exposed by
    # Pack 1 without globally declaring all XML to be metadata.
    # --------------------------------------------------------

    if _is_copernicus_metadata(path):
        return RouteDecision(
            role=ObjectRole.METADATA,
            handler="dataset_metadata",
            admissible_to_text_pipeline=False,
            reason=(
                "Copernicus DSM XML is geospatial dataset "
                "metadata and should attach to its dataset, "
                "not enter ordinary document chunking."
            ),
        )

    # --------------------------------------------------------
    # Geospatial payloads
    # --------------------------------------------------------

    if suffix in GEOSPATIAL_EXTENSIONS:
        return RouteDecision(
            role=ObjectRole.DATASET,
            handler="geospatial_dataset",
            admissible_to_text_pipeline=False,
            reason=(
                "Geospatial data object; route to dataset/"
                "provider handling rather than text retrieval."
            ),
        )

    # --------------------------------------------------------
    # Web archives / offline knowledge providers
    # --------------------------------------------------------

    if suffix in WEB_ARCHIVE_EXTENSIONS:
        return RouteDecision(
            role=ObjectRole.WEB_ARCHIVE,
            handler="web_archive_provider",
            admissible_to_text_pipeline=False,
            reason=(
                "Offline/web archive should be exposed "
                "through an archive-aware provider."
            ),
        )

    # --------------------------------------------------------
    # Source code
    # --------------------------------------------------------

    if suffix in SOURCE_CODE_EXTENSIONS:
        return RouteDecision(
            role=ObjectRole.SOURCE_CODE,
            handler="source_code",
            admissible_to_text_pipeline=False,
            reason=(
                "Source code requires code-aware "
                "assimilation and chunking."
            ),
        )

    # --------------------------------------------------------
    # Strong document formats
    # --------------------------------------------------------

    if suffix in DOCUMENT_EXTENSIONS:
        return RouteDecision(
            role=ObjectRole.DOCUMENT,
            handler="document_text",
            admissible_to_text_pipeline=True,
            reason=(
                "Recognized standalone textual/document "
                "knowledge format."
            ),
        )

    # --------------------------------------------------------
    # HTML is textual knowledge, but remains explicitly routed.
    # --------------------------------------------------------

    if suffix in WEB_EXTENSIONS:
        return RouteDecision(
            role=ObjectRole.DOCUMENT,
            handler="html_document",
            admissible_to_text_pipeline=True,
            reason=(
                "HTML document is suitable for textual "
                "assimilation with HTML-aware extraction."
            ),
        )

    # --------------------------------------------------------
    # Structured datasets
    # --------------------------------------------------------

    if suffix in STRUCTURED_DATA_EXTENSIONS:
        return RouteDecision(
            role=ObjectRole.DATASET,
            handler="structured_dataset",
            admissible_to_text_pipeline=False,
            reason=(
                "Structured data should be registered as a "
                "dataset instead of blindly text-chunked."
            ),
        )

    # --------------------------------------------------------
    # Ambiguous structured formats.
    #
    # XML/JSON/YAML/TOML can be genuine documents, configs,
    # manifests, metadata, or datasets. Pack 1A refuses to
    # pretend extension alone answers that question.
    # --------------------------------------------------------

    if suffix in AMBIGUOUS_STRUCTURED_EXTENSIONS:
        if _looks_dataset_path(path):
            return RouteDecision(
                role=ObjectRole.METADATA,
                handler="dataset_metadata",
                admissible_to_text_pipeline=False,
                reason=(
                    "Structured object resides inside a "
                    "dataset/geospatial hierarchy; treat as "
                    "dataset metadata pending specialized "
                    "processing."
                ),
            )

        if _looks_metadata_name(path):
            return RouteDecision(
                role=ObjectRole.METADATA,
                handler="metadata",
                admissible_to_text_pipeline=False,
                reason=(
                    "Structured object name indicates "
                    "metadata/manifest/schema semantics."
                ),
            )

        return RouteDecision(
            role=ObjectRole.UNKNOWN,
            handler="review_structured",
            admissible_to_text_pipeline=False,
            reason=(
                "Structured format is semantically ambiguous; "
                "requires inspection before admission."
            ),
        )

    # --------------------------------------------------------
    # Media
    # --------------------------------------------------------

    if suffix in MEDIA_EXTENSIONS:
        return RouteDecision(
            role=ObjectRole.MEDIA,
            handler="media",
            admissible_to_text_pipeline=False,
            reason=(
                "Media object requires a specialized "
                "extraction/provider handler."
            ),
        )

    # --------------------------------------------------------
    # Generic archives
    # --------------------------------------------------------

    if suffix in ARCHIVE_EXTENSIONS:
        return RouteDecision(
            role=ObjectRole.UNKNOWN,
            handler="archive_review",
            admissible_to_text_pipeline=False,
            reason=(
                "Generic archive requires inspection before "
                "its contents can be assigned corpus roles."
            ),
        )

    return RouteDecision(
        role=ObjectRole.UNKNOWN,
        handler="review",
        admissible_to_text_pipeline=False,
        reason=(
            "No canonical AS1 object-role handler is "
            "assigned to this object yet."
        ),
    )
