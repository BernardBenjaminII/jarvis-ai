from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import time
from typing import Iterable


SUPPORTED_ASSET_TYPES = {
    "dns",
    "wildcard_dns",
}


class ProgramScopeError(ValueError):
    pass


def _clean_host(value: str) -> str:
    value = str(value).strip().lower()

    if value.startswith("*."):
        value = value[2:]

    value = value.rstrip(".")

    if not value:
        raise ProgramScopeError(
            "Empty DNS asset"
        )

    if (
        "://" in value
        or "/" in value
        or " " in value
    ):
        raise ProgramScopeError(
            f"Unsupported DNS asset: {value}"
        )

    return value


@dataclass(frozen=True)
class ProgramAsset:
    value: str
    asset_type: str
    eligible: bool
    source_value: str
    instruction: str = ""

    def __post_init__(self):
        if self.asset_type not in SUPPORTED_ASSET_TYPES:
            raise ProgramScopeError(
                "Unsupported asset type: "
                f"{self.asset_type}"
            )

    @property
    def normalized(self) -> str:
        host = _clean_host(self.value)

        if self.asset_type == "wildcard_dns":
            return f"*.{host}"

        return host

    def to_dict(self) -> dict:
        return {
            "value": self.normalized,
            "asset_type": self.asset_type,
            "eligible": self.eligible,
            "source_value": self.source_value,
            "instruction": self.instruction,
        }


@dataclass(frozen=True)
class ProgramSnapshot:
    source: str
    handle: str
    name: str
    source_url: str
    assets: tuple[ProgramAsset, ...]
    rules_text: str
    retrieved_at: float
    source_digest: str

    # R9.0C review provenance.
    reviewer: str = ""
    source_draft_id: str = ""
    source_draft_digest: str = ""
    structured_scope_reviewed: bool = False
    testing_authorized: bool = False
    execution_enabled: bool = False

    @classmethod
    def reviewed_input(
        cls,
        *,
        source: str,
        handle: str,
        name: str,
        source_url: str,
        assets: Iterable[ProgramAsset],
        rules_text: str = "",
        source_material: str,
        reviewer: str = "",
        source_draft_id: str = "",
        source_draft_digest: str = "",
        structured_scope_reviewed: bool = False,
    ) -> "ProgramSnapshot":
        source = str(source).strip().lower()
        handle = str(handle).strip()
        name = str(name).strip()
        source_url = str(source_url).strip()

        if not source:
            raise ProgramScopeError(
                "Program source is required"
            )

        if not handle:
            raise ProgramScopeError(
                "Program handle is required"
            )

        if not name:
            raise ProgramScopeError(
                "Program name is required"
            )

        asset_tuple = tuple(assets)

        if not asset_tuple:
            raise ProgramScopeError(
                "Program must contain assets"
            )

        digest = hashlib.sha256(
            source_material.encode()
        ).hexdigest()

        return cls(
            source=source,
            handle=handle,
            name=name,
            source_url=source_url,
            assets=asset_tuple,
            rules_text=str(rules_text),
            retrieved_at=time.time(),
            source_digest=digest,
            reviewer=str(reviewer).strip(),
            source_draft_id=str(source_draft_id).strip(),
            source_draft_digest=str(
                source_draft_digest
            ).strip(),
            structured_scope_reviewed=bool(
                structured_scope_reviewed
            ),
            testing_authorized=False,
            execution_enabled=False,
        )

    def eligible_assets(self) -> tuple[ProgramAsset, ...]:
        return tuple(
            asset
            for asset in self.assets
            if asset.eligible
        )

    def excluded_assets(self) -> tuple[ProgramAsset, ...]:
        return tuple(
            asset
            for asset in self.assets
            if not asset.eligible
        )

    def authorization_scope(self) -> dict:
        include = []
        exclude = []

        for asset in self.assets:
            value = asset.normalized

            if asset.eligible:
                include.append(value)
            else:
                exclude.append(value)

        return {
            "include": sorted(set(include)),
            "exclude": sorted(set(exclude)),
        }

    def evidence(self) -> dict:
        return {
            "source": self.source,
            "handle": self.handle,
            "name": self.name,
            "source_url": self.source_url,
            "retrieved_at": self.retrieved_at,
            "source_digest": self.source_digest,
            "rules_text": self.rules_text,

            "reviewer": self.reviewer,
            "source_draft_id":
                self.source_draft_id,
            "source_draft_digest":
                self.source_draft_digest,

            "structured_scope_reviewed":
                self.structured_scope_reviewed,

            # A reviewed scope is not itself an execution
            # authorization.
            "testing_authorized":
                self.testing_authorized,
            "execution_enabled":
                self.execution_enabled,

            "assets": [
                asset.to_dict()
                for asset in self.assets
            ],
            "authorization_scope":
                self.authorization_scope(),
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.evidence(),
            sort_keys=True,
            separators=(",", ":"),
        )


