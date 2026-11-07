"""R9.17B: tightly scoped local Juice Shop observation."""

from __future__ import annotations

import hashlib
import http.client
import json
import os
import socket
import time
from pathlib import Path

from core.bounty_agent.autonomy.lab_authorization_r917 import (
    LocalLabAuthorization,
)

HOST = "127.0.0.1"
PORT = 3000
MAX_BODY = 65536


class LabBoundaryError(RuntimeError):
    pass


def observe_local_juice_shop(
    *, evidence_dir, authorization=None, timeout=5
):
    """One GET / against the loopback lab; no redirects or scanning."""
    if not isinstance(authorization, LocalLabAuthorization):
        raise LabBoundaryError("Explicit lab authorization required")

    authorization.require()

    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool):
        raise LabBoundaryError("Invalid timeout")
    if not 0 < timeout <= 10:
        raise LabBoundaryError("Timeout outside permitted range")

    output = Path(evidence_dir).resolve()
    if not output.is_dir() or output.is_symlink():
        raise LabBoundaryError("Evidence directory must exist")

    connection = http.client.HTTPConnection(HOST, PORT, timeout=timeout)
    try:
        connection.connect()
        if connection.sock.getpeername()[0] != HOST:
            raise LabBoundaryError("Unexpected network peer")

        connection.request(
            "GET", "/",
            headers={
                "Host": f"{HOST}:{PORT}",
                "Accept": "text/html",
                "Connection": "close",
            },
        )
        response = connection.getresponse()
        if 300 <= response.status < 400:
            raise LabBoundaryError("HTTP redirect rejected")

        body = response.read(MAX_BODY + 1)
        if len(body) > MAX_BODY:
            raise LabBoundaryError("Response exceeds evidence limit")

        evidence = {
            "schema": "jarvis.bounty.local_observation.r917b",
            "source": "local_juice_shop_adapter",
            "target": f"http://{HOST}:{PORT}/",
            "method": "GET",
            "path": "/",
            "status": response.status,
            "content_type": response.getheader("Content-Type"),
            "body_size": len(body),
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "observed_at_unix": time.time(),
            "authorization": {
                "target": authorization.target,
                "method": authorization.method,
                "path": authorization.path,
                "approved": authorization.approved,
            },
            "validated_vulnerability": False,
            "submission_authorized": False,
        }
    except (OSError, http.client.HTTPException) as exc:
        raise LabBoundaryError("Local lab request failed") from exc
    finally:
        connection.close()

    encoded = json.dumps(
        evidence, sort_keys=True, indent=2, allow_nan=False
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    path = output / f"local-observation-{digest[:16]}.json"

    try:
        fd = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
        )
    except FileExistsError as exc:
        raise LabBoundaryError(
            "Evidence already exists; refusing overwrite"
        ) from exc

    with os.fdopen(fd, "wb") as handle:
        handle.write(encoded)

    return {
        "status": "awaiting_human_review",
        "evidence_path": str(path),
        "evidence_sha256": digest,
        "observation": evidence,
    }
