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
