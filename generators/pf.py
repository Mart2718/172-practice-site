"""PF2-PF3 (chapter 4): graphs of the other trigonometric functions, and inverse trigonometric functions.

Answers are exact (multiples of pi). Each template checks its answer a second way with floating point.
"""
import math

import sympy as sp

from common import x, m
from util import frac_tex

R = sp.Rational
PI = sp.pi
NAMES = ["f", "g", "k"]


def _pi_tex(q):
    """q*pi as LaTeX for a rational q: 0, \\pi, \\dfrac{\\pi}{4}, -\\dfrac{3\\pi}{2}."""
    q = R(q)
    if q == 0:
        return "0"
    sign = "-" if q < 0 else ""
    p, d = abs(q.p), q.q
    top = r"\pi" if p == 1 else rf"{p}\pi"
    return sign + (top if d == 1 else rf"\dfrac{{{top}}}{{{d}}}")


def _plus_pi(q):
    """' + \\dfrac{\\pi}{4}' / ' - \\dfrac{\\pi}{4}' for building arguments."""
    q = R(q)
    return "" if q == 0 else (f" - {_pi_tex(-q)}" if q < 0 else f" + {_pi_tex(q)}")


def _arg(k, c):
    """The argument kx + c (c a rational multiple of pi) as LaTeX."""
    kx = "x" if k == 1 else (rf"\dfrac{{x}}{{{k.q}}}" if R(k).p == 1 and R(k).q != 1 else f"{R(k).p}x")
    return kx + _plus_pi(c)


def _n_term(k):
    """The step n*pi/k between excluded values."""
    k = R(k)
    step = R(1) / k           # as a multiple of pi
    if step == 1:
        return r"n\pi"
    if step.q == 1:
        return rf"{step.p}n\pi"
    return rf"\dfrac{{{step.p if step.p != 1 else ''}n\pi}}{{{step.q}}}"


def _excluded(offset, k):
    """x != offset*pi + n*pi/k (n an integer) as LaTeX math."""
    off = R(offset)
    lead = "" if off == 0 else _pi_tex(off) + " + "
    return rf"x \ne {lead}{_n_term(k)}"


def _stretch(a):
    return "" if a == 1 else ("-" if a == -1 else str(a))


# ============================================================================ PF2
def tan_cot_features(rng):
    F = rng.choice(NAMES)
    fn = rng.choice(["tan", "cot"])
    k = R(rng.choice([2, 3, 4, R(1, 2)]))
    A = rng.choice([1, 1, 2, 3, -1, -2])
    if fn == "tan":
        offset = R(1, 2) / k        # excluded: kx = pi/2 + n pi  ->  x = pi/(2k) + n pi/k
    else:
        offset = R(0)               # excluded: kx = n pi         ->  x = n pi/k
    period = R(1) / k               # multiple of pi
    # second routes: the function blows up at excluded points, is finite between them, and repeats every period
    g = (lambda t: math.tan(float(k) * t)) if fn == "tan" else (lambda t: 1 / math.tan(float(k) * t))
    for n in range(-3, 4):
        x0 = float(offset + n * period) * math.pi
        assert abs(g(x0 + 1e-7)) > 1e5 and abs(g(x0 - 1e-7)) > 1e5
        mid = x0 + float(period) * math.pi / 4
        assert abs(g(mid)) < 1e6
    assert abs(g(0.3 + float(period) * math.pi) - g(0.3)) < 1e-6 * (1 + abs(g(0.3)))
    expr = f"{F}(x) = {_stretch(A)}\\{fn}\\left({_arg(k, 0)}\\right)"
    why = ("The tangent is undefined where the cosine is " + m(0) + f", that is where {m(_arg(k, 0))} equals {m(r'\dfrac{\pi}{2} + n\pi')}."
           if fn == "tan" else
           "The cotangent is undefined where the sine is " + m(0) + f", that is where {m(_arg(k, 0))} equals {m(r'n\pi')}.")
    parts = [
        ("State the domain. Describe the values of " + m("x") + " that must be excluded.",
         f"{why} Solving for {m('x')}: the domain is all real numbers with {m(_excluded(offset, k))}, where {m('n')} is any integer."),
        ("State the range.", f"{m(r'(-\infty, \infty)')}. Stretching or reflecting a tangent or cotangent graph does not change its range."),
        ("State the period.", f"The period is {m(rf'\dfrac{{\pi}}{{{k}}}' if k.q == 1 else r'2\pi')}."),
    ]
    return {"stem": f"Let {m(expr)}.", "parts": parts, "figure": None}


