"""Genesis VII-A0 Pack 4A-3.2 certification tests."""
from __future__ import annotations

import multiprocessing
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from core.executive.events import ExecutiveEventBus
from core.executive.events.runtime import resolve_default_timeline_root
from core.executive.timeline import (
    ExecutiveTimelineRepository,
    TimelineEventDraft,
    TimelineEventKind,
    TimelineSubsystem,
)


def _publish_worker(root: str, count: int) -> None:
    bus = ExecutiveEventBus(
        repository=ExecutiveTimelineRepository(root)
    )
    for index in range(count):
        bus.publish(
            TimelineEventDraft(
                subsystem=TimelineSubsystem.SYSTEM,
                kind=TimelineEventKind.NOTE_RECORDED,
                payload={
                    "process": os.getpid(),
                    "index": index,
                },
            )
        )


class GenesisVIIA0Pack4A32Tests(unittest.TestCase):
    def test_stale_bus_reloads_and_retries(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            first = ExecutiveEventBus(
                repository=ExecutiveTimelineRepository(root),
                event_id_factory=lambda sequence: (
                    f"first-{sequence:04d}"
                ),
            )
            stale = ExecutiveEventBus(
                repository=ExecutiveTimelineRepository(root),
                event_id_factory=lambda sequence: (
                    f"stale-{sequence:04d}"
                ),
            )

            first_event = first.publish(
                TimelineEventDraft(
                    subsystem=TimelineSubsystem.SYSTEM,
                    kind=TimelineEventKind.NOTE_RECORDED,
                    payload={"writer": "first"},
                )
            ).event

            second_event = stale.publish(
                TimelineEventDraft(
                    subsystem=TimelineSubsystem.SYSTEM,
                    kind=TimelineEventKind.NOTE_RECORDED,
                    payload={"writer": "stale"},
                )
            ).event

            self.assertEqual(first_event.sequence, 1)
            self.assertEqual(second_event.sequence, 2)

            repository = ExecutiveTimelineRepository(root)
            self.assertEqual(
                [event.sequence for event in repository.events],
                [1, 2],
            )
            self.assertTrue(repository.verify().certified)

    def test_two_processes_preserve_one_certified_chain(self) -> None:
        with TemporaryDirectory() as directory:
            context = multiprocessing.get_context("spawn")
            workers = [
                context.Process(
                    target=_publish_worker,
                    args=(directory, 4),
                )
                for _ in range(2)
            ]

            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join(timeout=20)
                self.assertEqual(worker.exitcode, 0)

            repository = ExecutiveTimelineRepository(directory)
            self.assertEqual(len(repository.events), 8)
            self.assertEqual(
                [event.sequence for event in repository.events],
                list(range(1, 9)),
            )
            self.assertTrue(repository.verify().certified)

    def test_explicit_timeline_root_has_priority(self) -> None:
        previous = os.environ.get(
            "JARVIS_EXECUTIVE_TIMELINE_ROOT"
        )
        try:
            with TemporaryDirectory() as directory:
                os.environ[
                    "JARVIS_EXECUTIVE_TIMELINE_ROOT"
                ] = directory
                self.assertEqual(
                    resolve_default_timeline_root(),
                    Path(directory).resolve(),
                )
        finally:
            if previous is None:
                os.environ.pop(
                    "JARVIS_EXECUTIVE_TIMELINE_ROOT",
                    None,
                )
            else:
                os.environ[
                    "JARVIS_EXECUTIVE_TIMELINE_ROOT"
                ] = previous


if __name__ == "__main__":
    unittest.main()
