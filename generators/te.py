"""TE1-TE6 (chapter 4): identities, trigonometric equations, triangles and applications.

Exact values come from SymPy; rounded values are computed from unrounded ones, and every template checks
its answer a second way (floating point, or coordinates for triangles).
"""
import math
import re

import sympy as sp

from common import x, m
from util import frac_tex, safe_round, fmt_dec

R = sp.Rational
NAMES = ["f", "g", "k"]


# ============================================================================ TE1
def _val_tex(v):
    s = sp.latex(sp.expand(v)).replace(r"\frac", r"\dfrac")
    return f"\\left({s}\\right)" if s.startswith("-") else s


def _final_tex(v):
    """An exact value of the form (±sqrt6 ± sqrt2)/4, written as one fraction."""
    v = sp.expand(v)
    c6, c2 = v.coeff(sp.sqrt(6)), v.coeff(sp.sqrt(2))
    assert 4 * c6 in (-1, 1) and 4 * c2 in (-1, 1) and v == c6 * sp.sqrt(6) + c2 * sp.sqrt(2)
    if c6 > 0:
        num_ = r"\sqrt{6} + \sqrt{2}" if c2 > 0 else r"\sqrt{6} - \sqrt{2}"
        return rf"\dfrac{{{num_}}}{{4}}"
    if c2 > 0:
        return r"\dfrac{\sqrt{2} - \sqrt{6}}{4}"
    return r"-\dfrac{\sqrt{6} + \sqrt{2}}{4}"


SPECIAL = [30, 45, 60, 120, 135, 150, 210, 225, 240, 300, 315, 330]


def sum_difference_exact(rng):
    fn = rng.choice(["sin", "cos"])
    target = rng.choice([15, 75, 105, 165, 195, 255, 285, 345])
    # 15 and 75 appear only as cos 15 and sin 75, so a practice item is never word-for-word an item used in class
    assert (fn, target) not in (("sin", 15), ("cos", 75))
    options = [(A, B, op) for A in SPECIAL for B in (30, 45, 60) for op in "+-" if A != B
               and (A + B if op == "+" else A - B) == target]
    assert options
    A, B, op = rng.choice(options)
    f = sp.sin if fn == "sin" else sp.cos
    g = sp.cos if fn == "sin" else sp.sin
    rad = lambda d: sp.pi * d / 180
    sA, cA, sB, cB = sp.sin(rad(A)), sp.cos(rad(A)), sp.sin(rad(B)), sp.cos(rad(B))
    if fn == "cos":
        value = cA * cB - sA * sB if op == "+" else cA * cB + sA * sB
        formula = (rf"\cos A\cos B {'-' if op == '+' else '+'} \sin A\sin B")
        expanded = rf"\cos {A}^\circ\cos {B}^\circ {'-' if op == '+' else '+'} \sin {A}^\circ\sin {B}^\circ"
        substituted = rf"{_val_tex(cA)}\cdot {_val_tex(cB)} {'-' if op == '+' else '+'} {_val_tex(sA)}\cdot {_val_tex(sB)}"
        name = r"\cos(A \pm B)"
    else:
        value = sA * cB + cA * sB if op == "+" else sA * cB - cA * sB
        formula = (rf"\sin A\cos B {'+' if op == '+' else '-'} \cos A\sin B")
        expanded = rf"\sin {A}^\circ\cos {B}^\circ {'+' if op == '+' else '-'} \cos {A}^\circ\sin {B}^\circ"
        substituted = rf"{_val_tex(sA)}\cdot {_val_tex(cB)} {'+' if op == '+' else '-'} {_val_tex(cA)}\cdot {_val_tex(sB)}"
        name = r"\sin(A \pm B)"
    # second route: floating point
    exact = float(value)
    truth = (math.cos if fn == "cos" else math.sin)(math.radians(target))
    assert abs(exact - truth) < 1e-12
    final = _final_tex(value)
    q = f"Find the exact value of {m(rf'\{fn}\left({target}^\circ\right)')} using a sum or difference formula."
    a = (f"Write {m(f'{target}^\\circ = {A}^\\circ {op} {B}^\\circ')}. Then "
         f"{m(rf'\{fn}({A}^\circ {op} {B}^\circ) = ' + expanded + ' = ' + substituted + ' = ' + final)}.")
    return {"stem": "", "parts": [(q, a)], "figure": None}


TRIPLES = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (20, 21, 29), (9, 40, 41)]
QUAD = {1: (1, 1), 2: (1, -1), 3: (-1, -1), 4: (-1, 1)}      # (sign of cos... see below)
# sign of (cos, sin) by quadrant
SIGNS = {1: (1, 1), 2: (-1, 1), 3: (-1, -1), 4: (1, -1)}
QNAME = {1: "I", 2: "II", 3: "III", 4: "IV"}


def _angle_in(quad, a, b, c):
    """An angle (radians) in the given quadrant with |sin| = a/c, |cos| = b/c."""
    sc, ss = SIGNS[quad]
    return math.atan2(ss * a, sc * b)


def pythagorean_quadrant(rng):
    a, b, c = rng.choice(TRIPLES)
    if rng.random() < 0.5:
        a, b = b, a
    parts = []
    # (a) given sine or cosine, find the other
    q1 = rng.choice([1, 2, 3, 4])
    sc, ss = SIGNS[q1]
    given = rng.choice(["sin", "cos"])
    th = _angle_in(q1, a, b, c)
    if given == "sin":
        gv = R(ss * a, c)
        find_v = R(sc * b, c)
        assert abs(math.sin(th) - float(gv)) < 1e-12 and abs(math.cos(th) - float(find_v)) < 1e-12
        sq = 1 - gv ** 2
        ask, other = "cos", "sin"
    else:
        gv = R(sc * b, c)
        find_v = R(ss * a, c)
        assert abs(math.cos(th) - float(gv)) < 1e-12 and abs(math.sin(th) - float(find_v)) < 1e-12
        sq = 1 - gv ** 2
        ask, other = "sin", "cos"
    sign_word = "positive" if find_v > 0 else "negative"
    why_sign = (f"In Quadrant {QNAME[q1]}, the {'cosine' if ask == 'cos' else 'sine'} is {sign_word}.")
    a1 = (f"{m(r'\sin^{2}\theta + \cos^{2}\theta = 1')}, so {m(rf'\{ask}^{{2}}\theta = 1 - \left({frac_tex(gv)}\right)^{{2}} = ' + frac_tex(sq))}. "
          f"Then {m(rf'\{ask}\theta = \pm ' + frac_tex(sp.sqrt(sq)))}. {why_sign} So {m(rf'\{ask}\theta = ' + frac_tex(find_v))}.")
    parts.append((f"If {m(rf'\{given}\theta = ' + frac_tex(gv))} and {m(r'\theta')} is in Quadrant {QNAME[q1]}, find {m(rf'\{ask}\theta')}.", a1))
    # (b) given tangent, find the sine or cosine
    a2_, b2_, c2_ = rng.choice([t for t in TRIPLES if t != (a, b, c) and t != (b, a, c)])
    q2 = rng.choice([1, 2, 3, 4])
    sc2, ss2 = SIGNS[q2]
    tanv = R(ss2 * a2_, sc2 * b2_)
    th2 = _angle_in(q2, a2_, b2_, c2_)
    assert abs(math.tan(th2) - float(tanv)) < 1e-9
    ask2 = rng.choice(["sin", "cos"])
    val2 = R(sc2 * b2_, c2_) if ask2 == "cos" else R(ss2 * a2_, c2_)
    assert abs((math.cos if ask2 == "cos" else math.sin)(th2) - float(val2)) < 1e-12
    sec_sq = 1 + tanv ** 2
    a2 = (f"{m(r'1 + \tan^{2}\theta = \sec^{2}\theta')}, so {m(rf'\sec^{{2}}\theta = 1 + \left({frac_tex(tanv)}\right)^{{2}} = ' + frac_tex(sec_sq))} "
          f"and {m(r'\cos\theta = \pm ' + frac_tex(1 / sp.sqrt(sec_sq)))}. In Quadrant {QNAME[q2]}, the cosine is {'positive' if sc2 > 0 else 'negative'}, "
          f"so {m(r'\cos\theta = ' + frac_tex(R(sc2 * b2_, c2_)))}. " +
          (f"Then {m(r'\sin\theta = \tan\theta\cos\theta = ' + frac_tex(R(ss2 * a2_, c2_)))}." if ask2 == "sin" else ""))
    parts.append((f"If {m(r'\tan\theta = ' + frac_tex(tanv))} and {m(r'\theta')} is in Quadrant {QNAME[q2]}, find {m(rf'\{ask2}\theta')}.", a2))
    return {"stem": "", "parts": parts, "figure": None}


