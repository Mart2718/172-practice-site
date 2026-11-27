import { getIndex, getPool, getConfig, TIER_LABEL, EXAM_ORDER, EXAM_TEXT, shuffle, esc } from './data.js';
import { tally, totalMarked, resetMarks, getPref, setPref, saveSession, loadSession, clearSession, RATINGS, getMark } from './store.js';
import { renderProblem, typesetVisible } from './problem.js';
import { applyTabStops } from './math.js';
import { announce } from './live.js';

const el = (html) => { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstElementChild; };
const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;

// ------------------------------------------------------------------ shared pieces
function standardsList(idx, headingLevel) {
  const h = headingLevel;
  return EXAM_ORDER.map((ex) => {
    const list = idx.filter((s) => s.exam === ex);
    return `<section class="exam-group" aria-labelledby="g-${ex.replace(/\W/g, '')}">
      <h${h} id="g-${ex.replace(/\W/g, '')}">${EXAM_TEXT[ex]}</h${h}>
      <ul class="std-list">${list.map((s) => {
        const t = tally(s.code);
        const marks = t.total ? `<span class="meta">Your marks: ${t.got} got it, ${t.almost} almost, ${t.not} not yet</span>` : '';
        const n = s.items ? `<span class="meta">${plural(s.items, 'problem', 'problems')} so far</span>` : '<span class="meta">Practice problems coming soon</span>';
        return `<li><a href="#/practice/${s.code}"><span class="code">${s.code}</span> ${esc(s.title)}</a> ${n} ${marks}</li>`;
      }).join('')}</ul></section>`;
  }).join('');
}

function assistantNote(cfg) {
  return `<section class="note" aria-labelledby="ai-h"><h2 id="ai-h">Stuck? Ask the course assistant</h2>
    <p>Try the problem first. Then <a href="${esc(cfg.assistantUrl)}" target="_blank" rel="noopener">open the course assistant (opens in a new tab)</a> and ask it about your work. Check what it tells you against your own reasoning, because an assistant can make mistakes.</p></section>`;
}

// Pick the next item: a standard, then a family, then a version, so every kind of problem comes up
// and a family with many versions does not crowd out the others. Avoids repeats within a visit.
function pickItem(items, state, keyFn) {
  keyFn = keyFn || ((i) => i.family);
  let fresh = items.filter((i) => !state.seen.has(i.id));
  if (!fresh.length) { state.seen.clear(); fresh = items.slice(); }
  const byStd = {};
  fresh.forEach((i) => { (byStd[i.std] = byStd[i.std] || []).push(i); });
  const stds = Object.keys(byStd);
  const stdPick = stds.filter((s) => s !== state.lastStd);
  const s = (stdPick.length ? stdPick : stds)[Math.floor(Math.random() * (stdPick.length ? stdPick.length : stds.length))];
  const fams = {};
  byStd[s].forEach((i) => { (fams[keyFn(i)] = fams[keyFn(i)] || []).push(i); });
  let fkeys = Object.keys(fams);
  const notRecent = fkeys.filter((f) => !state.lastFam.includes(f));
  if (notRecent.length) fkeys = notRecent;
  const f = fkeys[Math.floor(Math.random() * fkeys.length)];
  const pool = fams[f];
  const it = pool[Math.floor(Math.random() * pool.length)];
  state.seen.add(it.id);
  state.lastStd = s;
  state.lastFam = [it.family].concat(state.lastFam).slice(0, 2);
  return it;
}
const newState = () => ({ seen: new Set(), lastFam: [], lastStd: '' });

