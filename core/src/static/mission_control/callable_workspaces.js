(() => {
  "use strict";
  const diagnostics={
    health:{label:"Health",controller:"executiveHealthRuntimeProjection",selector:"#executive-health-panel"},
    timeline:{label:"Timeline",controller:"executiveEventTimelineProjection",selector:".dashboard-panel--timeline"},
    operations:{label:"Operations",controller:"dashboardStatusProjection",selector:"#jarvis-r32-operations-body"},
    evidence:{label:"Evidence",controller:null,selector:null}
  };
  let host,launcher,current=null,displaced=[],mountTimer=null;
  function restore(){for(const item of displaced.reverse()){item.placeholder.parentNode?.insertBefore(item.node,item.placeholder);item.placeholder.remove();item.node.classList.remove("jarvis-system-mounted")}displaced=[]}
  function move(node,target){if(!node||!node.parentNode)return;const placeholder=document.createComment("jarvis-workspace-home");node.parentNode.insertBefore(placeholder,node);node.classList.add("jarvis-system-mounted");target.append(node);displaced.push({node,placeholder})}
  async function initController(name){const id=diagnostics[name]?.controller;if(!id)return;const registry=window.JARVIS?.controllers;if(registry&&typeof registry.initialize==="function")await registry.initialize(id)}
  function close(){restore();host.hidden=true;document.body.classList.remove("jarvis-workspace-active");current=null;launcher?.querySelectorAll("button").forEach(b=>b.setAttribute("aria-pressed","false"));document.dispatchEvent(new CustomEvent("jarvis:workspace-close"))}
  async function showDiagnostic(name){
    if(!diagnostics[name])return;restore();
    const content=host.querySelector("#jarvis-system-content");content.replaceChildren();
    host.querySelectorAll(".jarvis-system-tabs button").forEach(b=>b.setAttribute("aria-selected",String(b.dataset.diagnostic===name)));
    await initController(name);
    document.dispatchEvent(new CustomEvent("jarvis:workspace-open",{detail:{workspace:name==="evidence"?"evidence":"system",diagnostic:name}}));
    if(name==="evidence"){move(document.querySelector(".knowledge-result-metrics"),content);move(document.querySelector(".knowledge-inspection"),content);move(document.querySelector("#grounded-answer-projection"),content)}
    else move(document.querySelector(diagnostics[name].selector),content);
    if(!content.children.length)content.innerHTML='<p class="jarvis-system-empty">This diagnostic surface is unavailable.</p>';
  }
  function systemMarkup(){
    host.innerHTML='<button class="jarvis-workspace-close" type="button">← Return to chat</button><main id="jarvis-system"><header class="jarvis-system-header"><small>SECONDARY WORKSPACE</small><h1>System</h1><p>Diagnostics remain dormant until selected.</p></header><nav class="jarvis-system-tabs" aria-label="System diagnostics"></nav><section id="jarvis-system-content"><p class="jarvis-system-empty">Select a diagnostic surface.</p></section></main>';
    host.querySelector(".jarvis-workspace-close").onclick=close;
    const tabs=host.querySelector(".jarvis-system-tabs");
    Object.entries(diagnostics).forEach(([name,item])=>{const b=document.createElement("button");b.type="button";b.dataset.diagnostic=name;b.textContent=item.label;b.setAttribute("aria-selected","false");b.onclick=()=>showDiagnostic(name);tabs.append(b)});
  }
  function open(name){restore();current=name;host.hidden=false;document.body.classList.add("jarvis-workspace-active");launcher?.querySelectorAll("button").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.workspace===name)));if(name==="sitrep")window.JARVIS_SITREP?.mount(host);else systemMarkup()}
  function installLauncher(){
    const status=document.querySelector("#jarvis-r32-status");if(!status)return false;
    if(mountTimer)clearInterval(mountTimer);
    launcher=document.createElement("nav");launcher.id="jarvis-workspace-launcher";launcher.setAttribute("aria-label","JARVIS workspaces");
    [["sitrep","SITREP"],["system","System"]].forEach(([name,label])=>{const b=document.createElement("button");b.type="button";b.dataset.workspace=name;b.textContent=label;b.setAttribute("aria-pressed","false");b.onclick=()=>open(name);launcher.append(b)});
    status.append(launcher);
    const details=status.querySelector(".r322-status-details");if(details){details.textContent="System";details.addEventListener("click",event=>{event.preventDefault();event.stopImmediatePropagation();open("system")},{capture:true})}
    return true;
  }
  function boot(){
    if(location.hash!=="#knowledge")history.replaceState(null,"","#knowledge");
    host=document.createElement("section");host.id="jarvis-workspace-host";host.hidden=true;host.setAttribute("aria-label","Callable workspace");document.body.append(host);
    if(!installLauncher()){let attempts=0;mountTimer=setInterval(()=>{attempts++;if(installLauncher()||attempts>=80)clearInterval(mountTimer)},250)}
    window.JARVIS_WORKSPACES=Object.freeze({open,close,current:()=>current,showDiagnostic});
  }
  document.addEventListener("DOMContentLoaded",boot,{once:true});
})();
