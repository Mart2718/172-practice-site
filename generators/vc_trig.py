"""Checks for PF2, PF3 and TE1-TE3: each re-solves the question from its printed text, numerically."""
import math
import random
import re

from texeval import DEG, FreeVar, ParseError, compile_tex, evaluate, split_top
from vbase import Skip, check, close, fail, last_value, maths, strip_text

TAU = 2 * math.pi
RAND = random.Random(7)


def body_of(stem):
    m = re.search(r"\\\((\w)\(x\) = (.*?)\\\)", stem, flags=re.S)
    if not m:
        raise Skip()
    return m.group(2).strip()


def parse_iv(text):
    """One interval written with brackets and maybe \\pi: returns [(lo, hi), ...] with +-inf allowed."""
    text = text.replace(r"\left", "").replace(r"\right", "")
    out = []
    for lb, lo, hi, rb in re.findall(r"([\[(])\s*(.*?)\s*,\s*(.*?)\s*([\])])", text):
        def one(t):
            t = t.strip()
            if t == r"-\infty":
                return -math.inf
            if t == r"\infty":
                return math.inf
            return evaluate(t)
        out.append((one(lo), one(hi), lb == "[", rb == "]"))
    return out


# ------------------------------------------------------------------ PF2
def poles_of(F, lo=-12.0, hi=12.0, step=0.002):
    """x values where F is unbounded: sign changes of 1/F that sit where |F| is huge."""
    out, prev, x_ = [], None, lo
    while x_ <= hi:
        try:
            f = F({"x": x_})
            g = 1 / f if f != 0 else 0.0
        except (ZeroDivisionError, ValueError, OverflowError):
            g = None
        if g is not None and prev is not None and prev[1] * g < 0:
            a, b, ga = prev[0], x_, prev[1]
            for _ in range(60):
                mid = (a + b) / 2
                try:
                    fm = F({"x": mid})
                    gm = 1 / fm if fm != 0 else 0.0
                except (ZeroDivisionError, ValueError, OverflowError):
                    break
                if ga * gm < 0:
                    b = mid
                else:
                    a, ga = mid, gm
            r = (a + b) / 2
            try:
                big = abs(F({"x": r})) > 1e6
            except (ZeroDivisionError, OverflowError):
                big = True
            if big:
                out.append(r)
        prev = (x_, g) if g is not None else None
        x_ += step
    return out


def printed_excluded(a):
    for mt in maths(a):
        if r"\ne" in mt:
            rhs = mt.split(r"\ne", 1)[1]
            f = compile_tex(rhs)
            return [f({"n": float(n)}) for n in range(-90, 91)]
    return None


