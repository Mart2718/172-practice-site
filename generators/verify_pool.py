"""Independent check of the student pool's answers.

    python3 generators/verify_pool.py

The templates assert their own answers when they generate a problem. This script does not use
the templates: it reads site/pool/*.json, rebuilds each problem from its printed text (stem,
question, graph table, mapping alt text), recomputes the answer with sympy or plain logic, and
compares it with the printed answer. Problems it cannot parse are counted as `skipped`, never
as passed.

Coverage today: FN1 (function or not from pairs, tables, mappings, point graphs and equations;
domain and range of a mapping; domains of radical and rational formulas) and FN2 (evaluation of
formulas and piecewise functions, solving f(x) = k, difference quotient, and reading a graph from
its table of values).
"""
import json
import os
import re
import sys
from collections import Counter

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(ROOT, "site", "pool")
x, a, h = sp.symbols("x a h")
TR = standard_transformations + (implicit_multiplication_application,)
ARG = r"((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)"


def tex2sym(s):
    s = s.strip().replace(r"\left", "").replace(r"\right", "").replace(r"\cdot", "*").replace(r"\dfrac", r"\frac")
    s = s.replace(r"\lt", "<").replace(r"\gt", ">")
    for _ in range(8):
        n = s
        s = re.sub(r"\\frac\{" + ARG + r"\}\{" + ARG + r"\}", r"((\1)/(\2))", s)
        s = re.sub(r"\\sqrt\[(\d+)\]\{" + ARG + r"\}", r"real_root(\2,\1)", s)
        s = re.sub(r"\\sqrt\{" + ARG + r"\}", r"sqrt(\1)", s)
        s = re.sub(r"\^\{" + ARG + r"\}", r"**(\1)", s)
        if s == n:
            break
    s = re.sub(r"\^(\d)", r"**\1", s).replace("{", "(").replace("}", ")")
    return parse_expr(s, transformations=TR, local_dict={"x": x, "a": a, "h": h, "real_root": lambda e, n: sp.real_root(e, int(n))})


def maths(s):
    return re.findall(r"\\\((.*?)\\\)", s, flags=re.S)


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s)


def same(u, v):
    try:
        return abs(complex(sp.N(sp.simplify(u - v)))) < 1e-9
    except (TypeError, ValueError):
        return sp.simplify(u - v) == 0


# ------------------------------------------------------------------ model of a function from its stem
def model(stem):
    """Returns (name, f) where f(value) -> sympy value, or raises Undefined, or None if the stem has no formula."""
    m = re.match(r"\s*(?:A student was asked: <em>)?Let \\\((\w)\(x\)\s*=\s*(.*?)\\\)", stem, flags=re.S)
    if not m:
        return None
    name, body = m.group(1), m.group(2)
    body = body.strip()
    if r"\begin{cases}" in body:
        rows = re.search(r"\\begin\{cases\}(.*)\\end\{cases\}", body, flags=re.S).group(1).split(r"\\")
        pieces = []
        for r in rows:
            if not r.strip():
                continue
            e, c = r.split("&")
            pieces.append((tex2sym(e), c.replace(r"\le", "<=").replace(r"\ge", ">=").replace(r"\lt", "<").replace(r"\gt", ">").strip()))

        def f(v):
            for e, c in pieces:
                if eval(c, {"x": sp.Rational(v)}):  # noqa: S307 (our own pool text)
                    return e.subs(x, v)
            raise LookupError("undefined")
        return name, f, pieces
    expr = tex2sym(body)
    return name, (lambda v: expr.subs(x, v)), expr


def num(sv):
    return tex2sym(sv.replace(" ", ""))


def rhs(a_html):
    ms = maths(a_html)
    if not ms:
        raise ValueError("no math in answer")
    return tex2sym(ms[0].split("=")[-1])


def solutions(a_html):
    vals = []
    for mt in maths(a_html):
        for piece in re.findall(r"x\s*=\s*([^,;]+?)(?=$|\s+or\s+|,)", mt):
            vals.append(tex2sym(piece))
    for mt in maths(a_html):
        pass
    return vals


