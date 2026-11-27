# Math 172 Practice Site

A free, accessible practice and review website for **Math 172 (Precalculus & Trigonometry)** at Santa Ana College. Students practice any of the 38 standards, take a practice test, or do random recall, with a hint, an answer and common-slip notes for every problem.

It is a static site (no server, no accounts, no tracking) that deploys to Netlify. See [`site/README.md`](site/README.md) to run, deploy and embed it.

## How the three repos fit together

| Repo | Visibility | What it is for |
|---|---|---|
| **`172-practice-site`** (this repo) | Public | The student site, the problem pool it reads, and the generator that makes the pool |
| `172-textbook-problem-bank` | Public | End-of-section problems for the LibreTexts book *Building Toward Calculus*. The source of the audited templates copied here |
| `172-exam-bank` | **Private** | Real quizzes, exams, reassessments, their answer keys, the faculty problem banks and the seed register. Never deployed |

Nothing from `172-exam-bank` ever goes in this repo. New practice problems never reuse a real quiz or exam item.

## What is here

| Path | What it is |
|---|---|
| `site/` | The website: pages, MathJax (self-hosted), and the generated problem pool in `site/pool/` |
| `generators/pool.py` | Exports the pool: up to 12 versions per template, plus the hand-written problems |
| `generators/verify_pool.py` | Re-derives answers independently and fails if any is wrong (FN1 and FN2 so far) |
| `generators/fn1.py`, `fn2.py`, `common.py` | Problem templates and helpers. Answers are computed (SymPy), never typed by hand |
| `generators/build.py`, `packet.py` | Copied from the textbook repo; `pool.py` imports two helpers from `build.py` |
| `bank/standards.yaml` | The 38 standards |
| `bank/ch1/` | Template problems with `hint` and `slips` |
| `bank/fixed/` | Hand-written problems (the 38 Practice Exam 1 review questions) and their images |

## Make the pool

```bash
pip install pyyaml sympy matplotlib numpy
python3 generators/pool.py            # about 40 seconds; rewrites site/pool/
python3 generators/pool.py --check    # validates what is in site/pool/
python3 generators/verify_pool.py     # independent answer check
cd site && python3 -m http.server 8000   # then open http://localhost:8000
```

## Where templates come from

The templates and the chapter 1 bank files were copied from `172-textbook-problem-bank` at commit `2ce8242`. The bank files here add `hint` and `slips`, which the textbook repo does not have yet. When you copy updated templates in, **merge**; do not overwrite the hint and slip text.

## Docs

- [`SCHEMA.md`](SCHEMA.md): bank file and pool file formats, and what `pool.py` guarantees
- [`ACCESSIBILITY.md`](ACCESSIBILITY.md): what is built in, what was tested, what is not done yet
- [`ROADMAP.md`](ROADMAP.md): what comes next

---
*Built for Santa Ana College. Dr. Martin Romero, with an AI assistant (Claude).*
