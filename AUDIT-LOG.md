# Audit log

Independent reviews of the problems on this site. Add a new section for each review.

## 2026-11-27 · ChatGPT blind-solve audit (Exam 1 review set and generated FN1/FN2 pool)

**Method.** Two packets were built with `generators/audit_pool.py`. For each, the reviewer first solved every problem blind (problem text and images only). It then compared its own answers with the key, the hints, the common-slip notes, and the standard tags (`CONVENTIONS.md`, `standards.md`).

| Packet | Contents | Items |
|---|---|---|
| A | Practice Exam 1 review items (hand-written, `bank/fixed/PracticeExam1.yaml`) | 38 |
| B | Generated pool, 2 sample versions per family (FN1, FN2) | 40 |

**Result.** All 78 keyed answers matched the reviewer's independent solutions. All 29 images matched their alt-text descriptions and tables. The reviewer reported 99% confidence and noted that the checks cover the sampled items, not every possible generator output.

**Corrections requested and how each was resolved.**

| Item | Finding | Resolution |
|---|---|---|
| B #9 (FN1-B-01) | The slip hard-coded the radius 5 (`sqrt(25-x^2)`), but this version has radius 10 | Slip rewritten without a number: it now talks about the positive square root being only the top half |
| B #13, #14 (FN1-F-02) | The hint told students to test one input, which can disprove a function but cannot prove one | Hint now separates the two jobs: one input with two outputs is enough to show "not a function"; showing "is a function" needs an argument for every x. Added a slip for concluding "function" from one test input |
| A #18 (PE1-18) | Part (b) gave 5π/4 and a Quadrant III point, which revealed the answer to part (a) | Part (b) now uses θ = 2π/3 (Quadrant II) with its terminal point. Answer, hint and slip updated together |
| A #30 (PE1-30) | "A squared variable has two solutions" is too broad. `x = ±5` is shorthand | Slip now reads "an equation of the form x² = a positive number has two solutions". The answer is written as x = −5 or x = 5 |
| A #31, #32, #34 (LF3) | Tags disagreed with the standards sheet, which put equation-finding under LF2 | The sheet was wrong, not the tags. Dr. Romero's Quiz 2 lists "equation of a line from a point and an x-intercept" (1.4.2a) and "from both intercepts" (1.4.2b) under 1.4.2, which is LF3. The tags stay LF3. The LF2 and LF3 descriptions in `bank/standards.yaml` were corrected to match Quiz 2 |

**Still open from this audit.**

- The reviewer's full report (78 verdict rows and "smaller convention issues") was not available to Claude. Anything in it beyond the five items above is not yet reviewed.
- PE1-34 (equation read from a graph) keeps the tag LF3 from the original Practice Exam 1. Quiz 2 has no item of this exact kind, so the tag is a judgment call for Dr. Romero.
- Independent answer re-derivation (`generators/verify_pool.py`) covers FN1 and FN2 only: 507 checks pass, 0 fail. Other standards have no generated problems yet.

## 2026-11-27 · Independent verifier, planted-error test and reuse check (22 new standards)

**Scope.** EL1–EL7, PF2, PF3, TE1–TE6, PR3–PR9: 67 families, 804 items (12 versions per family), all status `checked`. This is a check by programs and a page test, **not** an outside audit. Nothing here is `audited` yet.

| Check | Result |
|---|---|
| Template self-checks (every answer computed two ways before export) | All pass; draws that fail an assert are dropped silently and counted in the `pool.py` output |
| Independent verifier `generators/verify_ch35.py` (reads only the printed problem) | 1,702 checks, **0 fail** (1,635 at first; the extra checks were added after the audit below) |
| Planted-error test `generators/mutate_ch35.py` (seed 5, 4 per family) | 599 plants: **95.8% caught**, 100% of wrong final answers, 93.4% of sign slips (95.0% of 598 before the audit below) |
| Real-item reuse check (against the private bank, never stored here) | No whole item reused. 5 templates changed to avoid word-for-word twins. About 10 near-variants remain (different sign, function or value, so a different answer). Short special-value questions coincide where there is only one way to write them |
| Page test, all 22 pages in Chrome | Math renders, no raw LaTeX on screen, no `None` or `nan`, exactly one `h1`, axe-core WCAG 2.1 A and AA: **0 violations**. Colour contrast is "incomplete" in axe (it cannot compute it for math), so it still needs a manual check |
| MathJax sweep of every math fragment in the new pools | 3,610 distinct fragments, 0 errors |

**Defects the checks found and that were fixed before this commit.** None was a wrong keyed answer in a final pool; they are listed so the next reviewer knows what kind of error to look for.