# ------------------------------------------------------------------ interval notation
def parse_intervals(s):
    s = re.sub(r"\\d?frac\{(\d+)\}\{(\d+)\}", r"\1/\2", s)
    s = s.replace(r"\infty", "oo").replace(" ", "")
    out = []
    for lb, lo, hi, rb in re.findall(r"([\[(])(-?[\d./o]+),(-?[\d./o]+)([\])])", s):
        lo = -sp.oo if lo in ("-oo",) else (sp.oo if lo == "oo" else sp.Rational(lo))
        hi = sp.oo if hi == "oo" else (-sp.oo if hi == "-oo" else sp.Rational(hi))
        out.append((lb == "[", lo, hi, rb == "]"))
    return out


def in_intervals(iv, v):
    return any((v > lo or (lc and v == lo)) and (v < hi or (rc and v == hi)) for lc, lo, hi, rc in iv)


# ------------------------------------------------------------------ the checks
class R:
    ok = Counter()
    skipped = Counter()
    bad = []


def fail(item, msg):
    R.bad.append(f"{item['id']}: {msg}")


def check_fn2(item, tables):
    stem = item["stem"]
    mdl = None
    try:
        mdl = model(stem)
    except Exception as e:  # noqa: BLE001
        R.skipped["fn2 model parse"] += 1
        return
    for p in item["parts"]:
        q, ans = p["q"], p["a"]
        try:
            # ---- graph reading
            if item.get("figures") and not mdl:
                t = item["figures"][0]["table"]
                tab = {sp.Rational(re.sub(r"[\\()]", "", r[0])): sp.Rational(re.sub(r"[\\()]", "", r[1])) for r in t["rows"]}
                mq = re.match(r"Find \\\(\w\((-?[\d.]+)\)\\\)", q)
                if mq:
                    v = sp.Rational(mq.group(1))
                    got = rhs(ans)
                    if not same(tab[v], got):
                        fail(item, f"{q} -> table says {tab[v]}, answer says {got}")
                    else:
                        R.ok["fn2 graph value"] += 1
                    continue
                mq = re.search(r"f\(x\) = (-?[\d.]+)|\w\(x\) = (-?[\d.]+)", q)
                if mq and "x" in q:
                    k = sp.Rational(next(g for g in mq.groups() if g))
                    want = sorted(xx for xx, yy in tab.items() if yy == k)
                    got = sorted(sp.Rational(v) for v in re.findall(r"x\s*=\s*(-?[\d.]+)", strip_html(ans)))
                    if want != got:
                        fail(item, f"solve = {k}: table gives {want}, answer gives {got}")
                    else:
                        R.ok["fn2 graph solve"] += 1
                    continue
            if not mdl:
                R.skipped["fn2 unparsed part"] += 1
                continue
            name, f = mdl[0], mdl[1]
            mq = re.match(r"Find \\\(" + name + r"\((-?\d+)\)\\\)", q)
            if mq:
                v = sp.Integer(mq.group(1))
                if "undefined" in ans:
                    try:
                        f(v)
                        fail(item, f"{q}: answer says undefined but the formula is defined")
                    except (LookupError, ZeroDivisionError):
                        R.ok["fn2 undefined"] += 1
                    continue
                got, want = rhs(ans), f(v)
                if same(want, got):
                    R.ok["fn2 value"] += 1
                else:
                    fail(item, f"{q}: formula gives {want}, answer says {got}")
                continue
            mq = re.match(r"Find and simplify \\\(" + name + r"\(a\s*\+\s*(\d+)\)\\\)", q)
            if mq:
                want = sp.expand(f(a + int(mq.group(1))).subs(x, a + int(mq.group(1))) if False else mdl[2].subs(x, a + int(mq.group(1))))
                got = tex2sym(maths(ans)[0].split("=")[-1])
                if sp.simplify(want - got) == 0:
                    R.ok["fn2 f(a+c)"] += 1
                else:
                    fail(item, f"{q}: expected {want}, answer {got}")
                continue
            mq = re.search(name + r"\(x\)\s*=\s*(-?\d+)\\\)", q)
            if mq and ("every input" in q or q.startswith("Solve")):
                k = int(mq.group(1))
                want = sorted(sp.solve(sp.Eq(mdl[2], k), x))
                got = sorted(sp.nsimplify(v) for v in solutions(ans))
                if [sp.nsimplify(w) for w in want] == got:
                    R.ok["fn2 solve"] += 1
                else:
                    fail(item, f"{q}: solutions {want} vs answer {got}")
                continue
            mq = re.match(r"Find and simplify \\\(\\frac\{" + name + r"\((\d+)\+h\) - " + name + r"\(\1\)\}\{h\}\\\)", q)
            if mq:
                c0 = int(mq.group(1))
                want = sp.simplify((mdl[2].subs(x, c0 + h) - mdl[2].subs(x, c0)) / h)
                got = tex2sym(strip_html(ans).replace("\\(", "").replace("\\)", ""))
                if sp.simplify(want - got) == 0:
                    R.ok["fn2 difference quotient"] += 1
                else:
                    fail(item, f"difference quotient {want} vs {got}")
                continue
            R.skipped["fn2 other part"] += 1
        except Exception as e:  # noqa: BLE001
            fail(item, f"could not check '{q[:50]}': {type(e).__name__} {e}")
    # slip item: the corrected answer must satisfy the equation in the stem
    if item["family"] == "FN2-S-01" and mdl:
        mm = re.search(r"\\\(" + mdl[0] + r"\(x\) = (-?\d+)\\\)", stem)
        if mm:
            want = sorted(sp.solve(sp.Eq(mdl[2], int(mm.group(1))), x))
            got = sorted(sp.nsimplify(v) for v in solutions(item["parts"][1]["a"]))
            (R.ok.update(["fn2 slip answer"]) if want == got else fail(item, f"slip answer {got} vs {want}"))


