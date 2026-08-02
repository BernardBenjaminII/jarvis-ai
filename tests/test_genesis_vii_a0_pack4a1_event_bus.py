"""Genesis VII-A0 Pack 4A-1 certification tests."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from core.executive.events import ExecutiveEventBus
from core.executive.timeline import (
    ExecutiveTimelineRepository,
    TimelineContext,
    TimelineEventDraft,
    TimelineEventKind,
    TimelineSubsystem,
)


class GenesisVIIA0Pack4A1Tests(unittest.TestCase):
    def build_bus(self, root: Path) -> ExecutiveEventBus:
        return ExecutiveEventBus(
            repository=ExecutiveTimelineRepository(root),
            event_id_factory=lambda sequence: f"event-{sequence:04d}",
        )

    def draft(
        self,
        *,
        kind: TimelineEventKind = TimelineEventKind.MISSION_CREATED,
        parent_event_id: str | None = None,
    ) -> TimelineEventDraft:
        return TimelineEventDraft(
            subsystem=TimelineSubsystem.MISSION,
            kind=kind,
            context=TimelineContext(
                session_id="session-1",
                mission_id="mission-1",
                correlation_id="correlation-1",
            ),
            payload={"summary": "Mission event"},
            parent_event_id=parent_event_id,
        )

    def test_publish_creates_persists_and_returns_event(self) -> None:
        with TemporaryDirectory() as directory:
            bus = self.build_bus(Path(directory))
            publication = bus.publish(self.draft())
            self.assertEqual(publication.event.sequence, 1)
            self.assertEqual(publication.event.event_id, "event-0001")
            self.assertTrue(publication.event.verify_fingerprint())
            self.assertEqual(bus.repository.events, (publication.event,))
            self.assertTrue(bus.verify().certified)

    def test_bus_hydrates_from_existing_repository(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            first_bus = self.build_bus(root)
            first = first_bus.publish(self.draft()).event
            second_bus = self.build_bus(root)
            second = second_bus.publish(
                self.draft(
                    kind=TimelineEventKind.MISSION_STARTED,
                    parent_event_id=first.event_id,
                )
            ).event
            self.assertEqual(second.sequence, 2)
            self.assertEqual(
                second.previous_event_fingerprint,
                first.event_fingerprint,
            )
            self.assertTrue(second_bus.verify().certified)

    def test_subscribers_receive_only_persisted_events(self) -> None:
        with TemporaryDirectory() as directory:
            bus = self.build_bus(Path(directory))
            observed = []
            subscription = bus.subscribe(observed.append, name="test-subscriber")
            publication = bus.publish(self.draft())
            self.assertEqual(observed, [publication.event])
            self.assertEqual(publication.delivered_subscribers, 1)
            self.assertTrue(publication.fully_delivered)
            self.assertTrue(bus.unsubscribe(subscription))

    def test_subscriber_failure_is_isolated(self) -> None:
        with TemporaryDirectory() as directory:
            bus = self.build_bus(Path(directory))
            observed = []
            def failing_subscriber(event) -> None:
                raise RuntimeError("subscriber failed")
            bus.subscribe(failing_subscriber, name="failing-subscriber")
            bus.subscribe(observed.append, name="healthy-subscriber")
            publication = bus.publish(self.draft())
            self.assertEqual(observed, [publication.event])
            self.assertEqual(publication.delivered_subscribers, 1)
            self.assertEqual(len(publication.subscriber_failures), 1)
            self.assertEqual(len(bus.repository.events), 1)

    def test_closed_registry_rejects_string_subsystem(self) -> None:
        with TemporaryDirectory() as directory:
            bus = self.build_bus(Path(directory))
            draft = TimelineEventDraft(
                subsystem="mission",  # type: ignore[arg-type]
                kind=TimelineEventKind.MISSION_CREATED,
            )
            from core.executive.timeline.contracts import (
                InvalidTimelineEventError,
            )

            with self.assertRaises(InvalidTimelineEventError):
                bus.publish(draft)

    def test_closed_registry_rejects_string_kind(self) -> None:
        with TemporaryDirectory() as directory:
            bus = self.build_bus(Path(directory))
            draft = TimelineEventDraft(
                subsystem=TimelineSubsystem.MISSION,
                kind="mission_created",  # type: ignore[arg-type]
            )
            from core.executive.timeline.contracts import (
                InvalidTimelineEventError,
            )

            with self.assertRaises(InvalidTimelineEventError):
                bus.publish(draft)


if __name__ == "__main__":
    unittest.main()
