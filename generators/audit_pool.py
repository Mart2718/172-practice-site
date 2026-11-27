#!/usr/bin/env python3
"""Make math-audit packets for ChatGPT (or any reviewer) from the practice pool.

    python3 generators/audit_pool.py [--out audit] [--per-family 2] [--conventions PATH]

Two packets are written under --out:

  pe1/        the hand-written Practice Exam 1 review problems (no code checks them, so a human or AI
              reviewer is the only check)
  generated/  --per-family spread-out versions of every template family (the independent checker,
              verify_pool.py, has already re-derived every answer; this is a spot check of wording,
              graphs, hints and slips)

Each packet holds:
  problems.md   problems only (the reviewer solves these first, blind)
  key.md        answers, hints, common slips, standard tags, author notes (sent second)
  figures/      PNG copies of every graph the reviewer needs to see
  CONVENTIONS.md, standards.md   (sent with the key; only when --conventions is given or found)

and --out/AUDIT-PROMPT.md holds the two prompts to paste.
"""
import argparse
import html
import json
import os
import re
import shutil
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
POOL = os.path.join(ROOT, "site", "pool")
sys.path.insert(0, HERE)
from packet import to_md as _to_md  # noqa: E402  (HTML + \( \) math -> Markdown with $ $)


def to_md(s):
    """_to_md, minus the \\allowbreak line-wrap hints that only matter on a web page."""
    s = s.replace("\\allowbreak ", "").replace("\\allowbreak", "")
    return _to_md(s.replace("$", r"\$"))  # a literal dollar sign must not look like a math delimiter

TIER = {"floor": "Core practice", "assessment": "Putting it together", "slip": "Spot the slip",
        "bridge": "Looking ahead to calculus", "review": "Exam 1 review question"}

PROMPT = """# Math audit for the Math 172 practice pool: reviewer instructions

Works with ChatGPT, a separate Claude agent, or a human colleague. Run each packet in **two messages**.

**Message 1.** Paste the Step 1 prompt below. Attach `problems.md` and every image in `figures/`. **Do not send the key.**

**Message 2.** After the reviewer has posted its own solutions, paste the Step 2 prompt. Attach `key.md`, `CONVENTIONS.md` and `standards.md`.

A reviewer who sees the answers first tends to agree with them. One who solves first catches real errors.

---

## Step 1 prompt (solve blind)

> You are reviewing practice problems for a community college precalculus course (Math 172 at Santa Ana College) that prepares students for calculus. Many students are first-generation, and the problems must be correct, clear and fair.
>
> The attached file has numbered problems. Graphs are attached as images, and each graph's alt text (what a screen-reader student hears) is printed under the problem.
>
> **Solve every problem and every part yourself, carefully.** Show brief work for each. For graph problems, read values from the image *and* check them against the alt text and any table of values. If the image, alt text and table disagree, say so.
>
> While solving, also note:
> 1. **Ambiguity:** any wording a student could reasonably read two ways.
> 2. **Fairness:** anything that needs knowledge beyond a first course in functions, or that a screen-reader student could not do from the alt text and table.
> 3. **Giveaways:** any part whose answer is revealed by another part, by the stem, or by the alt text.
>
> Do not ask for the answer key. I will send it after you have solved everything.

## Step 2 prompt (compare)

> Attached are the answer key (with the hint and common slips shown to students), the course's conventions sheet, and the list of standards. Compare the key with **your own solutions**, problem by problem.
>
> For each problem, report one row:
>
> | # | Verdict | Issue | Suggested fix |
> |---|---|---|---|
>
> Verdicts:
> - ✅ **Correct:** the key matches your solution and the conventions.
> - ⚠️ **Convention or wording:** the math is right, but the answer form, vocabulary or wording breaks the conventions or is unclear.
> - ❌ **Math error:** the key is wrong or incomplete, or the problem has no valid answer.
>
> Rules:
> - If you and the key disagree, **re-solve before deciding who is right**, and show the decisive step.
> - **Hint check:** the hint must be mathematically true for this problem, must not state the answer, and must not name a function or variable that this problem does not use.
> - **Slip check:** each common slip must be an error students really make, be mathematically accurate, and be worded as something to check, not as blame.
> - **Standard check:** say whether the standard code and title fit the skill the problem tests. If not, name the code that fits better.
> - Check every "Spot the slip" problem has **exactly one** error, and the key names it.
> - End with a one-line summary: counts of ✅ / ⚠️ / ❌, and a list of any problems whose standard tag you would change.
"""


def md(s):
    """Pool HTML -> Markdown (tables, lists and the student-work box included)."""
    s = re.sub(r'<div class="table-wrap">(.*?)</div>', r"\1", s, flags=re.S)
    s = re.sub(r"<li[^>]*>", "\n- ", s)
    s = re.sub(r"</?(ul|ol)[^>]*>", "\n", s)
    return to_md(s)


def compact_table(t):
    """A graph's table of values as one line (the full table is on the site, collapsed)."""
    rows = [[to_md(c) for c in r] for r in t["rows"]]
    cap = to_md(t["caption"])
    heads = " , ".join(to_md(h) for h in t["headers"])
    if len(rows) > 14:
        body = "; ".join("(" + ", ".join(r) + ")" for r in rows)
        return f"{cap} [columns: {heads}]: {body}"
    return f"{cap} [columns: {heads}]: " + "; ".join("(" + ", ".join(r) + ")" for r in rows)


def letter(i):
    return "abcdefghijklmnopqrstuvwxyz"[i]


