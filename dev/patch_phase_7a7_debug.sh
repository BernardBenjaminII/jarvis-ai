#!/usr/bin/env bash
set -euo pipefail

FILE="dev/tests/acquisition/test_phase_7a7.py"

cp "${FILE}" "${FILE}.bak"

python3 <<'PY'
from pathlib import Path

path = Path("dev/tests/acquisition/test_phase_7a7.py")
text = path.read_text()

marker = """        result = CanonicalAssimilationDispatcher(
            registration_port=registration,
            execution_port=execution,
        ).dispatch(
            conn=conn,
            limit=3,
            stop_on_error=True,
            timestamp=(
                "2026-07-17T01:00:00+00:00"
            ),
        )
"""

debug = marker + """

        print()
        print("===================================================")
        print("STOP-ON-ERROR DEBUG")
        print("===================================================")

        print("Configured failing object UUID:")
        print(first_object_uuid)

        print()

        print("Dispatch summary")
        print(f"claimed     = {result.claimed}")
        print(f"dispatched  = {result.dispatched}")
        print(f"failed      = {result.failed}")
        print(f"skipped     = {result.skipped}")

        print()

        print("Returned handoffs")
        for handoff in result.handoffs:
            print(
                handoff.handoff_id,
                handoff.handoff_state.value,
                handoff.assimilation_reference,
                handoff.last_error,
            )

        print("===================================================")
"""

if marker not in text:
    raise SystemExit("Unable to locate insertion point.")

text = text.replace(marker, debug, 1)

path.write_text(text)
print("[PASS] Debug instrumentation inserted.")
PY

echo
echo "Now rerun:"
echo
echo "/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \\"
echo "-m dev.tests.acquisition.test_phase_7a7"
