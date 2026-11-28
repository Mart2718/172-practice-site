"""Checks for EL1-EL7 (exponential and logarithmic functions): each re-solves the question from its printed text."""
import math
import random
import re

from texeval import FreeVar, ParseError, compile_tex, evaluate, split_top
from vbase import Skip, check, fail, maths, last_value, close, strip_text
from verify_pool import parse_intervals
from vc_gen import env_chains


def formula(stem, q=""):
    for text in (stem, q):
        m = re.search(r"\\\((\w)\(([xt])\) = (.*?)\\\)", text, flags=re.S)
        if m:
            return m.group(1), m.group(2), m.group(3).strip()
    raise Skip()


def rounding_tol(rhs_tex):
    m = re.search(r"(\d+)\.(\d+)\s*$", rhs_tex.strip())
    if m:
        return 0.5 * 10 ** (-len(m.group(2))) + 1e-9
    return 1e-6


def first_chain_value(a, before_approx=True):
    """Value of the first evaluable side of the first math fragment whose right-hand side can be evaluated."""
    for mt in maths(a):
        parts, ops = split_top(mt)
        for p in parts[1:] if len(parts) > 1 else []:
            try:
                return evaluate(p), parts
            except (FreeVar, ParseError, ZeroDivisionError, ValueError):
                continue
    raise Skip()


def printed_interval(text):
    return parse_intervals(text.replace(r"\left", "").replace(r"\right", ""))


# ------------------------------------------------------------------ EL1
def table_cells(stem):
    out = {}
    for cap, body in re.findall(r"<caption>(.*?)</caption>.*?<tbody>(.*?)</tbody>", stem, flags=re.S):
        rows = re.findall(r"<td>\\\((.*?)\\\)</td><td>\\\((.*?)\\\)</td>", body)
        out[cap.strip()] = [(evaluate(a), evaluate(b)) for a, b in rows]
    return out


def classify(rows):
    ys = [y for _, y in rows]
    ratios = [ys[i + 1] / ys[i] for i in range(len(ys) - 1)]
    diffs = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
    if all(close(r, ratios[0]) for r in ratios) and not all(close(d, diffs[0]) for d in diffs):
        return "exponential", ratios[0]
    if all(close(d, diffs[0]) for d in diffs):
        return "linear", diffs[0]
    return "neither", None


def el1_part(item, p):
    q, a = p["q"], p["a"]
    if "Which of the tables" in q:
        kinds = {cap: classify(rows) for cap, rows in table_cells(item["stem"]).items()}
        exps = [c for c, (k, _) in kinds.items() if k == "exponential"]
        if len(exps) != 1:
            fail(item, f"expected one exponential table, found {kinds}")
            return
        name = exps[0]
        if f"{name} is exponential" not in a:
            fail(item, f"printed answer does not name {name}")
        mr = re.search(r"Each output is \\\((.*?)\\\) times", a)
        if not mr or not close(evaluate(mr.group(1)), kinds[name][1]):
            fail(item, "common ratio")
        lin = [c for c, (k, _) in kinds.items() if k == "linear"]
        if lin:
            md = re.search(r"adds \\\((.*?)\\\)", a)
            if not md or not close(evaluate(md.group(1)), kinds[lin[0]][1]):
                fail(item, "common difference")
    elif "passes through" in q:
        pts = re.findall(r"\\\(\((.*?), (.*?)\)\\\)", q)
        if len(pts) != 2:
            raise Skip()
        pts = [(evaluate(a_), evaluate(b_)) for a_, b_ in pts]
        body = re.match(r"\w\(x\) = (.*)", maths(a)[-1].strip())
        if not body:
            fail(item, "no final function printed")
            return
        f = compile_tex(body.group(1))
        for xv, yv in pts:
            if not close(f({"x": xv}), yv, 1e-9):
                fail(item, f"function {body.group(1)} misses the point ({xv}, {yv})")
        (x1, y1), (x2, y2) = pts
        if x1 != x2 and y1 > 0 and y2 > 0:
            b_ = (y2 / y1) ** (1 / (x2 - x1))
            env_chains(item, a, [{"a": y1 / b_ ** x1, "b": b_}])
    elif "Evaluate" in q:
        name, var, body = formula(item["stem"], q)
        arg = re.search(r"Evaluate \\\(\w\((.*?)\)\\\)", q)
        want = evaluate(body, {"x": evaluate(arg.group(1))})
        if not close(last_value(a), want, 1e-9):
            fail(item, f"evaluation {last_value(a)} vs {want}")
    else:
        raise Skip()


