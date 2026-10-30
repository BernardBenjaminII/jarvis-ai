from __future__ import annotations

from .model import (
    ProgramAsset,
    ProgramScopeError,
)


def normalize_asset(
    value: str,
    *,
    eligible: bool,
    instruction: str = "",
) -> ProgramAsset:
    raw = str(value).strip()

    if not raw:
        raise ProgramScopeError(
            "Asset value is required"
        )

    if raw.startswith("*."):
        asset_type = "wildcard_dns"
        normalized_value = raw[2:]
    else:
        asset_type = "dns"
        normalized_value = raw

    return ProgramAsset(
        value=normalized_value,
        asset_type=asset_type,
        eligible=bool(eligible),
        source_value=raw,
        instruction=str(instruction or ""),
    )


def normalize_assets(
    *,
    in_scope,
    out_of_scope=(),
):
    assets = []

    for value in in_scope:
        assets.append(
            normalize_asset(
                value,
                eligible=True,
            )
        )

    for value in out_of_scope:
        assets.append(
            normalize_asset(
                value,
                eligible=False,
            )
        )

    return tuple(assets)