def power_reduce(rng):
    fn = rng.choice(["sin", "cos"])
    c = rng.choice([2, 3, 4, 5, 6, 7, 10, 12])
    k = rng.choice([1, 2, 3, 4, 5])
    arg = "x" if k == 1 else f"{k}x"
    double = f"{2 * k}x"
    half = R(c, 2)
    # second route: compare numerically
    for t in (0.3, 1.1, 2.7):
        lhs = c * (math.sin if fn == "sin" else math.cos)(k * t) ** 2
        rhs = float(half) + (float(half) if fn == "cos" else -float(half)) * math.cos(2 * k * t)
        assert abs(lhs - rhs) < 1e-9
    sgn = "+" if fn == "cos" else "-"
    result = f"{frac_tex(half)} {sgn} {frac_tex(half)}\\cos({double})"
    a = (f"Use {m(r'\cos^{2}u = \dfrac{1 + \cos(2u)}{2}' if fn == 'cos' else r'\sin^{2}u = \dfrac{1 - \cos(2u)}{2}')} with {m('u = ' + arg)}: "
         f"{m(f'{c}\\{fn}^{{2}}({arg}) = {c}\\cdot\\dfrac{{1 {sgn} \\cos({double})}}{{2}} = ' + result)}.")
    return {"stem": "", "parts": [(f"Rewrite {m(f'{c}\\{fn}^{{2}}({arg})')} using only first powers of cosine.", a)], "figure": None}


def power_reduce_fourth(rng):
    """Assessment: a fourth power needs the formula twice."""
    fn = rng.choice(["sin", "cos"])
    c = rng.choice([8, 16, 24, 32])
    k = rng.choice([1, 2, 3])
    arg = "x" if k == 1 else f"{k}x"
    s = c // 8
    for t in (0.4, 1.3, 2.9):
        lhs = c * (math.sin if fn == "sin" else math.cos)(k * t) ** 4
        mid = -4 * s if fn == "sin" else 4 * s
        rhs = 3 * s + mid * math.cos(2 * k * t) + s * math.cos(4 * k * t)
        assert abs(lhs - rhs) < 1e-9
    mid_sign = "-" if fn == "sin" else "+"
    mid_coef = 4 * s
    result = f"{3 * s} {mid_sign} {mid_coef}\\cos({2 * k}x) + {s}\\cos({4 * k}x)"
    a = (f"Write the fourth power as a square: {m(f'{c}\\{fn}^{{4}}({arg}) = {c}\\left(\\{fn}^{{2}}({arg})\\right)^{{2}}')}. "
         f"Apply the power-reducing formula to the inner square, expand, and apply the formula again to the {m('\\cos^{2}')} that appears. "
         f"The result is {m(result)}.")
    return {"stem": "", "parts": [(f"Rewrite {m(f'{c}\\{fn}^{{4}}({arg})')} using only first powers of cosine.", a)], "figure": None}


def double_angle_given(rng):
    """Assessment: sin 2θ, cos 2θ, tan 2θ from one value and a quadrant."""
    a, b, c = rng.choice([t for t in TRIPLES if t != (20, 21, 29)])
    if rng.random() < 0.5:
        a, b = b, a
    quad = rng.choice([1, 2, 3, 4])
    sc, ss = SIGNS[quad]
    given = rng.choice(["sin", "cos"])
    s_, c_ = R(ss * a, c), R(sc * b, c)
    gv = s_ if given == "sin" else c_
    th = _angle_in(quad, a, b, c)
    s2, c2 = 2 * s_ * c_, c_ ** 2 - s_ ** 2
    assert abs(math.sin(2 * th) - float(s2)) < 1e-9 and abs(math.cos(2 * th) - float(c2)) < 1e-9 and c2 != 0
    t2 = s2 / c2
    miss = "cosine" if given == "sin" else "sine"
    find_expr = r"\cos\theta" if given == "sin" else r"\sin\theta"
    find_val = c_ if given == "sin" else s_
    parts = [
        (f"Find {m(find_expr)}.", f"In Quadrant {QNAME[quad]} the {miss} is {'positive' if find_val > 0 else 'negative'}. "
                                 f"Using {m(r'\sin^{2}\theta + \cos^{2}\theta = 1')}: {m(find_expr + ' = ' + frac_tex(find_val))}."),
        (f"Find {m(r'\sin(2\theta)')}.", f"{m(r'\sin(2\theta) = 2\sin\theta\cos\theta = 2\left(' + frac_tex(s_) + r'\right)\left(' + frac_tex(c_) + r'\right) = ' + frac_tex(s2))}."),
        (f"Find {m(r'\cos(2\theta)')}.", f"{m(r'\cos(2\theta) = \cos^{2}\theta - \sin^{2}\theta = ' + frac_tex(c2))}."),
        (f"Find {m(r'\tan(2\theta)')}.", f"{m(r'\tan(2\theta) = \dfrac{\sin(2\theta)}{\cos(2\theta)} = ' + frac_tex(t2))}."),
    ]
    return {"stem": f"Suppose {m(rf'\{given}\theta = ' + frac_tex(gv))} and {m(r'\theta')} is in Quadrant {QNAME[quad]}.", "parts": parts, "figure": None}


def _plain_val(v):
    return sp.latex(sp.expand(v)).replace(r"\frac", r"\dfrac")