@check("exp_table_identify", "exp_evaluate", "exp_two_points", "exp_two_points_general", "exp_three_part")
def el1(item):
    for p in item["parts"]:
        el1_part(item, p)


# ------------------------------------------------------------------ EL2 / EL4 (graph features)
def scan_defined(F, lo=-60.0, hi=60.0, step=0.05):
    xs, mask = [], []
    v = lo
    while v <= hi + 1e-9:
        try:
            F({"x": v})
            mask.append(True)
        except (ValueError, ZeroDivisionError, OverflowError):
            mask.append(False)
        xs.append(v)
        v += step
    return xs, mask


def domain_edge(F):
    xs, mask = scan_defined(F)
    edges = [i for i in range(len(mask) - 1) if mask[i] != mask[i + 1]]
    if len(edges) != 1:
        raise Skip()
    i = edges[0]
    a, b = xs[i], xs[i + 1]
    for _ in range(60):
        mid = (a + b) / 2
        try:
            F({"x": mid})
            ok_ = True
        except (ValueError, ZeroDivisionError, OverflowError):
            ok_ = False
        if ok_ == mask[i]:
            a = mid
        else:
            b = mid
    return (a + b) / 2, mask[i + 1]       # boundary; True if the domain lies to the right


def exp_asymptote(F):
    left, right = F({"x": -80.0}), F({"x": 80.0})
    left2, right2 = F({"x": -90.0}), F({"x": 90.0})
    if abs(left - left2) < 1e-9 and abs(left) < 1e12:
        return left
    if abs(right - right2) < 1e-9 and abs(right) < 1e12:
        return right
    raise Skip()


def interval_endpoints(iv):
    return [(lc, lo, hi, rc) for lc, lo, hi, rc in iv]


def y_intercept_ok(item, F, a, name):
    pt = re.findall(r"\\\(\((.*?), (.*?)\)\\\)", a)
    if not pt or not close(evaluate(pt[-1][1]), F({"x": 0.0}), 1e-9) or evaluate(pt[-1][0]) != 0:
        fail(item, f"y-intercept {pt[-1:] } vs {F({'x': 0.0})}")


def exp_part(item, p, F):
    q, a = p["q"], p["a"]
    k = exp_asymptote(F)
    above = F({"x": 0.3}) > k
    iv_range = [(False, k, math.inf, False)] if above else [(False, -math.inf, k, False)]

    def same_interval(text):
        iv = printed_interval(text)
        if len(iv) != 1:
            return False
        lc, lo, hi, rc = iv[0]
        want = iv_range[0]
        return (float(lo) if lo != -math.inf and str(lo) != "-oo" else -math.inf) == want[1] or close(float(lo), want[1]) if str(lo) not in ("-oo",) else want[1] == -math.inf

    for mb in re.finditer(r"stays (?:above|below) \\\(y = (-?\d+)\\\)\. Shifting (up|down) \\\((\d+)\\\) units? moves that boundary to \\\(y = (-?\d+)\\\)", a):
        old, upd, shift, new = int(mb.group(1)), mb.group(2), int(mb.group(3)), int(mb.group(4))
        if new != old + (shift if upd == "up" else -shift) or new != round(k):
            fail(item, f"the boundary after shifting {upd} {shift} should be {round(k)}, not {new}")
    if "domain, range" in q:
        m = re.search(r"Domain \\\((.*?)\\\); range \\\((.*?)\\\); horizontal asymptote \\\(y = (.*?)\\\)", a)
        if not m:
            fail(item, "combined answer not found")
            return
        rng_iv = printed_interval(m.group(2))
        check_range(item, rng_iv, k, above)
        if not close(evaluate(m.group(3)), k, 1e-6):
            fail(item, f"horizontal asymptote {m.group(3)} vs {k}")
        if "(-\\infty, \\infty)" not in m.group(1):
            fail(item, "domain")
    elif "State the domain" in q:
        if r"(-\infty, \infty)" not in a:
            fail(item, "exponential domain")
    elif "State the range" in q:
        iv = printed_interval(re.match(r"\\\((.*?)\\\)", a).group(1))
        check_range(item, iv, k, above)
    elif "horizontal asymptote" in q:
        m = re.match(r"\\\(y = (.*?)\\\)", a)
        if not m or not close(evaluate(m.group(1)), k, 1e-6):
            fail(item, f"horizontal asymptote {a[:40]} vs {k}")
    elif re.search(r"y\\\)-intercept|y-intercept", q):
        y_intercept_ok(item, F, a, "f")
    elif "obtained from the graph" in q:
        check_steps(item, F, q, a)