| Where | Defect | Fix |
|---|---|---|
| TE1 sum and difference | A version wrote 15° = 330° + 45°, which is true only after subtracting 360° | The two angles must now add or subtract to the target exactly |
| PR6, PR9 | Printed `+ -2` and `- -2` (9 places in the earlier export) | Sign handled in the template |
| PR8 | "Subtract −2 from both sides" | "Add 2 to both sides" |
| EL7 | "A culture of a viral video's views" (grammar) | Subject, unit and noun are now chosen together |
| Hints and slips on the site (EL4) | A bare `x<c` was read as an HTML tag and cut the sentence off | `pool.py` now cleans hints and slips like problems. The same clean-up also touched FN2, TR5 and TE4–TE6 (`<` written `\lt`, degree signs written `\text{°}`); their wording is unchanged |
| Verifier itself | About twenty bugs in the checker (regexes, domain handling, a dead branch found by the planted-error test) | Fixed; none hid a wrong problem |

**Limits to keep in view.**

- The new items have **no graphs**. PF2, PF3, PR3 and PR7 are about graphs; the pool tests the algebra behind them (asymptotes, intercepts, period, end behaviour) in words.
- The verifier cannot judge wording, fairness, hints or slips. The outside audit is for those.
- `CONVENTIONS.md` (in the textbook repo) was written from Chapters 1–2 and is still a draft. It does not yet say how to round logarithm and trig answers, or how to write complex answers and inequalities. The audit packets ask the reviewer to mark such cases "convention to confirm".
- No testing with a real screen reader (NVDA, JAWS, VoiceOver) yet.
- Closed endpoint dots are clipped in the two-piece graphs of the existing Chapter 1–2 pool. Not touched here.

**Next.** Run the three audit packets (`Math172-ChatGPT-audit-2`), fix what comes back, then change `status: checked` to `audited` and add the results to this log.

## 2026-11-27 · ChatGPT blind-solve audit 2 (22 new standards, 134 sampled problems)

**Method.** Three packets built with `generators/audit_pool.py --standards` (C1 exponentials and logs, 46 problems; C2 trig, 54; C3 polynomials and rational, 34; two versions of every family). For each, the reviewer solved blind, then compared with the key, hints, slips and standard tags.

**Result.** All 134 keyed numerical values and solution sets matched the reviewer's own work. Two worked equations were wrong and three pieces of guidance were wrong or incomplete. Reviewer confidence: 99%, for the samples only.

| Where | Finding | Resolution |
|---|---|---|
| C3 #7, #8 (PR4-F-01) | The answer wrote `g(x) = (x+2)(x²−5x−6) − 8`, but the question defines g as the *fraction*; that expression is its numerator | Answer now reads `g(x) = x² − 5x − 6 − 8/(x+2)`, with `x ≠ −2`, and then states the identity for the numerator. A zero remainder now says `g(x) = q(x)` for `x ≠` the divisor's zero |
| C1 #29, #30 (EL5-F-01) | A logarithm expansion is only valid for positive variables | "Assume all variables are positive." added to the expand questions and, for consistency, the condense questions |
| C2 #8 (PF3-A-01) | The hint and slips were written for `arccos` only (`[0, π]`), but the family also uses `arcsin` | Hint and slips now cover both functions and give both intervals |
| C3 #25, #26 (PR7-F-01) | "A factor common to both gives a hole" is not true in general: if the factor is still in the denominator after canceling, the input is a vertical asymptote | Hint and slip state the rule. The answer to part (a) now shows the denominator left after canceling and that it is not 0 at the hole |

**Found while fixing, not reported by the reviewer.** The PR4 slip named a divisor (`x+2`) that most versions do not use, and the PR6-F-02 hint named a variable `p` that never appears in the problems. Both were reworded.

**Why the independent verifier missed the PR4 error.** It compared the rewritten `g(x)` with the numerator, the same mistake as the template. It now reads the question to see whether the function is a fraction, checks the printed `g(x) = q + r/D` against N/D, the excluded value, and the numerator identity. Other checks added: the left-over denominator in a hole answer, the positive-variables sentence, every inverse function used by a family named in its hint, and nine prose restatements that a planted-error run showed nothing was reading (the angle named in "is not in that interval", "whose tangent is …", the expression inside the domain inequality, `F(0)` in a y-intercept, the numerator in a zero-remainder answer). Run against the pool as it was before the fixes, the new checks fail on every affected family; after the fixes: 1,702 checks, 0 fail.

**Still open.**

- The reviewer's full report (134 verdict rows and the "remaining hint, wording, and convention issues") has not reached Claude. Only the five-row table above was available, so anything else in it is not yet reviewed.
- The fixed families are still `checked`. They move to `audited` after a re-check packet comes back clean.

