"""Checks for PR3-PR9 (polynomial and rational functions): each re-solves the question from its printed text."""
import re

import sympy as sp

from vbase import X as x, check, fail, maths, Skip, strip_text
from verify_pool import parse_intervals, tex2sym
from texeval import split_top
from vc_gen import env_chains

FRAG_X = r"\\\((x = (?:(?!\\\)).)*?)\\\)"           # one \(x = ...\) fragment; group 1 is its inside
ARG = r"((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)"


def stem_function(stem):
    m = re.match(r"\s*(?:Consider|Let) \\\((\w)\(x\) = (.*?)\\\)", stem, flags=re.S)
    if not m:
        raise Skip()
    return m.group(2)


def sym_with_i(tex):
    tex = re.sub(r"i\s*\\sqrt", r"i \\cdot \\sqrt", tex)
    e = tex2sym(tex)
    return e.subs(sp.Symbol("i"), sp.I)


def root_values(tex):
    """A root written as 3 \\pm i\\sqrt{5} becomes two values."""
    if r"\pm" in tex:
        return [sym_with_i(tex.replace(r"\pm", "+")), sym_with_i(tex.replace(r"\pm", "-"))]
    return [sym_with_i(tex)]


def same(u, v):
    return sp.simplify(sp.expand(u - v)) == 0


def x_values(text):
    """Every x = value in the math of `text`."""
    out = []
    for mt in maths(text):
        for part in re.findall(r"(?:^|\s)x = (.+?)(?=$|\s+and\s+|;)", mt):
            out.extend(root_values(part.strip()))
    return out


# ------------------------------------------------------------------ PR3
def end_behavior(deg, lc):
    even, pos = deg % 2 == 0, lc > 0
    return {(True, True): "rises to the left and rises to the right", (True, False): "falls to the left and falls to the right",
            (False, True): "falls to the left and rises to the right", (False, False): "rises to the left and falls to the right"}[(even, pos)]


@check("poly_zeros_multiplicity")
def poly_zeros_multiplicity(item):
    f = tex2sym(stem_function(item["stem"]))
    P = sp.Poly(sp.expand(f), x)
    truth = {k: v for k, v in sp.roots(P).items()}
    q0, q1, q2 = item["parts"]
    got = {}
    for v, mult in re.findall(r"\\\(x = (.*?)\\\) \(multiplicity \\\((\d+)\\\)\)", q0["a"]):
        got[tex2sym(v)] = int(mult)
    if got != truth:
        fail(item, f"zeros {got} vs {truth}")
    pt = re.findall(r"\\\(\(0, (.*?)\)\\\)", q1["a"])
    if not pt or not same(tex2sym(pt[-1]), f.subs(x, 0)):
        fail(item, f"y-intercept {pt} vs {f.subs(x, 0)}")
    if end_behavior(P.degree(), P.LC()) not in q2["a"] or f"degree is \\({P.degree()}\\)" not in q2["a"]:
        fail(item, "end behavior")
    md = re.search(r"degree is \\\((\d+)\\\) \((even|odd)\) and the leading coefficient \\\((-?\d+)\\\) is (positive|negative)", q2["a"])
    if not md or int(md.group(1)) != P.degree() or md.group(2) != ("even" if P.degree() % 2 == 0 else "odd") \
            or int(md.group(3)) != P.LC() or md.group(4) != ("positive" if P.LC() > 0 else "negative"):
        fail(item, f"degree/leading-coefficient sentence {md.groups() if md else None} vs {P.degree(), P.LC()}")