def pf2_part(item, p, F):
    q, a = p["q"], p["a"]
    poles = poles_of(F)
    if "domain" in q:
        ex = printed_excluded(a)
        if ex is None:
            fail(item, "no excluded values printed")
            return
        inside = [v for v in ex if -12 <= v <= 12]
        for r in poles:
            if not any(abs(r - v) < 1e-4 for v in inside):
                fail(item, f"pole at x = {r:.5f} is not excluded in the printed domain")
        for v in inside:
            if not any(abs(r - v) < 1e-4 for r in poles):
                fail(item, f"x = {v:.5f} is excluded in the printed domain but F is finite there")
    if "period" in q:
        P = last_value(a)
        for x_ in (0.123, 0.77, 1.31, -0.55):
            try:
                if abs(F({"x": x_ + P}) - F({"x": x_})) > 1e-7 * max(1, abs(F({"x": x_}))):
                    fail(item, f"{P:.6g} is not a period")
                    return
            except (ZeroDivisionError, OverflowError):
                continue
        for m_ in (2, 3, 4, 5, 6):
            same = True
            for x_ in (0.123, 0.77, 1.31, -0.55, 2.2):
                try:
                    if abs(F({"x": x_ + P / m_}) - F({"x": x_})) > 1e-7 * max(1, abs(F({"x": x_}))):
                        same = False
                        break
                except (ZeroDivisionError, OverflowError):
                    continue
            if same:
                fail(item, f"{P:.6g} is not the smallest period (so is {P / m_:.6g})")
    if "range" in q:
        frag = [t for t in maths(a) if r"\infty" in t][-1]
        iv = parse_iv(frag)
        samples = []
        x_ = -12.0
        while x_ <= 12.0:
            try:
                v = F({"x": x_})
                if abs(v) < 1e5:
                    samples.append(v)
                else:
                    samples.append(math.copysign(1e5, v))
            except (ZeroDivisionError, OverflowError):
                pass
            x_ += 0.003
        for v in samples:
            if abs(v) < 1e5 and not any((lo < v or (lc and v == lo)) and (v < hi or (rc and v == hi)) for lo, hi, lc, rc in iv):
                fail(item, f"F takes the value {v:.5g}, outside the printed range {frag}")
                return
        for lo, hi, lc, rc in iv:
            for e in (lo, hi):
                if math.isfinite(e) and min(abs(v - e) for v in samples) > 2e-3:
                    fail(item, f"the endpoint {e:.5g} of the printed range is never reached")
                    return
        if len(iv) == 1 and iv[0][0] == -math.inf and iv[0][1] == math.inf:
            near = []
            for r in poles:
                for dx in (-1e-7, 1e-7):
                    try:
                        near.append(F({"x": r + dx}))
                    except (ZeroDivisionError, OverflowError):
                        pass
            if not (near and min(near) <= -1e3 and max(near) >= 1e3):
                fail(item, "printed range is all reals but F is bounded")
    if "asymptotes" in q:
        norm = [(r % TAU) if TAU - (r % TAU) > 1e-6 else 0.0 for r in poles if -TAU <= r <= 2 * TAU]
        want = sorted({round(r, 6) for r in norm})
        mt = a.split("these are")[-1]
        got = []
        for frag in maths(mt):
            parts, ops = split_top(frag)
            if parts[0].strip() == "x":
                got.append(evaluate(parts[1]))
        if len(got) != len(want) or any(abs(g - w) > 1e-4 for g, w in zip(sorted(got), want)):
            fail(item, f"asymptotes in [0, 2pi): printed {got}, found {want}")


@check("tan_cot_features", "sec_csc_features", "trig_graph_assessment")
def pf2(item):
    F = compile_tex(body_of(item["stem"]))
    for p in item["parts"]:
        pf2_part(item, p, F)


# ------------------------------------------------------------------ PF3
def defined_range(F, lo=-12.0, hi=12.0):
    xs, vals = [], []
    x_ = lo
    while x_ <= hi:
        try:
            vals.append(F({"x": x_}))
            xs.append(x_)
        except (ValueError, ZeroDivisionError):
            pass
        x_ += 0.001
    return xs, vals


@check("inverse_trig_domain_range")
def inverse_domain_range(item):
    F = compile_tex(body_of(item["stem"]))
    xs, vals = defined_range(F)
    full = len(xs) > 23000

    def edge(inside, outside):
        for _ in range(60):
            mid = (inside + outside) / 2
            try:
                F({"x": mid})
                inside = mid
            except (ValueError, ZeroDivisionError):
                outside = mid
        return inside

    lo_e = hi_e = None
    if not full:
        lo_e, hi_e = edge(min(xs), min(xs) - 0.002), edge(max(xs), max(xs) + 0.002)
    for p in item["parts"]:
        q, a = p["q"], p["a"]
        iv = parse_iv([t for t in maths(a) if "," in t][-1])[0]
        if "domain" in q:
            if full:
                if not (iv[0] == -math.inf and iv[1] == math.inf):
                    fail(item, "domain should be all reals")
            elif abs(iv[0] - lo_e) > 1e-6 or abs(iv[1] - hi_e) > 1e-6 or not (iv[2] and iv[3]):
                fail(item, f"domain printed {iv} vs [{lo_e:.6f}, {hi_e:.6f}]")
        if "range" in q:
            if full:                               # arctan: approaches but never reaches its bounds
                lo_v, hi_v = F({"x": -1e9}), F({"x": 1e9})
                if abs(iv[0] - lo_v) > 1e-6 or abs(iv[1] - hi_v) > 1e-6 or iv[2] or iv[3]:
                    fail(item, f"range printed {iv} vs ({lo_v:.6f}, {hi_v:.6f})")
            else:
                ends = [F({"x": lo_e}), F({"x": hi_e})]
                lo_v, hi_v = min(vals + ends), max(vals + ends)
                if abs(iv[0] - lo_v) > 1e-6 or abs(iv[1] - hi_v) > 1e-6 or not (iv[2] and iv[3]):
                    fail(item, f"range printed {iv} vs [{lo_v:.6f}, {hi_v:.6f}]")


