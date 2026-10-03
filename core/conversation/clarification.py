"""Small session-aware clarification gate for ambiguous conversation requests.

R1 deliberately handles a narrow class of high-value ambiguity rather than
attempting to classify every vague utterance in the conversation layer.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import threading
import time


_PENDING_TTL_SECONDS = 15 * 60

_LOCK = threading.RLock()
_PENDING: dict[str, "PendingClarification"] = {}


@dataclass(frozen=True)
class PendingClarification:
    session_id: str
    original_input: str
    kind: str
    created_monotonic: float


@dataclass(frozen=True)
class ClarificationDecision:
    action: str
    prompt: str | None = None
    resolved_input: str | None = None
    original_input: str | None = None
    resolution: str | None = None

    @property
    def requires_clarification(self) -> bool:
        return self.action == "ask"

    @property
    def resolved(self) -> bool:
        return self.action == "resolved"


_SECURITY_DOMAIN_PATTERNS = {
    "physical": (
        r"\bphysical(?:\s+security)?\b",
        r"\bpersonal security\b",
    ),
    "cybersecurity": (
        r"\bcyber(?:security)?\b",
        r"\binformation security\b",
        r"\binfosec\b",
        r"\bcomputer security\b",
        r"\bnetwork security\b",
    ),
    "communications": (
        r"\bcommunications? security\b",
        r"\bcomms? security\b",
        r"\bcomsec\b",
    ),
    "operational": (
        r"\boperational security\b",
        r"\bopsec\b",
    ),
}


_SHORT_RESOLUTIONS = {
    "physical": "physical",
    "physical security": "physical",

    "cyber": "cybersecurity",
    "cyber security": "cybersecurity",
    "cybersecurity": "cybersecurity",

    "communications": "communications",
    "communication": "communications",
    "communications security": "communications",
    "communication security": "communications",
    "comms": "communications",
    "comsec": "communications",

    "operational": "operational",
    "operational security": "operational",
    "opsec": "operational",
}


_DOMAIN_PHRASES = {
    "physical": "physical security",
    "cybersecurity": "cybersecurity",
    "communications": "communications security",
    "operational": "operational security",
}


_CLARIFICATION_PROMPT = (
    "Do you mean physical security, cybersecurity, "
    "communications security, or operational security?"
)


def _normalize(value: str) -> str:
    return " ".join(
        str(value or "")
        .strip()
        .strip('"\'“”‘’')
        .lower()
        .split()
    ).rstrip(".?!")


def _purge_expired(now: float | None = None) -> None:
    now = time.monotonic() if now is None else now

    expired = [
        session_id
        for session_id, pending in _PENDING.items()
        if now - pending.created_monotonic > _PENDING_TTL_SECONDS
    ]

    for session_id in expired:
        _PENDING.pop(session_id, None)


def _explicit_security_domain(text: str) -> str | None:
    normalized = _normalize(text)

    for domain, patterns in _SECURITY_DOMAIN_PATTERNS.items():
        if any(re.search(pattern, normalized, re.I) for pattern in patterns):
            return domain

    return None


def security_question_is_ambiguous(text: str) -> bool:
    """Return True for broad actionable security questions lacking a domain."""

    normalized = _normalize(text)

    if not normalized:
        return False

    if not re.search(r"\bsecurity\b", normalized):
        return False

    if _explicit_security_domain(normalized) is not None:
        return False

    # Do not intercept simple catalog/source/document searches merely because
    # the title or subject contains the word security.
    if re.search(
        r"\b(?:find|show|list|locate|search|which|what)\b.*"
        r"\b(?:manual|manuals|document|documents|pdf|pdfs|file|files|source|sources)\b",
        normalized,
    ):
        return False

    # R1 targets requests whose answer materially changes by security domain.
    actionable = re.search(
        r"\b(?:how|improve|strengthen|increase|better|protect|secure|"
        r"posture|stance|practices?|measures?|recommend|recommendations?|"
        r"advice|what should|what can)\b",
        normalized,
    )

    return bool(actionable)


def _resolve_short_reply(text: str) -> str | None:
    normalized = _normalize(text)

    # Keep follow-up resolution conservative. A full new question should not
    # accidentally be swallowed as an answer to an old clarification.
    if len(normalized.split()) > 5:
        return None

    return _SHORT_RESOLUTIONS.get(normalized)


def _resolved_security_question(original: str, domain: str) -> str:
    phrase = _DOMAIN_PHRASES[domain]

    # Replace only the first standalone occurrence of "security".
    resolved, count = re.subn(
        r"\bsecurity\b",
        phrase,
        original,
        count=1,
        flags=re.I,
    )

    if count:
        return resolved

    # Defensive fallback; normally impossible for this clarification kind.
    return f"{original.rstrip()} ({phrase})"


def process_clarification(
    *,
    session_id: str,
    operator_input: str,
) -> ClarificationDecision:
    """Handle a pending clarification or detect a new ambiguous request."""

    session_key = str(session_id or "executive-session")
    text = str(operator_input or "")

    with _LOCK:
        _purge_expired()

        pending = _PENDING.get(session_key)

        if pending is not None:
            if pending.kind == "security_domain":
                resolution = _resolve_short_reply(text)

                if resolution is not None:
                    _PENDING.pop(session_key, None)

                    return ClarificationDecision(
                        action="resolved",
                        resolved_input=_resolved_security_question(
                            pending.original_input,
                            resolution,
                        ),
                        original_input=pending.original_input,
                        resolution=resolution,
                    )

            # A substantive new utterance means the user changed direction.
            # Clear stale clarification and process the new request normally.
            if len(_normalize(text).split()) > 5 or "?" in text:
                _PENDING.pop(session_key, None)

        if security_question_is_ambiguous(text):
            _PENDING[session_key] = PendingClarification(
                session_id=session_key,
                original_input=text,
                kind="security_domain",
                created_monotonic=time.monotonic(),
            )

            return ClarificationDecision(
                action="ask",
                prompt=_CLARIFICATION_PROMPT,
                original_input=text,
            )

    return ClarificationDecision(action="continue")


def pending_clarification(session_id: str) -> PendingClarification | None:
    """Read-only diagnostic/test helper."""

    with _LOCK:
        _purge_expired()
        return _PENDING.get(str(session_id or "executive-session"))


def clear_pending_clarification(session_id: str) -> None:
    """Explicit test/administrative cleanup helper."""

    with _LOCK:
        _PENDING.pop(str(session_id or "executive-session"), None)
