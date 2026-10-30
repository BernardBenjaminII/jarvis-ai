"""Reviewed live bounty scope.

R5 intentionally supports DNS host scope only.

This module does not fetch policies, infer authorization, execute commands,
or convert catalog text into authorization. A LiveScope must be constructed
from separately reviewed program rules.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
import time


class ScopeDenied(ValueError):
    pass


# R8.7B
#
# Authorization now distinguishes WHAT Jarvis may do from WHICH
# concrete provider may perform it.
#
# The legacy R5 provider names remain supported during migration.
LIVE_LOGICAL_CAPABILITIES = {
    "subdomain_discovery",
    "dns_resolution",
    "http_probe",
}

LIVE_APPROVED_PROVIDERS = {
    "subfinder",
    "dnsx",
    "httpx",
}

PROVIDER_LOGICAL_CAPABILITIES = {
    "subfinder": (
        "subdomain_discovery",
    ),
    "dnsx": (
        "dns_resolution",
    ),
    "httpx": (
        "http_probe",
    ),
}


def logical_capabilities_for_providers(providers):
    result = set()

    for provider in providers:
        provider = str(provider).strip().lower()

        result.update(
            PROVIDER_LOGICAL_CAPABILITIES.get(
                provider,
                (),
            )
        )

    return tuple(sorted(result))


_HOST_RE = re.compile(
    r"(?=^.{1,253}$)"
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)


def normalize_host(value: str) -> str:
    if not isinstance(value, str):
        raise ScopeDenied("Host must be text")

    value = value.strip().lower().rstrip(".")

    if (
        not value
        or "://" in value
        or "/" in value
        or ":" in value
        or "@" in value
        or " " in value
    ):
        raise ScopeDenied("Expected DNS hostname only")

    try:
        value = value.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ScopeDenied("Invalid internationalized hostname") from exc

    if not _HOST_RE.fullmatch(value):
        raise ScopeDenied("Invalid DNS hostname")

    return value


def normalize_pattern(value: str) -> str:
    if not isinstance(value, str):
        raise ScopeDenied("Scope pattern must be text")

    value = value.strip().lower().rstrip(".")

    if value.startswith("*."):
        return "*." + normalize_host(value[2:])

    return normalize_host(value)


def matches(host: str, pattern: str) -> bool:
    host = normalize_host(host)
    pattern = normalize_pattern(pattern)

    if pattern.startswith("*."):
        suffix = pattern[2:]
        return host != suffix and host.endswith("." + suffix)

    return host == pattern


@dataclass(frozen=True)
class LiveScope:
    program: str
    include: tuple[str, ...]
    exclude: tuple[str, ...]
    allowed_capabilities: tuple[str, ...]
    logical_capabilities: tuple[str, ...]
    reviewed_by: str
    source_digest: str
    reviewed_at: float

    @classmethod
    def reviewed(
        cls,
        *,
        program: str,
        include,
        exclude=(),
        allowed_capabilities=("subfinder", "httpx"),
        logical_capabilities=None,
        approved_providers=None,
        reviewed_by: str,
        source_material: str,
    ) -> "LiveScope":

        if not isinstance(program, str) or not program.strip():
            raise ScopeDenied("Program identifier required")

        if not isinstance(reviewed_by, str) or not reviewed_by.strip():
            raise ScopeDenied("Reviewer identity required")

        if not isinstance(source_material, str) or not source_material.strip():
            raise ScopeDenied("Reviewed source material required")

        included = tuple(sorted({normalize_pattern(x) for x in include}))
        excluded = tuple(sorted({normalize_pattern(x) for x in exclude}))

        if not included:
            raise ScopeDenied("At least one included host pattern required")

        # Backward compatibility:
        #
        # R5 callers supplied concrete providers through
        # allowed_capabilities. R8.7B keeps accepting that form.
        if approved_providers is None:
            approved_providers = allowed_capabilities

        providers = tuple(
            sorted({
                str(x).strip().lower()
                for x in approved_providers
            })
        )

        if not providers:
            raise ScopeDenied(
                "At least one approved provider required"
            )

        if any(
            provider not in LIVE_APPROVED_PROVIDERS
            for provider in providers
        ):
            raise ScopeDenied(
                "Unsupported live provider"
            )

        if logical_capabilities is None:
            logical = logical_capabilities_for_providers(
                providers
            )
        else:
            logical = tuple(
                sorted({
                    str(x).strip().lower()
                    for x in logical_capabilities
                })
            )

        if not logical:
            raise ScopeDenied(
                "At least one logical capability required"
            )

        if any(
            capability not in LIVE_LOGICAL_CAPABILITIES
            for capability in logical
        ):
            raise ScopeDenied(
                "Unsupported logical capability"
            )

        # Every approved provider must correspond to at least
        # one explicitly authorized logical capability.
        for provider in providers:
            provided = set(
                PROVIDER_LOGICAL_CAPABILITIES.get(
                    provider,
                    (),
                )
            )

            if not provided.intersection(logical):
                raise ScopeDenied(
                    f"Provider {provider} has no authorized "
                    "logical capability"
                )

        digest = hashlib.sha256(
            source_material.encode("utf-8")
        ).hexdigest()

        return cls(
            program=program.strip(),
            include=included,
            exclude=excluded,
            allowed_capabilities=providers,
            logical_capabilities=logical,
            reviewed_by=reviewed_by.strip(),
            source_digest=digest,
            reviewed_at=time.time(),
        )

    @property
    def approved_providers(self) -> tuple[str, ...]:
        """
        Concrete execution providers approved by the reviewer.

        allowed_capabilities remains as a compatibility alias for
        legacy R5 callers and persisted records.
        """
        return self.allowed_capabilities

    def require_capability(self, capability: str) -> str:
        capability = str(capability).strip().lower()

        if capability not in self.logical_capabilities:
            raise ScopeDenied(
                f"Logical capability not authorized: "
                f"{capability}"
            )

        return capability

    def permits_host(self, host: str) -> bool:
        host = normalize_host(host)

        if any(matches(host, x) for x in self.exclude):
            return False

        return any(matches(host, x) for x in self.include)

    def require(self, host: str, capability: str) -> str:
        capability = str(capability).strip().lower()

        if capability not in self.allowed_capabilities:
            raise ScopeDenied(
                f"Capability not authorized: {capability}"
            )

        host = normalize_host(host)

        if not self.permits_host(host):
            raise ScopeDenied(f"Host outside reviewed scope: {host}")

        return host

    def filter_hosts(self, hosts):
        accepted = []
        rejected = []

        for value in hosts:
            try:
                host = normalize_host(value)
                if self.permits_host(host):
                    accepted.append(host)
                else:
                    rejected.append(host)
            except ScopeDenied:
                rejected.append(str(value))

        return {
            "accepted": sorted(set(accepted)),
            "rejected": sorted(set(rejected)),
        }

    def evidence(self):
        record = {
            "program": self.program,
            "include": list(self.include),
            "exclude": list(self.exclude),
            # Legacy provider authorization field.
            "allowed_capabilities": list(
                self.allowed_capabilities
            ),

            # R8.7B canonical authorization concepts.
            "logical_capabilities": list(
                self.logical_capabilities
            ),
            "approved_providers": list(
                self.approved_providers
            ),

            "reviewed_by": self.reviewed_by,
            "source_digest": self.source_digest,
            "reviewed_at": self.reviewed_at,
        }

        raw = json.dumps(record, sort_keys=True).encode()

        return {
            **record,
            "scope_sha256": hashlib.sha256(raw).hexdigest(),
        }
