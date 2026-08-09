from __future__ import annotations
import json
from pathlib import Path

MARKER="# Genesis IX-A4.7 Pack 3 — grounded answer telemetry route"
ROUTE="""
# Genesis IX-A4.7 Pack 3 — grounded answer telemetry route
@router.get("/executive/grounded-answer")
def operations_grounded_answer_telemetry() -> dict[str, Any]:
    from core.conversation.grounded_answer.telemetry import get_grounded_answer_telemetry_store
    return get_grounded_answer_telemetry_store().projection()
"""
TAG='<script src="/mission-control/static/grounded_answer_projection.js" defer></script>'

def main():
    root=Path.cwd().resolve()
    route=root/"core/src/routes/operations.py"; text=route.read_text()
    rs="already_integrated"
    if MARKER not in text:
        if "router = APIRouter(" not in text or "Any" not in text:
            raise RuntimeError("Operations route module does not match audited surface.")
        route.write_text(text.rstrip()+"\n\n"+ROUTE.lstrip()); rs="integrated"
    index=root/"core/src/static/mission_control/index.html"; html=index.read_text()
    us="already_integrated"
    if TAG not in html:
        anchor='<script src="/mission-control/static/timeline_projection.js" defer></script>'
        if anchor in html: html=html.replace(anchor,anchor+"\n    "+TAG,1)
        elif "</body>" in html: html=html.replace("</body>","    "+TAG+"\n</body>",1)
        else: raise RuntimeError("Mission Control insertion point not found.")
        index.write_text(html); us="integrated"
    report={"route":rs,"mission_control":us,"endpoint":"/operations/executive/grounded-answer"}
    out=root/"docs/audits/genesis_ix_a4_7_pack3"; out.mkdir(parents=True,exist_ok=True)
    (out/"transparency_integration.json").write_text(json.dumps(report,indent=2)+"\n")
    (out/"transparency_integration.md").write_text(f"# Genesis IX-A4.7 Pack 3\n\n**Route:** `{rs}`\n**Mission Control:** `{us}`\n")
    print("[PASS] Grounded-answer route:",rs); print("[PASS] Mission Control projection:",us)
    return 0
if __name__=="__main__": raise SystemExit(main())
