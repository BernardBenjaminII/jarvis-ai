"use strict";
(() => {
  let root, map, markerLayer, snapshot;
  let selectedLevel = 0;
  let showTravel = true, showNuclear = true;
  const colors={critical:"#ff4f64",high:"#ffad42",watch:"#4aa8ff",info:"#59e0ac"};
  const esc=value=>String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const safeUrl=value=>{try{const url=new URL(String(value),window.location.origin);return ["https:","http:"].includes(url.protocol)?url.href:"#"}catch{return "#"}};
  const when=value=>value?new Date(value).toLocaleString():"Publication time unavailable";
  const visible=i=>!selectedLevel||Number(i.advisory_level)===selectedLevel;
  const detail=i=>{const source=i.source||{},site=i.kind==="nuclear_site";return `<button aria-label="Close incident">×</button><small>${site?"NUCLEAR SITE":esc(i.classification||i.severity).toUpperCase()} · ${esc(i.region||"MAPPED FACILITY")}</small><h2>${esc(i.title||i.name)}</h2><section><label>${site?"FACILITY":"AUTHORITATIVE SUMMARY"}</label><p>${esc(site?`${i.facility_type||"facility"}${i.operator?` · ${i.operator}`:""}`:i.summary)}</p></section>${site?"":`<section><label>${i.kind==="nuclear_event"?"NOTICE CLASS":"ADVISORY LEVEL"}</label><p>${i.kind==="nuclear_event"?esc(i.classification):(i.advisory_level?`Level ${esc(i.advisory_level)}`:"Not specified")}</p></section>`}<section><label>${site?"DATA RETRIEVED":"PUBLISHED"}</label><p>${esc(when(site?source.retrieved_at:i.published_at))}</p></section><section><label>PROVENANCE</label><p>${esc(source.publisher)} · ${esc(source.authority)}</p><p><a href="${safeUrl(source.url)}" target="_blank" rel="noopener noreferrer">Open source</a></p></section>`};
  function select(i){const panel=root.querySelector(".sitrep-detail");panel.innerHTML=detail(i);panel.hidden=false;panel.querySelector("button").onclick=()=>{panel.hidden=true}}
  function initMap(){
    const canvas=root.querySelector(".sitrep-map-canvas");
    if(typeof window.L!=="object"){canvas.innerHTML='<div class="sitrep-map-fallback">Interactive map library unavailable.<br>Advisory queue remains operational.</div>';return}
    if(map){map.remove()}
    map=L.map(canvas,{zoomControl:true,attributionControl:true,preferCanvas:true,minZoom:2,worldCopyJump:true}).setView([22,8],2);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:9,minZoom:2,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}).addTo(map);
    markerLayer=L.layerGroup().addTo(map);
    map.on("zoomend",()=>{if(snapshot)drawMarkers(snapshot.incidents||[])});
    window.setTimeout(()=>map.invalidateSize(),0);
  }
  function drawMarkers(incidents){
    if(!markerLayer)return;markerLayer.clearLayers();
    if(showNuclear)(snapshot?.nuclear_sites||[]).forEach(site=>{if(!Number.isFinite(site.location?.latitude)||!Number.isFinite(site.location?.longitude))return;const marker=L.circleMarker([site.location.latitude,site.location.longitude],{radius:4.5,color:"#f5d76e",weight:1.8,fillColor:"#101b19",fillOpacity:.95});marker.bindTooltip(`${esc(site.name)} · nuclear site`,{direction:"top"});marker.on("click",()=>select(site));marker.addTo(markerLayer)});
    if(!showTravel)return;
    const zoom=map.getZoom(),cell=zoom<=2?18:zoom===3?10:zoom===4?5:0;
    const located=incidents.filter(visible).filter(i=>Number.isFinite(i.location?.latitude)&&Number.isFinite(i.location?.longitude));
    if(!cell){located.forEach(i=>{const marker=L.circleMarker([i.location.latitude,i.location.longitude],{radius:Number(i.advisory_level)>=4?6:4.5,color:"#07110f",weight:1.5,fillColor:colors[i.severity]||colors.watch,fillOpacity:.92});marker.bindTooltip(`${esc(i.region)} · Level ${esc(i.advisory_level)}`,{direction:"top",opacity:.95});marker.on("click",()=>select(i));marker.addTo(markerLayer)});return}
    const groups=new Map();located.forEach(i=>{const key=`${Math.round(i.location.latitude/cell)}:${Math.round(i.location.longitude/cell)}`;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(i)});
    groups.forEach(group=>{if(group.length===1){const i=group[0],marker=L.circleMarker([i.location.latitude,i.location.longitude],{radius:5,color:"#07110f",weight:1.5,fillColor:colors[i.severity]||colors.watch,fillOpacity:.92});marker.bindTooltip(`${esc(i.region)} · Level ${esc(i.advisory_level)}`,{direction:"top"});marker.on("click",()=>select(i));marker.addTo(markerLayer);return}const lat=group.reduce((n,i)=>n+i.location.latitude,0)/group.length,lon=group.reduce((n,i)=>n+i.location.longitude,0)/group.length,level=Math.max(...group.map(i=>Number(i.advisory_level)||0)),severity=level===4?"critical":level===3?"high":level===2?"watch":"info";const marker=L.circleMarker([lat,lon],{radius:Math.min(16,7+Math.log2(group.length)*2),color:"#d7e6e0",weight:1.5,fillColor:colors[severity],fillOpacity:.88});marker.bindTooltip(`${group.length} advisories · highest Level ${level}`,{direction:"top"});marker.on("click",()=>map.setView([lat,lon],Math.min(6,zoom+2)));marker.addTo(markerLayer)})
  }
  function render(current){
    snapshot=current;const state=String(current.operational_state||"UNAVAILABLE").toUpperCase();const incidents=(Array.isArray(current.incidents)?[...current.incidents]:[]).sort((a,b)=>(Number(b.advisory_level)-Number(a.advisory_level))||String(b.published_at||"").localeCompare(String(a.published_at||"")));const shown=incidents.filter(visible),events=Array.isArray(current.nuclear_events)?current.nuclear_events:[],sites=Array.isArray(current.nuclear_sites)?current.nuclear_sites:[];
    root.querySelector(".sitrep-live-state").textContent=`SITREP · ${state} · ${incidents.length} ADVISORIES · ${sites.length} NUCLEAR SITES · ${events.length} NOTICES`;
    root.querySelectorAll(".sitrep-filter").forEach(button=>button.classList.toggle("active",Number(button.dataset.level)===selectedLevel));
    const cards=root.querySelector(".sitrep-cards");cards.replaceChildren();
    if(!shown.length){const empty=document.createElement("article");empty.className="sitrep-empty";empty.textContent=state==="UNAVAILABLE"?"No authoritative SITREP source is currently available.":"No records match this advisory-level filter.";cards.append(empty)}
    if(showNuclear)events.forEach(i=>{const card=document.createElement("article");card.className="sitrep-card nuclear-event";card.innerHTML=`<small>REGULATOR NOTICE · ${esc(i.region)}</small><h3>${esc(i.title)}</h3><p>${esc(i.summary)}</p><div class="sitrep-meta"><span>NRC</span><span>${esc(when(i.published_at))}</span></div>`;card.onclick=()=>select(i);cards.append(card)});
    if(showTravel)shown.forEach(i=>{const card=document.createElement("article");card.className=`sitrep-card level-${esc(i.advisory_level)}`;card.innerHTML=`<small>LEVEL ${esc(i.advisory_level)} · ${esc(i.region)}</small><h3>${esc(i.title)}</h3><p>${esc(i.summary)}</p><div class="sitrep-meta"><span>${esc(i.country_code||"INTL")}</span><span>${esc(when(i.published_at))}</span></div>`;card.onclick=()=>select(i);cards.append(card)});
    drawMarkers(incidents);const live=(current.sources||[]).filter(s=>s.state==="LIVE");root.querySelector(".sitrep-source-state").textContent=live.length?`${live.length} live sources · updated ${when(current.generated_at)}`:"Source connection unavailable";
  }
  async function load(){try{const response=await fetch("/operations/sitrep",{headers:{Accept:"application/json"},cache:"no-store"});if(!response.ok)throw new Error(`SITREP request failed: ${response.status}`);render(await response.json())}catch(error){render({operational_state:"UNAVAILABLE",incidents:[],sources:[],errors:[{message:String(error)}]})}}
  function mount(host){
    host.innerHTML=`<button class="jarvis-workspace-close" onclick="JARVIS_WORKSPACES.close()">← Return to chat</button><div class="jarvis-callable-status sitrep-live-state">SITREP · CONNECTING</div><main class="sitrep"><section class="sitrep-map"><div class="sitrep-map-canvas"></div><div class="sitrep-map-heading"><small>COMMON OPERATING PICTURE</small><h2>Global Situation</h2></div><div class="sitrep-layer-panel"><strong>LAYERS</strong><button class="sitrep-layer active" data-layer="travel"><i class="layer-on"></i>Travel advisories</button><button class="sitrep-layer active" data-layer="nuclear"><i class="layer-nuclear"></i>Nuclear sites + notices</button></div><div class="sitrep-legend"><span><i class="l4"></i>L4</span><span><i class="l3"></i>L3</span><span><i class="l2"></i>L2</span><span><i class="l1"></i>L1</span><span><i class="nuclear-dot"></i>Nuclear</span></div><div class="sitrep-source-state">Connecting to authoritative sources…</div><aside class="sitrep-detail" hidden></aside></section><aside class="sitrep-feed"><header><small>OFFICIAL + PUBLIC REFERENCE</small><h2>Operational Updates</h2><div class="sitrep-filters">${[[0,"ALL"],[4,"L4"],[3,"L3"],[2,"L2"],[1,"L1"]].map(([level,label])=>`<button class="sitrep-filter" data-level="${level}">${label}</button>`).join("")}</div></header><div class="sitrep-cards"><article class="sitrep-empty">Loading…</article></div></aside></main>`;
    root=host;root.querySelectorAll(".sitrep-filter").forEach(button=>button.onclick=()=>{selectedLevel=Number(button.dataset.level);if(snapshot)render(snapshot)});root.querySelectorAll(".sitrep-layer").forEach(button=>button.onclick=()=>{const travel=button.dataset.layer==="travel";if(travel)showTravel=!showTravel;else showNuclear=!showNuclear;button.classList.toggle("active",travel?showTravel:showNuclear);if(snapshot)render(snapshot)});initMap();load();
  }
  window.JARVIS_SITREP=Object.freeze({mount,refresh:load});
})();
