"""
Object-type dispatch registry for JARVIS controlled assimilation.

The dispatch registry describes which handler owns each knowledge object type.
Phase VI-A2 uses this information for planning only. Handler readiness controls
whether an object may eventually be executed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class HandlerReadiness(str, Enum):
    """Current implementation readiness of an assimilation handler."""

    AVAILABLE = "available"
    PLANNED = "planned"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class AssimilationHandlerSpec:
    """Dispatch metadata for one registered knowledge object type."""

    object_type: str
    handler_name: str
    handler_kind: str
    readiness: HandlerReadiness
    description: str
    executable_in_phase_vi_a2: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["readiness"] = self.readiness.value
        return payload


_HANDLER_SPECS: dict[str, AssimilationHandlerSpec] = {
    "single_document": AssimilationHandlerSpec(
        object_type="single_document",
        handler_name="document_assimilation",
        handler_kind="document",
        readiness=HandlerReadiness.AVAILABLE,
        description=(
            "Extract text, calculate checksums, create chunks, and update "
            "document assimilation state."
        ),
        executable_in_phase_vi_a2=False,
    ),
    "source_collection": AssimilationHandlerSpec(
        object_type="source_collection",
        handler_name="collection_expansion",
        handler_kind="collection",
        readiness=HandlerReadiness.PLANNED,
        description=(
            "Inspect a source collection and register its individual child "
            "knowledge objects."
        ),
    ),
    "folder_collection": AssimilationHandlerSpec(
        object_type="folder_collection",
        handler_name="folder_expansion",
        handler_kind="collection",
        readiness=HandlerReadiness.PLANNED,
        description=(
            "Traverse a folder collection and register supported child "
            "knowledge objects."
        ),
    ),
    "academic_or_code_project": AssimilationHandlerSpec(
        object_type="academic_or_code_project",
        handler_name="project_assimilation",
        handler_kind="project",
        readiness=HandlerReadiness.PLANNED,
        description=(
            "Analyze a structured academic or software project while "
            "preserving its file relationships."
        ),
    ),
    "single_image": AssimilationHandlerSpec(
        object_type="single_image",
        handler_name="image_assimilation",
        handler_kind="image",
        readiness=HandlerReadiness.PLANNED,
        description=(
            "Extract image metadata and later dispatch visual interpretation "
            "to a vision-capable specialist."
        ),
    ),
    "web_or_html_collection": AssimilationHandlerSpec(
        object_type="web_or_html_collection",
        handler_name="web_assimilation",
        handler_kind="web",
        readiness=HandlerReadiness.PLANNED,
        description=(
            "Process HTML and web-resource collections while preserving links "
            "and source provenance."
        ),
    ),
    "website_archive": AssimilationHandlerSpec(
        object_type="website_archive",
        handler_name="website_archive_assimilation",
        handler_kind="web",
        readiness=HandlerReadiness.PLANNED,
        description=(
            "Expand and analyze an offline website archive as a structured "
            "web knowledge source."
        ),
    ),
    "single_file": AssimilationHandlerSpec(
        object_type="single_file",
        handler_name="generic_file_assimilation",
        handler_kind="generic",
        readiness=HandlerReadiness.PLANNED,
        description=(
            "Classify a generic file and route it to a more specific handler."
        ),
    ),
}


def get_handler_spec(object_type: str) -> AssimilationHandlerSpec:
    """
    Return the handler specification for an object type.

    Unknown object types receive an explicit unsupported specification rather
    than being silently ignored.
    """

    normalized = str(object_type).strip()

    spec = _HANDLER_SPECS.get(normalized)
    if spec is not None:
        return spec

    return AssimilationHandlerSpec(
        object_type=normalized or "<empty>",
        handler_name="unsupported_object_handler",
        handler_kind="unsupported",
        readiness=HandlerReadiness.UNSUPPORTED,
        description="No assimilation handler has been registered.",
        executable_in_phase_vi_a2=False,
    )


def registered_handler_specs() -> tuple[AssimilationHandlerSpec, ...]:
    """Return all explicitly registered handler specifications."""

    return tuple(
        _HANDLER_SPECS[key]
        for key in sorted(_HANDLER_SPECS)
    )
