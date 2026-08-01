from __future__ import annotations

from enum import Enum


REPOSITORY_AUDIT_SCHEMA_VERSION = "1.0.0"


class AuditArtifactStatus(str, Enum):
    COMPLIANT = "compliant"
    REVIEW_REQUIRED = "review_required"
    NONCOMPLIANT = "noncompliant"
    NOT_APPLICABLE = "not_applicable"


DEFAULT_INCLUDED_SUFFIXES = (
    ".md",
    ".markdown",
    ".txt",
    ".rst",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
)

OPTIONAL_SOURCE_SUFFIXES = (
    ".py",
    ".sh",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
)

DEFAULT_EXCLUDED_DIRECTORIES = (
    ".git",
    ".migration_backups",
    ".pytest_cache",
    ".mypy_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    "artifacts",
)