function moreLinks(cfg, std) {
  const links = [`<li><a href="${esc(std.checkit)}" target="_blank" rel="noopener">CheckIt practice for ${std.code} (new numbers every time; opens in a new tab)</a></li>`];
  if (cfg.supportUrl) links.push(`<li><a href="${esc(cfg.supportUrl.replace(/\/$/, ''))}/${std.code.toLowerCase()}/" target="_blank" rel="noopener">${std.code} support page, with video and guided practice (opens in a new tab)</a></li>`);
  if (cfg.faqUrl) links.push(`<li><a href="${esc(cfg.faqUrl.replace(/\/$/, ''))}/${std.code.toLowerCase()}/" target="_blank" rel="noopener">${std.code} questions and answers (opens in a new tab)</a></li>`);
  links.push(`<li><a href="${esc(cfg.assistantUrl)}" target="_blank" rel="noopener">Ask the course assistant (opens in a new tab)</a></li>`);
  return `<section aria-labelledby="more-h"><h2 id="more-h">More ways to practice ${std.code}</h2><ul>${links.join('')}</ul></section>`;
}

// ------------------------------------------------------------------ home and standards list
export async function homeView() {
  const [idx, cfg] = await Promise.all([getIndex(), getConfig()]);
  const n = totalMarked();
  const root = el(`<div>
    <h1>Math 172 Practice and Review</h1>
    <p class="lead">Practice any of the ${idx.length} standards, mix problems from across the course, or take a practice test. Nothing here is graded, and your marks stay on this device.</p>
    <section aria-labelledby="ways-h"><h2 id="ways-h">Ways to practice</h2>
      <ul class="cards">
        <li class="card"><h3><a href="#/practice">Practice a standard</a></h3><p>Pick one standard. Get a problem, try it, then check your work with a hint, the answer, and the slips to watch for.</p></li>
        <li class="card"><h3><a href="#/recall">Random recall</a></h3><p>Problems from many standards, mixed. You decide which skill each one needs before you see its name.</p></li>
        <li class="card"><h3><a href="#/test">Practice test</a></h3><p>Build a test for Exam 1, Exam 2, the final, or standards you choose. Work on paper, then check every answer.</p></li>
        <li class="card"><h3><a href="#/progress">My progress</a></h3><p>${n ? `You have marked ${plural(n, 'problem', 'problems')}.` : 'See which standards you have practiced and how it went.'}</p></li>
      </ul></section>
    <section aria-labelledby="std-h"><h2 id="std-h">Practice by standard</h2>${standardsList(idx, 3)}</section>
    ${assistantNote(cfg)}
  </div>`);
  return { title: 'Home', el: root };
}

export async function practiceIndexView() {
  const idx = await getIndex();
  const root = el(`<div><h1>Practice by standard</h1>
    <p class="lead">Choose a standard. Each one lists the skill it checks.</p>
    ${standardsList(idx, 2)}</div>`);
  return { title: 'Practice by standard', el: root };
}

// ------------------------------------------------------------------ one standard
export async function standardView(code) {
  const [idx, cfg] = await Promise.all([getIndex(), getConfig()]);
  const std = idx.find((s) => s.code === code);
  if (!std) return notFoundView();
  const pool = await getPool(code);
  const root = el(`<div>
    <h1>${std.code} · ${esc(std.title)}</h1>
    <p class="meta-line">Chapter ${std.chapter}${std.section ? ', section ' + std.section : ''} · ${EXAM_TEXT[std.exam]}</p>
    <p>${esc(std.blurb)}</p>
    <div id="body"></div></div>`);
  const body = root.querySelector('#body');
  if (!pool.items.length) {
    body.innerHTML = `<div class="note"><p><strong>Practice problems for ${std.code} are coming soon.</strong> In the meantime, CheckIt gives you new problems for this standard with feedback.</p></div>${moreLinks(cfg, std)}`;
    return { title: `${std.code} ${std.title}`, el: root };
  }
  const tiers = [...new Set(pool.items.map((i) => i.fam.tier))];
  const state = newState();
  state.n = 0;
  body.innerHTML = `
    <div class="controls">
      <label for="kind">Kind of problem</label>
      <select id="kind"><option value="all">All kinds, mixed</option>${tiers.map((t) => `<option value="${t}">${TIER_LABEL[t]}</option>`).join('')}</select>
    </div>
    <div id="card"></div>
    <div class="actions"><button type="button" class="btn" id="next">Next problem</button></div>
    <p class="tally" id="tally"></p>
    ${moreLinks(cfg, std)}`;
  const card = body.querySelector('#card');
  const kind = body.querySelector('#kind');
  const tallyEl = body.querySelector('#tally');
  const showTally = () => {
    const t = tally(code);
    tallyEl.textContent = t.total ? `Your marks for ${code}: ${t.got} got it, ${t.almost} almost, ${t.not} not yet.` : '';
  };
  const next = async (focus) => {
    const items = pool.items.filter((i) => (kind.value === 'all' ? i.fam.tier !== 'bridge' : i.fam.tier === kind.value));
    const it = pickItem(items, state);
    state.n++;
    const art = renderProblem(it, { mode: 'practice', number: state.n, onRated: showTally });
    card.replaceChildren(art);
    await typesetVisible(art);
    showTally();
    if (focus) { art.querySelector('h2').focus(); announce(`Problem ${state.n} loaded.`); }
  };
  body.querySelector('#next').addEventListener('click', () => next(true));
  kind.addEventListener('change', () => { state.seen.clear(); state.lastFam = []; state.n = 0; next(true); });
  return { title: `${std.code} ${std.title}`, el: root, after: () => next(false) };
}

