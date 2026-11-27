# Accessibility (WCAG 2.1 AA): Math 172 practice site

The student site in `site/` targets **WCAG 2.1 Level AA**, the standard in the DOJ ADA Title II web rule.

## Built in

| Area | What the site does | WCAG |
|---|---|---|
| Math | MathJax 4.1.3, self-hosted, with MathSpeak speech. Equations are text, never images. An About-page option makes each equation a tab stop for exploring piece by piece. | 1.1.1, 1.3.1 |
| Structure | One `<h1>` per view, real headings and lists, `<main>`, labeled landmarks, a skip link, `aria-current` on the active navigation link | 1.3.1, 2.4.1, 2.4.6 |
| Focus | After navigation, focus moves to the page heading (not on first load). Visible 3 px focus outline on every control. | 2.4.3, 2.4.7 |
| Keyboard | Every control works with Tab, Enter, Space and arrow keys inside radio groups. No keyboard traps. | 2.1.1, 2.1.2 |
| Hints and answers | Buttons with `aria-expanded` and `aria-controls`; the label changes to "Hide …"; revealing the answer is announced in a polite live region | 4.1.2, 4.1.3 |
| Ratings | Radio group in a `fieldset` with a `legend` (Got it / Almost / Not yet); the saved message is announced | 1.3.1, 3.3.2, 4.1.3 |
| Graphs | Alt text describes what is visible and never gives a computed answer. A collapsed table of values or labeled points names its problem number. | 1.1.1 |
| Reflow | No horizontal scrolling at 320 px. Over-wide equations scroll inside their own region. Text-spacing overrides do not clip or overlap. | 1.4.10, 1.4.12 |
| Targets and contrast | Targets are at least 44 px; text contrast meets 4.5:1; nothing is conveyed by color alone | 1.4.1, 1.4.3, 2.5.5 |
| Time | The practice-test stopwatch counts up, can be paused or hidden, and never ends the test | 2.2.1 |
| Privacy and security | No third-party requests (a strict Content Security Policy enforces this), no accounts, marks kept only in the student's own browser | n/a |
| Print | Print stylesheet hides navigation, buttons and rating controls; hints and answers print only if they are open | Recommended |

## Checked so far (Nov 27, 2026)

| Check | Result |
|---|---|
| axe-core (WCAG 2.0/2.1 A and AA) on every view, including hint and answer open, tables open, test builder, test run, summary, progress, About | 0 violations. Pages report one "incomplete" for color contrast on MathJax glyphs, which axe cannot measure; the text color is #14232b on #f4f7f7 (14.9:1) and the white problem cards are higher. |
| Keyboard-only run through practice, recall, test, summary and progress | Passes |
| Reflow at 320 px, plain and with the WCAG text-spacing override, on nine views | No horizontal overflow |
| Speech lint: 2,052 rendered equations, MathSpeak string generated for each | 0 empty, 0 errors, 0 flagged |
| Figures: all 139 load, all have alt text | Pass |
| Answers: independent re-derivation of FN1 and FN2 answers (507 checks) | 0 failures |

## Not yet done

- **No real assistive-technology testing.** NVDA, JAWS and VoiceOver have not been run on this site. All of the above is automated or keyboard testing in a Chromium browser.
- **Degrees are spoken as the singular "degree"** by MathSpeak (for example "165 degree").
- **The college's formal accessibility review** has not happened. The About page says so.
- Curve graphs have alt text and a table of points, but that text has been checked against the generator's inputs, not read by a blind student.

This is an AI-assisted review and automated testing, not a compliance certification.