@check("poly_graph_behavior")
def poly_graph_behavior(item):
    f = tex2sym(stem_function(item["stem"]))
    P = sp.Poly(sp.expand(f), x)
    roots = sp.roots(P)
    a0, a1, a2, a3 = [p["a"] for p in item["parts"]]
    m0 = re.search(r"Degree \\\((\d+)\\\); leading coefficient \\\((-?\d+)\\\)", a0)
    if not m0 or (int(m0.group(1)), int(m0.group(2))) != (P.degree(), P.LC()):
        fail(item, f"degree/leading coefficient {m0.groups() if m0 else None} vs {P.degree(), P.LC()}")
    seen = {}
    for v, mult, how in re.findall(r"At \\\(x = (.*?)\\\) \(multiplicity \\\((\d+)\\\)\) the graph (crosses|touches)", a1):
        seen[tex2sym(v)] = (int(mult), how)
    expected = {r: (mu, "crosses" if mu % 2 else "touches") for r, mu in roots.items()}
    if seen != expected:
        fail(item, f"cross/touch {seen} vs {expected}")
    if end_behavior(P.degree(), P.LC()) not in a2:
        fail(item, "end behavior")
    pt = re.findall(r"\\\(\(0, (.*?)\)\\\)", a3)
    if not pt or not same(tex2sym(pt[-1]), f.subs(x, 0)):
        fail(item, "y-intercept")


# ------------------------------------------------------------------ PR4
def split_fraction(tex):
    m = re.search(r"\\dfrac\{" + ARG + r"\}\{" + ARG + r"\}", tex)
    return tex2sym(m.group(1)), tex2sym(m.group(2))


def division_matches(item, N, D, answer):
    q, r = sp.div(sp.Poly(sp.expand(N), x), sp.Poly(sp.expand(D), x))
    mq = re.search(r"q\(x\) = (.*?)\\\)", answer)
    mr = re.search(r"r\(x\) = (.*?)\\\)", answer) or re.search(r"remainder \\\((.*?)\\\)", answer)
    if not mq or not mr:
        fail(item, "quotient/remainder not found")
        return
    if not same(tex2sym(mq.group(1)), q.as_expr()) or not same(tex2sym(mr.group(1)), r.as_expr()):
        fail(item, f"quotient/remainder {mq.group(1)} | {mr.group(1)} vs {q.as_expr()} | {r.as_expr()}")
    m = re.match(r"f\(x\) = (.*)", maths(answer)[-1].strip()) or re.match(r"[fg]\(x\) = (.*)", maths(answer)[-1].strip())
    if m and not same(tex2sym(m.group(1)), sp.expand(N)):
        fail(item, "the rewritten form does not rebuild f")


@check("poly_long_division")
def poly_long_division(item):
    q = item["parts"][0]["q"]
    N, D = split_fraction(maths(q)[0])
    division_matches(item, N, D, item["parts"][0]["a"])


@check("poly_long_division_quadratic")
def poly_long_division_quadratic(item):
    p0, p1 = item["parts"]
    fm = re.search(r"\w\(x\) = (.*?)\\\) by \\\((.*?)\\\)", p0["q"])
    f, D = tex2sym(fm.group(1)), tex2sym(fm.group(2))
    division_matches(item, f, D, p0["a"])
    d2 = tex2sym(re.search(r"divided by \\\((.*?)\\\)", p1["q"]).group(1))
    root = sp.solve(d2, x)[0]
    want = f.subs(x, root)
    mc = re.search(r"The remainder is \\\(\w\((.*?)\)\\\)", p1["a"])
    if mc and not same(tex2sym(mc.group(1)), root):
        fail(item, f"the remainder theorem should evaluate at {root}, not {mc.group(1)}")
    rem = re.findall(r"remainder is \\\((.*?)\\\)", p1["a"])
    if not rem or not same(tex2sym(rem[-1]), want):
        fail(item, f"remainder theorem {rem} vs {want}")


# ------------------------------------------------------------------ PR5
def check_zeros_and_factors(item, f_tex, a_zeros, a_factors):
    f = tex2sym(f_tex)
    P = sp.Poly(sp.expand(f), x)
    truth = list(sp.roots(P).keys())
    printed = x_values(a_zeros)
    for r in printed:
        if not same(f.subs(x, r), 0):
            fail(item, f"printed zero {r} is not a zero")
    for r in truth:
        if not any(same(r, p) for p in printed):
            fail(item, f"zero {r} missing from the answer")
    roots_m = sp.roots(P)
    for v, mult in re.findall(r"\\\(x = (.*?)\\\) \(multiplicity \\\((\d+)\\\)\)", a_zeros):
        rv = root_values(v)
        if not any(same(rv[0], r) and roots_m[r] == int(mult) for r in roots_m):
            fail(item, f"multiplicity {mult} of x = {v} is wrong")
    m = re.search(r"= (.*)\\\)\.?\s*$", a_factors.strip())
    rhs = sym_with_i(m.group(1))
    if not same(sp.expand(rhs), sp.expand(f)):
        fail(item, "the factored form does not multiply back to f")