@check("inverse_trig_exact", "inverse_trig_compose")
def inverse_value(item):
    for p in item["parts"]:
        want = evaluate(maths(p["q"])[0])
        got = last_value(p["a"])
        if not close(got, want, 1e-9):
            fail(item, f"{maths(p['q'])[0]} = {want:.8g} but the answer ends with {got:.8g}")


# ------------------------------------------------------------------ TE1
QUAD_RANGE = {"I": (0, math.pi / 2), "II": (math.pi / 2, math.pi), "III": (math.pi, 1.5 * math.pi), "IV": (1.5 * math.pi, TAU)}


def angle_from(fn, g, quad):
    """An angle in the quadrant whose function value is g, found from the inverse function."""
    inv = {"sin": math.asin, "cos": math.acos, "tan": math.atan}[fn]
    t0 = inv(g)
    cands = {"sin": [t0, math.pi - t0], "cos": [t0, TAU - t0], "tan": [t0, t0 + math.pi]}[fn]
    lo, hi = QUAD_RANGE[quad]
    for c in cands:
        c %= TAU
        if lo < c < hi:
            return c
    raise Skip()


@check("pythagorean_quadrant")
def pythagorean_quadrant(item):
    for p in item["parts"]:
        frags = maths(p["q"])
        fn_given, rhs = re.match(r"\\(sin|cos|tan)\\theta = (.*)", frags[0]).groups()
        g = evaluate(rhs)
        quad = re.search(r"Quadrant (IV|III|II|I)", strip_text(p["q"]) + " " + p["q"]).group(1)
        fn_ask = re.match(r"\\(sin|cos|tan)\\theta", frags[-1]).group(1)
        th = angle_from(fn_given, g, quad)
        want = {"sin": math.sin, "cos": math.cos, "tan": math.tan}[fn_ask](th)
        got = last_value(p["a"])
        if not close(got, want, 1e-9):
            fail(item, f"{fn_ask} = {want:.8g} but the answer ends with {got:.8g}")


@check("sum_difference_exact", "half_angle_exact")
def exact_value(item):
    p = item["parts"][0]
    want = evaluate(maths(p["q"])[0])
    got = last_value(p["a"])
    if not close(got, want, 1e-9):
        fail(item, f"{maths(p['q'])[0]} = {want:.8g} but the answer ends with {got:.8g}")


@check("power_reduce", "power_reduce_fourth")
def power_reduce(item):
    p = item["parts"][0]
    fq = compile_tex(maths(p["q"])[0])
    final_tex = maths(p["a"])[-1].split("=")[-1]
    fr = compile_tex(final_tex)
    for _ in range(5):
        env = {"x": RAND.uniform(-3, 3)}
        if not close(fq(env), fr(env), 1e-9):
            fail(item, f"{maths(p['q'])[0]} is not {final_tex}")
            return
    if re.search(r"\\(sin|cos)\^\{[2-9]\}", final_tex):
        fail(item, "the final form still has a power of sine or cosine")


@check("double_angle_given")
def double_angle(item):
    frags = maths(item["stem"])
    fn_given, rhs = re.match(r"\\(sin|cos|tan)\\theta = (.*)", frags[0]).groups()
    quad = re.search(r"Quadrant (IV|III|II|I)", item["stem"]).group(1)
    th = angle_from(fn_given, evaluate(rhs), quad)
    for p in item["parts"]:
        want = compile_tex(maths(p["q"])[0])({"theta": th})
        got = last_value(p["a"])
        if not close(got, want, 1e-9):
            fail(item, f"{maths(p['q'])[0]} = {want:.8g} but the answer ends with {got:.8g}")


# ------------------------------------------------------------------ TE2
@check("verify_identity_basic", "verify_identity_fractions")
def verify_identity(item):
    p = item["parts"][0]
    parts, ops = split_top(maths(p["q"])[0])
    L, R = compile_tex(parts[0]), compile_tex(parts[1])
    steps = [compile_tex(t) for t in re.findall(r"(?:side, |: )\\\((.*?)\\\)\.", p["a"])]
    if len(steps) < 2:
        fail(item, "could not read the steps")
        return
    for ang in (0.37, 0.91, 1.21, 2.0, 2.6, 4.1, 5.3):
        env = {"x": ang, "t": ang, "u": ang, "theta": ang}
        try:
            l, r = L(env), R(env)
        except ZeroDivisionError:
            continue
        if not close(l, r, 1e-8):
            fail(item, f"not an identity: {parts[0]} vs {parts[1]} at {ang}")
            return
        for s in steps:
            try:
                if not close(s(env), l, 1e-8):
                    fail(item, "a step is not equal to the starting side")
                    return
            except ZeroDivisionError:
                continue