def pairs_in(s):
    return [(int(p), int(q)) for p, q in re.findall(r"\((-?\d+),\s*(?:\\allowbreak\s*)?(-?\d+)\)", re.sub(r"\\allowbreak", "", s))]


def is_function(pairs):
    d = {}
    for p, q in pairs:
        if p in d and d[p] != q:
            return False
        d[p] = q
    return True


def curve_verdict(alt, ans):
    """Re-derive the vertical-line-test verdict from the picture's own description (alt text)."""
    said_fn = "does not" not in ans
    if alt.startswith("A parabola opening"):
        want = not re.search(r"opening to the (left|right)", alt)
        return want == said_fn
    m = re.match(r"A straight line through \((-?\d+), (-?\d+)\) and \((-?\d+), (-?\d+)\)", alt)
    if m:
        return (m.group(1) != m.group(3)) == said_fn
    m = re.match(r"Two pieces, each with closed dots at both ends\. A line segment runs from \((-?\d+), (-?\d+)\) to \((-?\d+), (-?\d+)\)\. "
                 r"A horizontal segment at height (-?\d+) runs from \((-?\d+), (-?\d+)\) to \((-?\d+), (-?\d+)\)", alt)
    if m:
        x1, y1, x2, y2, h, x3, _, x4, _ = [int(v) for v in m.groups()]
        lo, hi = max(min(x1, x2), min(x3, x4)), min(max(x1, x2), max(x3, x4))
        if lo > hi:
            want = True
        elif lo < hi:
            want = False
        else:  # touch at a single x: a function only if both pieces have the same height there
            yseg = y1 + (y2 - y1) * (lo - x1) / (x2 - x1)
            want = abs(yseg - h) < 1e-9
        if not said_fn:
            k = re.search(r"x = (-?\d+)", ans)
            if not k or not (lo <= int(k.group(1)) <= hi):
                return False
        return want == said_fn
    return None


