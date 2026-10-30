import os

from core.bounty_worker.process_identity import (
    current_identity,
    identity_status,
    process_identity,
)


def test_current_process_identity():
    identity = current_identity()
    assert identity is not None
    assert identity["pid"] == os.getpid()
    assert identity["boot_id"]
    assert identity["start_ticks"] >= 0
    assert identity_status(identity) == "same_process"


def test_rejects_invalid_pid():
    import pytest

    for pid in (-1, 0, True, "123"):
        with pytest.raises(ValueError):
            process_identity(pid)


def test_detects_replaced_process_identity():
    identity = current_identity()
    assert identity is not None

    modified = dict(identity)
    modified["start_ticks"] += 1

    assert identity_status(modified) == (
        "absent_or_replaced"
    )


def test_invalid_identity_is_unknown():
    assert identity_status({}) == "unknown"
    assert identity_status(None) == "unknown"