@check("zeros_complex_factor", "zeros_irrational_factor")
def zeros_factor(item):
    p0, p1 = item["parts"]
    f_tex = re.search(r"\w\(x\) = (.*?)\\\)", p0["q"]).group(1)
    check_zeros_and_factors(item, f_tex, p0["a"], p1["a"])


@check("zeros_from_one_zero")
def zeros_from_one_zero(item):
    p0, p1, p2 = item["parts"]
    fm = re.search(r"\w\(x\) = (.*?)\\\) by \\\((.*?)\\\)", p0["q"])
    division_matches(item, tex2sym(fm.group(1)), tex2sym(fm.group(2)), p0["a"])
    check_zeros_and_factors(item, fm.group(1), p1["a"], p2["a"])
    for mq in re.finditer(r"quadratic formula on \\\((.*?) = 0\\\), \\\(x = (.*?)\\\)", p1["a"]):
        want = set(sp.roots(sp.Poly(tex2sym(mq.group(1)), x)).keys())
        got = set(root_values(mq.group(2)))
        if not (len(want) == len(got) and all(any(same(w, g) for g in got) for w in want)):
            fail(item, f"the quadratic {mq.group(1)} = 0 has roots {want}, not {got}")


# ------------------------------------------------------------------ PR6
def equation_sides(q):
    mt = maths(q)[0]
    parts, ops = split_top(mt)
    if len(parts) != 2:
        raise Skip()
    return tex2sym(parts[0]), tex2sym(parts[1])


def rational_prose(item, p0, g, num, den, cands, good):
    """Statements in the worked answer that name a factor, a denominator, an excluded value or the solution."""
    a = p0["a"]
    env_chains(item, a, [{"x": float(c)} for c in cands if c.is_real])
    for mf in re.finditer(r"Factor the numerator: \\\((.*?)\\\)", a):
        if not same(tex2sym(mf.group(1)), sp.expand(num)):
            fail(item, f"the factored numerator {mf.group(1)} is not {num}")
    mc = re.search(r"common denominator is \\\((.*?)\\\)", a)
    if mc:
        P = sp.Poly(sp.expand(tex2sym(mc.group(1))), x)
        d0 = sp.Poly(sp.fraction(sp.cancel(g))[1], x)
        if sp.div(P, d0)[1] != 0 or sp.div(sp.Poly(den, x), P)[1] != 0:
            fail(item, f"the common denominator {mc.group(1)} is not a common multiple of the denominators")
    for mz in re.finditer(r"numerator is \\\((.*?)\\\) at", a):
        if mz.group(1).strip() != "0":
            fail(item, "'the numerator is ... at' should say 0")
    for mk in re.finditer(r"Check: \\\((.*?)\\\) is not zero", a):          # the denominator named has to be one of the equation's
        E = sp.Poly(sp.expand(tex2sym(mk.group(1))), x)
        if sp.div(sp.Poly(den, x), E)[1] != 0:
            fail(item, f"'{mk.group(1)}' is not a denominator of the equation")
    for mm in re.finditer(r"Multiply both sides by \\\((.*?)\\\)", a):
        E = sp.Poly(sp.expand(tex2sym(mm.group(1))), x)
        if sp.div(sp.Poly(den, x), E)[1] != 0 or sp.div(E, sp.Poly(den, x))[1] != 0 and E.degree() > sp.Poly(den, x).degree():
            fail(item, f"'multiply both sides by {mm.group(1)}' is not the denominator of the equation")
    for sent in re.split(r"(?<=\.)\s+", a):
        if re.search(r"\bsolutions?\b", sent) and re.search(r"\b(?:is|are)\b", sent) and "no solution" not in sent and "extraneous" not in sent:
            vals = x_values(sent)
            if vals and not (len(vals) == len(good) and all(any(same(v, c) for c in good) for v in vals)):
                fail(item, f"the solution sentence says {[str(v) for v in vals]} but the solutions are {good}")
    for mt in re.findall(FRAG_X + r" makes the denominator", a):
        for v in x_values("\\(" + mt + "\\)"):
            if sp.simplify(den.subs(x, v)) != 0:
                fail(item, f"x = {v} is said to make the denominator 0 but it does not")
    for mt in re.finditer(r"But " + FRAG_X + r" makes the denominator", a):
        pass


