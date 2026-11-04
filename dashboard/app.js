/* CattleHealth AI — herd dashboard (vanilla JS, no build step) */
(() => {
  const $ = (s) => document.querySelector(s);
  const store = {
    get(k, d) { try { const v = localStorage.getItem('ch.' + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem('ch.' + k, JSON.stringify(v)); } catch (e) {} },
  };

  const I18N = {
    en: {
      title: 'CattleHealth AI', cows: 'Cows', healthy: 'Healthy', attention: 'Need attention', inheat: 'In heat',
      activeAlerts: 'Active alerts', herd: 'Herd', settings: 'Settings', server: 'Server URL', apikey: 'API key', save: 'Save',
      offline: 'Offline — showing last saved data', noAlerts: 'No active alerts. Herd looks good. ✅',
      noCows: 'No cows yet. Tags appear here automatically once the gateway uploads data.',
      ack: 'Done', temp: 'Temp', rum: 'Rumination', act: 'Activity', batt: 'Battery', seen: 'Seen',
      ok: 'Healthy', warning: 'Watch', critical: 'Urgent', heat: 'In heat', no_data: 'No data',
      allFarms: 'All farms', temp72: 'Body temperature · 72 h', rum7: 'Rumination per day · 7 days',
      act72: 'Activity · 72 h', history: 'Alert history', rename: 'Name', base: 'baseline', minDay: 'min/day',
      ago: 'ago', never: 'never', loadErr: 'Could not reach server',
    },
    hi: {
      title: 'कैटलहेल्थ AI', cows: 'पशु', healthy: 'स्वस्थ', attention: 'ध्यान दें', inheat: 'गर्मी में',
      activeAlerts: 'सक्रिय चेतावनी', herd: 'झुंड', settings: 'सेटिंग्स', server: 'सर्वर URL', apikey: 'API कुंजी', save: 'सहेजें',
      offline: 'ऑफ़लाइन — पिछला सहेजा डेटा दिख रहा है', noAlerts: 'कोई चेतावनी नहीं। झुंड ठीक है। ✅',
      noCows: 'अभी कोई पशु नहीं। गेटवे डेटा भेजते ही टैग यहाँ दिखेंगे।',
      ack: 'हो गया', temp: 'तापमान', rum: 'जुगाली', act: 'गतिविधि', batt: 'बैटरी', seen: 'देखा',
      ok: 'स्वस्थ', warning: 'नज़र रखें', critical: 'तुरंत', heat: 'गर्मी में', no_data: 'डेटा नहीं',
      allFarms: 'सभी फ़ार्म', temp72: 'शरीर का तापमान · 72 घंटे', rum7: 'प्रति दिन जुगाली · 7 दिन',
      act72: 'गतिविधि · 72 घंटे', history: 'चेतावनी इतिहास', rename: 'नाम', base: 'सामान्य', minDay: 'मिनट/दिन',
      ago: 'पहले', never: 'कभी नहीं', loadErr: 'सर्वर से संपर्क नहीं हो सका',
    },
  };
  let lang = store.get('lang', (navigator.language || 'en').startsWith('hi') ? 'hi' : 'en');
  const t = (k) => (I18N[lang] && I18N[lang][k]) || I18N.en[k] || k;

  const cfg = { url: store.get('url', ''), key: store.get('key', '') };
  let farmId = store.get('farm', '');

  async function api(path, opts = {}) {
    const headers = { 'Content-Type': 'application/json', ...(cfg.key ? { 'X-API-Key': cfg.key } : {}) };
    const res = await fetch(cfg.url.replace(/\/$/, '') + path, { ...opts, headers });
    if (!res.ok) throw new Error(res.status + ' ' + (await res.text()).slice(0, 120));
    return res.json();
  }

  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const cowName = (c) => c.name || c.cow_name || ('#' + c.tag_id);
  function ago(iso) {
    if (!iso) return t('never');
    const m = Math.max(0, Math.round((Date.now() - new Date(iso)) / 60000));
    if (m < 60) return m + 'm ' + t('ago');
    if (m < 2880) return Math.round(m / 60) + 'h ' + t('ago');
    return Math.round(m / 1440) + 'd ' + t('ago');
  }
  const alertClass = (a) => (a.kind === 'heat' ? 'heat' : a.severity);

  function applyI18n() {
    document.documentElement.lang = lang;
    document.querySelectorAll('[data-i18n]').forEach((el) => { el.textContent = t(el.dataset.i18n); });
    $('#lang').value = lang;
  }

  // ---------------------------------------------------------------- render
  function renderTiles(cows) {
    $('#t-cows').textContent = cows.length;
    $('#t-ok').textContent = cows.filter((c) => c.status === 'ok').length;
    $('#t-alert').textContent = cows.filter((c) => c.status === 'warning' || c.status === 'critical').length;
    $('#t-heat').textContent = cows.filter((c) => c.status === 'heat').length;
  }

  function renderAlerts(alerts) {
    const box = $('#alerts');
    if (!alerts.length) { box.innerHTML = `<div class="empty">${t('noAlerts')}</div>`; return; }
    box.innerHTML = alerts.map((a) => `
      <div class="alert ${alertClass(a)}">
        <div class="msg">${esc(a.message)}</div>
        <div class="when">${ago(a.created_at)}</div>
        <button class="btn" data-ack="${a.id}">${t('ack')}</button>
      </div>`).join('');
  }

  const ORDER = { critical: 0, warning: 1, heat: 2, no_data: 3, ok: 4 };
  function renderHerd(cows) {
    const box = $('#herd');
    if (!cows.length) { box.innerHTML = `<div class="empty" style="grid-column:1/-1">${t('noCows')}</div>`; return; }
    box.innerHTML = [...cows].sort((a, b) => (ORDER[a.status] - ORDER[b.status]) || (a.tag_id - b.tag_id)).map((c) => `
      <button class="cow" data-cow="${c.tag_id}">
        <div class="top"><div><div class="name">${esc(cowName(c))}</div><div class="tag">Tag ${c.tag_id}${c.breed ? ' · ' + esc(c.breed) : ''}</div></div>
          <span class="pill ${c.status}">${t(c.status)}</span></div>
        <div class="metrics">
          <div><b>${c.temp_c != null ? c.temp_c.toFixed(1) + '°' : '–'}</b><span>${t('temp')}</span></div>
          <div><b>${c.rumination_24h ?? '–'}</b><span>${t('rum')}</span></div>
          <div><b>${c.activity_mg ?? '–'}</b><span>${t('act')}</span></div>
        </div>
        <div class="foot"><span>🔋 ${c.battery_mv ? (c.battery_mv / 1000).toFixed(2) + ' V' : '–'}</span><span>${t('seen')} ${ago(c.last_seen)}</span></div>
      </button>`).join('');
  }

  function renderFarms(farms) {
    const sel = $('#farm');
    sel.innerHTML = `<option value="">${t('allFarms')}</option>` + farms.map((f) => `<option value="${f.id}">${esc(f.name)}</option>`).join('');
    sel.value = String(farmId || '');
    sel.style.display = farms.length ? '' : 'none';
  }

  // ---------------------------------------------------------------- charts (plain SVG)
  function lineChart(points, { w = 700, h = 160, color = '#166534', ref = null, min = null, max = null, fmt = (v) => v } = {}) {
    const pts = points.filter((p) => p.v != null);
    if (pts.length < 2) return '<svg viewBox="0 0 700 40"><text x="10" y="24">–</text></svg>';
    const xs = pts.map((p) => +new Date(p.t)), vs = pts.map((p) => p.v);
    let lo = min ?? Math.min(...vs, ref ?? Infinity), hi = max ?? Math.max(...vs, ref ?? -Infinity);
    if (hi - lo < 1e-6) { hi += 1; lo -= 1; }
    const pad = (hi - lo) * 0.1; lo -= pad; hi += pad;
    const L = 34, R = 8, T = 8, B = 18;
    const x = (v) => L + ((v - xs[0]) / (xs[xs.length - 1] - xs[0] || 1)) * (w - L - R);
    const y = (v) => T + (1 - (v - lo) / (hi - lo)) * (h - T - B);
    const d = pts.map((p, i) => (i ? 'L' : 'M') + x(+new Date(p.t)).toFixed(1) + ' ' + y(p.v).toFixed(1)).join('');
    const ticks = [lo + pad, (lo + hi) / 2, hi - pad];
    const days = [];
    const first = new Date(xs[0]); first.setHours(24, 0, 0, 0);
    for (let mid = first; +mid < xs[xs.length - 1]; mid = new Date(mid.getFullYear(), mid.getMonth(), mid.getDate() + 1)) days.push(mid);
    return `<svg viewBox="0 0 ${w} ${h}" width="100%" preserveAspectRatio="none" role="img">
      ${ticks.map((v) => `<line x1="${L}" x2="${w - R}" y1="${y(v)}" y2="${y(v)}" stroke="#E3E8E1"/><text x="2" y="${y(v) + 3}">${fmt(v)}</text>`).join('')}
      ${days.map((dd) => `<line x1="${x(+dd)}" x2="${x(+dd)}" y1="${T}" y2="${h - B}" stroke="#E3E8E1" stroke-dasharray="3 3"/><text x="${x(+dd) + 3}" y="${h - 5}">${dd.toLocaleDateString(lang, { weekday: 'short' })}</text>`).join('')}
      ${ref != null ? `<line x1="${L}" x2="${w - R}" y1="${y(ref)}" y2="${y(ref)}" stroke="#D97706" stroke-dasharray="5 4"/>` : ''}
      <path d="${d}" fill="none" stroke="${color}" stroke-width="1.8" stroke-linejoin="round"/>
    </svg>`;
  }

  function barChart(items, { w = 700, h = 140, low = 300 } = {}) {
    const max = Math.max(600, ...items.map((i) => i.v || 0));
    const bw = (w - 40) / items.length;
    const y = (v) => 8 + (1 - v / max) * (h - 30);
    return `<svg viewBox="0 0 ${w} ${h}" width="100%" role="img">
      <line x1="30" x2="${w}" y1="${y(low)}" y2="${y(low)}" stroke="#DC2626" stroke-dasharray="5 4"/><text x="0" y="${y(low) + 3}">${low}</text>
      ${items.map((it, i) => {
        const v = it.v || 0, X = 36 + i * bw;
        const col = it.v == null ? '#CBD5E1' : v < low ? '#DC2626' : '#22C55E';
        return `<rect x="${X}" y="${y(v)}" width="${bw - 10}" height="${Math.max(0, h - 22 - y(v))}" rx="4" fill="${col}"/>
          <text x="${X + (bw - 10) / 2}" y="${h - 6}" text-anchor="middle">${new Date(it.d + 'T12:00').toLocaleDateString(lang, { weekday: 'short' })}</text>
          <text x="${X + (bw - 10) / 2}" y="${y(v) - 3}" text-anchor="middle">${it.v ?? '–'}</text>`;
      }).join('')}
    </svg>`;
  }

  async function openCow(tag) {
    const dlg = $('#cowDlg');
    $('#cowBody').innerHTML = '…';
    if (!dlg.open) dlg.showModal();
    let c;
    try { c = await api(`/api/v1/cows/${tag}?hours=72`); } catch (e) { $('#cowBody').textContent = t('loadErr'); return; }
    $('#cowTitle').textContent = `${cowName(c)} · Tag ${c.tag_id}`;
    $('#cowPill').className = 'pill ' + c.status; $('#cowPill').textContent = t(c.status);
    const s = c.series;
    $('#cowBody').innerHTML = `
      <div class="row"><label>${t('rename')}</label><input id="cowName" value="${esc(c.name || '')}"><button class="btn primary" id="cowSave">${t('save')}</button></div>
      <div class="chart"><div class="t"><span>${t('temp72')}</span><span>${c.baseline_c ? t('base') + ' ' + c.baseline_c + '°C' : ''}</span></div>
        ${lineChart(s.map((r) => ({ t: r.ts, v: r.temp_c })), { ref: c.baseline_c, color: '#DC2626', fmt: (v) => v.toFixed(1) })}</div>
      <div class="chart"><div class="t"><span>${t('rum7')}</span><span>${t('minDay')}</span></div>
        ${barChart(c.daily_rumination.map((d) => ({ d: d.date, v: d.rumination_min })))}</div>
      <div class="chart"><div class="t"><span>${t('act72')}</span><span>mg</span></div>
        ${lineChart(s.map((r) => ({ t: r.ts, v: r.activity_mg })), { color: '#DB2777', min: 0, fmt: (v) => Math.round(v) })}</div>
      <h2>${t('history')}</h2>
      <div class="alerts">${c.alerts.length ? c.alerts.map((a) => `<div class="alert ${alertClass(a)}"><div class="msg">${esc(a.message)}</div><div class="when">${ago(a.created_at)}</div></div>`).join('') : `<div class="empty">–</div>`}</div>`;
    $('#cowSave').onclick = async () => {
      await api(`/api/v1/cows/${tag}`, { method: 'PATCH', body: JSON.stringify({ name: $('#cowName').value.trim() }) });
      openCow(tag); load();
    };
  }

  // ---------------------------------------------------------------- data
  async function load() {
    const q = farmId ? `?farm_id=${farmId}` : '';
    try {
      const [farms, cows, alerts] = await Promise.all([
        api('/api/v1/farms'), api('/api/v1/cows' + q), api('/api/v1/alerts?active=true' + (farmId ? '&farm_id=' + farmId : '')),
      ]);
      store.set('cache', { farms, cows, alerts });
      $('#offline').style.display = 'none';
      render(farms, cows, alerts);
    } catch (e) {
      console.warn(e);
      const c = store.get('cache', null);
      $('#offline').style.display = 'block';
      if (c) render(c.farms, c.cows, c.alerts);
    }
  }
  function render(farms, cows, alerts) { renderFarms(farms); renderTiles(cows); renderAlerts(alerts); renderHerd(cows); }

  // ---------------------------------------------------------------- events
  document.addEventListener('click', async (e) => {
    const ack = e.target.closest('[data-ack]');
    if (ack) { ack.disabled = true; try { await api(`/api/v1/alerts/${ack.dataset.ack}/ack`, { method: 'POST' }); } catch (x) {} load(); return; }
    const cow = e.target.closest('[data-cow]');
    if (cow) openCow(cow.dataset.cow);
  });
  $('#cowClose').onclick = () => $('#cowDlg').close();
  $('#setClose').onclick = () => $('#setDlg').close();
  $('#settings').onclick = () => { $('#sUrl').value = cfg.url; $('#sKey').value = cfg.key; $('#setDlg').showModal(); };
  $('#sSave').onclick = () => { cfg.url = $('#sUrl').value.trim(); cfg.key = $('#sKey').value.trim(); store.set('url', cfg.url); store.set('key', cfg.key); $('#setDlg').close(); load(); };
  $('#refresh').onclick = load;
  $('#farm').onchange = (e) => { farmId = e.target.value; store.set('farm', farmId); load(); };
  $('#lang').onchange = (e) => { lang = e.target.value; store.set('lang', lang); applyI18n(); load(); };

  applyI18n();
  load();
  setInterval(load, 60000);
  if ('serviceWorker' in navigator) window.addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => {}));
})();
