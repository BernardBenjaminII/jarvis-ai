"use strict";
(() => {
  let root, map, markerLayer, snapshot;
  let selectedLevel = 0;
  const colors={critical:"#ff4f64",high:"#ffad42",watch:"#4aa8ff",info:"#59e0ac"};
  const esc=value=>String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const safeUrl=value=>{try{const url=new URL(String(value),window.location.origin);return ["https:","http:"].includes(url.protocol)?url.href:"#"}catch{return "#"}};
  const when=value=>value?new Date(value).toLocaleString():"Publication time unavailable";
  const visible=i=>!selectedLevel||Number(i.advisory_level)===selectedLevel;
  const detail=i=>{const source=i.source||{};return `<button aria-label="Close incident">×</button><small>${esc(i.severity).toUpperCase()} · ${esc(i.region)} · ${esc(i.operational_state)}</small><h2>${esc(i.title)}</h2><section><label>AUTHORITATIVE SUMMARY</label><p>${esc(i.summary)}</p></section><section><label>ADVISORY LEVEL</label><p>${i.advisory_level?`Level ${esc(i.advisory_level)}`:"Not specified"}</p></section><section><label>PUBLISHED</label><p>${esc(when(i.published_at))}</p></section><section><label>PROVENANCE</label><p>${esc(source.publisher)} · ${esc(source.authority)}</p><p><a href="${safeUrl(source.url)}" target="_blank" rel="noopener noreferrer">Open authoritative source</a></p></section>`};
  function select(i){const panel=root.querySelector(".sitrep-detail");panel.innerHTML=detail(i);panel.hidden=false;panel.querySelector("button").onclick=()=>{panel.hidden=true}}
  function initMap(){
    const canvas=root.querySelector(".sitrep-map-canvas");
    if(typeof window.L!=="object"){canvas.innerHTML='<div class="sitrep-map-fallback">Interactive map library unavailable.<br>Advisory queue remains operational.</div>';return}
    if(map){map.remove()}
    map=L.map(canvas,{zoomControl:true,attributionControl:true,preferCanvas:true,minZoom:2,worldCopyJump:true}).setView([22,8],2);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:9,minZoom:2,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}).addTo(map);
    markerLayer=L.layerGroup().addTo(map);
    window.setTimeout(()=>map.invalidateSize(),0);
  }
  function drawMarkers(incidents){
    if(!markerLayer)return;markerLayer.clearLayers();
    incidents.filter(visible).forEach(i=>{const lat=i.location?.latitude,lon=i.location?.longitude;if(!Number.isFinite(lat)||!Number.isFinite(lon))return;const marker=L.circleMarker([lat,lon],{radius:Number(i.advisory_level)>=4?6:4.5,color:"#07110f",weight:1.5,fillColor:colors[i.severity]||colors.watch,fillOpacity:.9});marker.bindTooltip(`${esc(i.region)} · Level ${esc(i.advisory_level)}`,{direction:"top",opacity:.95});marker.on("click",()=>select(i));marker.addTo(markerLayer)})
  }
  function render(current){
    snapshot=current;const state=String(current.operational_state||"UNAVAILABLE").toUpperCase();const incidents=Array.isArray(current.incidents)?current.incidents:[];const shown=incidents.filter(visible);
    root.querySelector(".sitrep-live-state").textContent=`SITREP · ${state} · ${incidents.length} AUTHORITATIVE RECORDS`;
    root.querySelectorAll(".sitrep-filter").forEach(button=>button.classList.toggle("active",Number(button.dataset.level)===selectedLevel));
    const cards=root.querySelector(".sitrep-cards");cards.replaceChildren();
    if(!shown.length){const empty=document.createElement("article");empty.className="sitrep-empty";empty.textContent=state==="UNAVAILABLE"?"No authoritative SITREP source is currently available.":"No records match this advisory-level filter.";cards.append(empty)}
    shown.forEach(i=>{const card=document.createElement("article");card.className=`sitrep-card level-${esc(i.advisory_level)}`;card.innerHTML=`<small>LEVEL ${esc(i.advisory_level)} · ${esc(i.region)}</small><h3>${esc(i.title)}</h3><p>${esc(i.summary)}</p><div class="sitrep-meta"><span>${esc(i.country_code||"INTL")}</span><span>${esc(when(i.published_at))}</span></div>`;card.onclick=()=>select(i);cards.append(card)});
    drawMarkers(incidents);const source=current.sources?.[0];root.querySelector(".sitrep-source-state").textContent=source?`${source.publisher} · ${source.record_count} records · ${when(source.retrieved_at)}`:"Source connection unavailable";
  }
  async function load(){try{const response=await fetch("/operations/sitrep",{headers:{Accept:"application/json"},cache:"no-store"});if(!response.ok)throw new Error(`SITREP request failed: ${response.status}`);render(await response.json())}catch(error){render({operational_state:"UNAVAILABLE",incidents:[],sources:[],errors:[{message:String(error)}]})}}
  function mount(host){
    host.innerHTML=`<button class="jarvis-workspace-close" onclick="JARVIS_WORKSPACES.close()">← Return to chat</button><div class="jarvis-callable-status sitrep-live-state">SITREP · CONNECTING</div><main class="sitrep"><section class="sitrep-map"><div class="sitrep-map-canvas"></div><div class="sitrep-map-heading"><small>COMMON OPERATING PICTURE</small><h2>Global Situation</h2></div><div class="sitrep-legend"><span><i class="l4"></i>L4</span><span><i class="l3"></i>L3</span><span><i class="l2"></i>L2</span><span><i class="l1"></i>L1</span></div><div class="sitrep-source-state">Connecting to authoritative source…</div><aside class="sitrep-detail" hidden></aside></section><aside class="sitrep-feed"><header><small>STATE DEPARTMENT</small><h2>Travel Advisories</h2><div class="sitrep-filters">${[[0,"ALL"],[4,"L4"],[3,"L3"],[2,"L2"],[1,"L1"]].map(([level,label])=>`<button class="sitrep-filter" data-level="${level}">${label}</button>`).join("")}</div></header><div class="sitrep-cards"><article class="sitrep-empty">Loading…</article></div></aside></main>`;
    root=host;root.querySelectorAll(".sitrep-filter").forEach(button=>button.onclick=()=>{selectedLevel=Number(button.dataset.level);if(snapshot)render(snapshot)});initMap();load();
  }
  window.JARVIS_SITREP=Object.freeze({mount,refresh:load});
})();