@check("rational_eq_single", "rational_eq_denominators", "rational_zero_numerator", "rational_no_solution")
def rational_equation(item):
    p0 = item["parts"][0]
    L, R = equation_sides(p0["q"])
    g = sp.together(L - R)
    dens = [sp.fraction(sp.together(t))[1] for t in sp.Add.make_args(L) + sp.Add.make_args(R)]
    den = sp.lcm_list([d for d in dens]) if dens else sp.Integer(1)      # the denominators of the equation as written
    num = sp.expand(sp.cancel((L - R) * den))                            # the equation after multiplying through
    cands = sp.solve(num, x)
    good = [c for c in cands if sp.simplify(den.subs(x, c)) != 0]
    plain = strip_text(p0["a"])
    printed = x_values(p0["a"])
    rational_prose(item, p0, g, num, den, cands, good)
    if not good:
        if "no solution" not in plain:
            fail(item, "expected no solution")
        return
    if "no solution" in plain:
        fail(item, f"says no solution but {good} solves it")
    for c in good:
        if not any(sp.simplify(c - p) == 0 for p in printed):
            fail(item, f"solution {c} is not printed")
    for c in good:                                  # the printed solution really satisfies the original equation
        if sp.simplify((L - R).subs(x, c)) != 0:
            fail(item, f"{c} does not satisfy the equation")


# ------------------------------------------------------------------ PR7
@check("rational_hole_features", "rational_no_hole_features")
def rational_features(item):
    f_tex = stem_function(item["stem"])
    m = re.search(r"\\dfrac\{" + ARG + r"\}\{" + ARG + r"\}$", f_tex.strip())
    N, D = tex2sym(m.group(1)), tex2sym(m.group(2))
    Np, Dp = sp.Poly(sp.expand(N), x), sp.Poly(sp.expand(D), x)
    G = sp.gcd(Np, Dp)
    holes = sorted(sp.roots(G).keys(), key=float) if G.degree() > 0 else []
    red = sp.cancel(Np.as_expr() / Dp.as_expr())
    rn, rd = sp.fraction(red)
    zeros = sorted(sp.roots(sp.Poly(rn, x)).keys(), key=float)
    vas = sorted(sp.roots(sp.Poly(rd, x)).keys(), key=float)
    ha = sp.limit(red, x, sp.oo)
    yint = Np.as_expr().subs(x, 0) / Dp.as_expr().subs(x, 0)
    ans = [p["a"] for p in item["parts"]]
    # holes
    if holes:
        pt = re.findall(r"\\\(\((.*?), (.*?)\)\\\)", ans[0])
        h = holes[0]
        if not pt or not same(tex2sym(pt[-1][0]), h) or not same(tex2sym(pt[-1][1]), red.subs(x, h)):
            fail(item, f"hole {pt} vs {(h, red.subs(x, h))}")
    elif "no holes" not in ans[0]:
        fail(item, "should say there are no holes")
    for v in x_values(ans[0]):
        if not any(same(v, h) for h in holes):
            fail(item, f"the hole answer mentions x = {v}, which is not a hole")
    mo = re.search(r"\(the other numerator zero, \\\((.*?)\\\)", ans[1])
    if mo and not any(same(v, h) for v in x_values("\\(" + mo.group(1) + "\\)") for h in holes):
        fail(item, f"'the other numerator zero {mo.group(1)}' is not a hole")
    # zeros
    zs = x_values(re.split(r"\(the other", ans[1])[0])
    if sorted(zs, key=float) != zeros:
        fail(item, f"zeros {zs} vs {zeros}")
    # vertical asymptotes
    vs = x_values(ans[2])
    if sorted(vs, key=float) != vas:
        fail(item, f"vertical asymptotes {vs} vs {vas}")
    # horizontal asymptote
    hv = re.findall(r"y = (.*?)\\\)", ans[3])
    if not hv or not same(tex2sym(hv[-1]), ha):
        fail(item, f"horizontal asymptote {hv} vs {ha}")
    # y-intercept
    pt = re.findall(r"\\\(\(0, (.*?)\)\\\)", ans[4])
    if not pt or not same(tex2sym(pt[-1]), yint):
        fail(item, f"y-intercept {pt} vs {yint}")