# ------------------------------------------------------------------ TE3
def trig_roots(H, lo, hi, n=60000):
    """Real solutions of H = 0 on [lo, hi): sign changes, plus touching zeros (double roots)."""
    xs = [lo + (hi - lo) * i / n for i in range(n)]
    vals = []
    for v in xs:
        try:
            vals.append(H({"theta": v}))
        except (ZeroDivisionError, ValueError, OverflowError):
            vals.append(None)
    roots = []

    def add(r):
        if not any(abs(r - s) < 1e-7 for s in roots):
            roots.append(r)

    if vals[0] is not None and abs(vals[0]) < 1e-9:
        add(lo)
    for i in range(n - 1):
        a, b = vals[i], vals[i + 1]
        if a is None or b is None:
            continue
        if a * b < 0 and abs(a) < 1e3 and abs(b) < 1e3:
            lo_, hi_ = xs[i], xs[i + 1]
            fa = a
            for _ in range(70):
                mid = (lo_ + hi_) / 2
                fm = H({"theta": mid})
                if fa * fm <= 0:
                    hi_ = mid
                else:
                    lo_, fa = mid, fm
            r = (lo_ + hi_) / 2
            if abs(H({"theta": r})) < 1e-6:
                add(r)
    for i in range(1, n - 1):
        a, b, c = vals[i - 1], vals[i], vals[i + 1]
        if None in (a, b, c):
            continue
        if abs(b) < 1e-6 and abs(b) <= abs(a) and abs(b) <= abs(c):
            lo_, hi_ = xs[i - 1], xs[i + 1]
            for _ in range(80):                    # ternary search for the minimum of |H|
                m1, m2 = lo_ + (hi_ - lo_) / 3, hi_ - (hi_ - lo_) / 3
                if abs(H({"theta": m1})) < abs(H({"theta": m2})):
                    hi_ = m2
                else:
                    lo_ = m1
            r = (lo_ + hi_) / 2
            if abs(H({"theta": r})) < 1e-10:
                add(r)
    return sorted(roots)


def equation_of(q):
    mt = maths(q)[-1]
    parts, ops = split_top(mt)
    if len(parts) != 2:
        raise Skip()
    L, R = compile_tex(parts[0]), compile_tex(parts[1])
    return lambda env: L(env) - R(env)


def printed_angles(a):
    tail = re.split(r"[Ss]olutions are|All solutions:", a)[-1]
    out = []
    for frag in maths(tail):
        parts, ops = split_top(frag)
        out.append(evaluate(parts[-1]))
    return out


@check("trig_squared_interval", "trig_multiple_angle", "trig_quadratic_form")
def trig_interval(item):
    for p in item["parts"]:
        H = equation_of(p["q"])
        roots = [r for r in trig_roots(H, 0, TAU)]
        got = sorted(printed_angles(p["a"]))
        if len(got) != len(roots) or any(abs(g - r) > 1e-5 for g, r in zip(got, roots)):
            fail(item, f"{maths(p['q'])[-1]}: printed {[round(g, 5) for g in got]} vs found {[round(r, 5) for r in roots]}")


@check("trig_general_solution")
def trig_general(item):
    for p in item["parts"]:
        H = equation_of(p["q"])
        roots = trig_roots(H, -TAU, 2 * TAU, 90000)
        general = [t for t in maths(p["a"]) if r"n\pi" in t][-1]
        pieces = [s.replace(r"\theta =", "").strip() for s in general.split(r"\text{ or }")]
        vals = []
        for piece in pieces:
            f = compile_tex(piece)
            for n in range(-6, 7):
                vals.append(f({"n": float(n)}))
        for v in vals:
            if -TAU - 1e-9 <= v < 2 * TAU and abs(H({"theta": v})) > 1e-9:
                fail(item, f"{v:.6g} from the general solution does not satisfy {maths(p['q'])[-1]}")
                return
        for r in roots:
            if not any(abs(r - v) < 1e-6 for v in vals):
                fail(item, f"the solution {r:.6g} of {maths(p['q'])[-1]} is missing from the general solution {general}")
                return


