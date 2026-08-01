from __future__ import annotations
from enum import Enum

REPOSITORY_PROJECTION_SCHEMA_VERSION = "1.0.0"

class RepositoryNodeKind(str, Enum):
    REPOSITORY = "repository"
    PACKAGE = "package"
    MODULE = "module"
    DOCUMENT = "document"
    TEST = "test"
    VERIFICATION = "verification"
    CONFIGURATION = "configuration"
    EXECUTABLE = "executable"
    DATA_ARTIFACT = "data_artifact"
    UNKNOWN = "unknown"

class RepositoryEdgeKind(str, Enum):
    CONTAINS = "contains"
    BELONGS_TO = "belongs_to"
    IMPLEMENTS = "implements"
    TESTS = "tests"
    VERIFIES = "verifies"
    CONFIGURES = "configures"
    PRODUCES = "produces"

class RepositoryLifecycleState(str, Enum):
    CERTIFIED = "certified"
    IMPLEMENTED = "implemented"
    DOCUMENTED = "documented"
    TESTED = "tested"
    CONFIGURED = "configured"
    DISCOVERED = "discovered"
    UNKNOWN = "unknown"