def check_fn1(item):
    fam = item["family"]
    if fam.startswith("FN1-F-01"):
        parts = item["parts"]
        # (a) mapping from alt text
        alt = item["figures"][0]["alt"]
        arrows = re.findall(r"(-?\d+) to (-?\d+)", alt.split("Arrows:")[1])
        want = is_function([(int(u), int(v)) for u, v in arrows])
        said = "defines a function" in parts[0]["a"] and "does not" not in parts[0]["a"]
        (R.ok.update(["fn1 mapping"]) if want == said else fail(item, "mapping verdict"))
        # (b) table
        rows = re.findall(r"<tr><td>\\\((-?\d+)\\\)</td><td>\\\((-?\d+)\\\)</td></tr>", parts[1]["q"])
        want = is_function([(int(u), int(v)) for u, v in rows]) if rows else None
        if want is None:
            R.skipped["fn1 table"] += 1
        else:
            said = "does not" not in parts[1]["a"]
            (R.ok.update(["fn1 table"]) if want == said else fail(item, "table verdict"))
        # (c) ordered pairs
        want = is_function(pairs_in(parts[2]["q"]))
        said = "does not" not in parts[2]["a"]
        (R.ok.update(["fn1 pairs"]) if want == said else fail(item, "pairs verdict"))
    elif fam == "FN1-F-02":
        for p in item["parts"]:
            m = re.search(r"y\^\{(\d+)\}", p["q"])
            if not m:
                R.skipped["fn1 equation form"] += 1
                continue
            ypow = int(m.group(1))
            want = ypow % 2 == 1
            said = "does not" not in p["a"]
            (R.ok.update(["fn1 equation"]) if want == said else fail(item, f"{p['q']} verdict"))
    elif fam in ("FN1-F-03", "FN1-F-04"):
        for f, p in zip(item["figures"], item["parts"]):
            if "plotted points" not in f["table"]["caption"]:
                verdict = curve_verdict(f["alt"], p["a"])
                if verdict is None:
                    R.skipped["fn1 curve graph"] += 1
                else:
                    (R.ok.update(["fn1 curve graph"]) if verdict else fail(item, f"curve graph {f.get('label')} verdict"))
                continue
            pts = [(int(re.sub(r"[\\()]", "", r[0])), int(re.sub(r"[\\()]", "", r[1]))) for r in f["table"]["rows"]]
            said = "does not" not in p["a"]
            (R.ok.update(["fn1 point graph"]) if is_function(pts) == said else fail(item, f"graph {f.get('label')} verdict"))
    elif fam == "FN1-A-01":
        pa = pairs_in(item["parts"][0]["q"])
        pb = pairs_in(item["parts"][1]["q"])
        ok = is_function(pa) and not is_function(pb)
        said = item["parts"][0]["a"].startswith("Yes") and item["parts"][1]["a"].startswith("No")
        (R.ok.update(["fn1 two relations"]) if ok and said else fail(item, "A-01 verdicts"))
        # removing either duplicated-input pair must leave a function
        for pr in re.findall(r"\\\(\((-?\d+), (-?\d+)\)\\\)", item["parts"][2]["a"]):
            rem = [q for q in pb if q != (int(pr[0]), int(pr[1]))]
            (R.ok.update(["fn1 removal"]) if is_function(rem) else fail(item, f"removing {pr} does not fix B"))
    elif fam == "FN1-A-02":
        alt = item["figures"][0]["alt"]
        ins = [int(v) for v in re.search(r"Inputs, top to bottom: ([^.]*)\.", alt).group(1).split(",")]
        outs = [int(v) for v in re.search(r"Target values, top to bottom: ([^.]*)\.", alt).group(1).split(",")]
        arrows = [(int(u), int(v)) for u, v in re.findall(r"(-?\d+) to (-?\d+)", alt.split("Arrows:")[1])]
        dom = sorted(set(ins))
        rng = sorted({v for _, v in arrows})
        gd = sorted(int(v) for v in re.findall(r"-?\d+", maths(item["parts"][1]["a"])[0]))
        gr = sorted(int(v) for v in re.findall(r"-?\d+", maths(item["parts"][2]["a"])[0]))
        ok = dom == gd and rng == gr and is_function(arrows) == item["parts"][0]["a"].startswith("Yes")
        (R.ok.update(["fn1 mapping domain/range"]) if ok else fail(item, f"domain {dom}/{gd} range {rng}/{gr}"))
    elif fam in ("FN1-A-03", "FN1-A-04"):
        check_domain(item)
    elif fam == "FN1-S-01":
        pr = pairs_in(item["stem"])
        (R.ok.update(["fn1 slip"]) if is_function(pr) and item["parts"][1]["a"].startswith("It is a function") else fail(item, "slip verdict"))
    else:
        R.skipped["fn1 other"] += 1