# ------------------------------------------------------------------ intermediate claims inside the worked answers
def frag_list(a):
    return maths(a)


def eq_rhs_value(q):
    parts, ops = split_top(maths(q)[-1])
    return evaluate(parts[1])


def squared_roots_claim(item):
    """tan^2 = c is followed by tan = +-sqrt(c): the square of the printed value must be c."""
    for p in item["parts"]:
        c = eq_rhs_value(p["q"])
        for mt in maths(p["a"]):
            m = re.match(r"\\(sin|cos|tan)\\theta = \\pm (.*)$", mt.strip())
            if m and abs(evaluate(m.group(2)) ** 2 - c) > 1e-9:
                fail(item, f"{mt} but the square of the right-hand side is not {c:.6g}")


def split_commas(tex):
    out, depth, cur = [], 0, ""
    for ch in tex:
        if ch in "{(":
            depth += 1
        elif ch in "})":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return out


def multiple_angle_claims(item):
    for p in item["parts"]:
        q, a = p["q"], p["a"]
        eq = maths(q)[-1]
        m = re.match(r"\\(sin|cos|tan)\((\d+)\\theta\) = (.*)$", eq.strip())
        if not m:
            continue
        fn, k, c_tex = m.group(1), int(m.group(2)), m.group(3)
        c = evaluate(c_tex)
        if not re.search(rf"u = {k}\\theta", a):
            fail(item, f"the substitution should be u = {k}\\theta")
        mm = re.search(r"Solve \\\(\\" + fn + r"\(u\) = (.*?)\\\)", a)
        if not mm or abs(evaluate(mm.group(1)) - c) > 1e-9:
            fail(item, "the equation in u does not have the question's right-hand side")
        f = {"sin": math.sin, "cos": math.cos, "tan": math.tan}[fn]
        mu = re.search(r"in one period (?:is|are) \\\((u = .*?)\\\)", a)
        if not mu:
            fail(item, "the base solution(s) in u are not printed")
        else:
            vals = [evaluate(t.replace("u =", "").strip()) for t in split_commas(mu.group(1))]
            for u in vals:
                if not (0 <= u < (math.pi if fn == "tan" else TAU) + 1e-12) or abs(f(u) - c) > 1e-9:
                    fail(item, f"u = {u:.6g} is not a solution in one period of {fn}(u) = {c:.6g}")
            want = 1 if fn == "tan" else (1 if abs(abs(c) - 1) < 1e-9 else 2)
            if len(vals) != want:
                fail(item, f"{len(vals)} base solution(s) printed; {want} expected")
        mr = re.search(r"\\\(u\\\) ranges over \\\(\[0, (\d*)\\pi\)\\\)", a)
        if not mr or int(mr.group(1) or 1) != 2 * k:
            fail(item, f"u should range over [0, {2 * k}\\pi)")
        md = re.search(r"divide by \\\((\d+)\\\)", a)
        if not md or int(md.group(1)) != k:
            fail(item, f"the answer should divide by {k}")


def quadratic_form_claims(item):
    for p in item["parts"]:
        H = equation_of(p["q"])
        a = p["a"]
        mf = re.search(r"Factor it: \\\((.*?) = 0\\\)", a)
        if mf:
            F = compile_tex(mf.group(1))
            for ang in (0.4, 1.1, 2.3, 3.9, 5.2):
                if not close(F({"theta": ang}), H({"theta": ang}), 1e-8):
                    fail(item, f"the factored form {mf.group(1)} is not the question's left side")
                    break
        for mg in re.finditer(r"gives \\\(\\(sin|cos|tan)\\theta = (.*?)\\\), so (.*?)(?=;| All solutions|\.)", a):
            fn, v_tex, angles = mg.group(1), mg.group(2), mg.group(3)
            v = evaluate(v_tex)
            angs = [evaluate(t) for t in maths(angles)]
            f = {"sin": math.sin, "cos": math.cos, "tan": math.tan}[fn]
            for t in angs:
                if not (0 <= t < TAU) or abs(f(t) - v) > 1e-9:
                    fail(item, f"{t:.6g} is not an angle in [0, 2pi) with {fn} = {v_tex}")
            want = 2 if (fn == "tan" or abs(v) < 1 - 1e-9) else 1
            if abs(v) > 1 + 1e-9 and fn != "tan":
                want = 0
            if len(angs) != want:
                fail(item, f"{len(angs)} angle(s) printed for {fn}theta = {v_tex}; {want} expected")


