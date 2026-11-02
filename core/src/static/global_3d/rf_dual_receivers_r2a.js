/* JARVIS RF Dual Receiver R2A — monitor only; no device control. */
(() => {
  'use strict';
  const ROOT_ID = 'rfDualReceiversR2A';
  const ENDPOINT = '/api/rf/receivers';
  let active = false;
  function renderReceiver(receiver) {
    const serial = String(receiver.serial || '');
    const card = [...document.querySelectorAll('#' + ROOT_ID + ' [data-rf-serial]')]
      .find(item => item.dataset.rfSerial === serial);
    if (!card) return;
    const status = receiver.status || {};
    const state = String(status.state || 'unknown').toLowerCase();
    const task = status.task ? String(status.task) : 'Standby';
    const mhz = Number.isFinite(Number(status.frequency_hz)) && status.frequency_hz !== null
      ? (Number(status.frequency_hz) / 1e6).toFixed(3) + ' MHz'
      : (status.scan_start_hz != null && status.scan_stop_hz != null
          ? (Number(status.scan_start_hz)/1e6).toFixed(1) + '–' + (Number(status.scan_stop_hz)/1e6).toFixed(1) + ' MHz'
          : 'Not tuned');
    const stateEl = card.querySelector('.rf-dual-r2a-state');
    stateEl.textContent = state.toUpperCase();
    stateEl.dataset.state = state;
    card.querySelector('.rf-dual-r2a-mission').textContent = state === 'running' ? task.toUpperCase() + ' · ' + mhz : (status.detail || 'Idle');
    card.querySelector('.rf-dual-r2a-detail').textContent = 'Serial ' + serial + ' · ' + (status.pid ? 'PID ' + status.pid + ' · ' : '') + (status.gain != null ? 'Gain ' + status.gain + ' dB' : 'No active gain');
  }
  async function refresh() {
    const root = document.getElementById(ROOT_ID);
    if (!root || !root.isConnected) { active=false; return; }
    const updated = document.getElementById('rfDualUpdatedR2A');
    try {
      const response = await fetch(ENDPOINT, {cache:'no-store'});
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const result = await response.json();
      if (!Array.isArray(result.receivers)) throw new Error('Invalid receiver response');
      for (const receiver of result.receivers) renderReceiver(receiver);
      updated.textContent = 'Last update ' + new Date().toLocaleTimeString();
    } catch (error) {
      updated.textContent = 'API unavailable: ' + error.message;
      for (const el of root.querySelectorAll('.rf-dual-r2a-state')) {
        el.textContent='API OFFLINE'; el.dataset.state='offline';
      }
    }
  }
  function mount() {
    if (active || !document.getElementById(ROOT_ID)) return;
    active=true;
    refresh();
    window.setInterval(() => { if(active) refresh(); }, 2500);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',mount,{once:true});
  else mount();
})();
