from collections import defaultdict
from .result import AcceptanceStatus

def summarize_results(results):
    values = tuple(results)
    domains = defaultdict(lambda: {"total":0,"passed":0,"failed":0,"errors":0,"skipped":0})
    for item in values:
        bucket = domains[item.domain]
        bucket["total"] += 1
        if item.status is AcceptanceStatus.PASS: bucket["passed"] += 1
        elif item.status is AcceptanceStatus.FAIL: bucket["failed"] += 1
        elif item.status is AcceptanceStatus.ERROR: bucket["errors"] += 1
        else: bucket["skipped"] += 1
    total = len(values)
    passed = sum(x.status is AcceptanceStatus.PASS for x in values)
    durations = [x.duration_ms for x in values]
    return {
        "total": total, "passed": passed,
        "failed": sum(x.status is AcceptanceStatus.FAIL for x in values),
        "errors": sum(x.status is AcceptanceStatus.ERROR for x in values),
        "skipped": sum(x.status is AcceptanceStatus.SKIP for x in values),
        "pass_rate": 0.0 if not total else passed / total,
        "average_duration_ms": 0.0 if not durations else sum(durations)/len(durations),
        "domains": {k: dict(v) for k,v in sorted(domains.items())},
    }
