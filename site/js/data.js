let config = null, index = null;
const pools = {};

async function getJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(url + ' ' + r.status);
  return r.json();
}
export async function getConfig() { return config || (config = await getJSON('config.json')); }
export async function getIndex() {
  if (!index) index = (await getJSON('pool/index.json')).standards;
  return index;
}
export async function getPool(code) {
  if (!pools[code]) {
    const d = await getJSON('pool/' + code + '.json');
    // join each item to its family (tier, hint, slips)
    d.items.forEach((it) => { it.fam = d.families[it.family] || {}; it.std = code; });
    pools[code] = d;
  }
  return pools[code];
}
export const TIER_LABEL = {
  floor: 'Core practice',
  assessment: 'Putting it together',
  slip: 'Spot the slip',
  bridge: 'Looking ahead to calculus',
  review: 'Exam 1 review question'
};
export const EXAM_ORDER = ['Exam 1', 'Exam 2', 'Final only'];
export const EXAM_TEXT = {
  'Exam 1': 'Exam 1 (Chapters 1 and 2)',
  'Exam 2': 'Exam 2 (Chapters 3 and 4)',
  'Final only': 'Final exam (adds Chapter 5)'
};
export function shuffle(a) {
  a = a.slice();
  for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
  return a;
}
export function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