def sec_csc_features(rng):
    F = rng.choice(NAMES)
    fn = rng.choice(["sec", "csc"])
    k = R(rng.choice([1, 1, 2]))
    A = rng.choice([1, 1, 2, 3, -1])
    c = R(rng.choice([-1, 1, 1, -1, 0]), rng.choice([2, 3, 4, 6]))
    if c == 0:
        c = R(1, 4)
    # excluded: sec -> k x + c = pi/2 + n pi ; csc -> k x + c = n pi
    offset = ((R(1, 2) if fn == "sec" else R(0)) - c) / k
    step = R(1) / k
    func = (lambda t: 1 / math.cos(float(k) * t + float(c) * math.pi)) if fn == "sec" else (lambda t: 1 / math.sin(float(k) * t + float(c) * math.pi))
    for n in range(-3, 4):
        x0 = float(offset + n * step) * math.pi
        assert abs(func(x0 + 1e-7)) > 1e5
    vals = [A * func(t / 50) for t in range(-300, 300) if abs(func(t / 50)) < 1e4]
    assert all(abs(v) >= abs(A) - 1e-9 for v in vals) and any(v > 0 for v in vals) and any(v < 0 for v in vals)
    expr = f"{F}(x) = {_stretch(A)}\\{fn}\\left({_arg(k, c)}\\right)"
    a_ = abs(A)
    why = ("secant is " + m(r"\dfrac{1}{\cos}") if fn == "sec" else "cosecant is " + m(r"\dfrac{1}{\sin}"))
    zero_of = "cosine" if fn == "sec" else "sine"
    parts = [
        ("State the domain. Describe the values of " + m("x") + " that must be excluded.",
         f"The {why}, so it is undefined where the {zero_of} of {m(_arg(k, c))} is {m(0)}. "
         f"The domain is all real numbers with {m(_excluded(offset, k))}, where {m('n')} is any integer."),
        ("State the range.",
         f"The values of {m(chr(92) + fn + ' u')} are never between {m(-1)} and {m(1)}, and the stretch factor is {m(A)}, so the range is "
         f"{m(rf'(-\infty, -{a_}] \cup [{a_}, \infty)')}."),
    ]
    return {"stem": f"Let {m(expr)}.", "parts": parts, "figure": None}


def trig_graph_assessment(rng):
    """Assessment: period, asymptotes in [0, 2pi), and range for a secant or cosecant."""
    F = rng.choice(NAMES)
    fn = rng.choice(["sec", "csc"])
    k = R(rng.choice([1, 2]))
    A = rng.choice([2, 3, -2, -3, 1])
    c = R(rng.choice([1, -1]), rng.choice([2, 4]))
    offset = ((R(1, 2) if fn == "sec" else R(0)) - c) / k
    step = R(1) / k
    asym = sorted({offset + n * step for n in range(-8, 9) if 0 <= offset + n * step < 2})
    func = (lambda t: 1 / math.cos(float(k) * t + float(c) * math.pi)) if fn == "sec" else (lambda t: 1 / math.sin(float(k) * t + float(c) * math.pi))
    for a_ in asym:
        assert abs(func(float(a_) * math.pi + 1e-7)) > 1e5
    # no other point of [0, 2pi) is an asymptote: the count is 2k per 2pi
    assert len(asym) == int(2 * k)
    expr = f"{F}(x) = {_stretch(A)}\\{fn}\\left({_arg(k, c)}\\right)"
    per = R(2) / k
    a_abs = abs(A)
    parts = [
        ("State the period.", f"The period of {m(chr(92) + fn + '(kx)')} is {m(r'\dfrac{2\pi}{k}')}, so here it is {m(_pi_tex(per))}."),
        ("List the vertical asymptotes in the interval " + m(r"[0, 2\pi)") + ".",
         "The excluded values are " + m(_excluded(offset, k)) + ". In " + m(r"[0, 2\pi)") + " these are "
         + ", ".join(m("x = " + _pi_tex(a_)) for a_ in asym) + "."),
        ("State the range.", f"{m(rf'(-\infty, -{a_abs}] \cup [{a_abs}, \infty)')}."),
    ]
    return {"stem": f"Let {m(expr)}.", "parts": parts, "figure": None}


# ============================================================================ PF3
SIN_ANGLES = [R(-1, 2), R(-1, 3), R(-1, 4), R(-1, 6), R(0), R(1, 6), R(1, 4), R(1, 3), R(1, 2)]
COS_ANGLES = [R(0), R(1, 6), R(1, 4), R(1, 3), R(1, 2), R(2, 3), R(3, 4), R(5, 6), R(1)]
TAN_ANGLES = [R(-1, 3), R(-1, 4), R(-1, 6), R(0), R(1, 6), R(1, 4), R(1, 3)]


def _exact_tex(v):
    """An exact trig value as LaTeX."""
    v = sp.nsimplify(v)
    s = sp.latex(sp.radsimp(v))
    return s.replace(r"\frac", r"\dfrac")


