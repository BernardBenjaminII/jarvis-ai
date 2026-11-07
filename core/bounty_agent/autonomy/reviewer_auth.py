"""R9.14D.6D.2A: offline reviewer credential verification.

This module authenticates a reviewer but does not issue
approvals or authorize execution.
"""

import hmac
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
)


class ReviewerAuthenticationError(PermissionError):
    pass


@dataclass(frozen=True)
class AuthenticatedReviewer:
    identity: str


class ReviewerAuthenticator:
    def __init__(self, identity, password_hash):
        if not isinstance(identity, str) or not identity.strip():
            raise ValueError("Reviewer identity required")

        if not isinstance(password_hash, str) or not password_hash:
            raise ValueError("Password hash required")

        self.identity = identity
        self.password_hash = password_hash
        self.hasher = PasswordHasher()

    def authenticate(self, identity, password):
        if not isinstance(identity, str) or not isinstance(password, str):
            raise ReviewerAuthenticationError(
                "Invalid reviewer credentials"
            )

        valid_identity = hmac.compare_digest(
            identity.encode(),
            self.identity.encode(),
        )

        try:
            valid_password = self.hasher.verify(
                self.password_hash,
                password,
            )
        except (VerificationError, InvalidHashError):
            valid_password = False

        if not (valid_identity and valid_password):
            raise ReviewerAuthenticationError(
                "Invalid reviewer credentials"
            )

        return AuthenticatedReviewer(identity=self.identity)
