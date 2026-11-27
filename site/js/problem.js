// Builds one problem as an <article>. Content comes from our own pool files (trusted HTML with \( \) math).
import { TIER_LABEL, esc } from './data.js';
import { RATINGS, getMark, setMark } from './store.js';
import { typeset } from './math.js';
import { announce } from './live.js';

let uidn = 0;

function tableHTML(t, uid, suffix) {
  const th = t.headers.map((h) => `<th scope="col">${h}</th>`).join('');
  const rows = t.rows.map((r) => '<tr>' + r.map((c) => `<td>${c}</td>`).join('') + '</tr>').join('');
  return `<div class="table-wrap"><table class="data"><caption>${t.caption}${suffix}</caption><thead><tr>${th}</tr></thead><tbody>${rows}</tbody></table></div>`;
}

function figureHTML(f, uid, num) {
  const suffix = num ? ` (problem ${num})` : '';
  const label = f.label ? `<figcaption><strong>${f.label}</strong></figcaption>` : '';
  const tbl = f.table
    ? `<details class="figtable"><summary>${f.table.toggle || 'Table of values'}${suffix}</summary>${tableHTML(f.table, uid, suffix)}</details>`
    : '';
  return `<figure class="fig">${label}<img src="pool/${f.src}" alt="${esc(f.alt)}">${tbl}</figure>`;
}

function listHTML(parts, key) {
  if (parts.length === 1) return `<div class="single">${parts[0][key]}</div>`;
  return '<ol class="parts" type="a">' + parts.map((p) => `<li>${p[key]}</li>`).join('') + '</ol>';
}

/**
 * opts:
 *   mode      'practice' (hint + answer on request), 'test' (nothing revealed), 'review' (answer always shown)
 *   number    problem number to show (optional)
 *   heading   heading level (default 2)
 *   showStd   show the standard code in the heading
 *   stdTitle  title of the standard (used when showStd)
 *   afterAnswer(container)  called when the answer is shown (recall mode adds the standard name here)
 */
export function renderProblem(item, opts) {
  opts = opts || {};
  const uid = 'p' + (++uidn);
  const h = opts.heading || 2;
  const fam = item.fam || {};
  const tier = TIER_LABEL[fam.tier] || '';
  const label = (opts.number ? 'Problem ' + opts.number : 'Problem') + (opts.showStd ? ` · ${item.std}` : '');
  const art = document.createElement('article');
  art.className = 'problem';
  art.setAttribute('aria-labelledby', uid + '-h');
  const figs = (item.figures || []).map((f) => figureHTML(f, uid, opts.number)).join('');
  const parts = item.parts;
  const slips = (fam.slips || []).length
    ? `<h${h + 1} class="sub">Common slips to check for</h${h + 1}><ul class="slips">${fam.slips.map((s) => `<li>${s}</li>`).join('')}</ul>`
    : '';
  const rating = `<fieldset class="rate"><legend>How did this go for you?</legend>${RATINGS.map((r) =>
    `<label class="choice"><input type="radio" name="${uid}-r" value="${r.key}"><span>${r.label}</span></label>`).join('')}</fieldset>
    <p class="saved" id="${uid}-saved" aria-live="polite"></p>`;

  let actions = '';
  let hidden = '';
  const answerBody = `<h${h + 1} class="sub">Answer</h${h + 1}>${listHTML(parts, 'a')}<div class="after-answer"></div>${slips}${rating}`;
  if (opts.mode === 'practice') {
    actions = `<div class="actions">
      ${fam.hint ? `<button type="button" class="btn secondary" aria-expanded="false" aria-controls="${uid}-hint" data-act="hint">Show a hint</button>` : ''}
      <button type="button" class="btn secondary" aria-expanded="false" aria-controls="${uid}-ans" data-act="ans">Show the answer</button>
    </div>`;
    hidden = `<div class="reveal" id="${uid}-hint" hidden><h${h + 1} class="sub">Hint</h${h + 1}><p>${fam.hint || ''}</p></div>
      <div class="reveal" id="${uid}-ans" hidden>${answerBody}</div>`;
  } else if (opts.mode === 'review') {
    hidden = `<div class="reveal" id="${uid}-ans">${answerBody}</div>`;
  }
  art.innerHTML = `
    <h${h} id="${uid}-h" tabindex="-1">${label}${tier && opts.mode !== 'test' ? ` <span class="tier">${tier}</span>` : ''}</h${h}>
    ${item.stem ? `<div class="stem">${item.stem}</div>` : ''}
    ${figs}
    <div class="question">${listHTML(parts, 'q')}</div>
    ${actions}${hidden}`;

  // ---- behaviour
  const toggle = (btn, shownText, hiddenText) => {
    const target = art.querySelector('#' + btn.getAttribute('aria-controls'));
    const open = btn.getAttribute('aria-expanded') === 'true';
    if (open) {
      target.hidden = true;
      btn.setAttribute('aria-expanded', 'false');
      btn.textContent = hiddenText;
      return;
    }
    target.hidden = false;
    btn.setAttribute('aria-expanded', 'true');
    btn.textContent = shownText;
    // equations are rendered when first shown, so they wrap to the visible width
    if (!target.dataset.done) {
      target.dataset.done = '1';
      if (target.id.endsWith('-ans') && opts.afterAnswer) opts.afterAnswer(target.querySelector('.after-answer'), item);
      typeset(target);
    }
    if (target.id.endsWith('-ans')) announce('Answer shown below.');
  };
  art.querySelectorAll('[data-act]').forEach((b) => {
    if (b.dataset.act === 'hint') b.addEventListener('click', () => toggle(b, 'Hide the hint', 'Show a hint'));
    if (b.dataset.act === 'ans') b.addEventListener('click', () => toggle(b, 'Hide the answer', 'Show the answer'));
  });
  const std = item.std;
  const prior = getMark(item.id);
  art.querySelectorAll(`input[name="${uid}-r"]`).forEach((inp) => {
    if (inp.value === prior) inp.checked = true;
    inp.addEventListener('change', () => {
      const ok = setMark(std, item.id, inp.value);
      const lab = RATINGS.find((r) => r.key === inp.value).label;
      const msg = art.querySelector(`#${uid}-saved`);
      msg.textContent = ok ? `Saved: ${lab}.` : `Marked as ${lab} for now. This browser would not save it.`;
      if (opts.onRated) opts.onRated(inp.value);
    });
  });
  if (opts.mode === 'review') {
    const ans = art.querySelector(`#${uid}-ans`);
    if (opts.afterAnswer) opts.afterAnswer(ans.querySelector('.after-answer'), item);
  }
  return art;
}

// Render math in everything that is visible now (hidden hint/answer sections wait until they open).
export function typesetVisible(art) {
  const targets = [];
  art.querySelectorAll('.stem, .question, figure, .reveal:not([hidden])').forEach((n) => targets.push(n));
  return Promise.all(targets.map((n) => { if (n.dataset.done) return null; n.dataset.done = '1'; return typeset(n); }));
}
