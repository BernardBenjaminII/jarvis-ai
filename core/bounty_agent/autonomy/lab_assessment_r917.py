"""R9.17C: read-only security header assessment of local Juice Shop."""

from __future__ import annotations

import hashlib
import http.client
import json
from pathlib import Path

from core.bounty_agent.autonomy.lab_authorization_r917 import (
    LocalLabAuthorization,
)
from core.bounty_agent.autonomy.local_lab_r917 import (
    LabBoundaryError,
)

REQUIRED_HEADERS = {
    "strict-transport-security": "HTTPS transport protection",
    "content-security-policy": "Browser content restrictions",
    "x-content-type-options": "MIME sniffing protection",
    "x-frame-options": "Frame embedding protection",
}


def assess_local_headers(*, authorization, evidence_dir):
    if not isinstance(authorization, LocalLabAuthorization):
        raise LabBoundaryError("Authorization required")

    authorization.require()

    output = Path(evidence_dir)
    if not output.is_dir() or output.is_symlink():
        raise LabBoundaryError("Invalid evidence directory")

    connection = http.client.HTTPConnection(
        "127.0.0.1", 3000, timeout=5
    )

    try:
        connection.connect()
        if connection.sock.getpeername()[0] != "127.0.0.1":
            raise LabBoundaryError("Unexpected network peer")

        connection.request(
            "GET", "/",
            headers={"Connection": "close"},
        )
        response = connection.getresponse()

        if 300 <= response.status < 400:
            raise LabBoundaryError("Redirect rejected")

        headers = {
            key.lower(): value
            for key, value in response.getheaders()
        }

        findings = [
            {
                "header": header,
                "description": description,
                "classification": "security_hardening_observation",
                "validated_vulnerability": False,
                "human_review_required": True,
            }
            for header, description in REQUIRED_HEADERS.items()
            if header not in headers
            and header != "strict-transport-security"
        ]

        result = {
            "schema": "jarvis.bounty.lab_assessment.r917c1",
            "target": "http://127.0.0.1:3000/",
            "status": response.status,
            "headers": headers,
            "findings": findings,
            "validated_vulnerabilities": 0,
            "submission_authorized": False,
        }

    except (OSError, http.client.HTTPException) as exc:
        raise LabBoundaryError("Assessment request failed") from exc
    finally:
        connection.close()

    encoded = json.dumps(
        result, sort_keys=True, indent=2
    ).encode("utf-8")

    digest = hashlib.sha256(encoded).hexdigest()
    path = output / f"header-assessment-{digest[:16]}.json"

    with path.open("xb") as handle:
        handle.write(encoded)

    return {
        "status": "awaiting_human_review",
        "evidence_path": str(path),
        "sha256": digest,
        "findings": findings,
    }