def half_angle_exact(rng):
    """Exact sin, cos, or tan of half of a special angle, with the sign chosen by the quadrant."""
    theta = rng.choice([30, 45, 60, 120, 135, 150, 210, 240, 300, 315])
    fn = rng.choice(["sin", "cos", "tan"])
    half = R(theta, 2)
    hd = str(int(half)) if half.q == 1 else str(float(half))
    rad = lambda d: sp.pi * d / 180
    c = sp.cos(rad(theta))
    s_ = sp.sin(rad(theta))
    quad = 1 if half < 90 else 2 if half < 180 else 3 if half < 270 else 4
    sgn_sin = 1 if quad in (1, 2) else -1
    sgn_cos = 1 if quad in (1, 4) else -1
    th = f"{theta}^\\circ"
    if fn == "tan":
        value = sp.radsimp(s_ / (1 + c))
        vtex = sp.latex(value).replace(r"\frac", r"\dfrac")
        work = (f"Use {m(r'\tan\dfrac{\theta}{2} = \dfrac{\sin\theta}{1 + \cos\theta}')} with {m('\\theta = ' + th)}, "
                f"so {m(r'\sin\theta = ' + _plain_val(s_))} and {m(r'\cos\theta = ' + _plain_val(c))}. "
                f"Then {m(rf'\tan\left({hd}^\circ\right) = \dfrac{{{_plain_val(s_)}}}{{1 + {_val_tex(c)}}} = ' + vtex)}.")
        value_f = float(value)
    else:
        sign = sgn_sin if fn == "sin" else sgn_cos
        k = sp.expand(2 * (1 - c)) if fn == "sin" else sp.expand(2 * (1 + c))      # radicand = k / 4
        if k.is_Rational:
            vtex = _plain_val(sign * sp.sqrt(k) / 2)
            alt = ""
        else:
            t = k - 2
            ktex = "2 + " + sp.latex(t) if t > 0 else "2 - " + sp.latex(-t)
            vtex = ("-" if sign < 0 else "") + rf"\dfrac{{\sqrt{{{ktex}}}}}{{2}}"
            alt = ""
            den = sp.expand(sp.sqrtdenest(sp.sqrt(k)) / 2)
            if den.has(sp.sqrt(6)):
                alt = f" This is the same number as {m(_final_tex(sign * den))}."
        value_f = float(sign * sp.sqrt(k) / 2)
        form = r"\sin\dfrac{\theta}{2} = \pm\sqrt{\dfrac{1 - \cos\theta}{2}}" if fn == "sin" else r"\cos\dfrac{\theta}{2} = \pm\sqrt{\dfrac{1 + \cos\theta}{2}}"
        where = (f"{hd}\u00b0 is in Quadrant {QNAME[quad]}, where the {'sine' if fn == 'sin' else 'cosine'} is {'positive' if sign > 0 else 'negative'}, "
                 f"so use the {'plus' if sign > 0 else 'minus'} sign.")
        work = (f"Use {m(form)} with {m('\\theta = ' + th)}, so {m(r'\cos\theta = ' + _plain_val(c))}. {where} "
                f"Then {m(rf'\{fn}\left({hd}^\circ\right) = ' + vtex)}.{alt}")
    # second route: floating point
    assert abs(value_f - FUNC[fn](math.radians(float(half)))) < 1e-9, (fn, theta)
    q = f"Use a half-angle formula to find the exact value of {m(rf'\{fn}\left({hd}^\circ\right)')}."
    return {"stem": "", "parts": [(q, work)], "figure": None}


# ============================================================================ TE2
# (left side, right side, steps (expression, reason), start side)
IDENT_FLOOR = [
    (r"\tan {v}\cos {v}", r"\sin {v}", [(r"\dfrac{\sin {v}}{\cos {v}}\cdot\cos {v}", "quotient identity"), (r"\sin {v}", "cancel " + r"\(\cos {v}\)")], "left"),
    (r"\csc {v}\tan {v}", r"\sec {v}", [(r"\dfrac{1}{\sin {v}}\cdot\dfrac{\sin {v}}{\cos {v}}", "reciprocal and quotient identities"), (r"\dfrac{1}{\cos {v}}", "cancel " + r"\(\sin {v}\)"), (r"\sec {v}", "reciprocal identity")], "left"),
    (r"\cot {v}\sin {v}", r"\cos {v}", [(r"\dfrac{\cos {v}}{\sin {v}}\cdot\sin {v}", "quotient identity"), (r"\cos {v}", "cancel " + r"\(\sin {v}\)")], "left"),
    (r"\left(1+\tan^{2} {v}\right)\cos^{2} {v}", "1", [(r"\sec^{2} {v}\cos^{2} {v}", "Pythagorean identity"), (r"\dfrac{1}{\cos^{2} {v}}\cdot\cos^{2} {v}", "reciprocal identity"), ("1", "cancel")], "left"),
    (r"(1-\sin {v})(1+\sin {v})", r"\cos^{2} {v}", [(r"1-\sin^{2} {v}", "difference of squares"), (r"\cos^{2} {v}", "Pythagorean identity")], "left"),
    (r"\sec {v}-\cos {v}", r"\sin {v}\tan {v}", [(r"\dfrac{1}{\cos {v}}-\cos {v}", "reciprocal identity"), (r"\dfrac{1-\cos^{2} {v}}{\cos {v}}", "common denominator"),
                                              (r"\dfrac{\sin^{2} {v}}{\cos {v}}", "Pythagorean identity"), (r"\sin {v}\cdot\dfrac{\sin {v}}{\cos {v}}", "factor"), (r"\sin {v}\tan {v}", "quotient identity")], "left"),
    (r"(\csc {v}-\cot {v})(\csc {v}+\cot {v})", "1", [(r"\csc^{2} {v}-\cot^{2} {v}", "difference of squares"), ("1", r"Pythagorean identity \(1+\cot^{2} {v}=\csc^{2} {v}\)")], "left"),
    (r"(\sin {v}+1)(\sin {v}-1)", r"-\cos^{2} {v}", [(r"\sin^{2} {v}-1", "difference of squares"), (r"-\left(1-\sin^{2} {v}\right)", "factor out " + r"\(-1\)"), (r"-\cos^{2} {v}", "Pythagorean identity")], "left"),
    (r"\sin^{2} {v}-\cos^{2} {v}", r"1-2\cos^{2} {v}", [(r"\left(1-\cos^{2} {v}\right)-\cos^{2} {v}", "Pythagorean identity"), (r"1-2\cos^{2} {v}", "combine like terms")], "left"),
    (r"\dfrac{\tan {v}}{\sec {v}}", r"\sin {v}", [(r"\dfrac{\sin {v}/\cos {v}}{1/\cos {v}}", "quotient and reciprocal identities"), (r"\dfrac{\sin {v}}{\cos {v}}\cdot\cos {v}", "dividing by a fraction"), (r"\sin {v}", "cancel")], "left"),
    (r"\dfrac{\sec {v}}{\csc {v}}", r"\tan {v}", [(r"\dfrac{1/\cos {v}}{1/\sin {v}}", "reciprocal identities"), (r"\dfrac{1}{\cos {v}}\cdot\sin {v}", "dividing by a fraction"), (r"\dfrac{\sin {v}}{\cos {v}}", "rewrite"), (r"\tan {v}", "quotient identity")], "left"),
]
IDENT_ASSESS = [
    (r"\dfrac{\sin {v}}{1+\cos {v}}+\dfrac{1+\cos {v}}{\sin {v}}", r"2\csc {v}",
     [(r"\dfrac{\sin^{2} {v}+(1+\cos {v})^{2}}{(1+\cos {v})\sin {v}}", "common denominator"), (r"\dfrac{\sin^{2} {v}+1+2\cos {v}+\cos^{2} {v}}{(1+\cos {v})\sin {v}}", "expand"),
      (r"\dfrac{2+2\cos {v}}{(1+\cos {v})\sin {v}}", "Pythagorean identity"), (r"\dfrac{2(1+\cos {v})}{(1+\cos {v})\sin {v}}", "factor"), (r"\dfrac{2}{\sin {v}}", "cancel"), (r"2\csc {v}", "reciprocal identity")], "left"),
    (r"\dfrac{1}{1-\sin {v}}+\dfrac{1}{1+\sin {v}}", r"2\sec^{2} {v}",
     [(r"\dfrac{(1+\sin {v})+(1-\sin {v})}{(1-\sin {v})(1+\sin {v})}", "common denominator"), (r"\dfrac{2}{1-\sin^{2} {v}}", "simplify"), (r"\dfrac{2}{\cos^{2} {v}}", "Pythagorean identity"), (r"2\sec^{2} {v}", "reciprocal identity")], "left"),
    (r"\dfrac{\cos {v}}{1-\sin {v}}", r"\dfrac{1+\sin {v}}{\cos {v}}",
     [(r"\dfrac{\cos {v}(1+\sin {v})}{(1-\sin {v})(1+\sin {v})}", "multiply top and bottom by " + r"\(1+\sin {v}\)"), (r"\dfrac{\cos {v}(1+\sin {v})}{1-\sin^{2} {v}}", "difference of squares"),
      (r"\dfrac{\cos {v}(1+\sin {v})}{\cos^{2} {v}}", "Pythagorean identity"), (r"\dfrac{1+\sin {v}}{\cos {v}}", "cancel")], "left"),
    (r"\tan {v}+\cot {v}", r"\sec {v}\csc {v}",
     [(r"\dfrac{\sin {v}}{\cos {v}}+\dfrac{\cos {v}}{\sin {v}}", "quotient identities"), (r"\dfrac{\sin^{2} {v}+\cos^{2} {v}}{\cos {v}\sin {v}}", "common denominator"), (r"\dfrac{1}{\cos {v}\sin {v}}", "Pythagorean identity"),
      (r"\dfrac{1}{\cos {v}}\cdot\dfrac{1}{\sin {v}}", "split"), (r"\sec {v}\csc {v}", "reciprocal identities")], "left"),
    (r"\sin {v}\cos {v}(\tan {v}+\cot {v})", "1",
     [(r"\sin {v}\cos {v}\left(\dfrac{\sin {v}}{\cos {v}}+\dfrac{\cos {v}}{\sin {v}}\right)", "quotient identities"), (r"\sin^{2} {v}+\cos^{2} {v}", "distribute and cancel"), ("1", "Pythagorean identity")], "left"),
    (r"\dfrac{1-\cos {v}}{\sin {v}}", r"\dfrac{\sin {v}}{1+\cos {v}}",
     [(r"\dfrac{\sin {v}}{1+\cos {v}}", "start with the right side"), (r"\dfrac{\sin {v}(1-\cos {v})}{(1+\cos {v})(1-\cos {v})}", "multiply top and bottom by " + r"\(1-\cos {v}\)"),
      (r"\dfrac{\sin {v}(1-\cos {v})}{1-\cos^{2} {v}}", "difference of squares"), (r"\dfrac{\sin {v}(1-\cos {v})}{\sin^{2} {v}}", "Pythagorean identity"), (r"\dfrac{1-\cos {v}}{\sin {v}}", "cancel")], "right"),
]
VARS = [("x", "x"), (r"\theta", "theta"), ("t", "t"), ("u", "u")]


