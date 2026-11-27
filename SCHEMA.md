# Problem and pool formats

How a problem gets from the bank to a student. Three steps: **bank** (templates and hand-written problems) → **`generators/pool.py`** → **`site/pool/`** (what the site reads).

## Bank files

- `bank/standards.yaml`: the 38 standards (code, title, chapter, blurb; `section` for chapter 1 only).
- `bank/ch1/` (FN1, FN2), `bank/ch3/` (EL1–EL7), `bank/ch4/` (PF2, PF3, TE1–TE6), `bank/ch5/` (PR3–PR9): one file per standard that has templates. Each problem names a template in `generators/` (`fn1`, `fn2`, `el`, `pf`, `te`, `pr`) and a book `seed`. `BLUEPRINT.md` lists every family in `ch3`–`ch5` with a sample question.
- `bank/fixed/*.yaml`: hand-written problems with no template (see below).

A template problem in `bank/ch1/<CODE>.yaml`:

```yaml
- id: FN2-F-01            # standard - tier letter - number
  tier: floor             # floor | assessment | bridge | slip
  item_type: FN2.a
  kind: template
  template: piecewise_eval        # a function in generators/fn2.py
  seed: 11                        # the version printed in the textbook; the pool never reuses it
  answer: generated               # computed by the template, never typed by hand
  hint: 'Look at each input and decide which inequality it satisfies.'
  slips:
    - 'Using the wrong piece at the boundary value.'
  status: audited                 # proposed | draft | checked | audited | published
```

## Practice-site fields: `hint` and `slips`

Every problem that goes to the practice site needs both. They are written once per problem and apply to every version the pool makes from it.

| Field | Rule |
|---|---|
| `hint` | One or two sentences. Points at the first move or the idea; never states the answer. Written for a student who is stuck, not one who is checking. |
| `slips` | 1–3 short notes naming mistakes students really make. Phrased as what to check ("Did you evaluate inside the parentheses first?"), not as blame. |

The LibreTexts book build in `172-textbook-problem-bank` ignores both fields, so adding them never changes a published book page.

`pool.py` runs hints and slips through the same math clean-up as problems (degrees as `\text{°}`, `<` and `>` inside math as `\lt` and `\gt`). A bare `x<c` in a slip is read by the browser as an HTML tag and cuts the text off; the clean-up prevents that.

### Status

| Status | Meaning | Exported |
|---|---|---|
| `proposed`, `draft` | Not reviewed | No |
| `checked` | Passed the template's own asserts **and** the independent verifier (below); no outside audit yet | Yes |
| `audited` | An outside blind-solve audit found no open error (see `AUDIT-LOG.md`) | Yes |
| `published` | Audited and in the textbook | Yes |

All 67 families in `bank/ch3`–`ch5` are `checked`. They become `audited` when Dr. Romero's ChatGPT blind-solve loop comes back clean.

## Fixed problems: `bank/fixed/*.yaml`

Hand-written problems with no template (for example the Practice Exam 1 review set, `PE1-01` to `PE1-38`). They are exported to the pool as their own family so students see them like any other problem.

```yaml
source: where these came from            # optional
items:
- id: EXAMPLE-01
  standard: FN3                          # outcome code the problem practices
  stem: Let \(f(x) = 3x - 7\).         # HTML with \( \) math; may be empty
  parts:
  - q: Find \(f(2)\).
    a: \(f(2) = 3(2) - 7 = -1\).
  hint: Replace every \(x\) with the input.
  slips:
  - Dropping parentheses when the input is negative.
  figures:                               # optional
  - file: linear-graph.svg               # in bank/fixed/assets/
    alt: What is visible, never the answer
    table: {caption: ..., headers: [...], rows: [[...]]}   # collapsed table of values or labeled points
  table:                                 # optional data table shown in the problem; row_headers: true makes column 1 header cells
    caption: ...
    headers: [...]
    rows: [[...]]
  note: Changes from the Lab version     # for the author; not shown to students
```

Image files live in `bank/fixed/assets/` and are copied to `site/pool/figures/`. Because these items are fixed, every student sees the same numbers.

## Pool files (`site/pool/`)

Written by `generators/pool.py`. Never edit by hand.

