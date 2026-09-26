#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"

echo "================================================================"
echo " JARVIS BOUNTY R5 — REVIEWED SCOPE + FIXED KALI ADAPTERS"
echo "================================================================"

test -f core/bounty_worker/runner.py
test -f core/bounty_lab/engine.py

mkdir -p \
  core/bounty_scope \
  core/bounty_adapters \
  tests/bounty_scope \
  tests/bounty_adapters

cat > core/bounty_scope/__init__.py <<'PY'
from .model import LiveScope, ScopeDenied

__all__ = ["LiveScope", "ScopeDenied"]
PY

cat > core/bounty_scope/model.py <<'PY'
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
PY

cat > core/bounty_adapters/__init__.py <<'PY'
from .subfinder import enumerate_subdomains
from .httpx import probe_http

__all__ = ["enumerate_subdomains", "probe_http"]
PY

cat > core/bounty_adapters/base.py <<'PY'
"""Fixed-command bounty execution helpers.

Never expose command argv construction from this package to a language model,
HTTP request parameter, generic command dispatcher, or unreviewed mission data.
"""

from __future__ import annotations

import os
import shutil

from core.bounty_worker.runner import run_bounded


class AdapterUnavailable(RuntimeError):
    pass


_ALLOWED = {
    "subfinder",
    "httpx",
}


def binary(name: str) -> str:
    if name not in _ALLOWED:
        raise AdapterUnavailable("Unsupported adapter executable")

    path = shutil.which(name)

    if not path:
        raise AdapterUnavailable(f"{name} executable not found")

    path = os.path.realpath(path)

    if not os.path.isfile(path) or not os.access(path, os.X_OK):
        raise AdapterUnavailable(f"{name} is not executable")

    return path


def execute(argv, *, timeout=30, output_limit=1048576, cancel=None):
    return run_bounded(
        argv,
        timeout=timeout,
        output_limit=output_limit,
        cancel=cancel,
    )
PY

cat > core/bounty_adapters/subfinder.py <<'PY'
"""Fixed passive subfinder adapter."""

from __future__ import annotations

import time

from .base import binary, execute


CAPABILITY = "subfinder"


def enumerate_subdomains(scope, domain, *, cancel=None):
    domain = scope.require(domain, CAPABILITY)

    exe = binary("subfinder")

    # Fixed argument surface. No caller-supplied switches.
    argv = [
        exe,
        "-silent",
        "-d",
        domain,
    ]

    started = time.time()

    result = execute(
        argv,
        timeout=30,
        output_limit=1048576,
        cancel=cancel,
    )

    discovered = []

    if result.get("output"):
        discovered = [
            line.strip()
            for line in result["output"].splitlines()
            if line.strip()
        ]

    filtered = scope.filter_hosts(discovered)

    return {
        "adapter": CAPABILITY,
        "target": domain,
        "state": result.get("state"),
        "returncode": result.get("returncode"),
        "started_at": started,
        "finished_at": time.time(),
        "scope": scope.evidence(),
        "accepted": filtered["accepted"],
        "rejected": filtered["rejected"],
        "raw_output_bytes": result.get("bytes", 0),
    }
PY

cat > core/bounty_adapters/httpx.py <<'PY'
"""Fixed single-host HTTPX metadata probe."""

from __future__ import annotations

import json
import time

from .base import binary, execute


CAPABILITY = "httpx"


def probe_http(scope, host, *, scheme="https", cancel=None):
    host = scope.require(host, CAPABILITY)

    if scheme not in {"http", "https"}:
        raise ValueError("Scheme must be http or https")

    exe = binary("httpx")

    target = f"{scheme}://{host}"

    # Fixed argument surface.
    #
    # Redirect following is deliberately not enabled. A redirect destination may
    # be outside the reviewed bounty scope and should require its own scope check.
    argv = [
        exe,
        "-silent",
        "-u",
        target,
        "-json",
        "-no-color",
    ]

    started = time.time()

    result = execute(
        argv,
        timeout=30,
        output_limit=262144,
        cancel=cancel,
    )

    records = []

    for line in (result.get("output") or "").splitlines():
        line = line.strip()

        if not line:
            continue

        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue

        if isinstance(value, dict):
            records.append(value)

    return {
        "adapter": CAPABILITY,
        "target": host,
        "scheme": scheme,
        "state": result.get("state"),
        "returncode": result.get("returncode"),
        "started_at": started,
        "finished_at": time.time(),
        "scope": scope.evidence(),
        "records": records,
        "raw_output_bytes": result.get("bytes", 0),
    }
PY