def check_range(item, iv, k, above):
    if len(iv) != 1:
        fail(item, "range not one interval")
        return
    lc, lo, hi, rc = iv[0]
    if above:
        ok_ = (not lc) and close(float(lo), k, 1e-6) and str(hi) == "oo"
    else:
        ok_ = (not rc) and close(float(hi), k, 1e-6) and str(lo) == "-oo"
    if not ok_:
        fail(item, f"range {iv} vs asymptote {k} ({'above' if above else 'below'})")


def check_steps(item, F, q, a):
    """Rebuild the function from the printed steps and compare with the stem."""
    base = re.search(r"graph of \\\(y = (.*?)\\\)\.", q).group(1)
    B = compile_tex(base)
    ms = re.search(r"Starting from \\\(y = (.*?)\\\)", a)
    if ms:
        B2 = compile_tex(ms.group(1))
        if any(abs(B2({"x": xv}) - B({"x": xv})) > 1e-9 for xv in (-1.5, 0.3, 1.7)):
            fail(item, f"the starting function {ms.group(1)} is not the one in the question")
    steps = re.findall(r"shift (left|right) (\d+) units?|reflect over the \\\(x\\\)-axis|shift (up|down) (\d+) units?", a.split(":", 1)[1])
    seq = []
    for m in re.finditer(r"shift (left|right) (\d+) units?|(reflect over the \\\(x\\\)-axis)|shift (up|down) (\d+) units?", a.split(":", 1)[1]):
        if m.group(1):
            seq.append(("h", -int(m.group(2)) if m.group(1) == "left" else int(m.group(2))))
        elif m.group(3):
            seq.append(("r", 0))
        else:
            seq.append(("v", int(m.group(5)) if m.group(4) == "up" else -int(m.group(5))))
    for xv in (-2.5, -0.7, 0.0, 1.3, 3.1):
        vals = None
        # apply horizontal shift to the input and the vertical steps to the output, in the printed order
        shift_in = sum(s for kind, s in seq if kind == "h")
        y = B({"x": xv - shift_in})
        for kind, s in seq:
            if kind == "r":
                y = -y
            elif kind == "v":
                y = y + s
        if not close(y, F({"x": xv}), 1e-9):
            fail(item, f"printed steps do not rebuild f at x = {xv}")
            return


@check("exp_graph_features", "exp_graph_transform")
def el2(item):
    name, var, body = formula(item["stem"])
    F = compile_tex(body)
    for p in item["parts"]:
        exp_part(item, p, F)


def log_argument(text):
    """What is inside the first logarithm of the text, with \\left( \\right) pairs balanced."""
    mt = re.search(r"(?:\\log_\{[^}]*\}|\\ln)\s*(?:\\left)?\(", text)
    if not mt:
        return None
    depth, i = 1, mt.end()
    while i < len(text):
        if text.startswith("\\left(", i):
            depth += 1
            i += 6
        elif text.startswith("\\right)", i):
            depth -= 1
            if depth == 0:
                return text[mt.end():i]
            i += 7
        elif text[i] == "(":
            depth += 1
            i += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[mt.end():i]
            i += 1
        else:
            i += 1
    return None


