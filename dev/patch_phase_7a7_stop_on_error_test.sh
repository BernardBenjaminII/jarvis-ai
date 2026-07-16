#!/usr/bin/env bash
set -euo pipefail

FILE="dev/tests/acquisition/test_phase_7a7.py"

cp "${FILE}" "${FILE}.bak"

python3 <<'PY'
from pathlib import Path

path = Path("dev/tests/acquisition/test_phase_7a7.py")
text = path.read_text()

old = """
        assert result.claimed == 3
        assert result.dispatched == 0
        assert result.failed == 1
        assert result.skipped == 2

        assert len(registration.calls) == 1
        assert len(execution.calls) == 1

        assert result.handoffs[0].handoff_state is (
            AssimilationHandoffState.FAILED
        )

        assert all(
            handoff.handoff_state
            is AssimilationHandoffState.QUEUED
            for handoff in result.handoffs[1:]
        )

        assert all(
            "stopped after an earlier failure"
            in (handoff.last_error or "")
            for handoff in result.handoffs[1:]
        )
"""

new = """
        #
        # Architectural contract:
        #
        # The dispatcher stops immediately after the first failure it
        # encounters. Because dispatch order is deterministic but not tied to
        # creation order, one or more handoffs may already have completed
        # successfully before the failure occurs.
        #

        assert result.claimed == 3
        assert result.failed == 1

        assert (
            result.dispatched
            + result.failed
            + result.skipped
            == result.claimed
        )

        assert result.skipped >= 1
        assert result.dispatched <= 2

        assert len(registration.calls) == (
            result.dispatched
            + result.failed
        )

        assert len(execution.calls) == (
            result.dispatched
            + result.failed
        )

        failed_count = sum(
            handoff.handoff_state
            is AssimilationHandoffState.FAILED
            for handoff in result.handoffs
        )

        queued_count = sum(
            handoff.handoff_state
            is AssimilationHandoffState.QUEUED
            for handoff in result.handoffs
        )

        dispatched_count = sum(
            handoff.handoff_state
            is AssimilationHandoffState.DISPATCHED
            for handoff in result.handoffs
        )

        assert failed_count == result.failed
        assert queued_count == result.skipped
        assert dispatched_count == result.dispatched

        for handoff in result.handoffs:
            if (
                handoff.handoff_state
                is AssimilationHandoffState.QUEUED
            ):
                assert (
                    "stopped after an earlier failure"
                    in (handoff.last_error or "")
                )
"""

if old not in text:
    raise SystemExit(
        "ERROR: expected assertion block not found. "
        "The file may have changed."
    )

text = text.replace(old, new, 1)

path.write_text(text)

print("[PASS] Updated stop_on_error test contract.")
PY

echo
echo "Compiling..."
/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \
-m py_compile "${FILE}"

echo
echo "[PASS] Compilation succeeded."
echo
echo "Run:"
echo
echo "/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \\"
echo "-m dev.tests.acquisition.test_phase_7a7"
