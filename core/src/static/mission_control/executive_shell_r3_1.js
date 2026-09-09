(()=>{"use strict";
const text=e=>(e?.textContent||"").replace(/\s+/g," ").trim();
const heading=label=>[...document.querySelectorAll("h1,h2,h3,h4,h5,h6")].find(h=>text(h).toLowerCase()===label.toLowerCase());
const section=h=>h&&(h.closest("section,article,[class*='section'],[class*='panel'],[class*='card']")||h.parentElement);
const byHeading=labels=>{for(const l of labels){const n=section(heading(l));if(n)return n}return null};
const uniq=a=>[...new Set(a.filter(Boolean))];

function install(){
 if(document.getElementById("jarvis-r31-shell"))return;
 const jarvis=section(heading("JARVIS"))||byHeading(["Knowledge"]);
 if(!jarvis){console.warn("[JARVIS UI R3.1] Knowledge workspace not found");return}

 const candidates=uniq([
  byHeading(["Grounded Answer Telemetry"]),byHeading(["Commander Brief"]),
  byHeading(["Executive Summary"]),byHeading(["Operational Picture"]),
  byHeading(["Requires Attention"]),byHeading(["Runtime"]),byHeading(["Storage"]),
  byHeading(["Executive Activity"]),byHeading(["Recent Executive Events"]),
  byHeading(["Readiness"]),byHeading(["Active Workstreams"])
 ]).filter(n=>n!==jarvis&&!n.contains(jarvis));

 const stateText=text(byHeading(["Executive Status","Commander Brief"]));
 const state=/degrad|deficien|attention|warning/i.test(stateText)?"DEGRADED":/healthy|ready|operational/i.test(stateText)?"READY":"STATUS";

 const shell=document.createElement("main"); shell.id="jarvis-r31-shell"; shell.dataset.revision="3.1";
 const status=document.createElement("div"); status.id="jarvis-r31-status";
 status.innerHTML=`<span>Executive Status</span><strong class="r31-state">${state}</strong><button type="button" aria-expanded="false">Details</button>`;
 const kh=document.createElement("div"); kh.id="jarvis-r31-knowledge";
 const ops=document.createElement("details"); ops.id="jarvis-r31-ops";
 ops.innerHTML='<summary>Executive Operations</summary><div id="jarvis-r31-ops-body"></div>';
 const body=ops.querySelector("#jarvis-r31-ops-body");

 const anchor=candidates[0]||jarvis; anchor.parentNode.insertBefore(shell,anchor);
 shell.append(status,kh,ops); jarvis.classList.add("r31-moved"); kh.appendChild(jarvis);

 candidates.forEach(n=>{n.classList.add("r31-moved");if(/Recent Executive Events|Executive Activity/i.test(text(n)))n.dataset.r31EventStream="true";body.appendChild(n)});
 status.querySelector("button").onclick=()=>{ops.open=true;status.querySelector("button").setAttribute("aria-expanded","true");ops.scrollIntoView({behavior:"smooth",block:"start"})};
 ops.addEventListener("toggle",()=>status.querySelector("button").setAttribute("aria-expanded",String(ops.open)));
 console.info("[JARVIS UI R3.1] Executive Shell Compression active");
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",()=>setTimeout(install,0),{once:true});else setTimeout(install,0);
window.addEventListener("load",()=>{if(!document.getElementById("jarvis-r31-shell"))setTimeout(install,500)},{once:true});
})();
