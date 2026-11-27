# Roadmap

| # | Item | Status |
|---|---|---|
| 1 | Student site shell: practice by standard, random recall, practice test, progress, About | **Done** |
| 2 | Pool export with checks, plus independent answer verification (FN1, FN2) | **Done** |
| 3 | Deploy to Netlify; set `supportUrl` and `faqUrl` in `site/config.json` | Needs the deployed addresses |
| 4 | Test with NVDA, JAWS and VoiceOver; send to the college's accessibility review | Not started |
| 5a | Practice problems for the 22 standards that had none (EL1–EL7, PF2, PF3, TE1–TE6, PR3–PR9): 67 families, 804 items, text only | **Done** (status `checked`) |
| 5b | Templates for the 14 standards that have only the Exam 1 review items (FN3, FN4–6, LF1/2/3/5, PR1, PR2, TR1, TR2, TR5, PF1) | Not started; waiting for Dr. Romero's go-ahead |
| 6 | Independent answer checks. FN1, FN2 and the 22 Chapter 3–5 standards are covered; the 14 thin standards have no generated items yet | **Done** for all generated items |
| 6b | Outside blind-solve audit of the 22 new standards (three packets built; then flip `checked` to `audited`) | Packets ready; waiting for the ChatGPT run |
| 6c | Graphs in the new standards (exponential, logarithm, tangent and other trig graphs, polynomial and rational graphs) | Not started; every new item is text only |
| 7 | Ingest the CheckIt-support multiple-choice items as practice problems | Not started |
| 8 | "Critique this answer" items that pair with the course AI assistant | Later |

The faculty problem generator (at least 5 different problems per standard, Word export, seeds in a range this repo never uses) belongs in the private `172-exam-bank` repo, because its output feeds real assessments.