// ------------------------------------------------------------------ random recall
export async function recallView() {
  const [idx, cfg] = await Promise.all([getIndex(), getConfig()]);
  const root = el(`<div>
    <h1>Random recall</h1>
    <p class="lead">Retrieval practice: you get a problem without its standard's name, so you have to decide what kind of problem it is. Try it on paper first.</p>
    <div class="controls"><label for="scope">Problems from</label>
      <select id="scope"><option value="all">Everything (final exam)</option><option value="Exam 1">Exam 1 standards</option><option value="Exam 2">Exam 2 standards</option></select></div>
    <div id="card"></div>
    <div class="actions"><button type="button" class="btn" id="next">Next problem</button></div>
    <p class="meta-line" id="info"></p></div>`);
  const card = root.querySelector('#card');
  const scope = root.querySelector('#scope');
  const info = root.querySelector('#info');
  let state = newState();
  state.n = 0;
  const load = async () => {
    const ids = idx.filter((s) => s.items && (scope.value === 'all' || s.exam === scope.value));
    const pools = await Promise.all(ids.map((s) => getPool(s.code)));
    const tiers = ['floor', 'assessment', 'review', 'slip'];
    const items = [].concat(...pools.map((p) => p.items)).filter((i) => tiers.includes(i.fam.tier));
    info.textContent = `Drawing from ${plural(ids.length, 'standard', 'standards')} that have practice problems so far.`;
    return items;
  };
  let items = null;
  const next = async (focus) => {
    if (!items) items = await load();
    const it = pickItem(items, state);
    state.n++;
    const s = idx.find((x) => x.code === it.std);
    const art = renderProblem(it, {
      mode: 'practice', number: state.n,
      afterAnswer: (box) => {
        box.innerHTML = `<p class="from">This was a <strong>${s.code}</strong> problem: ${esc(s.title)}. <a href="#/practice/${s.code}">Practice ${s.code}</a></p>`;
      }
    });
    card.replaceChildren(art);
    await typesetVisible(art);
    if (focus) { art.querySelector('h2').focus(); announce(`Problem ${state.n} loaded.`); }
  };
  root.querySelector('#next').addEventListener('click', () => next(true));
  scope.addEventListener('change', async () => { items = null; state = newState(); state.n = 0; await next(true); });
  return { title: 'Random recall', el: root, after: () => next(false) };
}

// ------------------------------------------------------------------ practice test: build
const TEST_TIERS = ['floor', 'assessment', 'review'];