def check_domain(item):
    stem = item["stem"]
    fs = re.findall(r"\\\((\w)\(x\) = (.*?)\\\)", stem)
    qa = item["parts"]
    if item["family"] == "FN1-A-03":
        for (name, body), p in zip(fs, qa[:2]):
            ex = tex2sym(body)
            iv = parse_intervals(maths(p["a"])[0])
            for t in range(-30, 31):
                v = sp.Rational(t, 2)
                real = ex.subs(x, v).is_real
                if bool(real) != in_intervals(iv, v):
                    fail(item, f"{name}: x={v} real={real}, interval says {in_intervals(iv, v)}")
                    return
            R.ok["fn1 domain radical"] += 1
        # part (c): f(1) not real exactly when 1 not in domain
        name, body = fs[0]
        pt = tex2sym(re.match(r"Is \\\(" + name + r"\((.*)\)\\\) a real number", qa[2]["q"]).group(1))
        is_real = tex2sym(body).subs(x, pt).is_real
        said_undefined = qa[2]["a"].startswith("No")
        (R.ok.update(["fn1 domain follow-up"]) if bool(is_real) != said_undefined else fail(item, "A-03 part c"))
    else:
        name, body = fs[0]
        ex = tex2sym(body)
        iv = parse_intervals(maths(qa[2]["a"])[0])
        for t in range(-30, 31):
            v = sp.Rational(t, 2)
            val = ex.subs(x, v)
            real = val.is_real and val.is_finite
            if bool(real) != in_intervals(iv, v):
                fail(item, f"x={v}: defined={real}, interval says {in_intervals(iv, v)}")
                return
        R.ok["fn1 domain radical/rational"] += 1


def main():
    for code in ("FN1", "FN2"):
        d = json.load(open(os.path.join(POOL, f"{code}.json")))
        for item in d["items"]:
            if item["family"].startswith("PE1"):
                R.skipped["hand-written (checked by reading)"] += 1
                continue
            if item["family"].endswith("-B-01") and code == "FN1":
                # circle halves: x^2 + y^2 = r^2 gives y = +-sqrt, domain [-r, r]
                r = int(round(int(re.search(r"= (\d+)\\\)", item["stem"]).group(1)) ** 0.5))
                dom = parse_intervals(maths(item["parts"][2]["a"])[0])
                (R.ok.update(["fn1 circle domain"]) if dom and dom[0][1] == -r and dom[0][2] == r else fail(item, "circle domain"))
                continue
            try:
                (check_fn1(item) if code == "FN1" else check_fn2(item, None))
            except Exception as e:  # noqa: BLE001
                fail(item, f"checker error {type(e).__name__}: {e}")
    print("verified:")
    for k, v in sorted(R.ok.items()):
        print(f"  {k:<32} {v}")
    print("skipped (not checked):")
    for k, v in sorted(R.skipped.items()):
        print(f"  {k:<32} {v}")
    print(f"\n{sum(R.ok.values())} checks passed, {len(R.bad)} failed")
    for b in R.bad[:40]:
        print("  FAIL", b)
    sys.exit(1 if R.bad else 0)


if __name__ == "__main__":
    main()
