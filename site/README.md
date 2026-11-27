# Math 172 Practice Site (student side)

A static, no-build website where students practice any of the 38 Math 172 standards, one problem at a time, with hints, answers and common-slip notes. It reads pre-generated problem files from `pool/`, so it needs no server code and makes no third-party requests.

Pool problems are **not** the real quiz or exam items. Real assessments live in the private `172-exam-bank` repo, never here.

## What students can do

| Route | What it does |
|---|---|
| `#/` | Home: choose a standard, random recall, practice test, link to the AI assistant |
| `#/practice` and `#/practice/FN2` | All 38 standards, then one standard at a time (kind of problem, next problem, tally of marks) |
| `#/recall` | Random problem from the standards the student picks; the answer names the standard |
| `#/test` and `#/test/run` | Practice test built from chosen standards, with an optional count-up stopwatch (pause or hide) |
| `#/summary` | After a test: ratings and where to practice next |
| `#/progress` | The student's own marks per standard (Got it / Almost / Not yet) |
| `#/about` | How the site works, the accessibility statement, contact |

Marks stay in the student's own browser (localStorage). Nothing is sent anywhere. A test in progress lives in sessionStorage. If the browser blocks storage, the site still works and says so.

## Run it on your computer

The site must be served over HTTP. Opening `index.html` from a folder does not work, because MathJax's speech worker and the pool files are loaded with `fetch`.

```bash
cd site
python3 -m http.server 8000
# open http://localhost:8000/
```

That server does not send the security headers from `_headers`. To test with them, use any static server that reads Netlify's `_headers` file, such as `netlify dev`.

## Deploy to Netlify

The repo's `netlify.toml` already tells Netlify to publish the `site` folder with no build step, so importing the repo needs no manual settings. If you ever deploy another way (for example a drag-and-drop), the folder to upload is `site`, not the whole repo; otherwise the home page shows "Page not found" and the site only appears under `/site/`.

`_headers` is picked up automatically. It sets a strict Content Security Policy (everything from this site only), long caching for `/vendor/*`, and a 5-minute cache for `/pool/*` so a regenerated pool shows up quickly.

The headers deliberately do **not** set `X-Frame-Options` or `frame-ancestors`, so the site can be embedded in Canvas and LibreTexts.

## Embed in Canvas or LibreTexts

```html
<iframe src="https://YOUR-SITE.netlify.app/?embed=1#/practice/FN2"
        title="Math 172 practice: Function Notation"
        width="100%" height="900" style="border:0"></iframe>
```

- `?embed=1` hides the site brand and the footer text.
- Always give the iframe a meaningful `title`.
- Any route works after the `#`, for example `#/practice/TR1` or `#/recall`.

## Settings: `config.json`

| Key | Used for | Now |
|---|---|---|
| `course`, `college` | Page title and header | Set |
| `assistantUrl` | "Course assistant" links on the home page, on each standard's page and in the footer | Playlab assistant |
| `contactEmail` | About page | romero_martin@sac.edu |
| `checkitUrl` | CheckIt link for each standard (`{code}` is replaced by the standard code) | Set |
| `supportUrl` | Base address of the support pages. The site adds the lowercase code, so `https://example.netlify.app` becomes `https://example.netlify.app/fn2/` | **Blank: link hidden** |
| `faqUrl` | Base address of the FAQ pages, same pattern | **Blank: link hidden** |

Fill in `supportUrl` and `faqUrl` once those pages are deployed. Until then those links do not appear. If your pages use a different address pattern (for example one Netlify site per standard), the link code in `js/views.js` (function `moreLinks`) is the one place to change.

## Regenerate the problem pool

The pool is produced from the bank (`bank/` and `generators/`), never edited by hand.

```bash
python3 generators/pool.py                # full rebuild, about 40 seconds, wipes site/pool first
python3 generators/pool.py --only FN1,FN2 # rebuild just these standards
python3 generators/pool.py --check        # validate what is already in site/pool
python3 generators/verify_pool.py         # independent re-check of answers (FN1 and FN2)
```

`pool.py` only exports problems whose status is audited or published, plus the fixed problems in `bank/fixed/`. It refuses to write a problem that has unbalanced math delimiters, an empty answer, a figure without alt text, a missing figure file, or inline styles. See [`../SCHEMA.md`](../SCHEMA.md) for the file formats.

Pool seeds start at 100000 so they never collide with the book's seeds. The book's audited output (`.lock.json`) is not touched by the pool.

## Folder map

| Path | What it is |
|---|---|
| `index.html` | The one page; skip link, header, `<main>`, footer, live region |
| `js/` | `app.js` router · `views.js` pages · `problem.js` one problem · `math.js` MathJax helpers · `store.js` marks · `data.js` pool loading · `live.js` screen-reader announcements · `mathjax-config.js` |
| `css/styles.css` | All styles: 3 px focus outlines, 44 px targets, print rules, reflow down to 320 px |
| `vendor/mathjax/` | MathJax 4.1.3, self-hosted (core, fonts, speech worker, MathSpeak maps, license) |
| `pool/` | `index.json` (the 38 standards), `<CODE>.json` (problems), `figures/` |
| `_headers` | Netlify security and cache headers |
| `config.json` | Settings (above) |

## Accessibility in brief

Target: WCAG 2.1 Level AA. Full list and audit notes: [`../ACCESSIBILITY.md`](../ACCESSIBILITY.md).

- Math is real MathJax text with MathSpeak speech. Students who want to move through equations one at a time can turn on "Make each equation a stop when I press Tab" on the About page.
- Every graph has alt text that describes what is visible (never an answer) and a collapsed table of values or labeled points.
- Hints and answers use buttons with `aria-expanded`. Focus moves to the page heading after navigation.
- Light theme only, no timers that end anything, no color-only meaning, works at 320 px width and with text-spacing overrides.

**Not yet done:** testing with NVDA, JAWS or VoiceOver, and the college's formal accessibility review. Automated checks (axe-core, keyboard, reflow, a speech lint) all pass, but they are not a substitute for people using assistive technology.

## Known limits

- Degrees are spoken as the singular "degree" by MathSpeak.
- 22 of the 38 standards have no practice problems yet; their pages say "coming soon" and link to CheckIt, and the test builder leaves them out.
- The CheckIt link pattern is assumed to be the same for every standard.
