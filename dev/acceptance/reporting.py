import json
from .metrics import summarize_results

def write_reports(run_root, results):
    values = tuple(results)
    summary = summarize_results(values)
    report = [
        "# Executive Acceptance Report", "",
        f"- Tests executed: **{summary['total']}**",
        f"- Passed: **{summary['passed']}**",
        f"- Failed: **{summary['failed']}**",
        f"- Errors: **{summary['errors']}**",
        f"- Pass rate: **{summary['pass_rate']:.1%}**", "",
        "| Test | Domain | Status | Duration |",
        "|---|---|---|---:|",
    ]
    for x in values:
        report.append(f"| `{x.test_id}` | {x.domain} | **{x.status.value}** | {x.duration_ms:.1f} ms |")
    (run_root/"Executive_Acceptance_Report.md").write_text("\n".join(report)+"\n", encoding="utf-8")

    score = ["# Executive Runtime Scorecard", "", "| Domain | Total | Passed | Failed | Errors |", "|---|---:|---:|---:|---:|"]
    for domain, bucket in summary["domains"].items():
        score.append(f"| {domain} | {bucket['total']} | {bucket['passed']} | {bucket['failed']} | {bucket['errors']} |")
    text = "\n".join(score)+"\n"
    (run_root/"Executive_Runtime_Scorecard.md").write_text(text, encoding="utf-8")
    (run_root/"Capability_Matrix.md").write_text(text, encoding="utf-8")
    (run_root/"summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return summary
