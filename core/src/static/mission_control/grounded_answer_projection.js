(() => {
  "use strict";
  const ENDPOINT="/operations/executive/grounded-answer";
  const $=(s)=>document.querySelector(s);
  function ensure(){
    if($("#grounded-answer-projection")) return;
    const style=document.createElement("style");
    style.textContent=".grounded-answer-projection{margin:1rem 0;padding:1rem;border:1px solid rgba(255,255,255,.14);border-radius:.75rem}.ga-grid{display:flex;gap:1rem;flex-wrap:wrap}.ga-grid div{min-width:7rem}.ga-action{margin-top:.75rem;padding:.6rem;border-left:3px solid currentColor}";
    document.head.appendChild(style);
    const p=document.createElement("section"); p.id="grounded-answer-projection"; p.className="grounded-answer-projection";
    p.innerHTML=`<small>EXECUTIVE TRANSPARENCY</small><h3>Grounded Answer Telemetry</h3>
      <strong id="ga-state">UNAVAILABLE</strong><div class="ga-grid">
      <div><small>Confidence</small><b id="ga-confidence">0%</b></div>
      <div><small>Accepted</small><b id="ga-accepted">0</b></div>
      <div><small>Rejected</small><b id="ga-rejected">0</b></div>
      <div><small>Citations</small><b id="ga-citations">0</b></div>
      <div><small>Conflicts</small><b id="ga-conflicts">0</b></div></div>
      <p id="ga-uncertainty">No grounded-answer request has completed.</p>
      <div id="ga-action" class="ga-action" hidden></div>`;
    const target=$("#executive-activity-panel")||document.querySelector("main")||document.body;
    target.prepend(p);
  }
  function text(id,v){const n=$(id);if(n)n.textContent=String(v);}
  function render(x){
    ensure(); text("#ga-state",x.state||"unavailable");
    text("#ga-confidence",`${Math.round((Number(x.confidence)||0)*100)}%`);
    text("#ga-accepted",x.accepted_evidence||0); text("#ga-rejected",x.rejected_evidence||0);
    text("#ga-citations",x.citation_count||0); text("#ga-conflicts",x.conflict_count||0);
    text("#ga-uncertainty",x.uncertainty_note||"No uncertainty projection.");
    const a=$("#ga-action"); if(a){a.hidden=!x.recommended_action;a.textContent=x.recommended_action||"";}
  }
  async function refresh(){try{const r=await fetch(ENDPOINT,{cache:"no-store"});if(!r.ok)throw Error(`HTTP ${r.status}`);render(await r.json());}catch(e){render({state:"unavailable",uncertainty_note:`Telemetry unavailable: ${e.message||e}`});}}
  document.addEventListener("DOMContentLoaded",()=>{ensure();refresh();setInterval(refresh,5000);});
})();