def log_part(item, p, F):
    q, a = p["q"], p["a"]
    edge, right = domain_edge(F)
    if "domain" in q and "range" not in q:
        iv = printed_interval(re.search(r"Domain \\\((.*?)\\\)|domain is \\\((.*?)\\\)", a).group(1) or re.search(r"domain is \\\((.*?)\\\)", a).group(1))
        lc, lo, hi, rc = iv[0]
        ok_ = (close(float(lo), edge, 1e-6) and str(hi) == "oo") if right else (str(lo) == "-oo" and close(float(hi), edge, 1e-6))
        if not ok_ or lc or rc:
            fail(item, f"domain {iv} vs edge {edge} ({'right' if right else 'left'})")
    if "vertical asymptote" in q:
        m = re.search(r"vertical asymptote \\\(x = (.*?)\\\)|\\\(x = (.*?)\\\), the boundary", a)
        v = m.group(1) or m.group(2)
        if not close(evaluate(v), edge, 1e-6):
            fail(item, f"vertical asymptote {v} vs {edge}")
    for ms_ in re.finditer(r"Shifting (up|down) \\\((\d+)\\\) units? moves that boundary to \\\(y = (-?\d+)\\\)", a):
        pass
    for mi in re.finditer(r"\\\(x ([+-]) (\d+) \\gt\s+0\\\), so \\\(x \\gt\s+(-?\d+)\\\)", a):
        want = -int(mi.group(2)) if mi.group(1) == "+" else int(mi.group(2))
        if int(mi.group(3)) != want:
            fail(item, f"x {mi.group(1)} {mi.group(2)} > 0 gives x > {want}, not {mi.group(3)}")
    mg = re.search(r"argument must be positive(?:, so|:) \\\(((?:(?!\\\)).)*?) \\gt\s+0\\\)", a)
    if mg and F is not None:
        arg_ = compile_tex(mg.group(1))
        stem_arg = log_argument(item["stem"])
        if stem_arg is None:
            fail(item, "could not find the logarithm's argument in the stem")
        elif any(abs(arg_({"x": xv}) - compile_tex(stem_arg)({"x": xv})) > 1e-9 for xv in (-1.3, 0.4, 2.9)):
            fail(item, f"the argument {mg.group(1)} is not the argument of the logarithm in the stem")
    for mset in re.finditer(r"Set \\\(\w\(x\) = (.*?)\\\)", a):
        if mset.group(1).strip() != "0":
            fail(item, "'Set g(x) = ...' should be set equal to 0")
    if "State the range" in q and r"(-\infty, \infty)" not in a:
        fail(item, "logarithm range")
    if re.search(r"\\\(x\\\)-intercept|x-intercept", q):
        m = re.findall(r"x = (.*?)\\\)", a)
        v = evaluate(m[-1])
        if abs(F({"x": v})) > 1e-9:
            fail(item, f"x-intercept {v} gives f = {F({'x': v})}")
        else:
            env_chains(item, a, [{"x": v}], strict_domain=True)
    if re.search(r"Find \\\(\w\((.*?)\)\\\)", q):
        arg = evaluate(re.search(r"Find \\\(\w\((.*?)\)\\\)", q).group(1))
        if not close(last_value(a), F({"x": arg}), 1e-9):
            fail(item, f"value {last_value(a)} vs {F({'x': arg})}")
    if "obtained" in q:
        pass


@check("log_graph_features", "log_graph_transform")
def el4(item):
    name, var, body = formula(item["stem"])
    F = compile_tex(body)
    for p in item["parts"]:
        log_part(item, p, F)


# ------------------------------------------------------------------ EL3
def numbers_in(tex):
    return sorted(float(n) for n in re.findall(r"\d+\.?\d*", tex))