def general_solution_claims(item):
    for p in item["parts"]:
        H = equation_of(p["q"])
        for mt in maths(p["a"]):
            m = re.fullmatch(r"\\theta = ([^n]*?)", mt.strip())
            if m and "n" not in m.group(1):
                try:
                    t = evaluate(m.group(1))
                except Exception:
                    continue
                if abs(H({"theta": t})) > 1e-9:
                    fail(item, f"theta = {m.group(1)} is printed as a solution but it is not")


def bound_theta_claims(item):
    """After 'theta = D' (degrees or radians), every later 'sin/cos/tan theta = V' must hold at that theta."""
    for p in item["parts"]:
        th = None
        for mt in maths(p["a"]):
            m = re.fullmatch(r"\\theta = (.+)", mt.strip())
            if m:
                try:
                    th = evaluate(m.group(1))
                except Exception:
                    th = None
                continue
            m = re.fullmatch(r"\\(sin|cos|tan)\\theta = (.+)", mt.strip())
            if m and th is not None:
                try:
                    v = evaluate(m.group(2))
                except Exception:
                    continue
                if abs({"sin": math.sin, "cos": math.cos, "tan": math.tan}[m.group(1)](th) - v) > 1e-9:
                    fail(item, f"{mt.strip()} is false at the theta printed just before")


def half_angle_claims(item):
    p = item["parts"][0]
    target = evaluate(re.search(r"\\(?:sin|cos|tan)\\left\((.*?)\\right\)", p["q"]).group(1))
    m = re.search(r"with \\\(\\theta = (.*?)\\\)", p["a"])
    if not m or abs(evaluate(m.group(1)) - 2 * target) > 1e-9:
        fail(item, "theta in the half-angle formula should be twice the angle asked for")


def pm_claims(item, mode):
    """cos theta = +-v : v squared must be cos^2 of the angle that the givens describe."""
    if mode == "stem":
        frags = maths(item["stem"])
        fn_given, rhs = re.match(r"\\(sin|cos|tan)\\theta = (.*)", frags[0]).groups()
        quad = re.search(r"Quadrant (IV|III|II|I)", item["stem"]).group(1)
        jobs = [(item["parts"][0]["a"], angle_from(fn_given, evaluate(rhs), quad))]
    else:
        jobs = []
        for p in item["parts"]:
            frags = maths(p["q"])
            fn_given, rhs = re.match(r"\\(sin|cos|tan)\\theta = (.*)", frags[0]).groups()
            quad = re.search(r"Quadrant (IV|III|II|I)", p["q"]).group(1)
            jobs.append((p["a"], angle_from(fn_given, evaluate(rhs), quad)))
    for a, th in jobs:
        for mt in maths(a):
            m = re.match(r"\\(sin|cos|tan)\\theta = \\pm (.*)$", mt.strip())
            if m:
                want = {"sin": math.sin, "cos": math.cos, "tan": math.tan}[m.group(1)](th)
                if abs(evaluate(m.group(2)) ** 2 - want ** 2) > 1e-9:
                    fail(item, f"{mt.strip()} but the angle described has {m.group(1)}^2 = {want ** 2:.6g}")


EXTRA = {
    "trig_squared_interval": [squared_roots_claim],
    "trig_multiple_angle": [multiple_angle_claims],
    "trig_quadratic_form": [quadratic_form_claims],
    "trig_general_solution": [general_solution_claims],
    "half_angle_exact": [half_angle_claims, bound_theta_claims],
    "sum_difference_exact": [bound_theta_claims],
    "pythagorean_quadrant": [lambda it: pm_claims(it, "parts")],
}


def with_extras(name, base):
    def run(item):
        base(item)
        for f in EXTRA[name]:
            f(item)
    return run


from vbase import CHECKS  # noqa: E402

for _name in EXTRA:
    CHECKS[_name] = with_extras(_name, CHECKS[_name])


# ------------------------------------------------------------------ fixed statements that the templates print
def squash(tex):
    return re.sub(r"\s+", "", tex.replace(r"\left", "").replace(r"\right", ""))