export async function testBuilderView() {
  const idx = await getIndex();
  const hasItems = (s) => s.items > 0;
  const root = el(`<div><h1>Practice test</h1>
    <p class="lead">Build a test, work on paper, then check every answer. There are no hints during the test and no time limit.</p>
    <form id="tform">
      <fieldset class="group"><legend>What should the test cover?</legend>
        <label class="choice"><input type="radio" name="scope" value="Exam 1" checked><span>Exam 1 standards (Chapters 1 and 2)</span></label>
        <label class="choice"><input type="radio" name="scope" value="Exam 2"><span>Exam 2 standards (Chapters 3 and 4)</span></label>
        <label class="choice"><input type="radio" name="scope" value="all"><span>Final exam (every standard)</span></label>
        <label class="choice"><input type="radio" name="scope" value="custom"><span>Choose my own standards (use the list below)</span></label>
      </fieldset>
      <fieldset class="group"><legend>My own standards</legend>
        <p class="hint-text">Checking any box selects “Choose my own standards”. Standards marked “coming soon” have no problems yet.</p>
        ${EXAM_ORDER.map((ex) => `<div class="checks"><p class="sub"><strong>${EXAM_TEXT[ex]}</strong></p>${idx.filter((s) => s.exam === ex).map((s) =>
    `<label class="choice small"><input type="checkbox" name="std" value="${s.code}" ${hasItems(s) ? '' : 'disabled'}><span>${s.code} ${esc(s.title)}${hasItems(s) ? '' : ' (coming soon)'}</span></label>`).join('')}</div>`).join('')}
      </fieldset>
      <div class="controls"><label for="per">Problems for each standard</label>
        <select id="per"><option>1</option><option>2</option></select></div>
      <label class="choice"><input type="checkbox" id="sw"><span>Show a stopwatch. It counts up, you can pause or hide it, and there is no time limit.</span></label>
      <p class="error" id="err" role="alert" hidden></p>
      <div class="actions"><button type="submit" class="btn">Start the practice test</button></div>
    </form></div>`);
  const form = root.querySelector('#tform');
  form.addEventListener('change', (e) => {
    if (e.target.name === 'std') form.querySelector('input[name=scope][value=custom]').checked = true;
  });
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const scope = form.querySelector('input[name=scope]:checked').value;
    const err = root.querySelector('#err');
    let chosen;
    if (scope === 'custom') chosen = [...form.querySelectorAll('input[name=std]:checked')].map((i) => i.value);
    else chosen = idx.filter((s) => scope === 'all' || s.exam === scope).map((s) => s.code);
    const withItems = chosen.filter((c) => idx.find((s) => s.code === c).items > 0);
    if (!withItems.length) {
      err.hidden = false;
      err.textContent = scope === 'custom' ? 'Choose at least one standard that has problems.' : 'No practice problems are available for that choice yet. Try Exam 1.';
      return;
    }
    err.hidden = true;
    const per = parseInt(root.querySelector('#per').value, 10);
    const pools = await Promise.all(withItems.map((c) => getPool(c)));
    const picked = [];
    pools.forEach((p) => {
      const cands = p.items.filter((i) => TEST_TIERS.includes(i.fam.tier));
      const byFam = {};
      cands.forEach((i) => { (byFam[i.family] = byFam[i.family] || []).push(i); });
      const fams = shuffle(Object.keys(byFam)).slice(0, per);
      fams.forEach((f) => { const v = byFam[f]; picked.push({ std: p.code, id: v[Math.floor(Math.random() * v.length)].id }); });
    });
    const order = idx.map((s) => s.code);
    picked.sort((a, b) => order.indexOf(a.std) - order.indexOf(b.std));
    saveSession({
      v: 1, scope, sw: root.querySelector('#sw').checked, started: Date.now(), phase: 'taking',
      items: picked, skipped: chosen.filter((c) => !withItems.includes(c)), accum: 0, running: true, last: Date.now(), showClock: true
    });
    location.hash = '#/test/run';
  });
  return { title: 'Practice test', el: root };
}

// ------------------------------------------------------------------ practice test: take
async function loadSessionItems(sess) {
  const codes = [...new Set(sess.items.map((i) => i.std))];
  const pools = await Promise.all(codes.map((c) => getPool(c)));
  const map = {};
  pools.forEach((p) => p.items.forEach((i) => { map[i.id] = i; }));
  return sess.items.map((i) => map[i.id]).filter(Boolean);
}
const fmt = (ms) => { const s = Math.floor(ms / 1000); const m = Math.floor(s / 60); return `${String(m).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`; };
const elapsedOf = (s) => s.accum + (s.running ? Date.now() - s.last : 0);