def inverse_trig_exact(rng):
    items = []
    pool = [("arcsin", SIN_ANGLES, sp.sin), ("arccos", COS_ANGLES, sp.cos), ("arctan", TAN_ANGLES, sp.tan)]
    rng.shuffle(pool)
    for name, angles, fn in pool:
        theta = rng.choice([a for a in angles])
        val = fn(theta * PI)
        val = sp.simplify(val)
        # second route: numerics
        numeric = {"arcsin": math.asin, "arccos": math.acos, "arctan": math.atan}[name](float(val))
        assert abs(numeric - float(theta) * math.pi) < 1e-9
        rng_txt = {"arcsin": r"\left[-\dfrac{\pi}{2}, \dfrac{\pi}{2}\right]", "arccos": r"[0, \pi]", "arctan": r"\left(-\dfrac{\pi}{2}, \dfrac{\pi}{2}\right)"}[name]
        items.append((f"Compute {m(rf'\{name}\left({_exact_tex(val)}\right)')}.",
                      f"The output of {m(chr(92) + name)} must lie in {m(rng_txt)}. The angle there whose "
                      f"{ {'arcsin': 'sine', 'arccos': 'cosine', 'arctan': 'tangent'}[name] } is {m(_exact_tex(val))} is {m(_pi_tex(theta))}."))
    return {"stem": "", "parts": items, "figure": None}


def inverse_trig_domain_range(rng):
    F = rng.choice(NAMES)
    kind = rng.choice(["arcsin", "arccos", "arctan"])
    form = rng.choice(["plain", "shift_in", "scale_in", "shift_out"])
    c = rng.choice([1, 2, 3, -1, -2])
    sc = rng.choice([2, 3, 4])
    lo, hi = {"arcsin": (R(-1, 2), R(1, 2)), "arccos": (R(0), R(1)), "arctan": (R(-1, 2), R(1, 2))}[kind]
    closed = kind != "arctan"
    off = R(rng.choice([1, 2, -1, -2]), rng.choice([2, 4]))
    if form == "plain":
        inner, dom_lo, dom_hi = "x", -1, 1
        out_off = 0
    elif form == "shift_in":
        inner = f"x - {c}" if c > 0 else f"x + {-c}"
        dom_lo, dom_hi, out_off = c - 1, c + 1, 0
    elif form == "scale_in":
        inner = rf"\dfrac{{x}}{{{sc}}}"
        dom_lo, dom_hi, out_off = -sc, sc, 0
    else:
        inner, dom_lo, dom_hi, out_off = "x", -1, 1, off
    shift = "" if out_off == 0 else _plus_pi(out_off)
    if kind == "arctan":
        dom = r"(-\infty, \infty)"
    else:
        dom = f"[{dom_lo}, {dom_hi}]"
    rlo, rhi = lo + out_off, hi + out_off
    rng_txt = (f"[{_pi_tex(rlo)}, {_pi_tex(rhi)}]" if closed else f"({_pi_tex(rlo)}, {_pi_tex(rhi)})")
    # second route: sample the function on the claimed domain
    fn = {"arcsin": math.asin, "arccos": math.acos, "arctan": math.atan}[kind]
    if kind != "arctan":
        pts = [dom_lo + (dom_hi - dom_lo) * i / 40 for i in range(41)]
        arg = (lambda t: t) if form in ("plain", "shift_out") else ((lambda t: t - c) if form == "shift_in" else (lambda t: t / sc))
        ys = [fn(arg(t)) + float(out_off) * math.pi for t in pts]
        assert abs(min(ys) - float(rlo) * math.pi) < 1e-9 and abs(max(ys) - float(rhi) * math.pi) < 1e-9
        try:
            fn(arg(dom_hi + 0.01))
            raise AssertionError("domain too small")
        except ValueError:
            pass
    expr = f"{F}(x) = \\{kind}\\left({inner}\\right){shift}"
    if kind == "arctan":
        why_d = "The arctangent accepts every real number, so there is no restriction on the input."
    else:
        why_d = (f"The input of {m(chr(92) + kind)} must be between {m(-1)} and {m(1)}: {m('-1 \\le ' + inner + ' \\le 1')}, which gives {m('x \\in ' + dom)}.")
    base_rng = {"arcsin": r"\left[-\dfrac{\pi}{2}, \dfrac{\pi}{2}\right]", "arccos": r"[0, \pi]", "arctan": r"\left(-\dfrac{\pi}{2}, \dfrac{\pi}{2}\right)"}[kind]
    why_r = (f"The output of {m(chr(92) + kind)} lies in {m(base_rng)}." +
             (f" The added {m(_pi_tex(out_off))} shifts that interval." if out_off != 0 else
              " Moving the graph left or right does not change the range." if form == "shift_in" else
              " Stretching the graph horizontally does not change the range." if form == "scale_in" else ""))
    parts = [("State the domain.", f"{why_d} The domain is {m(dom)}."),
             ("State the range.", f"{why_r} The range is {m(rng_txt)}.")]
    return {"stem": f"Let {m(expr)}.", "parts": parts, "figure": None}


