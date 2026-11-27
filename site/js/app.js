import { getConfig } from './data.js';
import { typeset } from './math.js';
import {
  homeView, practiceIndexView, standardView, recallView, testBuilderView, testRunView,
  summaryView, progressView, aboutView, notFoundView, errorView
} from './views.js';

const main = document.getElementById('main');
let token = 0;
let first = true;

if (new URLSearchParams(location.search).get('embed') === '1') document.documentElement.classList.add('embed');

async function dispatch(name, arg) {
  switch (name) {
    case '': return homeView();
    case 'practice': return arg ? standardView(decodeURIComponent(arg).toUpperCase()) : practiceIndexView();
    case 'recall': return recallView();
    case 'test': return arg === 'run' ? testRunView() : testBuilderView();
    case 'summary': return summaryView();
    case 'progress': return progressView();
    case 'about': return aboutView();
    default: return notFoundView();
  }
}

function markNav(name) {
  const section = { '': 'home', practice: 'practice', recall: 'recall', test: 'test', summary: 'test', progress: 'progress', about: 'about' }[name];
  document.querySelectorAll('nav[aria-label="Main"] a').forEach((a) => {
    if (a.dataset.nav === section) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
  });
}

async function route() {
  const my = ++token;
  const parts = location.hash.replace(/^#\/?/, '').split('/');
  main.setAttribute('aria-busy', 'true');
  let v;
  try { v = await dispatch(parts[0], parts[1]); } catch (e) { console.error(e); v = errorView(e); }
  if (my !== token) return;
  main.replaceChildren(v.el);
  document.title = `${v.title} | Math 172 Practice and Review`;
  markNav(parts[0]);
  if (v.after) { try { await v.after(); } catch (e) { console.error(e); } }
  if (my !== token) return;
  await typeset(main.querySelector('h1') ? main.querySelector('h1').parentElement : main).catch(() => {});
  main.removeAttribute('aria-busy');
  if (!first) {
    window.scrollTo(0, 0);
    const h1 = main.querySelector('h1');
    if (h1) { h1.tabIndex = -1; h1.focus({ preventScroll: true }); }
  }
  first = false;
}

async function setupChrome() {
  const cfg = await getConfig();
  const f = document.getElementById('footer-links');
  if (f) {
    f.innerHTML = `<a href="${cfg.assistantUrl}" target="_blank" rel="noopener">Course assistant (opens in a new tab)</a> · <a href="#/about">Accessibility and privacy</a> · <a href="mailto:${cfg.contactEmail}?subject=Math%20172%20practice%20site">Report a problem</a>`;
  }
  const skip = document.querySelector('.skip');
  skip.addEventListener('click', (e) => { e.preventDefault(); main.tabIndex = -1; main.focus(); });
}

window.addEventListener('hashchange', route);
setupChrome().catch(() => {});
route();