export async function testRunView() {
  const sess = loadSession();
  if (!sess || !sess.items || !sess.items.length) { location.hash = '#/test'; return { title: 'Practice test', el: el('<div><h1>Practice test</h1><p>Starting a new test…</p></div>') }; }
  if (sess.phase === 'done') { location.hash = '#/summary'; return { title: 'Check your work', el: el('<div><h1>Check your work</h1></div>') }; }
  const items = await loadSessionItems(sess);
  const scopeText = { 'Exam 1': 'Exam 1 standards', 'Exam 2': 'Exam 2 standards', all: 'every standard', custom: 'standards you chose' }[sess.scope];
  const root = el(`<div class="testrun"><h1>Practice test: ${scopeText}</h1>
    <p class="lead">${plural(items.length, 'problem', 'problems')}. Work each one on paper and show your thinking. Answers appear when you finish.${sess.skipped && sess.skipped.length ? ` ${plural(sess.skipped.length, 'standard has', 'standards have')} no problems yet and ${sess.skipped.length === 1 ? 'was' : 'were'} left out.` : ''}</p>
    ${sess.sw ? `<div class="stopwatch" role="group" aria-label="Stopwatch">
      <span id="clock-wrap">Time: <span id="clock" role="timer" aria-live="off">${fmt(elapsedOf(sess))}</span></span>
      <button type="button" class="btn secondary" id="pause" aria-pressed="false">Pause</button>
      <button type="button" class="btn secondary" id="hide" aria-pressed="false">Hide the time</button></div>` : ''}
    <div id="problems"></div>
    <div class="actions"><button type="button" class="btn" id="finish">I am finished: show the answers</button>
      <button type="button" class="btn secondary" id="print">Print this test</button></div></div>`);
  const holder = root.querySelector('#problems');
  items.forEach((it, i) => holder.appendChild(renderProblem(it, { mode: 'test', number: i + 1 })));
  let timer = null;
  const clock = root.querySelector('#clock');
  if (sess.sw) {
    const tick = () => { clock.textContent = fmt(elapsedOf(sess)); };
    timer = setInterval(() => { if (!document.body.contains(clock)) { clearInterval(timer); return; } tick(); }, 1000);
    const pause = root.querySelector('#pause');
    pause.addEventListener('click', () => {
      if (sess.running) { sess.accum = elapsedOf(sess); sess.running = false; pause.textContent = 'Resume'; pause.setAttribute('aria-pressed', 'true'); }
      else { sess.running = true; sess.last = Date.now(); pause.textContent = 'Pause'; pause.setAttribute('aria-pressed', 'false'); }
      saveSession(sess); tick();
    });
    const hide = root.querySelector('#hide');
    hide.addEventListener('click', () => {
      const wrap = root.querySelector('#clock-wrap');
      wrap.hidden = !wrap.hidden;
      hide.textContent = wrap.hidden ? 'Show the time' : 'Hide the time';
      hide.setAttribute('aria-pressed', String(wrap.hidden));
    });
  }
  root.querySelector('#finish').addEventListener('click', () => {
    sess.accum = elapsedOf(sess); sess.running = false; sess.phase = 'done'; saveSession(sess);
    clearInterval(timer);
    location.hash = '#/summary';
  });
  root.querySelector('#print').addEventListener('click', () => window.print());
  return { title: 'Practice test', el: root, after: () => typesetVisible(root) };
}