def _eval(expr_tex, t):
    """Evaluate a small trig expression written in LaTeX at angle t (radians); our own template strings only."""
    s = expr_tex.replace("{v}", " v ").replace(r"\left", "").replace(r"\right", "")
    s = s.replace(r"\cdot", "*").replace(r"\dfrac", r"\frac").replace("^{2}", "**2")
    for _ in range(10):
        s2 = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"((\1)/(\2))", s)
        if s2 == s:
            break
        s = s2
    s = re.sub(r"\\(sin|cos|tan|cot|sec|csc)\*\*2\s*v", r"(\1(v)**2)", s)
    s = re.sub(r"\\(sin|cos|tan|cot|sec|csc)\s*v", r"\1(v)", s)
    assert "\\" not in s and "{" not in s, s
    s = re.sub(r"(\d)\s*(?=[a-z(])", r"\1*", s)
    s = re.sub(r"\)\s*(?=[a-z(\d])", r")*", s)
    env = {"sin": math.sin, "cos": math.cos, "tan": math.tan, "cot": lambda a: 1 / math.tan(a),
           "sec": lambda a: 1 / math.cos(a), "csc": lambda a: 1 / math.sin(a), "v": t}
    return eval(s, {"__builtins__": {}}, env)  # noqa: S307


def _verify_identity(rng, lib):
    lhs, rhs, steps, start = rng.choice(lib)
    vx, _ = rng.choice(VARS)
    sub = lambda s: s.replace("{v}", vx)
    if start == "right":
        first, rest, target, begin = steps[0][0], steps[1:], lhs, "right"
    else:
        first, rest, target, begin = lhs, steps, rhs, "left"
    assert rest[-1][0] == target, (rest[-1][0], target)
    # second route: every printed line equals the first one at several angles
    for t in (0.37, 0.91, 1.21, 2.0, 2.6):
        assert abs(_eval(lhs, t) - _eval(rhs, t)) < 1e-8, (lhs, rhs)
        base = _eval(first, t)
        for e, _ in rest:
            assert abs(_eval(e, t) - base) < 1e-8, (e, first)
    q = f"Verify that {m(sub(lhs) + ' = ' + sub(rhs))} is an identity."
    other = "left" if begin == "right" else "right"
    a = f"Start with the {begin} side, {m(sub(first))}. "
    for e, why in rest:
        w = sub(why)
        a += f"{w[0].upper() + w[1:]}: {m(sub(e))}. "
    a += f"This is the {other} side, so the identity is verified."
    return {"stem": "", "parts": [(q, a.strip())], "figure": None}


def verify_identity_basic(rng):
    return _verify_identity(rng, IDENT_FLOOR)


def verify_identity_fractions(rng):
    return _verify_identity(rng, IDENT_ASSESS)


# ============================================================================ TE3
VALS = {
    "sin": [R(1, 2), -R(1, 2), sp.sqrt(2) / 2, -sp.sqrt(2) / 2, sp.sqrt(3) / 2, -sp.sqrt(3) / 2],
    "cos": [R(1, 2), -R(1, 2), sp.sqrt(2) / 2, -sp.sqrt(2) / 2, sp.sqrt(3) / 2, -sp.sqrt(3) / 2],
    "tan": [sp.Integer(1), sp.Integer(-1), sp.sqrt(3), -sp.sqrt(3), sp.sqrt(3) / 3, -sp.sqrt(3) / 3],
}
FUNC = {"sin": math.sin, "cos": math.cos, "tan": math.tan}
GRID = 144


def _val_t(v):
    return sp.latex(sp.expand(v)).replace(r"\frac", r"\dfrac")


def _solutions(fn, c, k=1, squared=False):
    """Solutions in [0, 2pi) of fn(k*theta) = c (or its square), as rationals of pi, found on a fine grid."""
    cv = float(c)
    out = []
    for j in range(2 * GRID):
        th = math.pi * j / GRID
        arg = k * th
        if fn == "tan" and abs(math.cos(arg)) < 1e-9:
            continue
        v = FUNC[fn](arg)
        if abs(v * v - cv * cv if squared else v - cv) < 1e-9:
            out.append(R(j, GRID))
    return out


def _expected_count(fn, c, k, squared=False):
    if squared:
        return 4 * k if (abs(float(c)) != 1 and float(c) != 0) else 2 * k
    if fn == "tan":
        return 2 * k
    return k if abs(float(c)) == 1 else 2 * k


def _pi_tex(q):
    q = R(q)
    if q == 0:
        return "0"
    top = r"\pi" if q.p == 1 else rf"{q.p}\pi"
    return top if q.q == 1 else rf"\dfrac{{{top}}}{{{q.q}}}"


def _general(fn, sols):
    """General solution text from the solutions in [0, 2pi) of fn(theta) = c."""
    if fn == "tan":
        a = min(sols)
        return rf"\theta = {_pi_tex(a)} + n\pi"
    parts = [rf"\theta = {_pi_tex(s)} + 2n\pi" for s in sols]
    return r" \text{ or } ".join(parts)


def trig_general_solution(rng):
    items = []
    for fn in rng.sample(["sin", "cos", "tan"], 2):
        # sin = sqrt(3)/2 and tan = 1 are left for in-class use, so practice items are not word-for-word the same as class items
        c = rng.choice([v for v in VALS[fn] if not ((fn == "sin" and v == sp.sqrt(3) / 2) or (fn == "tan" and v == 1))])
        sols = _solutions(fn, c)
        assert len(sols) == _expected_count(fn, c, 1)
        gen = _general(fn, sols)
        why = ("The sine is positive/negative in two quadrants, giving two angles in one turn." if fn == "sin" else
               "The cosine takes this value at two angles in one turn." if fn == "cos" else
               "The tangent repeats every " + m(r"\pi") + ", so one family covers all solutions.")
        items.append((f"Find all solutions of {m(rf'\{fn}\theta = ' + _val_t(c))} (the general solution).",
                      f"In {m(r'[0, 2\pi)')} the solutions are " + ", ".join(m(r"\theta = " + _pi_tex(s)) for s in sols) +
                      f". Adding full periods ({m(r'2\pi' if fn != 'tan' else r'\pi')}) gives all solutions: {m(gen)}, where {m('n')} is any integer."))
    return {"stem": "", "parts": items, "figure": None}


