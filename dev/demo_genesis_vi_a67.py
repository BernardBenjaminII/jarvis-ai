#!/usr/bin/env python3
from datetime import datetime, timedelta, timezone
from core.executive.timeline import *

BASE = datetime(2026, 7, 22, 8, 41, 12, tzinfo=timezone.utc)
timeline = ExecutiveTimelineEngine(event_id_factory=lambda n: f"timeline-event-{n:04d}")

def add(offset, subsystem, kind, payload, parent=None):
    return timeline.append(TimelineEventDraft(
        subsystem=subsystem, kind=kind,
        context=TimelineContext(
            session_id="executive-session-demo",
            mission_id="mission-network-001",
            correlation_id="investigation-cycle-001",
        ),
        payload=payload, parent_event_id=parent,
        occurred_at=BASE + timedelta(seconds=offset),
    ))

boot = add(0, TimelineSubsystem.EXECUTIVE, TimelineEventKind.EXECUTIVE_BOOT_STARTED, {"state": "booting"})
add(1, TimelineSubsystem.EXECUTIVE, TimelineEventKind.EXECUTIVE_BOOT_COMPLETED, {"state": "ready"}, boot.event_id)
mission = add(2, TimelineSubsystem.MISSION, TimelineEventKind.MISSION_STARTED, {"title": "Investigate suspicious network activity"})
obs = add(3, TimelineSubsystem.OBSERVATION, TimelineEventKind.OBSERVATION_RECEIVED, {"summary": "Unexpected outbound connection"}, mission.event_id)
add(4, TimelineSubsystem.KNOWLEDGE, TimelineEventKind.KNOWLEDGE_RETRIEVED, {"evidence_count": 4}, obs.event_id)
reason = add(5, TimelineSubsystem.REASONING, TimelineEventKind.REASONING_STARTED, {"strategy": "hypothesis evaluation"}, obs.event_id)
hyp = add(6, TimelineSubsystem.REASONING, TimelineEventKind.HYPOTHESIS_SELECTED, {"hypothesis": "Unapproved service", "confidence": 0.88}, reason.event_id)
decision = add(7, TimelineSubsystem.DECISION, TimelineEventKind.DECISION_CERTIFIED, {"decision": "Isolate process"}, hyp.event_id)
add(8, TimelineSubsystem.PERSISTENCE, TimelineEventKind.CHECKPOINT_CREATED, {"checkpoint_id": "checkpoint-0043"}, decision.event_id)

print("=" * 94)
print("AUTHORITATIVE EXECUTIVE TIMELINE")
print("=" * 94)
for e in timeline.events:
    print(f"{e.sequence:03d}  {e.occurred_at:%H:%M:%S}  {e.subsystem.value:<12} {e.kind.value:<30} {dict(e.payload)}")

report = timeline.verify()
print("\n" + "=" * 94)
print("TIMELINE INTEGRITY CERTIFICATION")
print("=" * 94)
print(f"Certified            : {report.certified}")
print(f"Event count          : {report.event_count}")
print(f"Terminal fingerprint : {report.terminal_fingerprint}")
print(f"Report fingerprint   : {report.report_fingerprint}")
print(f"Findings             : {report.findings or 'NONE'}")
print("\nGENESIS VI-A6.7 TEST DRIVE COMPLETE")
