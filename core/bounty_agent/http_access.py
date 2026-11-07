"""R9.12D: HTTP access gate for bounty control routes."""

import hmac
import os

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

basic = HTTPBasic(auto_error=False)


def require_bounty_access(
    credentials: HTTPBasicCredentials | None = Depends(basic),
):
    username = os.environ.get("JARVIS_BOUNTY_USER", "")
    password = os.environ.get("JARVIS_BOUNTY_PASSWORD", "")

    if not username or len(password) < 32:
        raise HTTPException(
            status_code=503,
            detail="Bounty API authentication is not configured",
        )

    valid = (
        credentials is not None
        and hmac.compare_digest(
            credentials.username.encode(),
            username.encode(),
        )
        and hmac.compare_digest(
            credentials.password.encode(),
            password.encode(),
        )
    )

    if not valid:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": 'Basic realm="JARVIS Bounty"'},
        )