def trig_squared_interval(rng):
    items = []
    for fn in rng.sample(["sin", "cos", "tan"], 2):
        c = rng.choice([v for v in VALS[fn] if float(v) > 0 and not (fn == "sin" and v == sp.sqrt(3) / 2)])
        sols = _solutions(fn, c, squared=True)
        assert len(sols) == 4, (fn, c, sols)
        c2 = sp.expand(c ** 2)
        # second route: put every printed solution back into the original equation
        for sl in sols:
            assert abs(FUNC[fn](math.pi * float(sl)) ** 2 - float(c2)) < 1e-9
        items.append((f"Find all solutions in {m(r'[0, 2\pi)')} of {m(rf'\{fn}^{{2}}\theta = ' + frac_tex(c2))}.",
                      f"Take square roots of both sides: {m(rf'\{fn}\theta = \pm ' + _val_t(c))}. Each sign gives two angles in {m(r'[0, 2\pi)')}. "
                      f"The solutions are " + ", ".join(m(_pi_tex(s)) for s in sols) + "."))
    return {"stem": "", "parts": items, "figure": None}


def trig_multiple_angle(rng):
    items = []
    for fn in rng.sample(["sin", "cos", "tan"], 2):
        k = rng.choice([2, 3, 4])
        c = rng.choice(VALS[fn])
        if fn in ("sin", "cos") and rng.random() < 0.3:
            c = sp.Integer(rng.choice([1, -1]))
        sols = _solutions(fn, c, k=k)
        assert len(sols) == _expected_count(fn, c, k), (fn, c, k, len(sols))
        for sl in sols:                      # second route: substitute back
            assert abs(FUNC[fn](k * math.pi * float(sl)) - float(c)) < 1e-9
        base = _solutions(fn, c)
        if fn == "tan":
            base, period = base[:1], r"\pi"
        else:
            period = r"2\pi"
        base_txt = ", ".join(_pi_tex(b) for b in base)
        word = "solutions" if len(base) > 1 else "solution"
        items.append((f"Find all solutions in {m(r'[0, 2\pi)')} of {m(rf'\{fn}({k}\theta) = ' + _val_t(c))}.",
                      f"Let {m(rf'u = {k}\theta')}. Solve {m(rf'\{fn}(u) = ' + _val_t(c))}: the {word} in one period {'is' if len(base) == 1 else 'are'} {m('u = ' + base_txt)}, "
                      f"and every other solution differs from {'it' if len(base) == 1 else 'these'} by a multiple of {m(period)}. "
                      f"Since {m(r'0 \le \theta < 2\pi')}, {m('u')} ranges over {m(rf'[0, {2 * k}\pi)')}. Keep every solution for {m('u')} in that range, then divide by {m(k)} to get {m(r'\theta')}. "
                      f"The solutions are " + ", ".join(m(_pi_tex(s)) for s in sols) + "."))
    return {"stem": "", "parts": items, "figure": None}


def trig_quadratic_form(rng):
    """Assessment: a quadratic in sin or cos that factors over the integers; factor, then solve each factor."""
    fn = rng.choice(["sin", "cos"])
    r1, r2 = rng.sample([R(1, 2), R(-1, 2), R(1), R(-1), R(0)], 2)
    T = rf"\{fn}\theta"
    d1, c1 = r1.q, -r1.p                # factor d*s + c
    d2, c2 = r2.q, -r2.p
    A, B, C = d1 * d2, d1 * c2 + d2 * c1, c1 * c2

    def lin(d, c):
        t = (T if d == 1 else f"{d}{T}")
        return t if c == 0 else f"{t} {'+' if c > 0 else '-'} {abs(c)}"

    terms = [rf"{'' if A == 1 else A}\{fn}^{{2}}\theta"]
    if B:
        terms.append(f"{'+' if B > 0 else '-'} {'' if abs(B) == 1 else abs(B)}{T}")
    if C:
        terms.append(f"{'+' if C > 0 else '-'} {abs(C)}")
    eq = " ".join(terms) + " = 0"
    sols = sorted({sl for r in (r1, r2) for sl in _solutions(fn, r)})
    assert len(sols) == sum(_expected_count(fn, r, 1) for r in (r1, r2))
    for sl in sols:                      # second route: substitute back into the printed quadratic
        v = FUNC[fn](math.pi * float(sl))
        assert abs(A * v * v + B * v + C) < 1e-9
    per = []
    for r, (d, c) in ((r1, (d1, c1)), (r2, (d2, c2))):
        ss = _solutions(fn, r)
        per.append(f"{m(lin(d, c) + ' = 0')} gives {m(rf'\{fn}\theta = ' + frac_tex(r))}, so " + ", ".join(m(_pi_tex(t)) for t in ss))
    q = f"Find all solutions in {m(r'[0, 2\pi)')} of {m(eq)}."
    a = (f"This is a quadratic in {m(T)}. Factor it: {m('(' + lin(d1, c1) + ')(' + lin(d2, c2) + ') = 0')}. "
         f"Set each factor equal to {m(0)}: " + "; ".join(per) + ". All solutions: " + ", ".join(m(_pi_tex(t)) for t in sols) + ".")
    return {"stem": "", "parts": [(q, a)], "figure": None}


# ============================================================================ TE4 / TE5 / TE6 (triangles)
def _tri_coords(A_deg, c, b):
    """Place A at the origin and B on the x-axis: returns the three points."""
    A = math.radians(A_deg)
    return (0.0, 0.0), (c, 0.0), (b * math.cos(A), b * math.sin(A))


def _dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def _angle_at(p, q, r):
    """Angle at q in triangle p-q-r, in degrees."""
    v1 = (p[0] - q[0], p[1] - q[1])
    v2 = (r[0] - q[0], r[1] - q[1])
    return math.degrees(math.acos((v1[0] * v2[0] + v1[1] * v2[1]) / (math.hypot(*v1) * math.hypot(*v2))))


