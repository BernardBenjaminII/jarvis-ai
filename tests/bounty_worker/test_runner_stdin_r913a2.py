import sys
import threading

from core.bounty_worker.runner import run_bounded


def test_stdin_delivery():
    result = run_bounded(
        [
            sys.executable,
            "-I",
            "-c",
            "import sys; print(len(sys.stdin.buffer.read()))",
        ],
        stdin_text="x" * 4096,
        timeout=3,
    )

    assert result["state"] == "completed"
    assert result["returncode"] == 0
    assert result["output"].strip() == "4096"


def test_timeout_when_child_does_not_read_stdin():
    result = run_bounded(
        [
            sys.executable,
            "-I",
            "-c",
            "import time; time.sleep(10)",
        ],
        stdin_text="x" * 4096,
        timeout=0.2,
    )

    assert result["state"] == "timeout"


def test_cancel_while_child_does_not_read_stdin():
    cancel = threading.Event()
    timer = threading.Timer(0.15, cancel.set)

    timer.start()

    try:
        result = run_bounded(
            [
                sys.executable,
                "-I",
                "-c",
                "import time; time.sleep(10)",
            ],
            stdin_text="x" * 4096,
            timeout=3,
            cancel=cancel,
        )
    finally:
        timer.cancel()
        timer.join()

    assert result["state"] == "cancelled"
