"""Independent checks for the Chapter 3-5 standards (EL, PF2-3, TE, PR3-9).

The generators check their own answers a second way when they build an item. This script is a separate check that reads only
what the pool prints (stem, question, answer) and re-derives the result without importing a generator. It has two layers:

  G1  every chain of equalities in an answer (a = b = c, a \\approx b) that has no unknown symbol is re-evaluated;
  S*  per-standard checks that parse the question, solve it again, and compare with the printed answer.

Run:  python3 generators/verify_ch35.py [CODE ...]       exit status 1 if anything fails.
"""
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

import yaml

from texeval import DEG, FreeVar, ParseError, evaluate, split_top
import vbase
from vbase import CHECKS, Skip, bad, fail, maths, ok, skipped
import vc_pr  # noqa: F401  (registers the PR checks)
import vc_el  # noqa: F401
import vc_trig  # noqa: F401
import vc_tri  # noqa: F401
import vc_gen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(ROOT, "site", "pool")
CODES = [f"EL{i}" for i in range(1, 8)] + ["PF2", "PF3"] + [f"TE{i}" for i in range(1, 7)] + [f"PR{i}" for i in range(3, 10)]

# ------------------------------------------------------------------ G1: chains of equalities with a value
def tolerance(rhs_tex, rel_op):
    """How far apart two sides of a relation may be. An approximation is allowed half a unit of its last printed digit."""
    if rel_op != "approx":
        return 1e-7, True
    m = re.search(r"(\d+)\.(\d+)\s*(\^\{?\\circ\}?|\\text\{°\}|°)?\s*$", rhs_tex.strip())
    if m:
        d = len(m.group(2))
        t = 0.5 * 10 ** (-d) + 1e-9
        return (t * DEG if m.group(3) else t), False
    m = re.search(r"(\d+)\s*(\^\{?\\circ\}?|\\text\{°\}|°)?\s*$", rhs_tex.strip())
    if m:
        t = 0.5 + 1e-9
        return (t * DEG if m.group(2) else t), False
    return 1e-7, True


def g1(item, text):
    for mt in maths(text):
        parts, ops = split_top(mt)
        if len(parts) < 2:
            continue
        vals = []
        for p in parts:
            try:
                vals.append(evaluate(p))
            except ZeroDivisionError:
                fail(item, f"a printed expression divides by zero: {p.strip()}")
                return
            except (FreeVar, ParseError, ValueError, OverflowError, IndexError):
                vals.append(None)
        prev = None                     # (value, index)
        for i, v in enumerate(vals):
            if v is None:
                continue
            if prev is not None:
                pv, pi = prev
                rel = "approx" if "approx" in ops[pi:i] else "eq"
                tol, relative = tolerance(parts[i], rel) if rel == "approx" else (1e-7, True)
                if rel == "approx" and ops[i - 1] != "approx":
                    tol, relative = 1e-7, True
                err = abs(pv - v)
                if err > tol * (max(1.0, abs(v)) if relative else 1):
                    fail(item, f"chain claim is wrong: {parts[pi].strip()} vs {parts[i].strip()} ({pv:.6g} vs {v:.6g})")
                    return
                ok["g1 chain"] += 1
            prev = (v, i)


# ------------------------------------------------------------------ the families and their templates
def family_templates():
    out = {}
    for code in CODES:
        for sub in os.listdir(os.path.join(ROOT, "bank")):
            path = os.path.join(ROOT, "bank", sub, f"{code}.yaml")
            if os.path.exists(path):
                for p in yaml.safe_load(open(path))["problems"]:
                    out[p["id"]] = p["template"]
    return out


def norm_math(t):
    return re.sub(r"\s+", "", t).replace("\\dfrac", "\\frac").replace("\\left", "").replace("\\right", "")


def family_text(code):
    """Hints and slips live on the family, so check them against the items of that family."""
    d = json.load(open(os.path.join(POOL, f"{code}.json")))
    for fid, fam in d["families"].items():
        items = [it for it in d["items"] if it["family"] == fid]
        used = set()
        for it in items:
            for part in it["parts"]:
                used |= set(re.findall(r"\\(arcsin|arccos|arctan)", part["q"] + part["a"]))
        said = fam.get("hint", "") + " ".join(fam.get("slips", []))
        hint_named = set(re.findall(r"\\(arcsin|arccos|arctan)", fam.get("hint", "")))
        for fn in sorted(used):
            if hint_named and fn not in hint_named:       # a hint that names some inverse functions must name all that the family uses
                fail(items[0], f"the hint names {sorted(hint_named)} but items in this family also use \\{fn}")
            interval = {"arcsin": r"\left[-\dfrac{\pi}{2}, \dfrac{\pi}{2}\right]", "arccos": r"[0, \pi]"}.get(fn)
            asks_range = any("State the range" in part["q"] for it in items for part in it["parts"])   # there the interval is the answer, so the hint must not give it
            if fn != "arctan" and not asks_range and "\\" + fn in said and interval and interval not in said:
                fail(items[0], f"the hint and slips name \\{fn} but never give its interval")
        # a hint must not state the answer: no math fragment of the hint may be the last math fragment of an answer in its family
        hint_math = {norm_math(t) for t in re.findall(r"\\\((.*?)\\\)", fam.get("hint", "")) if len(norm_math(t)) >= 2}
        for it in items:
            for part in it["parts"]:
                tail = maths(part["a"])
                if tail and norm_math(tail[-1]) in hint_math:
                    fail(it, f"the hint states an answer: \\({tail[-1].strip()}\\)")
        asks_dr = any(re.search(r"\b(range|domain)\b", part["q"]) for it in items for part in it["parts"])
        if asks_dr and "all real numbers" in fam.get("hint", ""):
            fail(items[0], "the hint says 'all real numbers' but the family asks for a domain or range, so it gives the answer")
        ok["family hint covers every inverse function used"] += 1


def main():
    wanted = [a for a in sys.argv[1:] if a in CODES] or CODES
    tmpl = family_templates()
    for code in wanted:
        d = json.load(open(os.path.join(POOL, f"{code}.json")))
        family_text(code)
        for item in d["items"]:
            for part in item["parts"]:
                g1(item, part["a"])
            vc_gen.generic(item, tmpl.get(item["family"]))
            fn = CHECKS.get(tmpl.get(item["family"]))
            if fn:
                try:
                    fn(item)
                    ok[f"s {tmpl[item['family']]}"] += 1
                except Skip:
                    skipped[tmpl[item["family"]]] += 1
            else:
                skipped["(no specific check) " + tmpl.get(item["family"], "?")] += 1
    print("passed:")
    for k, v in sorted(ok.items()):
        print(f"  {v:5d}  {k}")
    if skipped:
        print("no specific check yet:")
        for k, v in sorted(skipped.items()):
            print(f"  {v:5d}  {k}")
    print(f"\n{sum(ok.values())} passed, {len(bad)} failed")
    for b in bad[:60]:
        print("  FAIL", b)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