# ------------------------------------------------------------------ PR8 / PR9
REL = [(r"\ge", lambda v: v >= 0), (r"\le", lambda v: v <= 0), (r"\gt", lambda v: v > 0), (r"\lt", lambda v: v < 0), (">", lambda v: v > 0), ("<", lambda v: v < 0)]


def inequality(q):
    mt = maths(q)[0]
    for tok, test in REL:
        if tok in mt:
            L, R = mt.split(tok, 1)
            return tex2sym(L), tex2sym(R), test
    raise Skip()



def same_fn(u, v):
    return sp.simplify(sp.expand(sp.together(u - v))) == 0


def relation_checks(item, q, a, g, num, den, crit, test):
    """Every sentence that restates the inequality, names critical numbers, or explains an endpoint is checked against g."""
    qtok = next(t for t, _ in REL if t in maths(q)[0])
    Lq, Rq = maths(q)[0].split(qtok, 1)
    for ms in re.finditer(r"(Subtract|Add) \\\((-?\d+)\\\) (?:from|to) both sides", a):
        c = int(ms.group(2))
        if ms.group(1) == "Subtract" and sp.simplify(tex2sym(Rq) - c) != 0:
            fail(item, f"'Subtract {c}' but the right-hand side is {Rq}")
        if ms.group(1) == "Add" and sp.simplify(tex2sym(Rq) + c) != 0:
            fail(item, f"'Add {c}' but the right-hand side is {Rq}")
    for mt in maths(a):
        tok = next((t for t, _ in REL if t in mt), None)
        if tok and "Solution" not in a.split(mt)[0][-12:]:
            lhs, rhs = mt.split(tok, 1)
            try:
                if rhs.strip() == "0" and not same_fn(tex2sym(lhs), g) and tok == qtok:
                    fail(item, f"the restated inequality {mt} is not (left side - right side) of the question")
            except Exception:
                pass
    for mm in re.finditer(r"Do not multiply by \\\((.*?)\\\)", a):
        E = sp.Poly(sp.expand(tex2sym(mm.group(1))), x)
        if sp.div(sp.Poly(den, x), E)[1] != 0:
            fail(item, f"'do not multiply by {mm.group(1)}' is not the denominator of the inequality")
    for mm in re.finditer(r"(numerator|denominator) is \\\((.*?)\\\) at", a):
        if mm.group(2).strip() != "0":
            fail(item, f"the {mm.group(1)} is said to be {mm.group(2)} at a critical number")
    m = re.search(r"critical numbers are \\\((.*?)\\\)", a)
    if m:
        printed = sorted(float(sp.nsimplify(tex2sym(t))) for t in m.group(1).split(","))
        if printed != [float(c) for c in crit]:
            fail(item, f"critical numbers printed {printed} vs {[float(c) for c in crit]}")
    for m in re.finditer(r"numerator is \\\(0\\\) at " + FRAG_X + r" and the denominator is \\\(0\\\) at " + FRAG_X, a):
        for v in x_values("\\(" + m.group(1) + "\\)"):
            if sp.simplify(num.subs(x, v)) != 0:
                fail(item, f"the numerator is not 0 at x = {v}")
        for v in x_values("\\(" + m.group(2) + "\\)"):
            if sp.simplify(den.subs(x, v)) != 0:
                fail(item, f"the denominator is not 0 at x = {v}")
    for m in re.finditer(r"((?:" + FRAG_X + r"(?:, and | and |, )?)+)\s*makes? the (numerator|denominator)", a):
        poly = num if m.group(m.lastindex) == "numerator" else den
        for mt in re.findall(FRAG_X, m.group(1)):
            for v in x_values("\\(" + mt + "\\)"):
                if sp.simplify(poly.subs(x, v)) != 0:
                    fail(item, f"x = {v} is said to make the {m.group(m.lastindex)} 0 but does not")
    for m in re.finditer(FRAG_X + r" is (never included|not included|included) because the (expression is undefined there|inequality is strict|inequality is not strict)", a):
        for v in x_values("\\(" + m.group(1) + "\\)"):
            if "undefined" in m.group(3):
                if sp.simplify(den.subs(x, v)) != 0:
                    fail(item, f"x = {v} is called undefined but the denominator is not 0 there")
            elif sp.simplify(g.subs(x, v)) != 0 or sp.simplify(den.subs(x, v)) == 0:
                fail(item, f"x = {v} is called an endpoint where the expression is 0, but it is not")
    for m in re.finditer(FRAG_X + r" is never included\.", a):
        for v in x_values("\\(" + m.group(1) + "\\)"):
            if sp.simplify(den.subs(x, v)) != 0:
                fail(item, f"x = {v} is 'never included' but the denominator is not 0 there")
    strict = qtok in (r"\gt", r"\lt")
    for m in re.finditer(r"because the inequality is (not strict|strict)", a):
        if (m.group(1) == "strict") != strict:
            fail(item, f"the answer says the inequality is {m.group(1)} but the question uses {qtok}")
    mp = re.search(r"so \\\((.*?)\\\) is always positive", a)
    if mp:
        P2 = sp.Poly(sp.expand(g), x)
        if not same_fn(tex2sym(mp.group(1)), g) and not same_fn(tex2sym(mp.group(1)), -g):
            fail(item, f"'{mp.group(1)} is always positive' is not the question's quadratic")
        if "opens upward" in a and P2.LC() <= 0 or "opens downward" in a and P2.LC() >= 0:
            fail(item, "opens upward/downward does not match the leading coefficient")
    mdisc = re.search(r"discriminant is \\\(b\^2 - 4ac = (-?\d+)\\\)", a)
    if mdisc:
        P = sp.Poly(sp.expand(g), x)
        if P.degree() != 2 or P.discriminant() != int(mdisc.group(1)):
            fail(item, f"discriminant printed {mdisc.group(1)} vs {P.discriminant()}")