// ------------------------------------------------------------------ practice test: summary
export async function summaryView() {
  const sess = loadSession();
  if (!sess || sess.phase !== 'done') { location.hash = '#/test'; return { title: 'Practice test', el: el('<div><h1>Practice test</h1><p>Starting a new test…</p></div>') }; }
  const [items, idx] = await Promise.all([loadSessionItems(sess), getIndex()]);
  const root = el(`<div class="summary"><h1>Check your work</h1>
    <p class="lead">${sess.sw ? `Time on the test: <strong>${fmt(sess.accum)}</strong>. ` : ''}For each problem, compare the answer with your work, then mark how it went. Be honest with yourself: “Almost” and “Not yet” tell you where to practice next.</p>
    <section class="note" aria-labelledby="sum-h"><h2 id="sum-h">Your marks on this test</h2><p id="sumline" aria-live="polite"></p><div id="next-up"></div></section>
    <div id="problems"></div>
    <div class="actions"><a class="btn" href="#/test">Build another test</a>
      <button type="button" class="btn secondary" id="print">Print the answers</button></div></div>`);
  const sumline = root.querySelector('#sumline');
  const nextUp = root.querySelector('#next-up');
  const update = () => {
    const c = { got: 0, almost: 0, not: 0, none: 0 };
    const review = new Set();
    items.forEach((it) => { const r = getMark(it.id); if (r) { c[r]++; if (r !== 'got') review.add(it.std); } else c.none++; });
    sumline.textContent = `Got it: ${c.got}. Almost: ${c.almost}. Not yet: ${c.not}. Not marked: ${c.none}.`;
    nextUp.innerHTML = review.size
      ? `<p>Practice next:</p><ul>${[...review].map((code) => { const s = idx.find((x) => x.code === code); return `<li><a href="#/practice/${code}">${code} ${esc(s.title)}</a></li>`; }).join('')}</ul>`
      : '';
  };
  const holder = root.querySelector('#problems');
  items.forEach((it, i) => holder.appendChild(renderProblem(it, { mode: 'review', number: i + 1, showStd: true, onRated: update })));
  update();
  root.querySelector('#print').addEventListener('click', () => window.print());
  return { title: 'Check your work', el: root, after: () => typesetVisible(root) };
}

// ------------------------------------------------------------------ progress
export async function progressView() {
  const idx = await getIndex();
  const rows = idx.map((s) => { const t = tally(s.code); return { s, t }; });
  const tot = rows.reduce((a, r) => ({ got: a.got + r.t.got, almost: a.almost + r.t.almost, not: a.not + r.t.not }), { got: 0, almost: 0, not: 0 });
  const root = el(`<div><h1>My progress</h1>
    <p class="lead">These marks come from the “How did this go for you?” choices. They are saved only in this browser. Nobody else can see them.</p>
    <div class="table-wrap"><table class="data progress"><caption>Your marks by standard</caption>
      <thead><tr><th scope="col">Standard</th><th scope="col">Got it</th><th scope="col">Almost</th><th scope="col">Not yet</th></tr></thead>
      <tbody>${rows.map(({ s, t }) => `<tr><th scope="row"><a href="#/practice/${s.code}">${s.code}</a> <span class="meta">${esc(s.title)}</span></th><td>${t.got}</td><td>${t.almost}</td><td>${t.not}</td></tr>`).join('')}</tbody>
      <tfoot><tr><th scope="row">All standards</th><td>${tot.got}</td><td>${tot.almost}</td><td>${tot.not}</td></tr></tfoot></table></div>
    <details class="text-summary"><summary>Plain-text summary to copy into a reflection</summary>
      <label for="plain">Your summary (select the text and copy it)</label>
      <textarea id="plain" readonly rows="8"></textarea></details>
    <div class="reset"><button type="button" class="btn secondary" id="reset">Clear my marks</button>
      <span id="confirm" hidden role="group" aria-label="Confirm clearing marks">This clears every mark on this device. <button type="button" class="btn" id="yes">Yes, clear them</button> <button type="button" class="btn secondary" id="no">Cancel</button></span></div>
    <p id="reset-msg" aria-live="polite"></p></div>`);
  const plain = root.querySelector('#plain');
  const lines = rows.filter((r) => r.t.total).map((r) => `${r.s.code} ${r.s.title}: got it ${r.t.got}, almost ${r.t.almost}, not yet ${r.t.not}`);
  plain.value = lines.length ? `My Math 172 practice marks\n${lines.join('\n')}` : 'No marks yet. Mark a problem with “How did this go for you?” and it will appear here.';
  const reset = root.querySelector('#reset'), conf = root.querySelector('#confirm');
  reset.addEventListener('click', () => { conf.hidden = false; reset.hidden = true; root.querySelector('#yes').focus(); });
  root.querySelector('#no').addEventListener('click', () => { conf.hidden = true; reset.hidden = false; reset.focus(); });
  root.querySelector('#yes').addEventListener('click', () => { resetMarks(); clearSession(); location.hash = '#/progress'; location.reload(); });
  return { title: 'My progress', el: root };
}

