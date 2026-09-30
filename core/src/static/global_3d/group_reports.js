(() => {
  'use strict';
  const base=new URL('.',document.currentScript.src);
  let attempts=0;
  const timer=setInterval(()=>{
    const parent=document.querySelector('#jarvis-group-activity .ga-body');
    if(parent){clearInterval(timer);mount(parent);}
    else if(++attempts>=40){clearInterval(timer);console.error('Group report inbox: R1 panel not found');}
  },250);
  function mount(parent){
    if(document.getElementById('ga-report-inbox'))return;
    const inbox=document.createElement('details');inbox.id='ga-report-inbox';
    inbox.innerHTML=`<summary>REPORT INBOX · SOURCES &amp; HEALTH</summary>
      <p>Discovery links require review. They are not mapped incidents or confirmed movements.</p>
      <div class="ga-row"><button data-ri="reload">Refresh inbox</button>
      <select data-ri="provider" aria-label="Report source"><option value="">All sources</option><option value="gdelt">GDELT discovery</option><option value="critical_threats">Critical Threats</option><option value="un_monitoring">UN monitoring</option></select>
      <input data-ri="search" type="search" aria-label="Search reports" placeholder="Search report titles"></div>
      <p data-ri="status" role="status">Loading source health…</p><div data-ri="health"></div>
      <div data-ri="list" style="max-height:240px;overflow:auto"></div>`;
    parent.appendChild(inbox);
    const el=k=>inbox.querySelector(`[data-ri="${k}"]`);
    let snapshot=null, busy=false;
    function render(){
      el('health').replaceChildren();el('list').replaceChildren();
      for(const [name,s] of Object.entries(snapshot.sources||{})){
        const line=document.createElement('p');
        const stale=s.last_success && (Date.now()-Date.parse(s.last_success))>2*(s.cadence_hours||24)*3600000;
        line.textContent=`${name}: ${stale?'STALE / ':''}${s.state} · last success ${s.last_success||'never'} · ${s.error||s.note||''}${s.next_retry_at?' · retry '+s.next_retry_at:''}`;
        el('health').appendChild(line);
      }
      const q=el('search').value.toLowerCase(),provider=el('provider').value;
      const rows=(snapshot.reports||[]).filter(r=>(!provider||r.provider===provider||(r.found_via||[]).includes(provider)) &&
        `${r.title} ${r.publisher} ${(r.groups||[]).join(' ')}`.toLowerCase().includes(q));
      el('status').textContent=`${rows.length} matching links · showing up to 100 · checked ${snapshot.generated_at||'not yet'}`;
      for(const r of rows.slice(0,100)){
        let url;try{url=new URL(r.url);}catch{continue;}
        if(!['https:','http:'].includes(url.protocol))continue;
        const article=document.createElement('article');article.style.margin='12px 0';
        const a=document.createElement('a');a.href=url.href;a.target='_blank';a.rel='noopener noreferrer';a.textContent=r.title;
        const note=document.createElement('p');note.style.fontSize='12px';
        note.textContent=`${r.publisher} · ${r.review_state||'unreviewed'} · first discovered ${r.first_seen||'unknown'} · publication date ${r.published_at||'unknown'}`;
        article.append(a,note);el('list').appendChild(article);
      }
    }
    async function load(){
      if(busy)return;busy=true;el('reload').disabled=true;
      const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),15000);
      try{
        const response=await fetch(new URL('group_activity/reports.json',base),{cache:'no-store',signal:controller.signal});
        if(!response.ok)throw new Error(`HTTP ${response.status}`);
        const data=await response.json();
        if(data.schema_version!==1||!Array.isArray(data.reports))throw new Error('Invalid inbox data');
        snapshot=data;render();
      }catch(e){el('status').textContent=`Inbox error: ${e.message}. ${snapshot?'Previous links retained.':'Run the source updater first.'}`;}
      finally{clearTimeout(timeout);busy=false;el('reload').disabled=false;}
    }
    el('reload').onclick=load;
    el('provider').onchange=()=>{if(snapshot)render();};
    el('search').oninput=()=>{if(snapshot)render();};
    load();setInterval(()=>{if(!document.hidden)load();},300000);
  }
})();
