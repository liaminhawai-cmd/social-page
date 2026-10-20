/* shared by every tool. Inlined by tools/build.py — do not load from a CDN. */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
function h(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const k in (attrs || {})) {
    if (k === 'class') e.className = attrs[k];
    else if (k === 'text') e.textContent = attrs[k];
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), attrs[k]);
    else if (attrs[k] !== false && attrs[k] != null) e.setAttribute(k, attrs[k] === true ? '' : attrs[k]);
  }
  for (const c of kids.flat()) if (c != null) e.append(c.nodeType ? c : document.createTextNode(c));
  return e;
}
function shuffle(a) { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
const wordsOf = id => D.words[id];
const flat = id => D.words[id].parts.flat();
function unitById(id) { return D.units.find(u => u.id === id) || D.units[0]; }
function dayKey(d = new Date()) { return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
function dayNum(k) { const [y, m, d] = k.split('-').map(Number); return Math.round(Date.UTC(y, m - 1, d) / 864e5); }

/* ---- storage: this device only. Falls back to memory if the browser blocks it. ---- */
const Store = (() => {
  const KEY = 'sharing-tools-v1'; let mem = null;
  function load() {
    if (mem) return mem;
    try { const s = localStorage.getItem(KEY); mem = s ? JSON.parse(s) : null; } catch (e) { mem = null; }
    if (!mem || mem.v !== 1) mem = { v: 1, items: {}, log: [], secs: {} };
    return mem;
  }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(mem)); } catch (e) { /* blocked: stays in memory */ } }
  function reset() { mem = { v: 1, items: {}, log: [], secs: {} }; save(); }
  return { get: load, save, reset };
})();

/* ---- time-gated review: five boxes, whole-day gaps. Gates promotion, never access. ----
   Box n means: answered first time correct after at least DUE[n-1] days since the last promotion. */
const DUE = [0, 0, 1, 3, 7, 21];   // index = box the item is currently in
function itemKey(tool, id) { return tool + '|' + id; }
function itemState(tool, id) { return Store.get().items[itemKey(tool, id)] || { box: 0, last: null }; }
function isDue(tool, id) {
  const s = itemState(tool, id); if (!s.last) return true;
  const gap = Math.max(0, dayNum(dayKey()) - dayNum(s.last));
  return s.box < 5 && gap >= DUE[s.box];
}
function recordFirstTry(tool, id, ok, extra) {
  const st = Store.get(), k = itemKey(tool, id), today = dayKey();
  let s = st.items[k] || { box: 0, last: null };
  if (!ok) { s = { box: 1, last: today }; }
  else if (!s.last) { s = { box: 1, last: today }; }
  else {
    const gap = Math.max(0, dayNum(today) - dayNum(s.last));
    if (s.box < 5 && gap >= DUE[s.box]) s = { box: s.box + 1, last: today };   // else: accepted, not promoted, clock not reset
  }
  st.items[k] = s;
  st.log.push(Object.assign({ d: today, t: Date.now(), tool, id, ok: !!ok }, extra || {}));
  if (st.log.length > 1500) st.log.splice(0, st.log.length - 1500);
  Store.save();
}
function dots(tool, id) { const b = itemState(tool, id).box; return '●'.repeat(b) + '○'.repeat(5 - b); }

/* ---- time on task: seconds with real activity, per day / tool / unit ---- */
const Clock = (() => {
  let last = 0, ctx = { tool: '', unit: '' };
  function poke() { last = Date.now(); }
  ['pointerdown', 'keydown', 'input'].forEach(ev => addEventListener(ev, poke, true));
  setInterval(() => {
    if (document.hidden || Date.now() - last > 20000 || !ctx.tool) return;
    const st = Store.get(), k = dayKey() + '|' + ctx.tool + '|' + ctx.unit;
    st.secs[k] = (st.secs[k] || 0) + 5; Store.save();
  }, 5000);
  return { set(t, u) { ctx = { tool: t, unit: u }; } };
})();

/* ---- speech: the browser's own voice. It can be wrong; the human overrules it. ---- */
const Say = (() => {
  const ok = 'speechSynthesis' in window;
  function pick(langs) {
    const vs = ok ? speechSynthesis.getVoices() : [];
    for (const l of langs) { const v = vs.find(v => v.lang.replace('_', '-').toLowerCase().startsWith(l.toLowerCase())); if (v) return v; }
    return null;
  }
  function en(text) {
    if (!ok) return; speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text); const v = pick(['en-AU', 'en-GB', 'en']);
    if (v) u.voice = v; u.lang = v ? v.lang : 'en-AU'; u.rate = 0.8; speechSynthesis.speak(u);
  }
  function zh(text) {
    if (!ok) return; const v = pick(['zh-HK', 'yue', 'zh-TW', 'zh']); if (!v) return;
    speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(text); u.voice = v; u.lang = v.lang; u.rate = 0.85; speechSynthesis.speak(u);
  }
  return { en, zh, canEn: () => ok, canZh: () => !!pick(['zh-HK', 'yue', 'zh-TW', 'zh']) };
})();
function speakBtn(text, label) {
  if (!Say.canEn()) return null;
  return h('button', { class: 'btn sp', type: 'button', 'aria-label': label || 'Hear it', title: 'Computer voice — it can get a sound wrong',
    onclick: e => { e.stopPropagation(); Say.en(text); } }, '🔊');
}