TRIPLES = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (20, 21, 29)]


def inverse_trig_compose(rng):
    """Assessment: a trig function of an inverse trig value, and an inverse trig of a trig value outside the range."""
    a_, b_, c_ = rng.choice(TRIPLES)
    kind = rng.choice([("sin", "arccos"), ("cos", "arcsin"), ("tan", "arcsin"), ("tan", "arccos")])
    outer, inner = kind
    sign = rng.choice([1, -1])
    # inner argument: arcsin(sign*a/c) or arccos(sign*a/c)
    num = sign * (a_ if inner == "arcsin" else b_)
    arg = R(num, c_)
    theta = math.asin(float(arg)) if inner == "arcsin" else math.acos(float(arg))
    val = {"sin": math.sin, "cos": math.cos, "tan": math.tan}[outer](theta)
    # exact value from the right triangle
    if inner == "arcsin":        # sin t = num/c, cos t = +b/c  (t in [-pi/2, pi/2])
        s_, c2 = R(num, c_), R(b_, c_)
    else:                        # cos t = num/c, sin t = +a/c  (t in [0, pi])
        c2, s_ = R(num, c_), R(a_, c_)
    exact = {"sin": s_, "cos": c2, "tan": s_ / c2}[outer]
    assert abs(float(exact) - val) < 1e-9
    q1 = rf"Find the exact value of {m(rf'\{outer}\left(\{inner}\left({frac_tex(arg)}\right)\right)')}."
    other = "cosine" if inner == "arcsin" else "sine"
    sign_why = ("The angle from " + m(chr(92) + inner) + (" is in " + m(r"\left[-\dfrac{\pi}{2}, \dfrac{\pi}{2}\right]") + ", where the cosine is never negative"
                if inner == "arcsin" else " is in " + m(r"[0, \pi]") + ", where the sine is never negative") + ".")
    theta_def = m("\\theta = \\" + inner + "\\left(" + frac_tex(arg) + "\\right)")
    a1 = (f"Let {theta_def}. {sign_why} "
          f"Draw a right triangle with the known side {m(abs(num))} and hypotenuse {m(c_)}: the other side is {m(b_ if inner == 'arcsin' else a_)}, "
          f"so the {other} is {m(frac_tex(c2 if inner == 'arcsin' else s_))}. Then {m('\\' + outer + '\\theta = ' + frac_tex(exact))}.")
    # (b) arcsin(sin t) or arccos(cos t) with t outside the range
    which = rng.choice(["arcsin", "arccos"])
    if which == "arcsin":
        t = rng.choice([R(2, 3), R(3, 4), R(5, 6), R(7, 6), R(5, 4), R(4, 3), R(5, 3)])
        ans_angle = R(1) - t if t > R(1, 2) and t <= R(3, 2) else t - 2
        if t >= R(3, 2):
            ans_angle = t - 2
        val_check = math.asin(math.sin(float(t) * math.pi))
    else:
        t = rng.choice([R(-1, 6), R(-1, 4), R(-1, 3), R(-1, 2), R(-2, 3), R(5, 4), R(4, 3), R(3, 2), R(5, 3)])
        ans_angle = -t if t < 0 else (2 - t)
        val_check = math.acos(math.cos(float(t) * math.pi))
    assert abs(val_check - float(ans_angle) * math.pi) < 1e-9
    func = "sin" if which == "arcsin" else "cos"
    rng_txt = r"\left[-\dfrac{\pi}{2}, \dfrac{\pi}{2}\right]" if which == "arcsin" else r"[0, \pi]"
    q2 = f"Find the exact value of {m(rf'\{which}\left(\{func}\left({_pi_tex(t)}\right)\right)')}."
    a2 = (f"The inverse function returns an angle in {m(rng_txt)}, and {m(_pi_tex(t))} is not in that interval, so the answer is not {m(_pi_tex(t))}. "
          f"Find the angle in {m(rng_txt)} with the same {'sine' if which == 'arcsin' else 'cosine'}: it is {m(_pi_tex(ans_angle))}.")
    return {"stem": "", "parts": [(q1, a1), (q2, a2)], "figure": None}


TEMPLATES = {
    "tan_cot_features": tan_cot_features,
    "sec_csc_features": sec_csc_features,
    "trig_graph_assessment": trig_graph_assessment,
    "inverse_trig_exact": inverse_trig_exact,
    "inverse_trig_domain_range": inverse_trig_domain_range,
    "inverse_trig_compose": inverse_trig_compose,
}