@check("log_convert")
def log_convert(item):
    for p in item["parts"]:
        qf, af = maths(p["q"])[0], maths(p["a"])[0]
        for tex in (qf, af):
            parts, ops = split_top(tex)
            if len(parts) != 2:
                raise Skip()
            if not close(evaluate(parts[0]), evaluate(parts[1]), 1e-9):
                fail(item, f"false equation {tex}")
        if numbers_in(qf) != numbers_in(af):
            fail(item, f"converted form uses different numbers: {qf} -> {af}")
        if (r"\log" in qf) == (r"\log" in af):
            fail(item, "did not change form")


@check("log_evaluate", "log_special_values", "log_combine_evaluate")
def log_evaluate(item):
    value_sentence(item)
    n = 0
    for p in item["parts"]:
        if not p["q"].lstrip().startswith("Evaluate"):
            continue
        vals = []
        for tex in maths(p["q"]):
            if r"\log" not in tex and r"\ln" not in tex:
                continue                       # a base such as 10 or e is not a value to evaluate
            try:
                vals.append(evaluate(tex))
            except (FreeVar, ParseError):
                pass
        if not vals:
            continue
        printed = []
        for mt in maths(p["a"]):
            for part in split_top(mt)[0]:
                try:
                    printed.append(evaluate(part))
                except (FreeVar, ParseError, ZeroDivisionError, ValueError):
                    pass
        for v in vals:
            if not any(close(v, w, 1e-9) for w in printed):
                fail(item, f"value {v} of {maths(p['q'])} is not printed")
        for mk in re.finditer(r"Ask: \\\((.*?)\\\) to what power is \\\((.*?)\\\)", p["a"]):
            b1, a1 = evaluate(mk.group(1)), evaluate(mk.group(2))
            if not any(close(b1 ** v, a1, 1e-9) for v in vals):
                fail(item, f"'{b1:g} to what power is {a1:g}' does not match the logarithm in the question")
        n += 1
    if not n:
        raise Skip()


# ------------------------------------------------------------------ EL5
RAND = random.Random(5)


def random_env(names, lo=0.6, hi=4.0):
    return {n: RAND.uniform(lo, hi) for n in names}


def value_sentence(item):
    for p in item["parts"]:
        for m in re.finditer(r"\\\((\d+)\^\{(-?\d+)\} = (\d+)\\\), so the value is \\\((-?\d+)\\\)", p["a"]):
            if int(m.group(2)) != int(m.group(4)):
                fail(item, f"{m.group(1)}^{m.group(2)} = {m.group(3)}, so the value is {m.group(2)}, not {m.group(4)}")


@check("log_expand", "log_condense")
def log_rewrite(item):
    p = item["parts"][0]
    if "positive" not in p["q"]:
        fail(item, "expanding or condensing logarithms needs the statement that all variables are positive")
    fq = compile_tex(maths(p["q"])[0])
    frags = [compile_tex(t) for t in maths(p["a"])]
    names = "abcdfghjklmnoprstuvwxyz"
    for _ in range(4):
        env = random_env(names)
        want = fq(env)
        for fr, tex in zip(frags, maths(p["a"])):
            if not close(fr(env), want, 1e-9):
                fail(item, f"{tex} is not equal to the original at {env}")
                return


@check("log_properties_given")
def log_properties(item):
    givens = re.findall(r"\\log_b\((\d+)\) = (\w)", item["stem"])
    if len(givens) != 2:
        raise Skip()
    for p in item["parts"]:
        fq = compile_tex(maths(p["q"])[0])
        final = compile_tex(maths(p["a"])[-1])
        for base in (2.5, 3.7, 10.0):
            env = {"b": base}
            for num, name in givens:
                env[name] = math.log(int(num), base)
            if not close(fq(env), final(env), 1e-9):
                fail(item, f"{maths(p['q'])[0]} is not {maths(p['a'])[-1]}")
                return


# ------------------------------------------------------------------ EL6
def scan_points():
    fine = [-30 + 0.02 * i for i in range(3001)]
    coarse = [v * 0.25 for v in range(-1600, 1601) if abs(v * 0.25) > 30]
    return sorted(fine + coarse)


POINTS = scan_points()