@dataclass(frozen=True)
class ProgramIntakeDraft:
    """
    Non-executable program acquisition record.

    A catalog listing is useful for research and policy review,
    but it is not equivalent to a reviewed structured scope.
    """

    source: str
    handle: str
    name: str
    program_url: str
    reward_status: str
    submission_state: str | None
    visibility: str | None
    policy_text: str
    source_updated_at: str | None
    source_page_url: str
    source_page_sha256: str
    source_run_id: str
    observed_at: float
    stale: bool
    source_digest: str

    @classmethod
    def from_catalog_record(
        cls,
        record: dict,
    ) -> "ProgramIntakeDraft":
        if (
            record.get("source")
            != "hackerone-api"
        ):
            raise ProgramScopeError(
                "Only authenticated HackerOne API "
                "catalog observations may become "
                "R9.0B acquisition drafts"
            )

        if record.get(
            "testing_authorized"
        ) is not False:
            raise ProgramScopeError(
                "Catalog record must remain "
                "non-executable"
            )

        handle = str(
            record.get("handle") or ""
        ).strip()

        name = str(
            record.get("name") or ""
        ).strip()

        program_url = str(
            record.get("program_url") or ""
        ).strip()

        if not handle or not name:
            raise ProgramScopeError(
                "Catalog record lacks program identity"
            )

        source_material = json.dumps(
            {
                "source":
                    record.get("source"),
                "handle":
                    handle,
                "name":
                    name,
                "program_url":
                    program_url,
                "reward_status":
                    record.get("reward_status"),
                "submission_state":
                    record.get("submission_state"),
                "visibility":
                    record.get("visibility"),
                "policy_text":
                    record.get("policy_text") or "",
                "source_updated_at":
                    record.get("source_updated_at"),
                "source_page_url":
                    record.get("source_url"),
                "source_page_sha256":
                    record.get("source_sha256"),
                "source_run_id":
                    record.get("run_id"),
                "observed_at":
                    record.get("last_seen"),
            },
            sort_keys=True,
            separators=(",", ":"),
        )

        digest = hashlib.sha256(
            source_material.encode()
        ).hexdigest()

        return cls(
            source="hackerone-api",
            handle=handle,
            name=name,
            program_url=program_url,
            reward_status=str(
                record.get(
                    "reward_status"
                )
                or "unknown"
            ),
            submission_state=(
                record.get(
                    "submission_state"
                )
            ),
            visibility=record.get(
                "visibility"
            ),
            policy_text=str(
                record.get(
                    "policy_text"
                )
                or ""
            ),
            source_updated_at=record.get(
                "source_updated_at"
            ),
            source_page_url=str(
                record.get(
                    "source_url"
                )
                or ""
            ),
            source_page_sha256=str(
                record.get(
                    "source_sha256"
                )
                or ""
            ),
            source_run_id=str(
                record.get("run_id")
                or ""
            ),
            observed_at=float(
                record.get(
                    "last_seen"
                )
                or 0
            ),
            stale=bool(
                record.get("stale")
            ),
            source_digest=digest,
        )

    def evidence(self) -> dict:
        return {
            "schema":
                "jarvis-bounty-program-draft-r9.0b",
            "source": self.source,
            "handle": self.handle,
            "name": self.name,
            "program_url":
                self.program_url,
            "reward_status":
                self.reward_status,
            "submission_state":
                self.submission_state,
            "visibility":
                self.visibility,
            "policy_text":
                self.policy_text,
            "source_updated_at":
                self.source_updated_at,
            "source_page_url":
                self.source_page_url,
            "source_page_sha256":
                self.source_page_sha256,
            "source_run_id":
                self.source_run_id,
            "observed_at":
                self.observed_at,
            "stale":
                self.stale,
            "source_digest":
                self.source_digest,

            # Critical R9.0B boundary.
            "structured_scope_reviewed":
                False,
            "authorization_scope":
                None,
            "testing_authorized":
                False,
            "execution_enabled":
                False,

            "required_review": [
                (
                    "Current official policy and "
                    "full structured scope"
                ),
                (
                    "In-scope and out-of-scope "
                    "assets"
                ),
                (
                    "Automation restrictions and "
                    "request limits"
                ),
                (
                    "Asset-specific permitted "
                    "testing methods"
                ),
            ],
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.evidence(),
            sort_keys=True,
            separators=(",", ":"),
        )
