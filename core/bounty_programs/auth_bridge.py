from __future__ import annotations

import hashlib
import json

from core.bounty_authorization import AuthorizationStore
from core.bounty_scope.model import (
    LIVE_APPROVED_PROVIDERS,
    LIVE_LOGICAL_CAPABILITIES,
    PROVIDER_LOGICAL_CAPABILITIES,
)

from .store import ProgramStore


class AuthorizationBridgeError(ValueError):
    pass


R90D_ALLOWED_LOGICAL_CAPABILITIES = {
    "subdomain_discovery",
    "dns_resolution",
    "http_probe",
}

R90D_ALLOWED_PROVIDERS = {
    "subfinder",
    "dnsx",
    "httpx",
}


def _review_material(snapshot: dict) -> str:
    """
    Reconstruct the exact R9.0C review material whose digest
    is stored in ProgramSnapshot.source_digest.
    """

    scope = snapshot.get(
        "authorization_scope"
    )

    if not isinstance(scope, dict):
        raise AuthorizationBridgeError(
            "Reviewed snapshot has no authorization scope"
        )

    include = scope.get("include")
    exclude = scope.get("exclude")

    if not isinstance(include, list):
        raise AuthorizationBridgeError(
            "Reviewed include scope is invalid"
        )

    if not isinstance(exclude, list):
        raise AuthorizationBridgeError(
            "Reviewed exclude scope is invalid"
        )

    return json.dumps(
        {
            "schema":
                "jarvis-bounty-program-review-r9.0c",
            "source_draft_id":
                snapshot.get(
                    "source_draft_id"
                ),
            "source_draft_digest":
                snapshot.get(
                    "source_draft_digest"
                ),
            "reviewer":
                snapshot.get("reviewer"),
            "program":
                snapshot.get("handle"),
            "program_url":
                snapshot.get("source_url"),
            "policy_text":
                snapshot.get("rules_text")
                or "",
            "include":
                sorted(include),
            "exclude":
                sorted(exclude),
            "policy_review_acknowledged":
                True,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _scope_from_assets(snapshot: dict) -> dict:
    """
    Independently reconstruct scope from the reviewed asset
    records. This prevents authorization_scope from drifting
    away from the reviewed asset list.
    """

    assets = snapshot.get("assets")

    if not isinstance(assets, list):
        raise AuthorizationBridgeError(
            "Reviewed snapshot assets are invalid"
        )

    include = set()
    exclude = set()

    for item in assets:
        if not isinstance(item, dict):
            raise AuthorizationBridgeError(
                "Reviewed asset entry is invalid"
            )

        value = str(
            item.get("value") or ""
        ).strip().lower()

        if not value:
            raise AuthorizationBridgeError(
                "Reviewed asset has no value"
            )

        eligible = item.get("eligible")

        if eligible is True:
            include.add(value)
        elif eligible is False:
            exclude.add(value)
        else:
            raise AuthorizationBridgeError(
                "Reviewed asset eligibility is invalid"
            )

    overlap = include & exclude

    if overlap:
        raise AuthorizationBridgeError(
            "Reviewed scope contains contradictory assets: "
            + ", ".join(sorted(overlap))
        )

    return {
        "include": sorted(include),
        "exclude": sorted(exclude),
    }


def verify_reviewed_program(
    stored: dict,
) -> dict:
    snapshot = stored.get("snapshot")

    if not isinstance(snapshot, dict):
        raise AuthorizationBridgeError(
            "Stored ProgramSnapshot is invalid"
        )

    stored_digest = str(
        stored.get("source_digest") or ""
    )

    snapshot_digest = str(
        snapshot.get("source_digest") or ""
    )

    if not stored_digest:
        raise AuthorizationBridgeError(
            "Stored program source digest is missing"
        )

    if stored_digest != snapshot_digest:
        raise AuthorizationBridgeError(
            "Stored program digest does not match snapshot"
        )

    if (
        snapshot.get(
            "structured_scope_reviewed"
        )
        is not True
    ):
        raise AuthorizationBridgeError(
            "Structured scope has not been human-reviewed"
        )

    if (
        snapshot.get("testing_authorized")
        is not False
    ):
        raise AuthorizationBridgeError(
            "Reviewed snapshot crossed an invalid "
            "testing authorization boundary"
        )

    if (
        snapshot.get("execution_enabled")
        is not False
    ):
        raise AuthorizationBridgeError(
            "Reviewed snapshot crossed an invalid "
            "execution boundary"
        )

    reviewer = str(
        snapshot.get("reviewer") or ""
    ).strip()

    if not reviewer:
        raise AuthorizationBridgeError(
            "Reviewed snapshot has no reviewer"
        )

    if not str(
        snapshot.get("source_draft_id")
        or ""
    ).strip():
        raise AuthorizationBridgeError(
            "Reviewed snapshot has no source draft"
        )

    if not str(
        snapshot.get("source_draft_digest")
        or ""
    ).strip():
        raise AuthorizationBridgeError(
            "Reviewed snapshot has no source draft digest"
        )

    recomputed_review_digest = hashlib.sha256(
        _review_material(
            snapshot
        ).encode()
    ).hexdigest()

    if recomputed_review_digest != snapshot_digest:
        raise AuthorizationBridgeError(
            "Reviewed ProgramSnapshot provenance "
            "verification failed"
        )

    reconstructed_scope = _scope_from_assets(
        snapshot
    )

    stored_scope = snapshot.get(
        "authorization_scope"
    )

    canonical_stored_scope = {
        "include": sorted(
            stored_scope.get(
                "include",
                [],
            )
        ),
        "exclude": sorted(
            stored_scope.get(
                "exclude",
                [],
            )
        ),
    }

    if (
        canonical_stored_scope
        != reconstructed_scope
    ):
        raise AuthorizationBridgeError(
            "Authorization scope does not match "
            "reviewed assets"
        )

    if not reconstructed_scope["include"]:
        raise AuthorizationBridgeError(
            "Reviewed program contains no in-scope assets"
        )

    return snapshot


def _validate_capability_plan(
    logical_capabilities,
    approved_providers,
):
    logical = tuple(
        sorted({
            str(item).strip().lower()
            for item in logical_capabilities
            if str(item).strip()
        })
    )

    providers = tuple(
        sorted({
            str(item).strip().lower()
            for item in approved_providers
            if str(item).strip()
        })
    )

    if not logical:
        raise AuthorizationBridgeError(
            "At least one logical capability "
            "must be explicitly selected"
        )

    if not providers:
        raise AuthorizationBridgeError(
            "At least one execution provider "
            "must be explicitly selected"
        )

    if any(
        item not in
        R90D_ALLOWED_LOGICAL_CAPABILITIES
        for item in logical
    ):
        raise AuthorizationBridgeError(
            "R9.0D only permits the validated "
            "low-impact recon capabilities"
        )

    if any(
        item not in R90D_ALLOWED_PROVIDERS
        for item in providers
    ):
        raise AuthorizationBridgeError(
            "R9.0D only permits the validated "
            "low-impact recon providers"
        )

    # Cross-check against the authoritative live scope model.
    if any(
        item not in LIVE_LOGICAL_CAPABILITIES
        for item in logical
    ):
        raise AuthorizationBridgeError(
            "Unsupported live logical capability"
        )

    if any(
        item not in LIVE_APPROVED_PROVIDERS
        for item in providers
    ):
        raise AuthorizationBridgeError(
            "Unsupported live provider"
        )

    # Every provider must serve an authorized capability.
    for provider in providers:
        provided = set(
            PROVIDER_LOGICAL_CAPABILITIES.get(
                provider,
                (),
            )
        )

        if not provided.intersection(
            logical
        ):
            raise AuthorizationBridgeError(
                f"Provider {provider} has no "
                "authorized logical capability"
            )

    # Every requested capability must have a selected provider.
    for capability in logical:
        matching = [
            provider
            for provider in providers
            if capability in
            PROVIDER_LOGICAL_CAPABILITIES.get(
                provider,
                (),
            )
        ]

        if not matching:
            raise AuthorizationBridgeError(
                f"Logical capability {capability} "
                "has no approved provider"
            )

    return logical, providers


def authorize_reviewed_program(
    *,
    program_store: ProgramStore,
    authorization_store: AuthorizationStore,
    program_id: str,
    reviewer: str,
    logical_capabilities,
    approved_providers,
    ttl: int = 86400,
    note: str = "",
) -> str:
    """
    Convert a verified R9.0C ProgramSnapshot into a live
    AuthorizationStore record.

    This creates authorization only.
    It never creates or executes a mission.
    """

    stored = program_store.get(
        program_id
    )

    snapshot = verify_reviewed_program(
        stored
    )

    reviewer = str(reviewer).strip()

    if not reviewer:
        raise AuthorizationBridgeError(
            "Authorization reviewer is required"
        )

    if reviewer != snapshot["reviewer"]:
        raise AuthorizationBridgeError(
            "Authorization reviewer must match "
            "the structured-scope reviewer"
        )

    logical, providers = (
        _validate_capability_plan(
            logical_capabilities,
            approved_providers,
        )
    )

    scope = snapshot[
        "authorization_scope"
    ]

    authorization_source = json.dumps(
        {
            "schema":
                "jarvis-bounty-authorization-r9.0d",
            "program_id":
                program_id,
            "program":
                snapshot["handle"],
            "program_name":
                snapshot["name"],
            "program_url":
                snapshot["source_url"],
            "reviewer":
                reviewer,
            "reviewed_snapshot_digest":
                snapshot["source_digest"],
            "source_draft_id":
                snapshot["source_draft_id"],
            "source_draft_digest":
                snapshot[
                    "source_draft_digest"
                ],
            "include":
                scope["include"],
            "exclude":
                scope["exclude"],
            "logical_capabilities":
                list(logical),
            "approved_providers":
                list(providers),
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    return authorization_store.create(
        program=snapshot["handle"],
        include=scope["include"],
        exclude=scope["exclude"],
        logical_capabilities=list(
            logical
        ),
        approved_providers=list(
            providers
        ),
        reviewer=reviewer,
        source_material=(
            authorization_source
        ),
        ttl=ttl,
        note=(
            note
            or (
                "R9.0D authorization from "
                f"reviewed ProgramSnapshot {program_id}"
            )
        ),
    )