CANON_NAME = {"secant": r"\dfrac{1}{\cos}", "cosecant": r"\dfrac{1}{\sin}", "tangent": r"\dfrac{\sin}{\cos}", "cotangent": r"\dfrac{\cos}{\sin}"}
RECIP_OF = {"sec": "cosine", "csc": "sine", "tan": "cosine", "cot": "sine"}
ARC_RANGE = {"arcsin": (-math.pi / 2, math.pi / 2, True), "arccos": (0.0, math.pi, True), "arctan": (-math.pi / 2, math.pi / 2, False)}


def interval_matches(tex, name):
    lo, hi, closed = ARC_RANGE[name]
    iv = parse_iv(tex)
    return len(iv) == 1 and abs(iv[0][0] - lo) < 1e-9 and abs(iv[0][1] - hi) < 1e-9 and iv[0][2] == closed and iv[0][3] == closed


def pf2_static(item):
    stem_arg = re.search(r"\\(sec|csc|tan|cot)\\left\((.*)\\right\)", item["stem"])
    for p in item["parts"]:
        a = p["a"]
        for m in re.finditer(r"The (secant|cosecant|tangent|cotangent) is \\\((.*?)\\\)", a):
            if squash(m.group(2)) != squash(CANON_NAME[m.group(1)]):
                fail(item, f"the {m.group(1)} is not {m.group(2)}")
        for m in re.finditer(r"the (sine|cosine) of \\\((.*?)\\\) is \\\((.*?)\\\)", a):
            if stem_arg and (squash(m.group(2)) != squash(stem_arg.group(2)) or RECIP_OF[stem_arg.group(1)] != m.group(1) or m.group(3).strip() != "0"):
                fail(item, f"'{m.group(0)[:60]}' does not match the function in the stem")
        for m in re.finditer(r"undefined where the (sine|cosine) is \\\((.*?)\\\)", a):
            if m.group(2).strip() != "0":
                fail(item, f"'undefined where the {m.group(1)} is {m.group(2)}' should say 0")
        for tex in maths(a):
            if re.fullmatch(r"\[[^,]*, [^)]*\\pi\)", tex.strip()) and squash(tex) != squash(r"[0, 2\pi)"):
                fail(item, f"the interval {tex} should be [0, 2\\pi)")


def pf3_static(item):
    for p in item["parts"]:
        a, q = p["a"], p["q"]
        for m in re.finditer(r"\\\(\\(arcsin|arccos|arctan)\\\) (?:must lie|lies) in \\\((.*?)\\\)", a):
            if not interval_matches(m.group(2), m.group(1)):
                fail(item, f"the range printed for {m.group(1)} is wrong: {m.group(2)}")
        for m in re.finditer(r"The angle from \\\(\\(arcsin|arccos|arctan)\\left\(.*?\\\) is in \\\((.*?)\\\)", a):
            if not interval_matches(m.group(2), m.group(1)):
                fail(item, f"the range printed for {m.group(1)} is wrong: {m.group(2)}")
        outer = re.search(r"\\(arcsin|arccos|arctan)", q)
        for m in re.finditer(r"(?:returns an angle in|Find the angle in) \\\((.*?)\\\)", a):
            if outer and not interval_matches(m.group(1), outer.group(1)):
                fail(item, f"the interval {m.group(1)} is not the range of {outer.group(1)}")
        inner = re.search(r"\\(?:sin|cos|tan)\\left\((.*)\\right\)\\right\)", q)
        mn = re.search(r"is not \\\((.*?)\\\)", a)
        if inner and mn and abs(evaluate(inner.group(1)) - evaluate(mn.group(1))) > 1e-9:
            fail(item, f"'the answer is not {mn.group(1)}' but the angle inside is {inner.group(1)}")


HALF_BAD = re.compile(r"\\(sin|cos|tan)\\dfrac\{\\theta\}\{(?!2\})")
HALF = {"sin": r"\sin\dfrac{\theta}{2} = \pm\sqrt{\dfrac{1 - \cos\theta}{2}}", "cos": r"\cos\dfrac{\theta}{2} = \pm\sqrt{\dfrac{1 + \cos\theta}{2}}"}


