"""Offline tests for dedicated reviewer authentication."""

import pytest
from argon2 import PasswordHasher

from core.bounty_agent.autonomy.reviewer_auth import (
    ReviewerAuthenticator,
    ReviewerAuthenticationError,
)


@pytest.fixture
def authenticator():
    password_hash = PasswordHasher().hash(
        "synthetic-test-password-with-sufficient-length"
    )
    return ReviewerAuthenticator(
        identity="synthetic-reviewer",
        password_hash=password_hash,
    )


def test_valid_reviewer(authenticator):
    reviewer = authenticator.authenticate(
        "synthetic-reviewer",
        "synthetic-test-password-with-sufficient-length",
    )
    assert reviewer.identity == "synthetic-reviewer"


def test_wrong_password_rejected(authenticator):
    with pytest.raises(ReviewerAuthenticationError):
        authenticator.authenticate(
            "synthetic-reviewer",
            "wrong-password",
        )


def test_wrong_identity_rejected(authenticator):
    with pytest.raises(ReviewerAuthenticationError):
        authenticator.authenticate(
            "different-reviewer",
            "synthetic-test-password-with-sufficient-length",
        )


def test_missing_credentials_rejected(authenticator):
    with pytest.raises(ReviewerAuthenticationError):
        authenticator.authenticate(None, None)


def test_malformed_hash_rejected():
    authenticator = ReviewerAuthenticator(
        identity="synthetic-reviewer",
        password_hash="invalid-hash",
    )

    with pytest.raises(ReviewerAuthenticationError):
        authenticator.authenticate(
            "synthetic-reviewer",
            "synthetic-password",
        )