def _right_triangle(rng, case):
    for _ in range(100):
        try:
            if case == "angle_leg":
                A = rng.randint(20, 70)
                a = rng.randint(5, 30)
                b = a / math.tan(math.radians(A))
                c = a / math.sin(math.radians(A))
                B = 90 - A
                given = f"{m(f'A = {A}^\\circ')} and {m(f'a = {a}')}"
                dec_s, dec_a = 1, 0
                ans = (f"{m(f'B = 90^\\circ - {A}^\\circ = {B}^\\circ')}. {m(f'b = \\dfrac{{a}}{{\\tan A}} = \\dfrac{{{a}}}{{\\tan {A}^\\circ}} \\approx {fmt_dec(safe_round(b, dec_s), dec_s)}')}. "
                       f"{m(f'c = \\dfrac{{a}}{{\\sin A}} = \\dfrac{{{a}}}{{\\sin {A}^\\circ}} \\approx {fmt_dec(safe_round(c, dec_s), dec_s)}')}.")
                rule = "round the sides to the nearest tenth"
            elif case == "two_legs":
                a, b = rng.randint(5, 24), rng.randint(5, 24)
                if a == b:
                    continue
                c = math.hypot(a, b)
                A = math.degrees(math.atan2(a, b))
                B = 90 - A
                given = f"{m(f'a = {a}')} and {m(f'b = {b}')}"
                dec_s, dec_a = 1, 1
                ans = (f"{m(f'c = \\sqrt{{{a}^{{2}} + {b}^{{2}}}} \\approx {fmt_dec(safe_round(c, dec_s), dec_s)}')}. "
                       f"{m(f'A = \\tan^{{-1}}\\left(\\dfrac{{{a}}}{{{b}}}\\right) \\approx {fmt_dec(safe_round(A, dec_a), dec_a)}^\\circ')}. "
                       f"{m(f'B = 90^\\circ - A \\approx {fmt_dec(safe_round(B, dec_a), dec_a)}^\\circ')}.")
                rule = "round the side to the nearest tenth and the angles to the nearest tenth of a degree"
            elif case == "angle_adj":
                A = rng.randint(20, 70)
                b = rng.randint(5, 30)
                a = b * math.tan(math.radians(A))
                c = b / math.cos(math.radians(A))
                B = 90 - A
                given = f"{m(f'A = {A}^\\circ')} and {m(f'b = {b}')}"
                dec_s, dec_a = 1, 0
                ans = (f"{m(f'B = 90^\\circ - {A}^\\circ = {B}^\\circ')}. {m(f'a = b\\tan A = {b}\\tan {A}^\\circ \\approx {fmt_dec(safe_round(a, dec_s), dec_s)}')}. "
                       f"{m(f'c = \\dfrac{{b}}{{\\cos A}} = \\dfrac{{{b}}}{{\\cos {A}^\\circ}} \\approx {fmt_dec(safe_round(c, dec_s), dec_s)}')}.")
                rule = "round the sides to the nearest tenth"
            elif case == "hyp_leg":
                c = rng.randint(10, 40)
                a = rng.randint(4, c - 3)
                if a * 2 == c:
                    continue
                b = math.sqrt(c * c - a * a)
                A = math.degrees(math.asin(a / c))
                B = 90 - A
                given = f"{m(f'a = {a}')} and {m(f'c = {c}')}"
                dec_s, dec_a = 1, 1
                ans = (f"{m(f'b = \\sqrt{{{c}^{{2}} - {a}^{{2}}}} \\approx {fmt_dec(safe_round(b, dec_s), dec_s)}')}. "
                       f"{m(f'A = \\sin^{{-1}}\\left(\\dfrac{{{a}}}{{{c}}}\\right) \\approx {fmt_dec(safe_round(A, dec_a), dec_a)}^\\circ')}. "
                       f"{m(f'B = 90^\\circ - A \\approx {fmt_dec(safe_round(B, dec_a), dec_a)}^\\circ')}.")
                rule = "round the side to the nearest tenth and the angles to the nearest tenth of a degree"
            else:
                B = rng.randint(20, 70)
                c = rng.randint(8, 40)
                A = 90 - B
                a = c * math.cos(math.radians(B))
                b = c * math.sin(math.radians(B))
                given = f"{m(f'B = {B}^\\circ')} and {m(f'c = {c}')}"
                dec_s, dec_a = 1, 0
                ans = (f"{m(f'A = 90^\\circ - {B}^\\circ = {A}^\\circ')}. {m(f'a = c\\cos B = {c}\\cos {B}^\\circ \\approx {fmt_dec(safe_round(a, dec_s), dec_s)}')}. "
                       f"{m(f'b = c\\sin B = {c}\\sin {B}^\\circ \\approx {fmt_dec(safe_round(b, dec_s), dec_s)}')}.")
                rule = "round the sides to the nearest tenth"
            # second route: rebuild the triangle from two sides and compare all six numbers
            P0, P1, P2 = (0.0, 0.0), (b, 0.0), (b, a)       # C at (b,0): right angle at C; A at origin
            assert abs(_dist(P0, P2) - c) < 1e-9 and abs(_angle_at(P2, P0, P1) - A) < 1e-9 and abs(_angle_at(P0, P2, P1) - B) < 1e-9
            break
        except AssertionError:
            continue
    else:
        raise ValueError("no clean draw")
    return {"stem": f"In triangle {m('ABC')}, {m(r'C = 90^\circ')}, {given}. Solve the triangle ({rule}).",
            "parts": [("Find all the missing sides and angles.", ans)], "figure": None}


def right_triangle_angle_given(rng):
    return _right_triangle(rng, rng.choice(["angle_leg", "angle_adj", "angle_hyp"]))


def right_triangle_sides_given(rng):
    return _right_triangle(rng, rng.choice(["two_legs", "hyp_leg"]))


def _pair(rng, lo, hi):
    return rng.randint(lo, hi)


def _tenth(v):
    return fmt_dec(safe_round(v, 1, 0.03), 1)


def law_cosines_sss(rng):
    for _ in range(200):
        a, b, c = sorted([rng.randint(5, 18), rng.randint(5, 18), rng.randint(5, 18)])
        if a + b <= c + 1:
            continue
        cos_C = (a * a + b * b - c * c) / (2 * a * b)
        cos_B = (a * a + c * c - b * b) / (2 * a * c)
        C = math.degrees(math.acos(cos_C))
        B = math.degrees(math.acos(cos_B))
        A = 180 - B - C
        if not (20 < A < 120 and 20 < B < 120 and 20 < C < 120):
            continue
        try:
            Ar, Br, Cr = safe_round(A, 1, 0.03), safe_round(B, 1, 0.03), safe_round(C, 1, 0.03)
        except AssertionError:
            continue
        if abs(Ar + Br + Cr - 180) > 1e-9:
            continue
        # second route: rebuild from coordinates
        P0, P1, P2 = _tri_coords(A, c, b)
        if abs(_dist(P1, P2) - a) > 1e-9:
            continue
        a_, b_, c_ = (a, b, c) if rng.random() < 2 else (a, b, c)
        break
    else:
        raise ValueError("no draw")
    sides = [("a", a), ("b", b), ("c", c)]
    rng.shuffle(sides)
    s = dict(sides)
    # relabel so the printed triangle uses the shuffled labels; recompute angles opposite each label
    def ang(x_, y_, z_):                 # angle opposite x_
        return math.degrees(math.acos((y_ * y_ + z_ * z_ - x_ * x_) / (2 * y_ * z_)))
    aa, bb, cc = s["a"], s["b"], s["c"]
    A2, B2, C2 = ang(aa, bb, cc), ang(bb, aa, cc), ang(cc, aa, bb)
    Ar, Br, Cr = safe_round(A2, 1, 0.03), safe_round(B2, 1, 0.03), safe_round(C2, 1, 0.03)
    assert abs(Ar + Br + Cr - 180) < 1e-9
    # largest angle first, by the Law of Cosines
    ans = (f"All three sides are known and no angle is, so use the Law of Cosines: {m(r'\cos A = \dfrac{b^{2} + c^{2} - a^{2}}{2bc}')}. "
           f"{m(f'A = \\cos^{{-1}}\\left(\\dfrac{{{bb}^{{2}} + {cc}^{{2}} - {aa}^{{2}}}}{{2({bb})({cc})}}\\right) \\approx {fmt_dec(Ar, 1)}^\\circ')}. "
           f"In the same way, {m(f'B \\approx {fmt_dec(Br, 1)}^\\circ')} and {m(f'C \\approx {fmt_dec(Cr, 1)}^\\circ')}. "
           f"Check: the angles add to {m('180^\\circ')}.")
    q = (f"In triangle {m('ABC')}, {m(f'a = {aa}')}, {m(f'b = {bb}')}, and {m(f'c = {cc}')}. Find all three angles (round to the nearest tenth of a degree). "
         f"State which law you used and why.")
    return {"stem": "", "parts": [(q, ans)], "figure": None}


