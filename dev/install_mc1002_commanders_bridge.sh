#!/usr/bin/env bash
set -euo pipefail

ROOT="${PROJECT_ROOT:-$(pwd)}"
PY="${PYTHON_BIN:-python3}"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/.migration_backups/mc1002_$STAMP"

[ -d "$ROOT/core/src" ] || { echo "Run from the JARVIS repository root."; exit 1; }
mkdir -p "$BACKUP/core/src"

for f in \
  core/src/main.py \
  core/src/routes/mission_control.py \
  core/src/static/mission_control/index.html \
  core/src/static/mission_control/styles.css \
  core/src/static/mission_control/app.js \
  tests/test_mc1002_commanders_bridge.py \
  docs/architecture/commanders_bridge_foundation.md \
  dev/verification/verify_mc1002.py \
  dev/verify_mc1002.sh
do
  if [ -e "$ROOT/$f" ]; then
    mkdir -p "$BACKUP/$(dirname "$f")"
    cp -a "$ROOT/$f" "$BACKUP/$f"
  fi
done

mkdir -p \
  "$ROOT/core/src/routes" \
  "$ROOT/core/src/static/mission_control" \
  "$ROOT/tests" \
  "$ROOT/docs/architecture" \
  "$ROOT/dev/verification"

cat > "$ROOT/core/src/routes/mission_control.py" <<'PY'
"""MC-1002 Commander's Bridge HTTP routes."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


router = APIRouter(tags=["Mission Control"])
INDEX = Path(__file__).resolve().parents[1] / "static" / "mission_control" / "index.html"


@router.get("/bridge", include_in_schema=False)
@router.get("/mission-control", include_in_schema=False)
def commanders_bridge() -> FileResponse:
    if not INDEX.is_file():
        raise HTTPException(503, "Mission Control is unavailable.")
    return FileResponse(INDEX, media_type="text/html", headers={"Cache-Control": "no-store"})
PY

cat > "$ROOT/core/src/static/mission_control/index.html" <<'HTML'
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#090c10">
  <title>JARVIS — Commander's Bridge</title>
  <link rel="stylesheet" href="/mission-control/static/styles.css">
</head>
<body>
<div class="shell">
  <header>
    <div class="identity"><b>J</b><span><small>EXECUTIVE COMMAND SYSTEM</small><strong>JARVIS</strong></span></div>
    <div class="bridge-title">COMMANDER'S BRIDGE <i></i> <time id="clock">--:--:--</time></div>
    <span id="link" class="pill unknown">CONNECTING</span>
  </header>

  <nav>
    <button class="active"><em>01</em>Bridge</button>
    <button disabled><em>02</em>Operations</button>
    <button disabled><em>03</em>Intelligence</button>
    <button disabled><em>04</em>Cognition</button>
    <button disabled><em>05</em>Planning</button>
    <button disabled><em>06</em>Engineering</button>
    <footer><small>MC-1002</small><b>FOUNDATION</b></footer>
  </nav>

  <main>
    <div class="brief">
      <div><small>COMMANDER BRIEF</small><h1>Operational Picture</h1></div>
      <span id="snapshot-time">Awaiting telemetry</span>
    </div>

    <section class="executive panel">
      <div><small>EXECUTIVE STATUS</small><h2 id="status">UNKNOWN</h2><p id="status-detail">Establishing Operations link</p></div>
      <div class="readiness"><b id="readiness">--</b><small>READINESS</small></div>
    </section>

    <div class="grid">
      <section class="panel mission wide">
        <div class="heading"><div><small>PRIMARY MISSION</small><h3 id="mission">No active mission</h3></div><span id="mission-state" class="pill unknown">UNKNOWN</span></div>
        <p id="objective">Awaiting mission projection from Operations.</p>
        <div class="metrics">
          <div><small>ACTIVE</small><b id="active">0</b></div>
          <div><small>QUEUED</small><b id="queued">0</b></div>
          <div><small>COMPLETE</small><b id="complete">0</b></div>
        </div>
      </section>

      <section class="panel divisions">
        <div class="heading"><div><small>EXECUTIVE DIVISIONS</small><h3>Operational Readiness</h3></div></div>
        <div id="divisions-list"></div>
      </section>

      <section class="panel timeline wide">
        <div class="heading"><div><small>OPERATIONAL TIMELINE</small><h3>Recent Activity</h3></div><span id="event-count">0 EVENTS</span></div>
        <ol id="timeline"><li class="empty">No operational events received.</li></ol>
      </section>

      <section class="panel resources">
        <div class="heading"><div><small>RESOURCES</small><h3>Platform Capacity</h3></div></div>
        <div id="resources-list"></div>
      </section>

      <section class="panel recommendations wide">
        <div class="heading"><div><small>COMMANDER ATTENTION</small><h3>Recommendations</h3></div><span id="recommendation-count">0 PENDING</span></div>
        <div id="recommendations" class="empty">No recommendations require authorization.</div>
      </section>

      <section class="panel alerts">
        <div class="heading"><div><small>OPERATIONAL INTEGRITY</small><h3>Alerts</h3></div><span id="alert-count">0 ACTIVE</span></div>
        <div id="alerts" class="empty">No active operational alerts.</div>
      </section>
    </div>

    <section class="command">
      <div><small>COMMAND INTERFACE</small><p>What are your orders?</p></div>
      <button id="refresh" class="primary">Refresh Operational Picture</button>
    </section>
  </main>

  <aside class="statusline">
    <span>OPERATIONS API <b id="api">CONNECTING</b></span>
    <span>LAST SYNC <b id="sync">NEVER</b></span>
    <span>MODE <b>COMMAND</b></span>
  </aside>
</div>
<script src="/mission-control/static/app.js" defer></script>
</body>
</html>
HTML

cat > "$ROOT/core/src/static/mission_control/styles.css" <<'CSS'
:root{color-scheme:dark;--bg:#080a0d;--surface:#0d1116;--raised:#111720;--line:#252d37;--strong:#3a4653;--text:#edf1f4;--muted:#8d98a5;--dim:#5f6b78;--green:#78c99a;--amber:#d8b66a;--red:#d57b7b;--cyan:#79bcc7;--purple:#9f93c9;font-family:Inter,system-ui,sans-serif}
*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:var(--bg);color:var(--text)}button{font:inherit;color:inherit}
.shell{min-height:100vh;display:grid;grid-template:"head head" 72px "nav main" 1fr "status status" 34px/190px 1fr}
header{grid-area:head;display:grid;grid-template-columns:1fr auto 1fr;align-items:center;padding:0 24px;border-bottom:1px solid var(--line);background:#090c10}
.identity{display:flex;align-items:center;gap:12px}.identity>b{display:grid;place-items:center;width:38px;height:38px;border:1px solid var(--strong)}.identity span{display:flex;flex-direction:column}.identity small,small{color:var(--muted);font-size:.65rem;font-weight:700;letter-spacing:.15em}.identity strong{letter-spacing:.25em}
.bridge-title{display:flex;align-items:center;gap:13px;color:var(--muted);font-size:.7rem;font-weight:700;letter-spacing:.14em}.bridge-title i{height:18px;border-left:1px solid var(--strong)}
#link{justify-self:end}.pill{padding:5px 8px;border:1px solid var(--line);font-size:.62rem;font-weight:800;letter-spacing:.1em}
nav{grid-area:nav;display:flex;flex-direction:column;gap:4px;padding:18px 12px;border-right:1px solid var(--line);background:#0a0e13}
nav button{display:grid;grid-template-columns:34px 1fr;align-items:center;min-height:42px;border:1px solid transparent;background:none;text-align:left}nav button.active{border-color:var(--line);background:var(--raised)}nav button:disabled{color:var(--dim)}nav em{font-style:normal;color:var(--dim);font-size:.62rem}nav footer{margin-top:auto;display:flex;flex-direction:column;gap:4px;padding:12px 8px;border-top:1px solid var(--line);font-size:.68rem;letter-spacing:.1em}
main{grid-area:main;min-width:0;padding:28px;overflow:auto}.brief{display:flex;justify-content:space-between;align-items:end;margin-bottom:20px}.brief h1{margin:6px 0 0;font-size:2rem;font-weight:500}.brief>span{color:var(--muted);font-size:.72rem}
.panel{border:1px solid var(--line);background:var(--surface);padding:20px}.executive{min-height:148px;margin-bottom:18px;display:flex;justify-content:space-between;align-items:center;padding:24px 28px}.executive h2{margin:8px 0;font-size:clamp(2rem,4vw,4rem);font-weight:500;letter-spacing:.08em}.executive p{margin:0;color:var(--muted)}
.readiness{width:96px;height:96px;border:1px solid var(--strong);border-radius:50%;display:grid;place-content:center;text-align:center}.readiness b{font-size:1.5rem}.readiness small{font-size:.52rem}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:18px}.grid>section{grid-column:span 5}.grid>.wide{grid-column:span 7}
.heading{display:flex;justify-content:space-between;gap:12px;margin-bottom:18px}.heading h3{margin:5px 0 0;font-size:1rem}.heading>span{color:var(--muted);font-size:.64rem;letter-spacing:.1em}
.mission>p{min-height:46px;color:var(--muted);line-height:1.5}.metrics{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--line)}.metrics div{display:flex;flex-direction:column;gap:6px;padding:14px 12px 0;border-right:1px solid var(--line)}.metrics div:first-child{padding-left:0}.metrics div:last-child{border:0}.metrics b{font-size:1.3rem}
.row{display:flex;justify-content:space-between;align-items:center;min-height:40px;padding:0 10px;margin-top:9px;border:1px solid var(--line);background:#0a0e13}
ol{list-style:none;margin:0;padding:0;max-height:300px;overflow:auto}.event{display:grid;grid-template-columns:88px 1fr;gap:14px;padding:12px 0;border-bottom:1px solid var(--line)}.event time{color:var(--dim);font:11px monospace}.event b{font-size:.82rem}.event p{margin:4px 0 0;color:var(--muted);font-size:.76rem}
.resource{margin-top:14px}.resource-title{display:flex;justify-content:space-between;font-size:.75rem}.meter{height:5px;margin-top:7px;background:var(--line)}.meter i{display:block;height:100%;background:var(--muted)}
.card{padding:12px;margin-top:10px;border:1px solid var(--line);background:#0a0e13}.card b{font-size:.82rem}.card p{margin:5px 0 0;color:var(--muted);font-size:.75rem;line-height:1.45}.empty{color:var(--muted);font-size:.8rem}
.command{display:flex;justify-content:space-between;align-items:center;margin-top:18px;padding:18px 20px;border:1px solid var(--strong);background:#0b1016}.command p{margin:5px 0 0}.primary{min-height:40px;padding:0 16px;border:0;background:var(--text);color:var(--bg);font-weight:800;font-size:.72rem;cursor:pointer}
.statusline{grid-area:status;display:flex;align-items:center;gap:28px;padding:0 18px;border-top:1px solid var(--line);font-size:.6rem;letter-spacing:.1em;color:var(--dim)}.statusline b{color:var(--muted)}
.healthy,.operational,.complete,.connected{color:var(--green);border-color:var(--green)}.warning,.pending,.degraded{color:var(--amber);border-color:var(--amber)}.critical,.failed,.error,.disconnected{color:var(--red);border-color:var(--red)}.active,.running,.live{color:var(--cyan);border-color:var(--cyan)}.reasoning,.analyzing{color:var(--purple);border-color:var(--purple)}.unknown,.idle{color:var(--muted)}
@media(max-width:850px){.shell{grid-template:"head" auto "nav" auto "main" 1fr "status" auto/1fr}header{grid-template-columns:1fr auto;padding:14px}.bridge-title{display:none}nav{flex-direction:row;overflow:auto;border-right:0;border-bottom:1px solid var(--line)}nav button{min-width:125px}nav footer{display:none}.grid>section,.grid>.wide{grid-column:1/-1}.statusline{padding:8px 14px;flex-wrap:wrap}}
@media(max-width:560px){main{padding:16px}.brief,.executive,.command{align-items:flex-start;flex-direction:column;gap:18px}.metrics{grid-template-columns:1fr}.metrics div{padding:12px 0;border-right:0;border-bottom:1px solid var(--line)}.primary{width:100%}}
CSS

cat > "$ROOT/core/src/static/mission_control/app.js" <<'JS'
"use strict";
const E={status:"/operations/status",health:"/operations/health",missions:"/operations/missions",resources:"/operations/resources",timeline:"/operations/timeline",events:"/operations/events"};
const $=id=>document.getElementById(id);
const pick=(...v)=>v.find(x=>x!==undefined&&x!==null);
const list=v=>Array.isArray(v)?v:Array.isArray(v?.items)?v.items:Array.isArray(v?.results)?v.results:[];
const norm=v=>String(v||"unknown").toLowerCase().replace(/[^a-z0-9]+/g,"-");
const esc=v=>String(v??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");
const stamp=v=>{const d=new Date(v);return Number.isNaN(d.getTime())?String(v||"UNKNOWN"):d.toLocaleString()};
function pill(el,v){el.className=`pill ${norm(v)}`;el.textContent=String(v||"UNKNOWN").toUpperCase()}
async function get(url){const r=await fetch(url,{cache:"no-store",headers:{Accept:"application/json"}});if(!r.ok)throw Error(`${url}: ${r.status}`);return r.json()}
function connection(ok){$("link").textContent=ok?"OPERATIONS LINK":"LINK DEGRADED";$("link").className=`pill ${ok?"connected":"disconnected"}`;$("api").textContent=ok?"CONNECTED":"DEGRADED"}
function status(p){const s=pick(p.status,p.state,p.operational_state,p.executive_status,"unknown"),r=pick(p.readiness,p.readiness_score,p.score),t=pick(p.generated_at,p.timestamp);$("status").textContent=String(s).toUpperCase();$("status").className=norm(s);$("status-detail").textContent=pick(p.detail,p.message,p.summary,"Operations snapshot received.");$("readiness").textContent=typeof r==="number"?`${Math.round(r<=1?r*100:r)}%`:"--";$("snapshot-time").textContent=t?`Snapshot ${stamp(t)}`:"Operational snapshot received"}
function missions(p){const a=list(p),m=a.find(x=>["active","running","executing","in-progress"].includes(norm(pick(x.state,x.status))))||a[0],c={active:0,queued:0,complete:0};a.forEach(x=>{const s=norm(pick(x.state,x.status));["active","running","executing","in-progress"].includes(s)?c.active++:["complete","completed","certified","done"].includes(s)?c.complete++:c.queued++});$("active").textContent=pick(p.active_count,c.active);$("queued").textContent=pick(p.queued_count,c.queued);$("complete").textContent=pick(p.completed_count,p.complete_count,c.complete);if(!m){pill($("mission-state"),"idle");return}$("mission").textContent=pick(m.title,m.name,m.mission_id,"Active mission");$("objective").textContent=pick(m.objective,m.description,m.summary,"Mission objective not supplied.");pill($("mission-state"),pick(m.state,m.status,"active"))}
function health(p){let a=list(p);if(!a.length&&p&&typeof p==="object")a=Object.entries(p).filter(([,v])=>v&&typeof v==="object").map(([name,v])=>({name,...v}));$("divisions-list").innerHTML=["operations","knowledge","reasoning","cognition"].map(n=>{const x=a.find(i=>norm(pick(i.name,i.component,i.service))===n),s=pick(x?.state,x?.status,x?.health,"unknown");return `<div class="row"><span>${n[0].toUpperCase()+n.slice(1)}</span><span class="pill ${norm(s)}">${esc(String(s).toUpperCase())}</span></div>`}).join("")}
function resources(p){const a=list(p),find=n=>a.find(x=>norm(pick(x.name,x.kind,x.resource))===n);$("resources-list").innerHTML=["cpu","memory","storage"].map(n=>{let v=pick(p?.[n],p?.[`${n}_percent`],n==="storage"?p?.disk:null,find(n));if(v&&typeof v==="object")v=pick(v.percent,v.utilization,v.used_percent,v.value);const q=typeof v==="number"?Math.max(0,Math.min(100,v<=1?v*100:v)):0;return `<div class="resource"><div class="resource-title"><span>${n.toUpperCase()}</span><b>${q?Math.round(q)+"%":"--"}</b></div><div class="meter"><i style="width:${q}%"></i></div></div>`}).join("")}
function timeline(p){const a=list(p).slice(0,12);$("event-count").textContent=`${a.length} EVENTS`;$("timeline").innerHTML=a.length?a.map(x=>`<li class="event"><time>${esc(stamp(pick(x.timestamp,x.occurred_at,x.created_at)))}</time><div><b>${esc(pick(x.title,x.name,x.event_type,x.type,"Operational event"))}</b><p>${esc(pick(x.detail,x.description,x.message,x.summary,""))}</p></div></li>`).join(""):'<li class="empty">No operational events received.</li>'}
function cards(p,key,target,count,label){const a=list(p?.[key]);$(count).textContent=`${a.length} ${label}`;$(target).innerHTML=a.length?a.slice(0,5).map(x=>`<div class="card"><b>${esc(pick(x.title,x.name,key==="alerts"?x.severity:"Recommendation"))}</b><p>${esc(pick(x.rationale,x.detail,x.description,x.message,x.summary,""))}</p></div>`).join(""):`No ${key==="alerts"?"active operational alerts":"recommendations require authorization"}.`}
async function refresh(){const b=$("refresh");b.disabled=true;b.textContent="Refreshing Operational Picture";const pairs=await Promise.all(Object.entries(E).map(async([k,u])=>{try{return[k,await get(u),null]}catch(e){return[k,null,e]}}));const r=Object.fromEntries(pairs.map(([k,d,e])=>[k,{d,e}]));connection(Object.values(r).some(x=>!x.e));if(r.status.d)status(r.status.d);if(r.missions.d)missions(r.missions.d);if(r.health.d)health(r.health.d);if(r.resources.d)resources(r.resources.d);timeline(r.timeline.d||r.events.d||{});cards(r.status.d||{},"recommendations","recommendations","recommendation-count","PENDING");cards(r.status.d||{},"alerts","alerts","alert-count","ACTIVE");$("sync").textContent=new Date().toLocaleTimeString();b.disabled=false;b.textContent="Refresh Operational Picture"}
document.addEventListener("DOMContentLoaded",()=>{setInterval(()=>$("clock").textContent=new Date().toLocaleTimeString([],{hour12:false}),1000);$("refresh").addEventListener("click",refresh);refresh();setInterval(refresh,15000)});
JS

cat > "$ROOT/tests/test_mc1002_commanders_bridge.py" <<'PY'
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "core/src/static/mission_control"


class MC1002Tests(unittest.TestCase):
    def test_files(self):
        for name in ("index.html", "styles.css", "app.js"):
            self.assertTrue((STATIC / name).is_file())

    def test_identity(self):
        html = (STATIC / "index.html").read_text()
        self.assertIn("COMMANDER'S BRIDGE", html)
        self.assertIn("What are your orders?", html)

    def test_operations_boundary(self):
        js = (STATIC / "app.js").read_text()
        self.assertIn("/operations/status", js)
        self.assertIn("/operations/missions", js)
        self.assertNotIn("/executive/", js)
        self.assertNotIn("/reasoning/", js)

    def test_single_primary_action(self):
        html = (STATIC / "index.html").read_text()
        self.assertEqual(html.count('class="primary"'), 1)

    def test_responsive(self):
        css = (STATIC / "styles.css").read_text()
        self.assertIn("@media(max-width:850px)", css)
        self.assertIn("@media(max-width:560px)", css)

    def test_semantic_colors(self):
        css = (STATIC / "styles.css").read_text()
        for token in ("--green:", "--amber:", "--red:", "--cyan:", "--purple:"):
            self.assertIn(token, css)
PY

cat > "$ROOT/docs/architecture/commanders_bridge_foundation.md" <<'MD'
# MC-1002 — Commander's Bridge Foundation

**Status:** Implemented  
**Routes:** `/bridge`, `/mission-control`

MC-1002 establishes Mission Control's first operational workspace. The browser
consumes only the MC-1001 Operations endpoints and does not access Executive,
Reasoning, Cognition, Knowledge, or Runtime internals directly.

The initial Bridge presents executive readiness, mission projection, division
health, recent activity, resources, recommendations, and alerts. It implements
one primary action: **Refresh Operational Picture**.

Native HTML, CSS, and JavaScript are used deliberately. This keeps the initial
interface dependency-light while the information architecture and command
doctrine stabilize. A component framework may later replace the renderer without
changing the Operations boundary.
MD

cat > "$ROOT/dev/verification/verify_mc1002.py" <<'PY'
#!/usr/bin/env python3
from pathlib import Path
import importlib
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)) if str(ROOT) not in sys.path else None
FILES = (
    "core/src/routes/mission_control.py",
    "core/src/static/mission_control/index.html",
    "core/src/static/mission_control/styles.css",
    "core/src/static/mission_control/app.js",
    "tests/test_mc1002_commanders_bridge.py",
    "docs/architecture/commanders_bridge_foundation.md",
)

def report(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f": {detail}" if detail and not ok else ""))
    return 0 if ok else 1

def main():
    failed = 0
    print("=" * 70)
    print("JARVIS — MC-1002 COMMANDER'S BRIDGE FOUNDATION")
    print("=" * 70)
    missing = [x for x in FILES if not (ROOT / x).is_file()]
    failed += report("Canonical MC-1002 file set", not missing, ", ".join(missing))
    c = subprocess.run([sys.executable, "-m", "compileall", "-q", "core/src/routes/mission_control.py"], cwd=ROOT)
    failed += report("Mission Control compilation", c.returncode == 0)
    try:
        mod = importlib.import_module("core.src.routes.mission_control")
        ok, detail = hasattr(mod, "router"), ""
    except Exception as exc:
        ok, detail = False, f"{type(exc).__name__}: {exc}"
    failed += report("Mission Control route importability", ok, detail)
    main_text = (ROOT / "core/src/main.py").read_text()
    failed += report("Mission Control registered in FastAPI", "mission_control_router" in main_text and "/mission-control/static" in main_text)
    js = (ROOT / "core/src/static/mission_control/app.js").read_text()
    failed += report("Operations-only browser boundary", "/operations/status" in js and "/executive/" not in js)
    t = subprocess.run([sys.executable, "-m", "unittest", "-v", "tests.test_mc1002_commanders_bridge"], cwd=ROOT)
    failed += report("MC-1002 unit tests", t.returncode == 0)
    print("-" * 70)
    print(f"Checks failed : {failed}")
    print(f"Overall status: {'EXCELLENT' if failed == 0 else 'FAILED'}")
    print("=" * 70)
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
PY

cat > "$ROOT/dev/verify_mc1002.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
"${PYTHON_BIN:-python3}" dev/verification/verify_mc1002.py
SH
chmod +x "$ROOT/dev/verify_mc1002.sh" "$ROOT/dev/verification/verify_mc1002.py"

"$PY" - "$ROOT" <<'PY'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
path = root / "core/src/main.py"
text = path.read_text()

route_import = "from core.src.routes.mission_control import router as mission_control_router\n"
if route_import not in text:
    lines = text.splitlines(keepends=True)
    pos = 0
    for i, line in enumerate(lines):
        if line.startswith("from __future__ import"):
            pos = i + 1
    lines.insert(pos, route_import)
    text = "".join(lines)

if "from fastapi.staticfiles import StaticFiles" not in text:
    text = "from fastapi.staticfiles import StaticFiles\n" + text
if "from pathlib import Path" not in text:
    text = "from pathlib import Path\n" + text

if "MISSION_CONTROL_STATIC_ROOT" not in text:
    match = re.search(r"^app\s*=\s*FastAPI\s*\(", text, re.M)
    if not match:
        raise SystemExit("Could not find app = FastAPI(...) in core/src/main.py")
    start = text.find("(", match.start())
    depth = 0
    end = None
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        raise SystemExit("Could not parse FastAPI constructor")
    block = (
        '\nMISSION_CONTROL_STATIC_ROOT = Path(__file__).resolve().parent / "static" / "mission_control"\n'
        'app.mount(\n'
        '    "/mission-control/static",\n'
        '    StaticFiles(directory=MISSION_CONTROL_STATIC_ROOT),\n'
        '    name="mission-control-static",\n'
        ')\n'
        'app.include_router(mission_control_router)\n'
    )
    text = text[:end] + block + text[end:]

path.write_text(text)
PY

echo
echo "MC-1002 installed."
echo "Backup: $BACKUP"
echo
echo "Verify:"
echo "PYTHON_BIN=$PY ./dev/verify_mc1002.sh"
echo
echo "Launch JARVIS normally and open http://127.0.0.1:8000/bridge"
