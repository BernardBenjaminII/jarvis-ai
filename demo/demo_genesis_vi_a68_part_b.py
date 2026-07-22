from tests.test_genesis_vi_a68_part_b import fixture_repository
from core.executive.timeline import TimelineQueryEngine, assess_replay_readiness

def main():
    repo = fixture_repository(); engine = TimelineQueryEngine(repo); stats = engine.statistics(); report = assess_replay_readiness(repo)
    print("="*72); print("GENESIS VI-A6.8 PART B — TIMELINE QUERY ENGINE DEMO"); print("="*72)
    print("\nMission m1 history")
    for event in engine.by_mission("m1"): print(f"  {event.sequence:02d} {event.subsystem:<12} {event.event_kind}")
    print("\nLatest two events")
    for event in engine.latest(2): print(f"  {event.sequence:02d} {event.subsystem:<12} {event.event_kind}")
    print("\nRepository statistics")
    print(f"  Events      : {stats.total_events}"); print(f"  Fingerprint : {stats.fingerprint}")
    print("\nReplay readiness")
    for finding in report.findings: print(f"  [{'PASS' if finding.passed else 'FAIL'}] {finding.code}: {finding.detail}")
    print("\nExecutive Timeline Repository"); print("CERTIFIED" if report.ready else "NOT CERTIFIED"); print("Replay Ready" if report.ready else "Replay Blocked")

if __name__ == "__main__": main()