cat > tests/bounty_scope/test_scope.py <<'PY'
import pytest

from core.bounty_scope import LiveScope, ScopeDenied


def make_scope():
    return LiveScope.reviewed(
        program="demo",
        include=["example.com", "*.example.com"],
        exclude=["private.example.com"],
        allowed_capabilities=["subfinder", "httpx"],
        reviewed_by="tester",
        source_material="synthetic reviewed fixture",
    )


def test_exact_and_wildcard_scope():
    s = make_scope()

    assert s.require("example.com", "subfinder") == "example.com"
    assert s.require("WWW.Example.Com.", "httpx") == "www.example.com"


def test_exclusion_wins():
    s = make_scope()

    with pytest.raises(ScopeDenied):
        s.require("private.example.com", "httpx")


def test_outside_scope_denied():
    s = make_scope()

    with pytest.raises(ScopeDenied):
        s.require("example.org", "httpx")


def test_capability_denied():
    s = make_scope()

    with pytest.raises(ScopeDenied):
        s.require("example.com", "nuclei")


def test_filter_derived_hosts():
    s = make_scope()

    result = s.filter_hosts([
        "a.example.com",
        "private.example.com",
        "outside.example.org",
    ])

    assert result["accepted"] == ["a.example.com"]

    assert set(result["rejected"]) == {
        "outside.example.org",
        "private.example.com",
    }
PY

cat > tests/bounty_adapters/test_adapters.py <<'PY'
from core.bounty_scope import LiveScope
from core.bounty_adapters import subfinder, httpx


def scope():
    return LiveScope.reviewed(
        program="demo",
        include=["example.com", "*.example.com"],
        exclude=["private.example.com"],
        allowed_capabilities=["subfinder", "httpx"],
        reviewed_by="tester",
        source_material="synthetic reviewed fixture",
    )


def test_subfinder_filters_output(monkeypatch):
    monkeypatch.setattr(
        subfinder,
        "binary",
        lambda name: "/test/subfinder",
    )

    monkeypatch.setattr(
        subfinder,
        "execute",
        lambda argv, **kw: {
            "state": "completed",
            "returncode": 0,
            "bytes": 64,
            "output": (
                "a.example.com\n"
                "private.example.com\n"
                "outside.example.org\n"
            ),
        },
    )

    result = subfinder.enumerate_subdomains(
        scope(),
        "example.com",
    )

    assert result["accepted"] == ["a.example.com"]

    assert set(result["rejected"]) == {
        "private.example.com",
        "outside.example.org",
    }

    assert result["state"] == "completed"


def test_httpx_fixed_target(monkeypatch):
    seen = {}

    monkeypatch.setattr(
        httpx,
        "binary",
        lambda name: "/test/httpx",
    )

    def fake(argv, **kw):
        seen["argv"] = argv

        return {
            "state": "completed",
            "returncode": 0,
            "bytes": 40,
            "output": '{"url":"https://a.example.com","status_code":200}\n',
        }

    monkeypatch.setattr(httpx, "execute", fake)

    result = httpx.probe_http(
        scope(),
        "a.example.com",
    )

    assert seen["argv"] == [
        "/test/httpx",
        "-silent",
        "-u",
        "https://a.example.com",
        "-json",
        "-no-color",
    ]

    assert result["records"][0]["status_code"] == 200


def test_httpx_does_not_enable_redirects(monkeypatch):
    seen = {}

    monkeypatch.setattr(
        httpx,
        "binary",
        lambda name: "/test/httpx",
    )

    def fake(argv, **kw):
        seen["argv"] = argv

        return {
            "state": "completed",
            "returncode": 0,
            "bytes": 0,
            "output": "",
        }

    monkeypatch.setattr(httpx, "execute", fake)

    httpx.probe_http(
        scope(),
        "a.example.com",
    )

    assert "-follow-redirects" not in seen["argv"]
    assert "-fr" not in seen["argv"]
PY

echo
echo "=== RUN R5 TESTS ================================================"

python3 -m pytest \
  tests/bounty_scope \
  tests/bounty_adapters \
  tests/bounty_catalog \
  tests/bounty_credentials \
  tests/bounty_missions \
  tests/bounty_worker \
  -q

echo
echo "=== PYTHON COMPILE =============================================="

python3 -m compileall -q \
  core/bounty_scope \
  core/bounty_adapters

echo
echo "=== DIFF CHECK =================================================="

git diff --check

echo
echo "=== STATUS ======================================================"

git status --short

echo
echo "================================================================"
echo " R5 INSTALLATION / VERIFICATION COMPLETE"
echo "================================================================"
