"""R9.17C.4: localhost-only application version verification."""

from __future__ import annotations

import hashlib
import http.client
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from core.bounty_agent.autonomy.local_lab_r917 import LabBoundaryError

HOST = "127.0.0.1"
PORT = 3000
PATH = "/rest/admin/application-version"
MAX_BODY = 4096


@dataclass(frozen=True)
class VersionLabAuthorization:
    target: str
    method: str
    path: str
    approved: bool

    def require(self):
        if (
            self.approved is not True
            or self.target != f"http://{HOST}:{PORT}{PATH}"
            or self.method != "GET"
            or self.path != PATH
        ):
            raise LabBoundaryError("Version endpoint not authorized")


def verify_local_version(*, authorization, evidence_dir):
    if not isinstance(authorization, VersionLabAuthorization):
        raise LabBoundaryError("Explicit version authorization required")

    authorization.require()

    output = Path(evidence_dir)

    if not output.is_dir() or output.is_symlink():
        raise LabBoundaryError("Invalid evidence directory")

    connection = http.client.HTTPConnection(HOST, PORT, timeout=5)

    try:
        connection.connect()

        if connection.sock.getpeername() != (HOST, PORT):
            raise LabBoundaryError("Unexpected network peer")

        connection.request(
            "GET",
            PATH,
            headers={"Connection": "close"},
        )

        response = connection.getresponse()

        if 300 <= response.status < 400:
            raise LabBoundaryError("Redirect rejected")

        body = response.read(MAX_BODY + 1)

        if len(body) > MAX_BODY:
            raise LabBoundaryError("Response body exceeds limit")

        headers = {
            key.lower(): value
            for key, value in response.getheaders()
        }

        try:
            payload = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            payload = None

    except (OSError, http.client.HTTPException) as exc:
        raise LabBoundaryError("Version request failed") from exc
    finally:
        connection.close()

    version = (
        payload.get("version")
        if isinstance(payload, dict)
        and isinstance(payload.get("version"), str)
        else None
    )

    result = {
        "schema": "jarvis.bounty.lab_version.r917c4",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target": authorization.target,
        "method": authorization.method,
        "http_status": response.status,
        "headers": headers,
        "body_sha256": hashlib.sha256(body).hexdigest(),
        "version": version,
        "classification": "public_version_metadata",
        "validated_vulnerability": False,
        "submission_authorized": False,
        "human_review_required": True,
    }

    encoded = json.dumps(
        result, sort_keys=True, indent=2
    ).encode("utf-8")

    digest = hashlib.sha256(encoded).hexdigest()
    path = output / f"version-evidence-{digest[:16]}.json"

    try:
        fd = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
        )
    except FileExistsError as exc:
        raise LabBoundaryError("Evidence collision") from exc

    with os.fdopen(fd, "wb") as handle:
        handle.write(encoded)

    return {
        "status": "awaiting_human_review",
        "version": version,
        "http_status": result["http_status"],
        "classification": result["classification"],
        "validated_vulnerability": False,
        "evidence_path": str(path),
        "sha256": digest,
    }
