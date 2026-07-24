"""Stable additive public API for executive persistence.

Genesis phases may add public symbols, but must not remove symbols introduced
by prior certified phases.
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Iterable


def _public_names(module: ModuleType) -> tuple[str, ...]:
    declared = getattr(module, "__all__", None)
    if declared is not None:
        return tuple(str(name) for name in declared)
    return tuple(
        name
        for name in vars(module)
        if not name.startswith("_")
    )


def _reexport(module_name: str) -> tuple[str, ...]:
    try:
        module = import_module(f"{__name__}.{module_name}")
    except ImportError:
        return ()

    exported: list[str] = []
    for name in _public_names(module):
        if not hasattr(module, name):
            continue
        globals()[name] = getattr(module, name)
        exported.append(name)
    return tuple(exported)


# Preserve the complete public surfaces established by VI-A6.1 and VI-A6.2.
_prior_exports: list[str] = []
for _module_name in ("contracts", "canonical", "serializer"):
    _prior_exports.extend(_reexport(_module_name))


# Genesis VI-A6.3 additions.
from .checkpoint import (
    CHECKPOINT_FORMAT,
    CHECKPOINT_FORMAT_VERSION,
    ZERO_DIGEST,
    CheckpointError,
    CheckpointFormatError,
    CheckpointIntegrityError,
    CheckpointSequenceError,
    CheckpointStatus,
    CheckpointSummary,
    ExecutiveCheckpoint,
    compute_checkpoint_sha256,
    create_checkpoint,
    decode_checkpoint,
    encode_checkpoint,
)
from .repository import (
    CheckpointConflictError,
    CheckpointHistoryError,
    CheckpointNotFoundError,
    CheckpointRepository,
    CheckpointRepositoryError,
    FileCheckpointRepository,
    RepositoryPolicy,
)
from .storage import (
    AtomicFileStorage,
    StorageError,
    StorageLockTimeoutError,
    StoragePathError,
    StoragePolicy,
    StorageSizeLimitError,
)


_a63_exports = (
    "AtomicFileStorage",
    "CHECKPOINT_FORMAT",
    "CHECKPOINT_FORMAT_VERSION",
    "CheckpointConflictError",
    "CheckpointError",
    "CheckpointFormatError",
    "CheckpointHistoryError",
    "CheckpointIntegrityError",
    "CheckpointNotFoundError",
    "CheckpointRepository",
    "CheckpointRepositoryError",
    "CheckpointSequenceError",
    "CheckpointStatus",
    "CheckpointSummary",
    "ExecutiveCheckpoint",
    "FileCheckpointRepository",
    "RepositoryPolicy",
    "StorageError",
    "StorageLockTimeoutError",
    "StoragePathError",
    "StoragePolicy",
    "StorageSizeLimitError",
    "ZERO_DIGEST",
    "compute_checkpoint_sha256",
    "create_checkpoint",
    "decode_checkpoint",
    "encode_checkpoint",
)

__all__ = tuple(dict.fromkeys((*_prior_exports, *_a63_exports)))

del _a63_exports
del _module_name
del _prior_exports
del _public_names
del _reexport
# Genesis VI-A6.4 public API
from .evaluator import IntegrityEvaluator
from .integrity import ExecutiveIntegrityEngine, IntegrityEngine, verify_session
from .policies import IntegrityPolicy
from .reports import IntegrityCode, IntegrityDisposition, IntegrityFinding, IntegrityObservation, IntegrityReport, IntegritySeverity
from .scanner import CheckpointRepositoryProtocol, IntegrityScanner

# BEGIN GENESIS VI-A6.5 RECOVERY EXPORTS
from .recovery import (
    CheckpointRepository, ExecutiveRecoveryEngine, RecoveryAuthorization,
    RecoveryError, RecoveryPointNotFoundError, RecoveryPolicy,
    RecoveryPolicyKind, RecoveryReconstructionError, RecoveryRefusedError,
    RecoveryReport, RecoveryResult, RecoveryStatus,
)
# END GENESIS VI-A6.5 RECOVERY EXPORTS