def real_roots(H, lo=-30.0, hi=30.0, step=0.02):
    roots, prev = [], None
    for v in POINTS:
        try:
            cur = H({"x": v})
        except (ValueError, ZeroDivisionError, OverflowError):
            cur = None
        if cur is not None and prev is not None and prev[1] * cur <= 0 and abs(cur) < 1e15 and abs(prev[1]) < 1e15:
            a, b, fa = prev[0], v, prev[1]
            for _ in range(80):
                mid = (a + b) / 2
                try:
                    fm = H({"x": mid})
                except (ValueError, ZeroDivisionError, OverflowError):
                    break
                if fa * fm <= 0:
                    b = mid
                else:
                    a, fa = mid, fm
            r = (a + b) / 2
            try:
                if abs(H({"x": r})) < 1e-6 and not any(abs(r - s) < 1e-6 for s in roots):
                    roots.append(r)
            except (ValueError, ZeroDivisionError, OverflowError):
                pass
        prev = (v, cur) if cur is not None else None
    return roots


def printed_x(a):
    out = []
    for mt in maths(a):
        parts, ops = split_top(mt)
        if parts and parts[0].strip() == "x":
            for rhs in parts[1:]:
                try:
                    out.append(evaluate(rhs))
                except (FreeVar, ParseError, ZeroDivisionError, ValueError):
                    pass
    return out


def step_checks(item, p, L, R):
    """'Divide by c: E', 'Subtract c: E', 'the left side is E', 'Combine with the product rule: E' restate the question's equation."""
    a = p["a"]
    pts = [0.7, 1.3, 2.6, 4.1, 6.2, 9.4, 14.5]

    def eq_of(tex):
        parts, ops = split_top(tex)
        return (compile_tex(parts[0]), compile_tex(parts[1])) if len(parts) == 2 else None

    def val(f, xv):
        try:
            return f({"x": xv})
        except (ValueError, ZeroDivisionError, OverflowError):
            return None

    def compare(pairs, message):
        used = 0
        for u, v in pairs:
            if u is None or v is None:
                continue
            used += 1
            if abs(u - v) > 1e-8 * max(1, abs(v)):
                fail(item, message)
                return
        return used

    for m in re.finditer(r"(Divide by|Subtract|Add) \\\((-?[\d.]+)\\\): \\\((.*?)\\\)", a):
        e2 = eq_of(m.group(3))
        if not e2:
            continue
        c = float(m.group(2))
        pairs = []
        for xv in pts:
            lv, rv, a1, a2 = val(L, xv), val(R, xv), val(e2[0], xv), val(e2[1], xv)
            if None in (lv, rv, a1, a2):
                continue
            if m.group(1) == "Divide by":
                pairs += [(a1, lv / c), (a2, rv / c)]
            else:
                sgn = -1 if m.group(1) == "Subtract" else 1
                pairs += [(a1, lv + sgn * c), (a2, rv + sgn * c)]
        compare(pairs, f"'{m.group(1)} {m.group(2)}' does not give {m.group(3)} from the question's equation")
    for m in re.finditer(r"the left side is \\\((.*?)\\\)", a):
        F2 = compile_tex(m.group(1))
        compare([(val(F2, xv), val(L, xv)) for xv in pts], f"'the left side is {m.group(1)}' is not the question's left side")
    for m in re.finditer(r"product rule: \\\((.*?)\\\)", a):
        e2 = eq_of(m.group(1))
        if e2:
            compare([(val(e2[0], xv), val(L, xv)) for xv in pts], f"the combined left side {m.group(1)} is not the question's left side")
            compare([(val(e2[1], xv), val(R, xv)) for xv in pts], "the combined right side is not the question's right side")


