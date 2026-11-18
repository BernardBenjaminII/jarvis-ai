import io

import pytest

from core.bounty_worker import runner


def test_selector_failure_still_cleans_up(monkeypatch):
    """A selector setup failure must not abandon the child."""

    calls = []

    class FakeOutput(io.BytesIO):
        def fileno(self):
            return 42

    class FakeProcess:
        pid = 123456
        stdin = None

        def __init__(self):
            self.stdout = FakeOutput(b"")

        def wait(self):
            calls.append("wait")
            return 0

    class BrokenSelector:
        def register(self, *args):
            raise OSError("simulated selector failure")

        def close(self):
            calls.append("selector_close")

    monkeypatch.setattr(
        runner.subprocess,
        "Popen",
        lambda *args, **kwargs: FakeProcess(),
    )

    monkeypatch.setattr(
        runner.selectors,
        "DefaultSelector",
        BrokenSelector,
    )

    # FakeOutput has no real OS file descriptor.
    monkeypatch.setattr(
        runner.os,
        "set_blocking",
        lambda fd, blocking: None,
    )

    monkeypatch.setattr(
        runner.os,
        "killpg",
        lambda *args: calls.append("killpg"),
    )

    with pytest.raises(
        OSError,
        match="simulated selector failure",
    ):
        runner.run_bounded(["synthetic-tool"])

    assert "killpg" in calls
    assert "wait" in calls
    assert "selector_close" in calls
