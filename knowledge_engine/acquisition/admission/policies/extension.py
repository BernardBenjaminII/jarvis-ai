"""
File-extension admission policy.

Approved knowledge-bearing formats are accepted.
Known executable or unsafe binary formats are rejected.
Unclassified extensions require review.
"""

from __future__ import annotations

from collections.abc import Iterable

from knowledge_engine.acquisition.admission.models import (
    AdmissionAction,
    AdmissionContext,
    PolicyEvaluation,
)
from knowledge_engine.acquisition.admission.policies.base import (
    AdmissionPolicy,
)
from knowledge_engine.acquisition.models import (
    SourceCandidate,
)


DEFAULT_ACCEPTED_EXTENSIONS = frozenset({
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".csv",
    ".doc",
    ".docx",
    ".epub",
    ".go",
    ".h",
    ".hpp",
    ".htm",
    ".html",
    ".java",
    ".jpeg",
    ".jpg",
    ".js",
    ".json",
    ".kml",
    ".kt",
    ".md",
    ".odt",
    ".pdf",
    ".php",
    ".png",
    ".py",
    ".rb",
    ".rs",
    ".rst",
    ".rtf",
    ".sh",
    ".sql",
    ".swift",
    ".tex",
    ".tif",
    ".tiff",
    ".ts",
    ".tsv",
    ".txt",
    ".webp",
    ".xml",
    ".yaml",
    ".yml",
    ".zim",
})

DEFAULT_REJECTED_EXTENSIONS = frozenset({
    ".appimage",
    ".bat",
    ".cmd",
    ".com",
    ".dll",
    ".dmg",
    ".exe",
    ".iso",
    ".msi",
    ".scr",
    ".so",
})


def _normalize_extensions(
    extensions: Iterable[str],
) -> frozenset[str]:
    normalized: set[str] = set()

    for extension in extensions:
        value = extension.strip().lower()

        if not value:
            raise ValueError(
                "extensions must not contain blank values"
            )

        if not value.startswith("."):
            value = f".{value}"

        normalized.add(value)

    return frozenset(normalized)


class ExtensionAdmissionPolicy(AdmissionPolicy):
    """Evaluate candidate admission using its normalized extension."""

    policy_id = "extension"
    priority = 20

    def __init__(
        self,
        *,
        accepted_extensions: Iterable[str] = (
            DEFAULT_ACCEPTED_EXTENSIONS
        ),
        rejected_extensions: Iterable[str] = (
            DEFAULT_REJECTED_EXTENSIONS
        ),
    ):
        self.accepted_extensions = _normalize_extensions(
            accepted_extensions
        )

        self.rejected_extensions = _normalize_extensions(
            rejected_extensions
        )

        overlap = (
            self.accepted_extensions
            & self.rejected_extensions
        )

        if overlap:
            raise ValueError(
                "Extensions cannot be both accepted and rejected: "
                + ", ".join(sorted(overlap))
            )

    def evaluate(
        self,
        *,
        candidate: SourceCandidate,
        context: AdmissionContext,
    ) -> PolicyEvaluation:
        del context

        extension = candidate.extension.strip().lower()

        if extension and not extension.startswith("."):
            extension = f".{extension}"

        if extension in self.rejected_extensions:
            return PolicyEvaluation(
                policy_id=self.policy_id,
                priority=self.priority,
                action=AdmissionAction.REJECT,
                reason_code="rejected_extension",
                message=(
                    f"Extension {extension!r} is prohibited by the "
                    "admission policy."
                ),
                details={
                    "extension": extension,
                    "classification": "rejected",
                },
            )

        if extension in self.accepted_extensions:
            return PolicyEvaluation(
                policy_id=self.policy_id,
                priority=self.priority,
                action=AdmissionAction.ACCEPT,
                reason_code="accepted_extension",
                message=(
                    f"Extension {extension!r} is an approved "
                    "knowledge format."
                ),
                details={
                    "extension": extension,
                    "classification": "accepted",
                },
            )

        return PolicyEvaluation(
            policy_id=self.policy_id,
            priority=self.priority,
            action=AdmissionAction.REVIEW,
            reason_code="unknown_extension",
            message=(
                f"Extension {extension!r} is not yet classified and "
                "requires review."
            ),
            details={
                "extension": extension,
                "classification": "unknown",
            },
        )


__all__ = [
    "DEFAULT_ACCEPTED_EXTENSIONS",
    "DEFAULT_REJECTED_EXTENSIONS",
    "ExtensionAdmissionPolicy",
]