@check("exp_eq_basic", "log_eq_basic", "exp_log_eq_advanced")
def equations(item):
    for p in item["parts"]:
        mt = maths(p["q"])[0]
        parts, ops = split_top(mt)
        if len(parts) != 2:
            raise Skip()
        L, R = compile_tex(parts[0]), compile_tex(parts[1])
        H = lambda env: L(env) - R(env)
        roots = real_roots(H)
        xs = printed_x(p["a"])
        if not roots:
            fail(item, f"no real solution found for {mt}")
            continue
        env_chains(item, p["a"], [{"x": r} for r in roots], strict_domain=True)
        step_checks(item, p, L, R)
        for r in roots:
            if not any(abs(r - v) < 1e-6 * max(1, abs(r)) for v in xs):
                fail(item, f"solution {r:.6g} of {mt} is not printed ({xs})")
        if xs and not any(abs(xs[-1] - r) < max(1e-6 * max(1, abs(r)), 0.0051) for r in roots):
            fail(item, f"the last x printed ({xs[-1]:.6g}) is not a solution of {mt} (roots {roots})")


# ------------------------------------------------------------------ EL7
def to_number(s):
    return float(s.replace(",", ""))


def bisect(F, target, lo=0.0, hi=400.0):
    flo = F({"t": lo}) - target
    for _ in range(200):
        mid = (lo + hi) / 2
        try:
            fm = F({"t": mid}) - target
        except OverflowError:
            hi = mid                        # far too large an exponent: the solution is to the left
            continue
        if flo * fm <= 0:
            hi = mid
        else:
            lo, flo = mid, fm
    return (lo + hi) / 2


@check("growth_compound", "growth_doubling", "decay_half_life", "growth_continuous")
def applications(item):
    name, var, body = formula(item["stem"])
    F = compile_tex(body)
    for p in item["parts"]:
        q, a = p["q"], p["a"]
        if re.search(r"how many|When will|When does", q):
            plain = strip_text(q)
            nums = re.findall(r"\$?(\d[\d,]*\.?\d*)", plain)
            if not nums:
                raise Skip()
            target = to_number(nums[-1].rstrip(","))
            tstar = bisect(F, target)
            env_chains(item, a, [{"t": tstar}])
            for md in re.finditer(r"divide by \\\((.*?)\\\) to get", a):
                if abs(evaluate(md.group(1)) - F({"t": 0.0})) > 1e-9:
                    fail(item, f"'divide by {md.group(1)}' but the starting amount is {F({'t': 0.0}):g}")
            mfin = re.search(r"during year \\\((\d+)\\\): \\\((\d+)\\\) years", a)
            if mfin and (mfin.group(1) != mfin.group(2) or int(mfin.group(1)) != math.ceil(tstar - 1e-9)):
                fail(item, f"'during year {mfin.group(1)}: {mfin.group(2)} years' but t = {tstar:.4f}")
            for mp in re.finditer(r"(below|above) \$([\d,]+) after \\\((\d+)\\\) years and (below|above) it after \\\((\d+)\\\) years", a):
                n1, n2 = int(mp.group(3)), int(mp.group(5))
                V = to_number(mp.group(2))
                s1 = F({"t": n1}) - V
                s2 = F({"t": n2}) - V
                if n2 != n1 + 1 or (s1 < 0) != (mp.group(1) == "below") or (s2 < 0) != (mp.group(4) == "below"):
                    fail(item, f"'{mp.group(0)}' does not bracket the target {V}")
            for mt in maths(a):
                parts, ops = split_top(mt)
                if parts[0].strip() == "t" and len(parts) > 1:
                    got = evaluate(parts[1])
                    if abs(got - tstar) > 1e-5 * max(1, tstar):
                        fail(item, f"t = {got} vs {tstar} for target {target}")
                    break
            else:
                fail(item, "no t = line in the answer")
        else:
            arg = re.search(r"\\\((\d+\.?\d*)\\\)", q) or re.search(r"\w\((\d+\.?\d*)\)", q)
            if not arg:
                raise Skip()
            want = F({"t": float(arg.group(1))})
            v, parts = first_chain_value(a)
            tol = rounding_tol(re.sub(r"\\\)|\\\(", "", parts[-1])) if "approx" in a else 1e-9
            if abs(v - want) > max(tol, 1e-9) * max(1, abs(want)) and abs(last_value(a) - want) > max(tol, 1e-9):
                fail(item, f"value {v} vs {want}")
