"""Public API for the JARVIS Engineering Operating System."""

from .api_inventory import (
    PackageAPIInventory,
    TargetAPIInventory,
    PublicSymbol,
    discover_definition_index,
    inventory_package,
    inventory_packages,
    inventory_target,
    inventory_targets,
)
from .compatibility import (
    APIExpectation,
    CompatibilityFinding,
    CompatibilityReport,
    analyze_compatibility,
    expectations_from_tests,
    load_expectations,
    save_expectations,
)
from .constitution import ENGINEERING_CONSTITUTION, constitution_fingerprint
from .contracts import (
    ChangeProposal,
    EngineeringAssessment,
    EngineeringContract,
    EngineeringGate,
    EngineeringPrinciple,
    GovernanceDecision,
    VerificationEvidence,
)
from .enums import (
    ChangeKind,
    ChangeRisk,
    DecisionStatus,
    EvidenceStatus,
    GateStatus,
    StableStringEnum,
    VerificationKind,
)
from .errors import (
    EngineeringError,
    EngineeringEvidenceError,
    EngineeringGovernanceError,
    EngineeringValidationError,
)
from .import_resolution import (
    PythonImportResolver,
    resolve_import_target,
)
from .inventory_targets import (
    InventoryResolution,
    InventoryTarget,
    InventoryTargetKind,
    import_name_to_relative_path,
    normalize_import_name,
    stable_inventory_targets,
)
from .reporting import (
    render_compatibility_markdown,
    write_compatibility_report,
)
from .restoration import (
    RestorationRecommendation,
    build_restoration_plan,
    recommendation_for_finding,
)

__all__ = [
    "stable_inventory_targets",
    "resolve_import_target",
    "normalize_import_name",
    "inventory_targets",
    "inventory_target",
    "import_name_to_relative_path",
    "TargetAPIInventory",
    "PythonImportResolver",
    "InventoryTargetKind",
    "InventoryTarget",
    "InventoryResolution",
    "APIExpectation",
    "ENGINEERING_CONSTITUTION",
    "ChangeKind",
    "ChangeProposal",
    "ChangeRisk",
    "CompatibilityFinding",
    "CompatibilityReport",
    "DecisionStatus",
    "EngineeringAssessment",
    "EngineeringContract",
    "EngineeringError",
    "EngineeringEvidenceError",
    "EngineeringGate",
    "EngineeringGovernanceError",
    "EngineeringPrinciple",
    "EngineeringValidationError",
    "EvidenceStatus",
    "GateStatus",
    "GovernanceDecision",
    "PackageAPIInventory",
    "PublicSymbol",
    "RestorationRecommendation",
    "StableStringEnum",
    "VerificationEvidence",
    "VerificationKind",
    "analyze_compatibility",
    "build_restoration_plan",
    "constitution_fingerprint",
    "discover_definition_index",
    "expectations_from_tests",
    "inventory_package",
    "inventory_packages",
    "load_expectations",
    "recommendation_for_finding",
    "render_compatibility_markdown",
    "save_expectations",
    "write_compatibility_report",
]
