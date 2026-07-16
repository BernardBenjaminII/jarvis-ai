"""
Stable architecture contracts for the JARVIS acquisition subsystem.

Phase VII-A8 freezes the dependency direction and public package structure
established during VII-A1 through VII-A7.

This module performs no persistence, discovery, admission, mission execution,
handoff preparation, dispatch, or network access.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


ACQUISITION_LAYER_ORDER: tuple[str, ...] = (
    "admission",
    "provenance",
    "intake",
    "missions",
    "handoff",
    "dispatch",
)


ACQUISITION_LAYER_INDEX: dict[str, int] = {
    layer_name: index
    for index, layer_name in enumerate(
        ACQUISITION_LAYER_ORDER
    )
}


ACQUISITION_PUBLIC_MODULES: tuple[str, ...] = (
    "knowledge_engine.acquisition.admission",
    "knowledge_engine.acquisition.provenance",
    "knowledge_engine.acquisition.intake",
    "knowledge_engine.acquisition.missions",
    "knowledge_engine.acquisition.handoff",
    "knowledge_engine.acquisition.dispatch",
)


EXPECTED_PUBLIC_SYMBOLS: dict[str, tuple[str, ...]] = {
    "knowledge_engine.acquisition.admission": (
        "AdmissionAction",
        "AdmissionContext",
        "AdmissionDecision",
        "AdmissionDirector",
        "AdmissionPolicyRegistry",
        "build_default_admission_director",
    ),
    "knowledge_engine.acquisition.provenance": (
        "ProvenanceRepository",
        "ProvenanceService",
        "ensure_provenance_schema",
    ),
    "knowledge_engine.acquisition.intake": (
        "AcquisitionIntakeResult",
        "AcquisitionIntakeService",
    ),
    "knowledge_engine.acquisition.missions": (
        "AcquisitionMissionBuildResult",
        "AcquisitionMissionItemRecord",
        "AcquisitionMissionItemState",
        "AcquisitionMissionRecord",
        "AcquisitionMissionRepository",
        "AcquisitionMissionService",
        "AcquisitionMissionState",
        "build_acquisition_mission_id",
        "ensure_acquisition_mission_schema",
    ),
    "knowledge_engine.acquisition.handoff": (
        "AssimilationHandoffBuildResult",
        "AssimilationHandoffRecord",
        "AssimilationHandoffRepository",
        "AssimilationHandoffService",
        "AssimilationHandoffState",
        "build_assimilation_handoff_id",
        "ensure_assimilation_handoff_schema",
    ),
    "knowledge_engine.acquisition.dispatch": (
        "AcquisitionRegistrationPort",
        "AssimilationDispatchRepository",
        "AssimilationDispatchResult",
        "CanonicalAssimilationDispatcher",
        "PhaseVIExecutionPort",
        "PhaseVIRunnerExecutionAdapter",
    ),
}


PHASE_VI_IMPORT_ALLOWLIST: tuple[str, ...] = (
    "knowledge_engine.acquisition.dispatch.phase_vi",
)


@dataclass(frozen=True, slots=True)
class AcquisitionContractSnapshot:
    """Deterministic acquisition architecture snapshot."""

    layers: tuple[str, ...]
    public_modules: tuple[str, ...]
    public_symbols: tuple[
        tuple[str, tuple[str, ...]],
        ...
    ]
    phase_vi_import_allowlist: tuple[str, ...]
    fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "layers": list(self.layers),
            "public_modules": list(
                self.public_modules
            ),
            "public_symbols": {
                module_name: list(symbols)
                for module_name, symbols
                in self.public_symbols
            },
            "phase_vi_import_allowlist": list(
                self.phase_vi_import_allowlist
            ),
            "fingerprint": self.fingerprint,
        }


def build_acquisition_contract_snapshot(
) -> AcquisitionContractSnapshot:
    """Build the deterministic VII-A architecture snapshot."""

    public_symbols = tuple(
        (
            module_name,
            tuple(
                EXPECTED_PUBLIC_SYMBOLS[
                    module_name
                ]
            ),
        )
        for module_name in sorted(
            EXPECTED_PUBLIC_SYMBOLS
        )
    )

    payload = {
        "layers": list(
            ACQUISITION_LAYER_ORDER
        ),
        "public_modules": list(
            ACQUISITION_PUBLIC_MODULES
        ),
        "public_symbols": {
            module_name: list(symbols)
            for module_name, symbols
            in public_symbols
        },
        "phase_vi_import_allowlist": list(
            PHASE_VI_IMPORT_ALLOWLIST
        ),
    }

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    fingerprint = hashlib.sha256(
        encoded
    ).hexdigest()

    return AcquisitionContractSnapshot(
        layers=ACQUISITION_LAYER_ORDER,
        public_modules=(
            ACQUISITION_PUBLIC_MODULES
        ),
        public_symbols=public_symbols,
        phase_vi_import_allowlist=(
            PHASE_VI_IMPORT_ALLOWLIST
        ),
        fingerprint=fingerprint,
    )


__all__ = [
    "ACQUISITION_LAYER_INDEX",
    "ACQUISITION_LAYER_ORDER",
    "ACQUISITION_PUBLIC_MODULES",
    "EXPECTED_PUBLIC_SYMBOLS",
    "PHASE_VI_IMPORT_ALLOWLIST",
    "AcquisitionContractSnapshot",
    "build_acquisition_contract_snapshot",
]