def law_sines_aas(rng):
    for _ in range(200):
        A, B = rng.randint(30, 85), rng.randint(30, 85)
        if A + B >= 150 or A == B:
            continue
        C = 180 - A - B
        a = rng.randint(6, 25)
        b = a * math.sin(math.radians(B)) / math.sin(math.radians(A))
        c = a * math.sin(math.radians(C)) / math.sin(math.radians(A))
        try:
            br, cr = safe_round(b, 1, 0.03), safe_round(c, 1, 0.03)
        except AssertionError:
            continue
        P0, P1, P2 = _tri_coords(A, c, b)
        assert abs(_dist(P1, P2) - a) < 1e-9 and abs(_angle_at(P0, P1, P2) - B) < 1e-9
        break
    else:
        raise ValueError("no draw")
    ans = (f"Two angles are known, so {m(f'C = 180^\\circ - {A}^\\circ - {B}^\\circ = {C}^\\circ')}. We know an angle and the side opposite it ({m('A')} and {m('a')}), "
           f"so use the Law of Sines: {m(f'b = \\dfrac{{{a}\\sin {B}^\\circ}}{{\\sin {A}^\\circ}} \\approx {fmt_dec(br, 1)}')} and "
           f"{m(f'c = \\dfrac{{{a}\\sin {C}^\\circ}}{{\\sin {A}^\\circ}} \\approx {fmt_dec(cr, 1)}')}.")
    q = (f"In triangle {m('ABC')}, {m(f'A = {A}^\\circ')}, {m(f'B = {B}^\\circ')}, and {m(f'a = {a}')}. Find {m('C')}, {m('b')}, and {m('c')} "
         f"(round sides to the nearest tenth). State which law you used and why.")
    return {"stem": "", "parts": [(q, ans)], "figure": None}


def law_cosines_sas(rng):
    for _ in range(300):
        a, b = rng.randint(5, 18), rng.randint(5, 18)
        C = rng.randint(30, 125)
        c = math.sqrt(a * a + b * b - 2 * a * b * math.cos(math.radians(C)))
        A = math.degrees(math.acos((b * b + c * c - a * a) / (2 * b * c)))
        B = 180 - A - C
        if not (15 < A < 120 and 15 < B < 120):
            continue
        try:
            cr, Ar = safe_round(c, 1, 0.03), safe_round(A, 1, 0.03)
        except AssertionError:
            continue
        P0, P1, P2 = (0.0, 0.0), (b, 0.0), (a * math.cos(math.radians(C)), a * math.sin(math.radians(C)))   # C at origin
        assert abs(_dist(P1, P2) - c) < 1e-9
        break
    else:
        raise ValueError("no draw")
    Br = safe_round(B, 1, 0.03)
    A_from_rounded_c = math.degrees(math.acos((b * b + cr * cr - a * a) / (2 * b * cr)))
    assert abs(round(A_from_rounded_c, 1) - Ar) < 1e-9, 'rounded c changes A'
    ans = (f"Two sides and the angle between them are known, so use the Law of Cosines: "
           f"{m(f'c^{{2}} = {a}^{{2}} + {b}^{{2}} - 2({a})({b})\\cos {C}^\\circ')}, so {m(f'c \\approx {fmt_dec(cr, 1)}')}. "
           f"Then {m(f'\\cos A = \\dfrac{{{b}^{{2}} + c^{{2}} - {a}^{{2}}}}{{2bc}}')} (use the unrounded value of {m('c')}) gives {m(f'A \\approx {fmt_dec(Ar, 1)}^\\circ')}, and "
           f"{m(f'B = 180^\\circ - A - C \\approx {fmt_dec(Br, 1)}^\\circ')}.")
    q = (f"In triangle {m('ABC')}, {m(f'a = {a}')}, {m(f'b = {b}')}, and {m(f'C = {C}^\\circ')}. Find {m('c')}, {m('A')}, and {m('B')} "
         f"(round the side and the angles to the nearest tenth). State which law you used first and why.")
    return {"stem": "", "parts": [(q, ans)], "figure": None}


def ambiguous_ssa(rng):
    for _ in range(300):
        A = rng.randint(25, 60)
        b = rng.randint(8, 20)
        case = rng.choice(["none", "one", "two", "two"])
        h = b * math.sin(math.radians(A))
        if case == "none":
            a = math.floor(h) - rng.choice([0, 1])
            if a < 2 or h - a < 0.5:
                continue
        elif case == "one":
            a = b + rng.randint(1, 6)
        else:
            lo, hi = math.floor(h) + 1, b - 1
            if lo > hi or lo - h < 0.3:
                continue
            a = rng.randint(lo, hi)
        sinB = b * math.sin(math.radians(A)) / a
        if case == "none":
            assert sinB > 1
            ans = (f"We know an angle and the side opposite it, so use the Law of Sines: {m(f'\\sin B = \\dfrac{{{b}\\sin {A}^\\circ}}{{{a}}} \\approx {sinB:.3f}')}. "
                   f"A sine cannot be greater than {m(1)}, so no angle {m('B')} exists. There are {m(0)} triangles.")
            break
        B1 = math.degrees(math.asin(sinB))
        C1 = 180 - A - B1
        c1 = a * math.sin(math.radians(C1)) / math.sin(math.radians(A))
        try:
            B1r, C1r, c1r = safe_round(B1, 1, 0.03), safe_round(C1, 1, 0.03), safe_round(c1, 1, 0.03)
        except AssertionError:
            continue
        P0, P1, P2 = _tri_coords(A, c1, b)
        assert abs(_dist(P1, P2) - a) < 1e-9
        if case == "one":
            assert a > b and A + B1 < 180
            ans = (f"Use the Law of Sines: {m(f'\\sin B = \\dfrac{{{b}\\sin {A}^\\circ}}{{{a}}} \\approx {sinB:.4f}')}, so {m(f'B \\approx {fmt_dec(B1r, 1)}^\\circ')}. "
                   f"The other angle with this sine, {m('180^\\circ - B')}, is too large because side {m('a')} is longer than side {m('b')} (so {m('A')} is larger than {m('B')}). "
                   f"There is one triangle: {m(f'C \\approx {fmt_dec(C1r, 1)}^\\circ')} and {m(f'c \\approx {fmt_dec(c1r, 1)}')}.")
            break
        B2 = 180 - B1
        C2 = 180 - A - B2
        if C2 <= 0.5:
            continue
        c2 = a * math.sin(math.radians(C2)) / math.sin(math.radians(A))
        try:
            B2r, C2r, c2r = safe_round(B2, 1, 0.03), safe_round(C2, 1, 0.03), safe_round(c2, 1, 0.03)
        except AssertionError:
            continue
        P0, P1, P2 = _tri_coords(A, c2, b)
        assert abs(_dist(P1, P2) - a) < 1e-9 and a < b and h < a
        ans = (f"Use the Law of Sines: {m(f'\\sin B = \\dfrac{{{b}\\sin {A}^\\circ}}{{{a}}} \\approx {sinB:.4f}')}. Since {m(f'{b}\\sin {A}^\\circ < {a} < {b}')}, there are two triangles. "
               f"Triangle 1: {m(f'B \\approx {fmt_dec(B1r, 1)}^\\circ')}, {m(f'C \\approx {fmt_dec(C1r, 1)}^\\circ')}, {m(f'c \\approx {fmt_dec(c1r, 1)}')}. "
               f"Triangle 2: {m(f'B \\approx 180^\\circ - {fmt_dec(B1r, 1)}^\\circ = {fmt_dec(B2r, 1)}^\\circ')}, {m(f'C \\approx {fmt_dec(C2r, 1)}^\\circ')}, {m(f'c \\approx {fmt_dec(c2r, 1)}')}.")
        break
    else:
        raise ValueError("no draw")
    q = (f"In triangle {m('ABC')}, {m(f'A = {A}^\\circ')}, {m(f'a = {a}')}, and {m(f'b = {b}')}. Determine whether zero, one, or two triangles exist, and solve for all valid "
         f"triangles (round angles to the nearest tenth of a degree and sides to the nearest tenth).")
    return {"stem": "", "parts": [(q, ans)], "figure": None}


