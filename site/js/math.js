import { getPref } from './store.js';

let mathOk = null;
export async function mathReady() {
  if (mathOk !== null) return mathOk;
  const timeout = new Promise((r) => setTimeout(() => r(false), 10000));
  mathOk = await Promise.race([window.__mjReady, timeout]);
  if (!mathOk) {
    const n = document.getElementById('math-warning');
    if (n) n.hidden = false;
  }
  return mathOk;
}

// Render the equations inside el. Returns when finished (or immediately if MathJax is unavailable).
export async function typeset(el) {
  if (!(await mathReady()) || !window.MathJax || !window.MathJax.typesetPromise) return;
  try { await window.MathJax.typesetPromise([el]); } catch (e) { console.warn('MathJax:', e); }
  applyTabStops(el);
  fitWide(el);
}

// An inline equation wider than its line (a long piecewise function, a big set) would push the page
// sideways on a phone. Give it its own line with its own horizontal scroll instead (WCAG 1.4.10).
export function fitWide(root) {
  (root || document).querySelectorAll('mjx-container:not([display])').forEach((c) => {
    c.classList.remove('wide');
    const host = c.closest('p, li, td, th, div') || c.parentElement;
    if (!host) return;
    const cs = getComputedStyle(host);
    const avail = host.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
    if (c.getBoundingClientRect().width > avail + 1) c.classList.add('wide');
  });
}
let rz;
window.addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(() => fitWide(document), 150); });

// By default an equation is not a separate tab stop (so keyboard users are not slowed down).
// A setting on the About page turns on one tab stop per equation.
export function applyTabStops(root) {
  const on = !!getPref('mathTab', false);
  (root || document).querySelectorAll('mjx-container').forEach((c) => {
    if (on) c.setAttribute('tabindex', '0'); else c.removeAttribute('tabindex');
  });
}