// ------------------------------------------------------------------ about
export async function aboutView() {
  const cfg = await getConfig();
  const root = el(`<div class="prose"><h1>About this site</h1>
    <section aria-labelledby="how-h"><h2 id="how-h">How to use it</h2>
      <ul><li><strong>Practice by standard:</strong> one problem at a time. Try it on paper. If you are stuck, open the hint. Then open the answer, read the slips to watch for, and mark how it went.</li>
      <li><strong>Random recall:</strong> problems from several standards, mixed. The standard’s name appears only after you open the answer.</li>
      <li><strong>Practice test:</strong> a set of problems with no hints. Answers appear when you finish.</li></ul>
      <p>The marks are for you. They do not go to your instructor and they are not part of your grade.</p></section>
    <section aria-labelledby="math-h"><h2 id="math-h">Reading equations</h2>
      <p>Equations are drawn with MathJax. Each equation has a spoken label for screen readers (MathSpeak), and you can zoom the page without losing anything.</p>
      <label class="choice"><input type="checkbox" id="mathtab"><span>Make each equation a stop when I press Tab (for exploring an equation piece by piece with a screen reader)</span></label>
      <p class="hint-text" id="mathtab-msg" aria-live="polite"></p></section>
    <section aria-labelledby="acc-h"><h2 id="acc-h">Accessibility</h2>
      <p>This site is designed to meet WCAG 2.1 Level AA. It works with a keyboard alone, it reflows down to a 320-pixel-wide screen, every graph has a text description and a table of its values, and it uses no color-only cues. It was checked with automated tools and by keyboard. It has not yet been through the college’s formal accessibility review, and it has not been tested with every screen reader.</p>
      <p>If something does not work for you, <a href="mailto:${esc(cfg.contactEmail)}?subject=Math%20172%20practice%20site%20accessibility">email Dr. Romero</a> and describe what you were doing. You will get another way to do the same practice.</p></section>
    <section aria-labelledby="priv-h"><h2 id="priv-h">Privacy</h2>
      <p>There are no accounts, no tracking, and no outside services on this site. Your marks and any test in progress are stored in your own browser.</p></section>
    <section aria-labelledby="cred-h"><h2 id="cred-h">Where the problems come from</h2>
      <p>The problems follow the skills in the Math 172 standards for <em>Building Toward Calculus</em> and the CheckIt problem types from the TBIL Precalculus project. Many are generated, so the numbers change from one visit to the next. The “Exam 1 review question” problems are written out by hand. Dr. Martin Romero designed the course and this site, with help from an AI assistant (Claude, from Anthropic) to build it. If you think an answer is wrong, please <a href="mailto:${esc(cfg.contactEmail)}?subject=Math%20172%20practice%20site%20problem">send the problem and what you expected</a>.</p></section></div>`);
  const cb = root.querySelector('#mathtab');
  cb.checked = !!getPref('mathTab', false);
  cb.addEventListener('change', () => {
    setPref('mathTab', cb.checked);
    applyTabStops(document);
    root.querySelector('#mathtab-msg').textContent = cb.checked ? 'Equations are now tab stops.' : 'Equations are no longer tab stops.';
  });
  return { title: 'About', el: root };
}

export function notFoundView() {
  return { title: 'Page not found', el: el('<div><h1>That page is not here</h1><p><a href="#/">Go to the home page</a>.</p></div>') };
}
export function errorView(e) {
  return { title: 'Something went wrong', el: el(`<div><h1>Something went wrong</h1><p>The page could not load (${esc(e && e.message ? e.message : 'unknown error')}). Check your connection and <a href="#/">go to the home page</a>.</p></div>`) };
}