# ============================================================================ TE6
def right_triangle_application(rng):
    kind = rng.choice(["ladder", "elevation", "depression"])
    if kind == "ladder":
        L = rng.randint(12, 30)
        hgt = rng.randint(int(L * 0.4), int(L * 0.95))
        if hgt >= L:
            raise ValueError("height must be less than the ladder")
        ang = math.degrees(math.asin(hgt / L))
        r = safe_round(ang, 0, 0.05)
        q = (f"A {L}-foot ladder is leaned against a wall and reaches a height of {hgt} feet. What angle does the ladder make with the ground? "
             f"(Round to the nearest degree.)")
        a = (f"The ladder is the hypotenuse and the height is the side opposite the angle, so {m(f'\\sin\\theta = \\dfrac{{{hgt}}}{{{L}}}')}. "
             f"Then {m(f'\\theta = \\sin^{{-1}}\\left(\\dfrac{{{hgt}}}{{{L}}}\\right) \\approx {int(r)}^\\circ')}.")
        check = math.sin(math.radians(ang)) * L
        assert abs(check - hgt) < 1e-9
    elif kind == "elevation":
        d = rng.randint(30, 150)
        ang = rng.randint(20, 65)
        h_ = d * math.tan(math.radians(ang))
        r = safe_round(h_, 1, 0.03)
        thing = rng.choice(["a flagpole", "a building", "a tree", "a radio tower"])
        q = (f"From a point {d} feet from the base of {thing}, the angle of elevation to its top is {ang}\u00b0. How tall is it? (Round to the nearest tenth of a foot.)")
        a = (f"The distance is the side adjacent to the angle and the height is opposite, so use the tangent: {m(f'\\tan {ang}^\\circ = \\dfrac{{h}}{{{d}}}')}. "
             f"Then {m(f'h = {d}\\tan {ang}^\\circ \\approx {fmt_dec(r, 1)}')} feet.")
        assert abs(h_ / d - math.tan(math.radians(ang))) < 1e-12
    else:
        hgt = rng.randint(40, 200)
        ang = rng.randint(15, 60)
        d = hgt / math.tan(math.radians(ang))
        r = safe_round(d, 1, 0.03)
        q = (f"From the top of a {hgt}-foot cliff, the angle of depression to a boat is {ang}\u00b0. How far is the boat from the base of the cliff? "
             f"(Round to the nearest tenth of a foot.)")
        a = (f"The angle of depression equals the angle of elevation from the boat, so {m(f'\\tan {ang}^\\circ = \\dfrac{{{hgt}}}{{d}}')}. "
             f"Then {m(f'd = \\dfrac{{{hgt}}}{{\\tan {ang}^\\circ}} \\approx {fmt_dec(r, 1)}')} feet.")
        assert abs(hgt / d - math.tan(math.radians(ang))) < 1e-12
    return {"stem": "", "parts": [(q, a)], "figure": None}


def law_of_cosines_application(rng):
    for _ in range(100):
        d1, d2 = rng.randint(3, 12), rng.randint(3, 12)
        ang = rng.randint(25, 140)
        dist = math.sqrt(d1 * d1 + d2 * d2 - 2 * d1 * d2 * math.cos(math.radians(ang)))
        try:
            r = safe_round(dist, 1, 0.03)
        except AssertionError:
            continue
        P = (d1, 0.0)
        Q = (d2 * math.cos(math.radians(ang)), d2 * math.sin(math.radians(ang)))
        assert abs(_dist(P, Q) - dist) < 1e-9
        break
    else:
        raise ValueError("no draw")
    who = rng.choice([
        ("hikers", "hiker", "walks", "miles", "mile", "leave the same trailhead on straight paths"),
        ("boats", "boat", "travels", "miles", "mile", "leave the same dock on straight courses"),
        ("joggers", "jogger", "runs", "kilometers", "kilometer", "leave the same corner on straight streets"),
    ])
    pl, sg, verb, unit, unit1, leave = who
    q = (f"Two {pl} {leave} that form an angle of {ang}°. One {sg} {verb} {d1} {unit} and the other {sg} {verb} {d2} {unit}. "
         f"How far apart are the {pl}? (Round to the nearest tenth of a {unit1}.)")
    a = (f"The two paths and the line between the {pl} form a triangle with two known sides and the angle between them, so use the Law of Cosines: "
         f"{m(f'd^{{2}} = {d1}^{{2}} + {d2}^{{2}} - 2({d1})({d2})\\cos {ang}^\\circ')}. Then {m(f'd \\approx {fmt_dec(r, 1)}')} {unit}.")
    return {"stem": "", "parts": [(q, a)], "figure": None}


def law_of_sines_application(rng):
    for _ in range(100):
        base = rng.randint(4, 15)
        A, B = rng.randint(35, 80), rng.randint(35, 80)
        if A + B >= 150:
            continue
        C = 180 - A - B
        d1 = base * math.sin(math.radians(B)) / math.sin(math.radians(C))          # from observer A to the object
        d2 = base * math.sin(math.radians(A)) / math.sin(math.radians(C))
        try:
            r1, r2 = safe_round(d1, 1, 0.03), safe_round(d2, 1, 0.03)
        except AssertionError:
            continue
        P0, P1, P2 = _tri_coords(A, base, d1)
        assert abs(_angle_at(P0, P1, P2) - B) < 1e-9 and abs(_dist(P1, P2) - d2) < 1e-9
        break
    else:
        raise ValueError("no draw")
    thing = rng.choice(["boat", "hot-air balloon", "ship", "campfire"])
    q = (f"Two observers stand {base} miles apart and both can see a {thing}. The angle between the line joining the observers and the line of sight to the {thing} "
         f"is {A}° at the first observer and {B}° at the second observer. How far is the {thing} from the first observer? (Round to the nearest tenth of a mile.)")
    a_ = (f"The angle at the {thing} is {m(f'C = 180^\\circ - {A}^\\circ - {B}^\\circ = {C}^\\circ')}. The side from the first observer to the {thing} is opposite the second observer's angle, "
          f"so use the Law of Sines: {m(f'\\dfrac{{d}}{{\\sin {B}^\\circ}} = \\dfrac{{{base}}}{{\\sin {C}^\\circ}}')}. Then {m(f'd = \\dfrac{{{base}\\sin {B}^\\circ}}{{\\sin {C}^\\circ}} \\approx {fmt_dec(r1, 1)}')} miles.")
    q2 = f"How far is the {thing} from the second observer? (Round to the nearest tenth of a mile.)"
    a2 = f"The side from the second observer is opposite the first observer's angle: {m(f'd = \\dfrac{{{base}\\sin {A}^\\circ}}{{\\sin {C}^\\circ}} \\approx {fmt_dec(r2, 1)}')} miles."
    return {"stem": "", "parts": [(q, a_), (q2, a2)], "figure": None}


TEMPLATES = {
    "sum_difference_exact": sum_difference_exact,
    "pythagorean_quadrant": pythagorean_quadrant,
    "power_reduce": power_reduce,
    "power_reduce_fourth": power_reduce_fourth,
    "double_angle_given": double_angle_given,
    "half_angle_exact": half_angle_exact,
    "verify_identity_basic": verify_identity_basic,
    "verify_identity_fractions": verify_identity_fractions,
    "trig_general_solution": trig_general_solution,
    "trig_squared_interval": trig_squared_interval,
    "trig_multiple_angle": trig_multiple_angle,
    "trig_quadratic_form": trig_quadratic_form,
    "right_triangle_angle_given": right_triangle_angle_given,
    "right_triangle_sides_given": right_triangle_sides_given,
    "law_cosines_sss": law_cosines_sss,
    "law_sines_aas": law_sines_aas,
    "law_cosines_sas": law_cosines_sas,
    "ambiguous_ssa": ambiguous_ssa,
    "right_triangle_application": right_triangle_application,
    "law_of_cosines_application": law_of_cosines_application,
    "law_of_sines_application": law_of_sines_application,
}
