/* Source-backed group activity overlay. Isolated from viewer.entities. */
(() => {
  'use strict';
  const DAY = 86400000;
  const date = value => Date.parse(String(value).slice(0, 10) + 'T00:00:00Z');
  const iso = value => new Date(value).toISOString().slice(0, 10);
  function visible(records, options) {
    return records.filter(r =>
      (!options.group || r.groups.includes(options.group)) &&
      (!options.kind || r.kind === options.kind) &&
      (options.inferred || r.movement_basis !== 'inferred') &&
      date(r.start) <= options.cursor && date(r.end) >= options.cursor - options.windowDays * DAY &&
      date(r.end) >= options.start && date(r.start) <= options.end);
  }
  function mount(viewer, base) {
    if (document.getElementById('jarvis-group-activity')) return;
    const C = window.Cesium;
    const layer = new C.CustomDataSource('jarvis-group-activity');
    viewer.dataSources.add(layer);
    const host = document.createElement('section');
    host.id = 'jarvis-group-activity';
    host.innerHTML = `
      <style>
      #jarvis-group-activity{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);width:min(350px,70vw);z-index:80;background:#101d2bf2;color:#e7edf4;border:1px solid #48617a;border-radius:6px;font:9px system-ui;box-shadow:0 6px 18px #0008}
      #jarvis-group-activity summary{padding:6px 7px;cursor:pointer;font-weight:650;font-size:9px}
      #jarvis-group-activity .ga-body{padding:0 7px 7px;max-height:32vh;overflow:auto}
      #jarvis-group-activity .ga-row{display:flex;gap:4px;flex-wrap:wrap;align-items:center;margin:4px 0}
      #jarvis-group-activity label{display:flex;gap:3px;align-items:center}
      #jarvis-group-activity select,#jarvis-group-activity button,#jarvis-group-activity input[type=date]{background:#1c3045;color:#fff;border:1px solid #526a80;border-radius:3px;padding:3px 4px;max-width:100%;font-size:9px}
      #jarvis-group-activity button{cursor:pointer}#jarvis-group-activity button:disabled{opacity:.45;cursor:default}
      #jarvis-group-activity input[type=range]{width:100%}
      #jarvis-group-activity .ga-status,#jarvis-group-activity .ga-muted{color:#b2c3d3;font-size:9px;line-height:1.15}
      #jarvis-group-activity .ga-list{max-height:60px;overflow:auto}
      #jarvis-group-activity .ga-list button{text-align:left;display:block;width:100%;margin:2px 0;padding:3px 4px}
      #jarvis-group-activity .ga-detail{white-space:pre-wrap;border-top:1px solid #48617a;padding-top:4px;max-height:74px;overflow:auto;font-size:9px;line-height:1.2}#jarvis-group-activity .ga-detail p{margin:3px 0}
      #jarvis-group-activity a{color:#7bddff}
      </style>
      <details open><summary>GROUP ACTIVITY · HISTORICAL REPLAY</summary><div class="ga-body">
      <div class="ga-status" role="status">Loading evidence…</div>
      <div class="ga-row"><label><input data-ga="enabled" type="checkbox" checked>Show layer</label>
      <label>Group <select data-ga="group"><option value="">All imported groups</option></select></label>
      <label>Evidence <select data-ga="kind"><option value="">All</option><option value="activity">Activity</option><option value="presence">Presence</option><option value="movement">Movement</option></select></label></div>
      <div class="ga-row"><label>From <input data-ga="from" type="date"></label><label>To <input data-ga="to" type="date"></label>
      <label>Trail <select data-ga="trail"><option value="7">7 days</option><option value="30" selected>30 days</option><option value="90">90 days</option><option value="365">365 days</option></select></label></div>
      <div class="ga-row"><button data-ga="play" disabled>▶ Play</button><button data-ga="restart" disabled>↺ Restart</button>
      <label>Speed <select data-ga="speed"><option value="1">1 day/sec</option><option value="7" selected>7 days/sec</option><option value="30">30 days/sec</option></select></label>
      <button data-ga="reload">Reload data</button><strong data-ga="date">—</strong></div>
      <input data-ga="slider" type="range" aria-label="Replay date" min="0" max="0" value="0" step="1" disabled>
      <div class="ga-row"><label><input data-ga="inferred" type="checkbox">Include inferred movements</label><span data-ga="count">0 records</span></div>
      <p class="ga-muted">Amber: activity · cyan: reported presence · arrow: reported relocation · dashed line: inferred shift. Lines connect reported endpoints; they do not establish a travel route. Dates are UTC. Displayed points may be approximate.</p>
      <div class="ga-list"></div><div class="ga-detail" hidden></div>
      </div></details>`;
    document.body.appendChild(host);
    const el = name => host.querySelector(`[data-ga="${name}"]`);
    let records = [], cursor = 0, start = 0, end = 0, timer = null, error = '', generated = null;
    const status = host.querySelector('.ga-status');
    const list = host.querySelector('.ga-list');
    const detail = host.querySelector('.ga-detail');
    function pause() { clearInterval(timer); timer = null; el('play').textContent = '▶ Play'; }
    function validPoint(p) {
      return p && typeof p.latitude === 'number' && typeof p.longitude === 'number' &&
        Number.isFinite(p.latitude) && Number.isFinite(p.longitude) && Math.abs(p.latitude) <= 90 && Math.abs(p.longitude) <= 180;
    }
    function check(r) {
      return r && typeof r.id === 'string' && ['activity','presence','movement'].includes(r.kind) &&
        Array.isArray(r.groups) && r.groups.length && r.groups.every(g => typeof g === 'string') &&
        Number.isFinite(date(r.start)) && Number.isFinite(date(r.end)) && date(r.end) >= date(r.start) &&
        Array.isArray(r.sources) && r.sources.length &&
        (r.kind === 'movement' ? validPoint(r.origin) && validPoint(r.destination) &&
          ['reported','inferred'].includes(r.movement_basis) && typeof r.evidence === 'string' && r.evidence.trim() : validPoint(r.location));
    }
    function showDetail(r) {
      detail.hidden = false;
      detail.replaceChildren();
      const text = document.createElement('p');
      const loc = r.location || r.destination;
      text.textContent = `${r.title || r.kind}\n${r.groups.join(' / ')} · ${r.start} → ${r.end}\n` +
        `${r.kind}${r.movement_basis ? ' / ' + r.movement_basis : ''} · confidence: ${r.confidence || 'unrated'}\n` +
        `Published: ${r.published_at || 'unknown'} · ingested: ${r.ingested_at || 'unknown'}\n` +
        `Location precision: ${loc.precision || 'unspecified'} · date precision: ${r.time_precision || 'unspecified'}\n` +
        `${r.summary || ''}\n${r.evidence || ''}`;
      detail.appendChild(text);
      for (const s of r.sources) {
        const line = document.createElement('p');
        let url;
        try { url = new URL(s.url); } catch { continue; }
        if (!['http:', 'https:'].includes(url.protocol)) continue;
        const link = document.createElement('a');
        link.href = url.href; link.target = '_blank'; link.rel = 'noopener noreferrer';
        link.textContent = s.publisher || 'Source'; line.appendChild(link);
        if (s.reference) line.appendChild(document.createTextNode(' — ' + s.reference));
        detail.appendChild(line);
      }
    }
    function render() {
      layer.show = el('enabled').checked;
      layer.entities.removeAll();
      list.replaceChildren();
      const shown = visible(records, {group: el('group').value, kind: el('kind').value,
        inferred: el('inferred').checked, cursor, start, end, windowDays: Number(el('trail').value)});
      const drawn = shown.slice(0, 5000);
      el('count').textContent = `${shown.length} records${shown.length > 5000 ? ' · map capped at 5,000; narrow filters' : ''}`;
      el('date').textContent = cursor ? iso(cursor) : '—';
      el('slider').value = Math.max(0, Math.round((cursor - start) / DAY));
      for (const r of drawn) {
        const point = r.location || r.destination;
        const color = r.kind === 'activity' ? C.Color.ORANGE : r.kind === 'presence' ? C.Color.CYAN : C.Color.MAGENTA;
        const age = Math.max(0, (cursor - date(r.end)) / DAY);
        const alpha = Math.max(.25, 1 - age / (Number(el('trail').value) + 1));
        const entity = {id: `group-activity:${r.id}`, name: r.title || r.kind,
          position: C.Cartesian3.fromDegrees(point.longitude, point.latitude),
          point: {pixelSize: r.kind === 'presence' ? 10 : 7, color: color.withAlpha(alpha), outlineColor: C.Color.BLACK, outlineWidth: 1},
          properties: {groupActivityRecord: JSON.stringify(r),
            jarvisRecord: JSON.stringify({...r, location:point, source:r.sources[0]})}};
        if (r.kind === 'movement') {
          entity.polyline = {
            positions: C.Cartesian3.fromDegreesArray([r.origin.longitude, r.origin.latitude, r.destination.longitude, r.destination.latitude]),
            width: r.movement_basis === 'reported' ? 7 : 3,
            material: r.movement_basis === 'reported' ? new C.PolylineArrowMaterialProperty(color.withAlpha(alpha)) : new C.PolylineDashMaterialProperty({color: color.withAlpha(alpha)})
          };
        }
        layer.entities.add(entity);
      }
      for (const r of shown.slice().sort((a,b) => date(b.start)-date(a.start)).slice(0, 50)) {
        const button = document.createElement('button');
        button.textContent = `${r.start} · ${r.groups.join(' / ')} · ${r.title || r.kind}`;
        button.onclick = () => {showDetail(r); const p = r.location || r.destination;
          viewer.camera.flyTo({destination: C.Cartesian3.fromDegrees(p.longitude, p.latitude, 1200000), duration: 1});};
        list.appendChild(button);
      }
      status.textContent = error || (records.length ? `${records.length} imported records · updated ${generated || 'unknown'} · source reporting may lag` : 'No evidence imported. Import a provider dataset or reviewed report records; no live feeds are enabled.');
      viewer.scene.requestRender();
    }
    function rangeChanged() {
      pause();
      const a = date(el('from').value), b = date(el('to').value);
      if (!Number.isFinite(a) || !Number.isFinite(b) || b < a) {
        el('play').disabled = true; el('restart').disabled = true; el('slider').disabled = true;
        status.textContent = 'Choose a valid date range (From must precede To).'; return;
      }
      start = a; end = b; cursor = Math.min(end, Math.max(start, cursor));
      el('slider').max = Math.round((end-start)/DAY);
      el('play').disabled = !records.length || start === end;
      el('restart').disabled = !records.length; el('slider').disabled = !records.length;
      render();
    }
    async function load() {
      pause(); el('reload').disabled = true;
      const controller = new AbortController(), timeout = setTimeout(() => controller.abort(), 15000);
      try {
        const response = await fetch(new URL('group_activity/events.json', base), {cache:'no-store', signal:controller.signal});
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (data.schema_version !== 1 || !Array.isArray(data.records) || !data.records.every(check)) throw new Error('Invalid evidence schema');
        if (new Set(data.records.map(r => r.id)).size !== data.records.length) throw new Error('Duplicate evidence IDs');
        records = data.records; generated = data.generated_at; error = '';
        const selected = el('group').value;
        el('group').replaceChildren(new Option('All imported groups', ''));
        [...new Set(records.flatMap(r => r.groups))].sort().forEach(g => el('group').add(new Option(g,g)));
        el('group').value = [...el('group').options].some(o => o.value === selected) ? selected : '';
        if (records.length) {
          start = records.reduce((v,r) => Math.min(v,date(r.start)), Infinity);
          end = records.reduce((v,r) => Math.max(v,date(r.end)), -Infinity);
          cursor = end;
          el('from').value = iso(start); el('to').value = iso(end); rangeChanged();
        } else { el('play').disabled = true; el('restart').disabled = true; el('slider').disabled = true; }
        detail.hidden = true;
      } catch (e) { error = `DATA ERROR: ${e.message}. ${records.length ? 'Retaining last loaded evidence.' : 'No evidence available.'}`; }
      finally {clearTimeout(timeout); el('reload').disabled = false; render();}
    }
    el('play').onclick = () => {
      if (timer) {pause(); return;}
      if (cursor >= end) cursor = start;
      el('play').textContent = '❚❚ Pause'; render();
      timer = setInterval(() => {cursor = Math.min(end, cursor + Number(el('speed').value)*DAY); render(); if (cursor >= end) pause();}, 1000);
    };
    el('restart').onclick = () => {pause(); cursor = start; render();};
    el('slider').oninput = () => {pause(); cursor = start + Number(el('slider').value)*DAY; render();};
    el('from').onchange = rangeChanged; el('to').onchange = rangeChanged;
    for (const name of ['group','kind','inferred','trail','enabled']) el(name).onchange = () => {detail.hidden = true; render();};
    el('reload').onclick = load;
    viewer.selectedEntityChanged.addEventListener(entity => {
      const raw = entity?.properties?.groupActivityRecord?.getValue();
      if (raw) showDetail(JSON.parse(raw));
    });
    document.addEventListener('visibilitychange', () => {if (document.hidden) pause();});
    load();
    return {layer, reload:load, pause};
  }
  window.JarvisGroupActivity = Object.freeze({mount, visible});
})();