- `index.json`: `{standards: [{code, title, chapter, section?, blurb, exam, items, families, checkit}]}`. `exam` is Exam 1 (Ch. 1–2), Exam 2 (Ch. 3–4) or Final only (Ch. 5).
- `<CODE>.json`: `{families: {id: {tier, types, hint, slips, bridge_note?, source?}}, items: [{id, family, stem, parts: [{q, a}], figures: [{src, alt, label?, table?}], seed?}]}`.
- Tiers shown to students: floor "Core practice", assessment "Putting it together", slip "Spot the slip", bridge "Looking ahead to calculus", review "Exam 1 review question".
- Only `checked`, `audited` or `published` problems are exported; `draft` and `proposed` problems stay out until approved.

### What `pool.py` does to every problem

| Step | Rule |
|---|---|
| Seeds | `100000 + 1000 × family index + try`, so pool versions never collide with the small book seeds |
| Versions | Up to 12 per template (`--versions`). A version is skipped if its printed text (stem, parts, figure description) matches a book version or an earlier pool version. Some templates cannot make 12 different versions (FN1-B-01 makes 3). |
| Math | Degrees written `\text{°}`; `<` and `>` inside math written `\lt` and `\gt`; `\allowbreak` between ordered pairs so long lists wrap |
| HTML | Inline `style` attributes removed; the student-work box becomes `class="work"`; tables become `table.data` with header cells and math in numeric cells |
| Checks (`check_item`) | Balanced `\( \)`, non-empty answers, every figure has alt text and an existing file, no inline styles. A failure stops the export. |

### Independent check

Two programs re-derive answers from the printed problem alone, without calling the templates.

| Program | Covers | Result |
|---|---|---|
| `generators/verify_pool.py` (LaTeX-to-SymPy reader) | FN1, FN2 | 507 checks, 0 fail |
| `generators/verify_ch35.py` | EL1–EL7, PF2, PF3, TE1–TE6, PR3–PR9 (804 items) | 1,635 checks, 0 fail |

`verify_ch35.py` reads only the printed stem, question and answer from `site/pool/*.json`. It has four layers: **G1** re-evaluates every chain of equalities in an answer (`a = b = c`, `a \approx b`) with a small LaTeX evaluator (`texeval.py`), allowing half a unit of the last printed digit for an approximation; a **generic worked-step layer** (`vc_gen.py`) re-checks each intermediate step at the true values of its letters; **per-template checks** (`vc_el.py`, `vc_pr.py`, `vc_trig.py`, `vc_tri.py`) parse the question, solve it again (roots, intercepts, asymptotes, ranges, triangles, inequalities) and compare with the printed answer; and **env chains** substitute the solution back into the printed steps.

```bash
python3 generators/verify_ch35.py [CODE ...]        # exit status 1 on any failure
python3 generators/mutate_ch35.py [CODE ...] [--per-family N] [--seed S]
```

**Does the checker catch errors?** `mutate_ch35.py` copies an answer, plants one wrong number or sign, and asks whether the verifier fails. Run with `--seed 5 --per-family 4`: 598 plants, **95.0% caught**; 100% of plants that change a final answer; 92.6% of sign changes; 91.9% of changes anywhere in the text. The survivors are mostly wording that no program reads (a prose sentence with the number in it) and plants that leave an equivalent expression. The tool writes survivors to `.mutation-survivors.json` (ignored by git).

What a program does **not** judge: whether a hint gives the answer away, whether a slip is a mistake students really make, whether wording is ambiguous, whether a problem is fair. That is what the outside audit is for.

### Public pool and private assessments

- **Public pool (this repo):** each template exports up to 12 versions, drawn from seeds 100000 and up. Decision, Nov 27 2026 (Dr. Romero): publish all of them for now rather than capping the public pool at 3. Faculty assessments use a separate seed range, so no assessment version appears in the public pool. The site picks a standard, then a kind of problem, then a version, and avoids repeating recent ones.
- **Faculty pool (planned, private):** at least 5 different problems per standard for assessments and reassessments, drawn from the same templates with seeds in a separate range that this repo never uses, and the faculty generator skips any version whose printed text matches a public one. The seed register lives in `172-exam-bank`.
- **Real quiz and exam items and their keys** live only in the private `172-exam-bank` repo. New bank problems never reuse them.
- **How that rule is checked.** Before each export, every question in the new standards is compared with the text of the real items (kept outside this repo, never committed). Nov 27 2026: no whole item is reused. A few short special-value questions (for example `\arcsin` of a standard value) coincide with an item because there is only one way to write them. Where a template produced a word-for-word twin of a real item, the template was changed so it cannot (five templates). About ten near-variants remain: the same kind of problem with a different sign, function or value, so a different answer.