def check_inequality(item, q, a):
    L, R, test = inequality(q)
    g = sp.together(L - R)
    num, den = sp.fraction(g)
    crit = sorted({c for p in (num, den) for c in sp.roots(sp.Poly(p, x)).keys() if sp.im(c) == 0}, key=float) if (num.has(x) or den.has(x)) else []
    pts = []
    if crit:
        pts += [crit[0] - 5, crit[-1] + 5]
        pts += list(crit)
        pts += [(crit[i] + crit[i + 1]) / 2 for i in range(len(crit) - 1)]
        pts += [c + sp.Rational(1, 1000) for c in crit] + [c - sp.Rational(1, 1000) for c in crit]
    pts += [sp.Integer(k) for k in (-40, -7, 0, 3, 40)]
    relation_checks(item, q, a, g, num, den, crit, test)
    plain = strip_text(a)
    if "no real solution" in plain or "no solution" in plain:
        iv = []
    else:
        frag = re.search(r"Solution: \\\((.*?)\\\)", a) or None
        text = frag.group(1) if frag else maths(a)[-1]
        iv = parse_intervals(text.replace(r"\left", "").replace(r"\right", ""))
    for v in pts:
        try:
            d = sp.simplify(den.subs(x, v))
            truth = d != 0 and bool(test(sp.simplify(g.subs(x, v))))
        except (TypeError, ZeroDivisionError):
            continue
        inside = any((v > lo or (lc and v == lo)) and (v < hi or (rc and v == hi)) for lc, lo, hi, rc in iv)
        if truth != inside:
            fail(item, f"{q[:60]} ... at x = {v}: true is {truth}, printed solution says {inside}")
            return


@check("quad_inequality", "quad_inequality_rearranged", "rational_inequality", "rational_inequality_product")
def inequality_item(item):
    n = 0
    for p in item["parts"]:
        if re.match(r"\s*Solve", p["q"]) and any(t in p["q"] for t in (r"\gt", r"\lt", r"\ge", r"\le")):
            check_inequality(item, p["q"], p["a"])
            n += 1
    if not n:
        raise Skip()