def te1_static(item):
    for p in item["parts"] if item["parts"] else []:
        for tex in maths(p["a"]) + maths(item["stem"]):
            t = squash(tex)
            for fn, canon in HALF.items():
                if t.startswith(squash(r"\%s\dfrac{\theta}{2} =" % fn)) and t != squash(canon):
                    fail(item, f"the half-angle formula for {fn} is misprinted: {tex}")
            if t.startswith(r"\sin^") and t.endswith("=1") and t != squash(r"\sin^{2}\theta + \cos^{2}\theta = 1"):
                fail(item, f"the Pythagorean identity is misprinted: {tex}")
            if HALF_BAD.search(t):
                fail(item, f"a half-angle expression should divide theta by 2: {tex}")


def te3_static(item):
    for p in item["parts"]:
        for tex in maths(p["a"]) + maths(p["q"]):
            t = squash(tex)
            if re.fullmatch(r"[^\\]*\\le\\theta\\lt.*", t) and t != squash(r"0 \le \theta \lt 2\pi"):
                fail(item, f"the interval condition should be 0 <= theta < 2pi: {tex}")
            if re.fullmatch(r"\[\d+,\d*\\pi\)", t) and t not in ("[0,2\\pi)", "[0,4\\pi)", "[0,6\\pi)", "[0,8\\pi)", "[0,10\\pi)", "[0,12\\pi)"):
                fail(item, f"unexpected interval {tex}")
            if t.startswith("[") and t.endswith(r"\pi)") and not t.startswith("[0,"):
                fail(item, f"an interval should start at 0: {tex}")
        for m in re.finditer(r"Each sign gives two angles in \\\((.*?)\\\)", p["a"]):
            if squash(m.group(1)) != squash(r"[0, 2\pi)"):
                fail(item, f"'Each sign gives two angles in {m.group(1)}' should say [0, 2\\pi)")
        for m in re.finditer(r"In \\\((.*?)\\\) the solutions are", p["a"]):
            if squash(m.group(1)) != squash(r"[0, 2\pi)"):
                fail(item, f"'In {m.group(1)} the solutions are' should say [0, 2\\pi)")
        for m in re.finditer(r"Set each factor equal to \\\((.*?)\\\)", p["a"]):
            if m.group(1).strip() != "0":
                fail(item, "each factor should be set equal to 0")
        fn = re.search(r"\\(sin|cos|tan)", maths(p["q"])[-1])
        for m in re.finditer(r"Adding full periods \(\\\((.*?)\\\)\)", p["a"]):
            want = r"\pi" if fn and fn.group(1) == "tan" else r"2\pi"
            if m.group(1).strip() != want:
                fail(item, f"full periods should be {want} here")


def ssa_static(item):
    angles, sides = gather_givens(item)
    A = next(iter(angles))
    x_ = A.lower()
    y_ = next(sd for sd in sides if sd != x_)
    for m in re.finditer(r"\\\((\d+)\\sin (\d+)\\text\{°\} \\lt\s+(\d+) \\lt\s+(\d+)\\\)", item["parts"][0]["a"]):
        c, ang, mid, top = map(int, m.groups())
        if (c, ang, mid, top) != (int(sides[y_]), round(angles[A] / DEG), int(sides[x_]), int(sides[y_])):
            fail(item, f"the inequality {m.group(0)} does not match the givens")
    for m in re.finditer(r"The other angle with this sine, \\\((.*?)\\\)", item["parts"][0]["a"]):
        if squash(m.group(1)) != squash(r"180\text{°} - B"):
            fail(item, f"the supplementary angle should be 180 - B: {m.group(1)}")


def gather_givens(item):
    from vc_tri import givens
    html = item["stem"] + " " + " ".join(p["q"] for p in item["parts"])
    return givens(html)


from texeval import DEG  # noqa: E402

STATIC = {
    "tan_cot_features": [pf2_static], "sec_csc_features": [pf2_static], "trig_graph_assessment": [pf2_static],
    "inverse_trig_exact": [pf3_static], "inverse_trig_domain_range": [pf3_static], "inverse_trig_compose": [pf3_static],
    "power_reduce": [te1_static], "power_reduce_fourth": [te1_static], "half_angle_exact": [te1_static],
    "double_angle_given": [te1_static], "pythagorean_quadrant": [te1_static],
    "trig_general_solution": [te3_static], "trig_squared_interval": [te3_static], "trig_multiple_angle": [te3_static], "trig_quadratic_form": [te3_static],
}


def with_static(name, base):
    def run(item):
        base(item)
        for f in STATIC[name]:
            f(item)
    return run


for _name in STATIC:
    CHECKS[_name] = with_static(_name, CHECKS[_name])