def to_png(src, dst):
    """SVG or PNG -> PNG (ChatGPT does not read SVG files reliably)."""
    if src.lower().endswith(".png"):
        shutil.copyfile(src, dst)
        return
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(device_scale_factor=2).new_page()
        pg.goto("file://" + src)
        pg.locator("svg").first.screenshot(path=dst, omit_background=False)
        b.close()


def pick(items, k):
    n = len(items)
    if n <= k:
        return items
    return [items[(n * (2 * j + 1)) // (2 * k)] for j in range(k)]  # spread through the list, never the first


def write_packet(out_dir, title, selected, families, notes, std_title, conventions, standards_md):
    os.makedirs(os.path.join(out_dir, "figures"), exist_ok=True)
    prob, key = [f"# {title}: problems\n",
                 "Solve everything yourself before asking for the key. Math is written in LaTeX between $ signs.\n"], \
                [f"# {title}: answer key\n",
                 "Compare with **your own solutions**. Each problem shows the hint and the common slips students see.\n"]
    nfig = 0
    for n, it in enumerate(selected, 1):
        fam = families[it["family"]]
        parts = it["parts"]
        p = [f"\n---\n\n## Problem {n}\n"]
        if it.get("stem"):
            p.append(md(it["stem"]) + "\n")
        for f in it.get("figures", []):
            nfig += 1
            name = f"problem-{n:02d}-{it['figures'].index(f) + 1}.png" if len(it["figures"]) > 1 else f"problem-{n:02d}.png"
            to_png(os.path.join(POOL, f["src"]), os.path.join(out_dir, "figures", name))
            label = f" ({to_md(f['label'])})" if f.get("label") else ""
            p.append(f"**Image attached: `{name}`{label}.** Alt text a screen-reader student hears: {to_md(f['alt'])}\n")
            if f.get("table"):
                p.append(f"Table of values students can open under the graph: {compact_table(f['table'])}\n")
        if len(parts) == 1:
            p.append(md(parts[0]["q"]) + "\n")
        else:
            for i, pt in enumerate(parts):
                p.append(f"{letter(i)}) {md(pt['q'])}\n")
        prob.append("\n".join(p))

        k = [f"\n---\n\n## Problem {n}\n",
             f"`{it['id']}` · standard **{it['std']} {std_title[it['std']]}** · {TIER.get(fam['tier'], fam['tier'])}\n"]
        if len(parts) == 1:
            k.append(md(parts[0]["a"]) + "\n")
        else:
            for i, pt in enumerate(parts):
                k.append(f"{letter(i)}) {md(pt['a'])}\n")
        k.append(f"**Hint shown to students:** {to_md(fam.get('hint', ''))}\n")
        if fam.get("slips"):
            k.append("**Common slips shown to students:**\n" + "\n".join(f"- {to_md(s)}" for s in fam["slips"]) + "\n")
        if notes.get(it["id"]):
            k.append(f"**Author note:** {notes[it['id']]}\n")
        key.append("\n".join(k))
    open(os.path.join(out_dir, "problems.md"), "w").write("\n".join(prob) + "\n")
    open(os.path.join(out_dir, "key.md"), "w").write("\n".join(key) + "\n")
    open(os.path.join(out_dir, "standards.md"), "w").write(standards_md)
    if conventions and os.path.exists(conventions):
        shutil.copyfile(conventions, os.path.join(out_dir, "CONVENTIONS.md"))
    return len(selected), nfig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "audit"))
    ap.add_argument("--per-family", type=int, default=2)
    ap.add_argument("--conventions", default=os.path.join(ROOT, "CONVENTIONS.md"))
    a = ap.parse_args()

    idx = json.load(open(os.path.join(POOL, "index.json")))["standards"]
    std_title = {s["code"]: s["title"] for s in idx}
    standards_md = "# The 38 Math 172 standards\n\n| Code | Title | What it covers |\n|---|---|---|\n" + "".join(
        f"| {s['code']} | {s['title']} | {s.get('blurb', '')} |\n" for s in idx)

    notes = {}
    for pth in os.listdir(os.path.join(ROOT, "bank", "fixed")):
        if pth.endswith(".yaml"):
            for raw in yaml.safe_load(open(os.path.join(ROOT, "bank", "fixed", pth)))["items"]:
                if raw.get("note"):
                    notes[raw["id"]] = html.unescape(raw["note"])

    families, items = {}, []
    for s in idx:
        if not s["items"]:
            continue
        d = json.load(open(os.path.join(POOL, f"{s['code']}.json")))
        for fid, fam in d["families"].items():
            families[fid] = fam
        for it in d["items"]:
            it["std"] = s["code"]
            items.append(it)

    pe1 = sorted([i for i in items if i["family"].startswith("PE1")], key=lambda i: i["id"])
    by_fam = {}
    for it in items:
        if not it["family"].startswith("PE1"):
            by_fam.setdefault(it["family"], []).append(it)
    gen = []
    for fid in sorted(by_fam):
        gen += pick(by_fam[fid], a.per_family)

    os.makedirs(a.out, exist_ok=True)
    open(os.path.join(a.out, "AUDIT-PROMPT.md"), "w").write(PROMPT)
    for name, title, sel in (("pe1", "Practice Exam 1 review problems", pe1),
                             ("generated", "Generated practice problems (sample)", gen)):
        d = os.path.join(a.out, name)
        shutil.rmtree(d, ignore_errors=True)
        n, nf = write_packet(d, title, sel, families, notes, std_title, a.conventions, standards_md)
        size = os.path.getsize(os.path.join(d, "problems.md")) + os.path.getsize(os.path.join(d, "key.md"))
        print(f"{name}: {n} problems, {nf} images, {size // 1000} KB of text")


if __name__ == "__main__":
    main()