/* ---- clipboard ---- */
async function copyText(t) {
  try { await navigator.clipboard.writeText(t); return true; } catch (e) {
    const ta = h('textarea', { style: 'position:fixed;left:-999px' }); ta.value = t; document.body.append(ta); ta.select();
    let r = false; try { r = document.execCommand('copy'); } catch (e2) {} ta.remove(); return r;
  }
}

/* ---- report: first tries only, misses named, time on task. ---- */
function buildReport(tool, toolLabel, days) {
  const st = Store.get(), today = dayNum(dayKey());
  const recent = st.log.filter(e => e.tool === tool && today - dayNum(e.d) < days);
  const groups = {};
  for (const e of recent) { const k = e.d + '|' + (e.unit || '') + '|' + (e.mode || ''); (groups[k] = groups[k] || []).push(e); }
  const keys = Object.keys(groups).sort().reverse();
  const lines = [], rows = [], timeShown = {};
  lines.push(toolLabel + ' — first tries only, last ' + days + ' days');
  if (!keys.length) lines.push('', 'No first tries recorded on this device yet.');
  for (const k of keys) {
    const [d, unit, mode] = k.split('|'), es = groups[k], right = es.filter(e => e.ok).length;
    const missed = es.filter(e => !e.ok).map(e => e.id + (e.why ? ' (' + e.why + ')' : ''));
    const tk = d + '|' + unit, secs = st.secs[d + '|' + tool + '|' + unit] || 0, mins = Math.round(secs / 60);
    const timeLine = timeShown[tk] ? '' : '  time on task that day (all clues): ' + mins + ' min'; timeShown[tk] = 1;
    const u = D.units.find(x => x.id === unit);
    lines.push('', d + '  ' + (u ? u.title : unit) + (mode ? '  [' + mode + ']' : ''),
      '  first try right: ' + right + ' of ' + es.length + (missed.length ? '' : ''),
      '  missed: ' + (missed.length ? missed.join('; ') : 'none'),
      ...(timeLine ? [timeLine] : []));
    rows.push([d, u ? u.title : unit, mode || '', right, es.length, missed.join('; '), timeLine ? mins : ''].join('\t'));
  }
  lines.push('', 'Review dots (●●●○○) count right-first-time answers on separate days, after gaps of 1, 3, 7 and 21 days. Five dots = right first time after a gap of 21 days or more.');
  lines.push('This record cannot show: whether anyone helped, whether the sounds were said aloud, or whether a right answer was understood.');
  return { text: lines.join('\n'), tsv: rows.join('\n') };
}
function reportDialog(tool, toolLabel) {
  const pre = h('pre'), msg = h('span', { class: 'small', 'aria-live': 'polite' });
  const rep = () => buildReport(tool, toolLabel, 14);
  const veil = h('div', { class: 'veil', hidden: true, role: 'dialog', 'aria-modal': 'true', 'aria-label': 'Report' },
    h('div', { class: 'dlg' },
      h('header', {}, h('h2', { text: 'Report' }), h('button', { class: 'btn', type: 'button', onclick: () => veil.hidden = true }, 'Close')),
      pre,
      h('footer', {},
        h('button', { class: 'btn pri', type: 'button', onclick: async () => { msg.textContent = (await copyText(rep().text)) ? 'Text copied.' : 'Copy failed — select the text and copy it.'; } }, 'Copy text'),
        h('button', { class: 'btn', type: 'button', onclick: async () => { msg.textContent = (await copyText(rep().tsv)) ? 'Rows copied (tab-separated, one row per day and clue).' : 'Copy failed.'; } }, 'Copy rows'),
        h('button', { class: 'btn', type: 'button', onclick: () => { if (confirm('Delete everything saved on this device for these tools?')) { Store.reset(); pre.textContent = rep().text; msg.textContent = 'Deleted.'; } } }, 'Delete record'),
        h('span', { class: 'small' }, 'Saved on this device only. Nothing is sent anywhere.'), msg)));
  document.body.append(veil);
  addEventListener('keydown', e => { if (e.key === 'Escape') veil.hidden = true; });
  return { open() { pre.textContent = rep().text; msg.textContent = ''; veil.hidden = false; $('.btn', veil).focus(); } };
}
