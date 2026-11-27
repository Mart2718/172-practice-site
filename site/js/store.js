// Everything a student does is stored only in this browser (localStorage), never sent anywhere.
// Every read and write is wrapped: storage can be blocked (private windows, strict settings).
const KEY = 'm172.practice.v1';
const SKEY = 'm172.session.v1';
let mem = { marks: {}, prefs: {} };

(function load() {
  try {
    const s = localStorage.getItem(KEY);
    if (s) { const d = JSON.parse(s); if (d && typeof d === 'object') mem = { marks: d.marks || {}, prefs: d.prefs || {} }; }
  } catch (e) { /* storage unavailable: marks last until the tab closes */ }
})();

function save() {
  try { localStorage.setItem(KEY, JSON.stringify(mem)); return true; } catch (e) { return false; }
}

export const RATINGS = [
  { key: 'got', label: 'Got it' },
  { key: 'almost', label: 'Almost' },
  { key: 'not', label: 'Not yet' }
];

export function setMark(std, id, rating) {
  mem.marks[id] = { s: std, r: rating, t: Date.now() };
  return save();
}
export function getMark(id) { return mem.marks[id] ? mem.marks[id].r : ''; }
export function tally(std) {
  const t = { got: 0, almost: 0, not: 0 };
  for (const k in mem.marks) if (mem.marks[k].s === std) t[mem.marks[k].r]++;
  t.total = t.got + t.almost + t.not;
  return t;
}
export function totalMarked() { return Object.keys(mem.marks).length; }
export function resetMarks() { mem.marks = {}; return save(); }
export function getPref(k, d) { return k in mem.prefs ? mem.prefs[k] : d; }
export function setPref(k, v) { mem.prefs[k] = v; return save(); }

// A test in progress survives a page refresh (sessionStorage only).
export function saveSession(obj) { try { sessionStorage.setItem(SKEY, JSON.stringify(obj)); } catch (e) { window.__session = obj; } }
export function loadSession() {
  try { const s = sessionStorage.getItem(SKEY); if (s) return JSON.parse(s); } catch (e) { /* fall through */ }
  return window.__session || null;
}
export function clearSession() { try { sessionStorage.removeItem(SKEY); } catch (e) { /* ignore */ } window.__session = null; }
