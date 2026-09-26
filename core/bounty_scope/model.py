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

        permitted = {"subfinder", "httpx"}

        capabilities = tuple(
            sorted({str(x).strip().lower() for x in allowed_capabilities})
        )

        if not capabilities:
            raise ScopeDenied("At least one capability required")

        if any(x not in permitted for x in capabilities):
            raise ScopeDenied("Unsupported R5 capability")

        digest = hashlib.sha256(
            source_material.encode("utf-8")
        ).hexdigest()

        return cls(
            program=program.strip(),
            include=included,
            exclude=excluded,
            allowed_capabilities=capabilities,
            reviewed_by=reviewed_by.strip(),
            source_digest=digest,
            reviewed_at=time.time(),
        )

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
            "allowed_capabilities": list(self.allowed_capabilities),
            "reviewed_by": self.reviewed_by,
            "source_digest": self.source_digest,
            "reviewed_at": self.reviewed_at,
        }

        raw = json.dumps(record, sort_keys=True).encode()

        return {
            **record,
            "scope_sha256": hashlib.sha256(raw).hexdigest(),
        }
