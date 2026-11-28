"""PR3-PR9 (chapter 5, Final only): polynomial and rational functions and inequalities.

Item types follow the kinds of questions on Dr. Romero's exam bank (zeros and multiplicities, long division,
complex and irrational zeros, rational equations, rational functions' features, quadratic and rational
inequalities). Parameters are drawn fresh; nothing is copied from a real quiz or exam.
"""
import math
import random

import sympy as sp

from common import x, m
from util import lin, sgn, tex, frac_tex, iv_tex

NAMES = ["f", "g"]


def _coef(a):
    return "" if a == 1 else "-" if a == -1 else str(a)


def _nonzero(rng, lo, hi, avoid=()):
    return rng.choice([v for v in range(lo, hi + 1) if v != 0 and v not in avoid])


def _poly_tex(e):
    return sp.latex(sp.expand(e), order="lex")


# ============================================================================ PR3
def _factored(a, factors):
    return _coef(a) + "".join(lin(r, mm) for r, mm in factors)


def _end_behavior(a, deg, F="f"):
    """(words, symbols) for the ends of a polynomial with leading coefficient a and degree deg."""
    left_up = (a > 0) == (deg % 2 == 0)
    right_up = a > 0
    words = f"The graph {'rises' if left_up else 'falls'} to the left and {'rises' if right_up else 'falls'} to the right."
    sym = (rf"As {m('x \\to -\\infty')}, {m(F + '(x) \\to ' + ('\\infty' if left_up else '-\\infty'))}; "
           rf"as {m('x \\to \\infty')}, {m(F + '(x) \\to ' + ('\\infty' if right_up else '-\\infty'))}.")
    return words, sym, left_up, right_up


def poly_zeros_multiplicity(rng):
    F = rng.choice(NAMES)
    k = rng.choice([2, 2, 3])
    rs = sorted(rng.sample([r for r in range(-5, 6) if r != 0], k))
    ms = [rng.choice([1, 2, 3]) for _ in rs] if k == 2 else [rng.choice([1, 2]) for _ in rs]
    deg = sum(ms)
    assert 3 <= deg <= 6 and max(ms) >= 2
    a = rng.choice([-3, -2, -1, 1, 2, 3])
    fac = list(zip(rs, ms))
    expr = a * sp.prod([(x - r) ** mm for r, mm in fac])
    zeros = "; ".join(f"{m(f'x = {r}')} (multiplicity {m(mm)})" for r, mm in fac)
    y0 = sp.expand(expr).subs(x, 0)
    f0 = r"\cdot ".join([_coef(a) if abs(a) != 1 else ("-1" if a == -1 else "1")] +
                        [f"({-r})" + (f"^{{{mm}}}" if mm != 1 else "") for r, mm in fac])
    words, sym, lu, ru = _end_behavior(a, deg, F)
    # second routes: numeric ends and the constant term
    assert (expr.subs(x, -1000) > 0) == lu and (expr.subs(x, 1000) > 0) == ru
    assert sp.Poly(expr, x).degree() == deg and sp.Poly(expr, x).LC() == a
    assert sorted(sp.roots(sp.Poly(expr, x)).items()) == sorted((r, mm) for r, mm in fac)
    lead_word = "positive" if a > 0 else "negative"
    parts = [
        (f"Find the zeros of {m(F + '(x)')}, with their multiplicities.", zeros + "."),
        (f"Find the {m('y')}-intercept.", f"{m(F + '(0) = ' + f0 + ' = ' + str(y0))}, so the {m('y')}-intercept is {m(f'(0, {y0})')}."),
        ("Describe the end behavior of the graph.",
         f"The degree is {m(deg)} ({'even' if deg % 2 == 0 else 'odd'}) and the leading coefficient {m(a)} is {lead_word}. {words} {sym}"),
    ]
    return {"stem": f"Let {m(F + '(x) = ' + _factored(a, fac))}.", "parts": parts, "figure": None}


def poly_graph_behavior(rng):
    """Assessment: includes a zero at x = 0, cross or touch at each zero, and the end behavior."""
    F = rng.choice(NAMES)
    p0 = rng.choice([1, 2, 3])                      # multiplicity of the zero at 0
    others = sorted(rng.sample([r for r in range(-4, 5) if r != 0], 2))
    ms = [rng.choice([1, 2, 3]), rng.choice([1, 2])]
    fac = [(0, p0)] + list(zip(others, ms))
    fac.sort()
    deg = sum(mm for _, mm in fac)
    assert 4 <= deg <= 7 and len({mm % 2 for _, mm in fac}) == 2  # at least one crossing and one touching zero
    a = rng.choice([-2, -1, 1, 2])
    expr = a * sp.prod([(x - r) ** mm for r, mm in fac])
    rows = []
    for r, mm in fac:
        if mm % 2 == 0:
            beh = "touches the " + m("x") + "-axis and turns around (even multiplicity)"
        elif mm == 1:
            beh = "crosses the " + m("x") + "-axis (odd multiplicity)"
        else:
            beh = "crosses the " + m("x") + "-axis and flattens near the zero (odd multiplicity greater than " + m(1) + ")"
        rows.append(f"At {m(f'x = {r}')} (multiplicity {m(mm)}) the graph {beh}.")
    words, sym, lu, ru = _end_behavior(a, deg, F)
    assert (expr.subs(x, -1000) > 0) == lu and (expr.subs(x, 1000) > 0) == ru
    assert expr.subs(x, 0) == 0
    # numeric sign change test at each zero (independent of the multiplicity rule)
    for r, mm in fac:
        left, right = expr.subs(x, r - sp.Rational(1, 100)), expr.subs(x, r + sp.Rational(1, 100))
        assert (left * right < 0) == (mm % 2 == 1)
    parts = [
        (f"State the degree of {m(F)} and its leading coefficient.", f"Degree {m(deg)}; leading coefficient {m(a)}."),
        ("At each zero, does the graph cross the " + m("x") + "-axis or touch it and turn around? Explain.", " ".join(rows)),
        ("Describe the end behavior.", f"{words} {sym}"),
        (f"Find the {m('y')}-intercept.", f"{m(F + '(0) = 0')} because {m('x')} is a factor, so the {m('y')}-intercept is {m('(0, 0)')}."),
    ]
    return {"stem": f"Let {m(F + '(x) = ' + _factored(a, fac))}.", "parts": parts, "figure": None}


# ============================================================================ PR4
def _plus(r_poly, rt):
    """' + 3' / ' - 3' for a constant remainder, ' + (5 - x)' for a polynomial one."""
    r_poly = sp.sympify(r_poly)
    if r_poly.is_number:
        return f" - {abs(r_poly)}" if r_poly < 0 else f" + {r_poly}"
    return f" + ({rt})"


def _div_answer(F, dividend, divisor_tex, q, r_poly, variable_r=False, excluded=None):
    """Answer text for a division. If `excluded` is given, F(x) is the *fraction* dividend/divisor (undefined at
    x = excluded), so F(x) = q + r/divisor; the form 'divisor times quotient plus remainder' is then stated for the numerator."""
    qt, rt = tex(q), tex(r_poly)
    if excluded is not None:
        ne = m(rf"x \ne {excluded}")
        num_t = _poly_tex(dividend)
        if r_poly == 0:
            return (f"Quotient {m('q(x) = ' + qt)}, remainder {m('0')}. Because the remainder is {m('0')}, {m(divisor_tex)} divides evenly into the numerator "
                    f"{m(num_t)}, so {m(f'{F}(x) = ' + qt)} for {ne}.")
        frac = rf"\dfrac{{{abs(r_poly)}}}{{{divisor_tex}}}"
        sgn = "-" if r_poly < 0 else "+"
        return (f"Quotient {m('q(x) = ' + qt)}, remainder {m('r(x) = ' + rt)}. In other words, {m(f'{F}(x) = {qt} {sgn} ' + frac)}, with {ne}. "
                f"Multiplying by the divisor gives the same fact for the numerator: {m(f'{num_t} = ({divisor_tex})({qt})' + _plus(r_poly, rt))}.")
    if r_poly == 0:
        return (f"Quotient {m('q(x) = ' + qt)}, remainder {m('0')}. Because the remainder is {m('0')}, "
                f"{m(divisor_tex)} divides evenly into {m(F + '(x)')}.")
    return (f"Quotient {m('q(x) = ' + qt)}, remainder {m('r(x) = ' + rt)}. In other words, "
            f"{m(f'{F}(x) = ({divisor_tex})({qt})' + _plus(r_poly, rt))}.")


def poly_long_division(rng):
    F = rng.choice(NAMES)
    c = rng.choice([-4, -3, -2, -1, 1, 2, 3, 4])
    q = rng.choice([1, 1, 2, 3]) * x ** 2 + rng.randint(-5, 5) * x + rng.randint(-6, 6)
    r = 0 if rng.random() < 0.2 else _nonzero(rng, -9, 9)
    d = x - c
    dividend = sp.expand(q * d + r)
    assert sp.degree(dividend, x) == 3 and max(abs(co) for co in sp.Poly(dividend, x).all_coeffs()) <= 25
    qq, rr = sp.div(dividend, d, x)
    assert sp.expand(qq - q) == 0 and rr == r and dividend.subs(x, c) == r  # division algorithm and remainder theorem
    divisor_tex = f"x - {c}" if c > 0 else f"x + {-c}"
    q_txt = f"Use long division to find the quotient and remainder for {m(F + '(x) = \\dfrac{' + _poly_tex(dividend) + '}{' + divisor_tex + '}')}."
    return {"stem": "", "parts": [(q_txt, _div_answer(F, dividend, divisor_tex, q, r, excluded=c))], "figure": None}


def poly_long_division_quadratic(rng):
    """Assessment: a quadratic divisor, then the remainder theorem for a linear divisor."""
    F = rng.choice(NAMES)
    pp, qq_ = rng.randint(-3, 3), _nonzero(rng, -4, 4)
    d = x ** 2 + pp * x + qq_
    quo = rng.choice([1, 2]) * x + rng.randint(-4, 4)
    rem = _nonzero(rng, -3, 3) * x + rng.randint(-5, 5)
    dividend = sp.expand(quo * d + rem)
    assert sp.degree(dividend, x) == 3
    q, r = sp.div(dividend, d, x)
    assert sp.expand(q - quo) == 0 and sp.expand(r - rem) == 0
    c = rng.choice([-3, -2, -1, 1, 2, 3])
    val = dividend.subs(x, c)
    lin_q, lin_r = sp.div(dividend, x - c, x)
    assert lin_r == val  # remainder theorem
    divisor_tex = tex(d)
    lin_tex = f"x - {c}" if c > 0 else f"x + {-c}"
    parts = [
        (f"Use long division to divide {m(F + '(x) = ' + _poly_tex(dividend))} by {m(divisor_tex)}. Give the quotient and the remainder.",
         _div_answer(F, dividend, divisor_tex, quo, rem)),
        (f"Use the remainder theorem to find the remainder when {m(F + '(x)')} is divided by {m(lin_tex)}, without dividing.",
         f"The remainder is {m(F + f'({c})')}. {m(F + f'({c}) = ' + str(val))}, so the remainder is {m(val)}."),
    ]
    return {"stem": "", "parts": parts, "figure": None}


# ============================================================================ PR5
def _isq(n):
    return int(math.isqrt(n)) ** 2 == n


def _im(t):
    """Imaginary part text for t = sqrt(k): '3i' or 'i\\sqrt{5}'."""
    k = round(t * t)                      # t = sqrt(k) as a float: t * t can be 2.9999999999999996
    return f"{int(t)}i" if t == int(t) else f"i\\sqrt{{{k}}}"


def _rad(k):
    return f"{int(math.isqrt(k))}" if _isq(k) else f"\\sqrt{{{k}}}"


def _xminus(s, tail):
    """The factor (x - s - tail) written with the constant first: s may be negative or zero."""
    return "(x" + (f" - {s}" if s > 0 else f" + {-s}" if s < 0 else "") + tail + ")"


def zeros_complex_factor(rng):
    F = rng.choice(NAMES)
    r = _nonzero(rng, -4, 4)
    mm = rng.choice([1, 1, 2])
    if rng.random() < 0.5:
        s, k = 0, rng.choice([1, 2, 3, 4, 5, 6, 9, 16])
        quad = x ** 2 + k
    else:
        s, k = rng.choice([-3, -2, -1, 1, 2, 3]), rng.choice([1, 2, 3, 4, 5])  # roots s +- sqrt(k) i
        quad = sp.expand((x - s) ** 2 + k)
    expr = sp.expand((x - r) ** mm * quad)
    shown = lin(r, mm) + "(" + _poly_tex(quad) + ")"
    t = math.sqrt(k)
    zi = f"{'' if s == 0 else str(s)}" + (f"\\pm {_im(t)}" if s == 0 else f" \\pm {_im(t)}")
    zeros_txt = f"{m(f'x = {r}')} (multiplicity {m(mm)}) and {m('x = ' + zi)}."
    factors = lin(r, mm) + _xminus(s, " - " + _im(t)) + _xminus(s, " + " + _im(t))
    # second routes: expand the linear factors back; read the roots from SymPy
    z1, z2 = s + sp.I * sp.sqrt(k), s - sp.I * sp.sqrt(k)
    assert sp.expand((x - r) ** mm * (x - z1) * (x - z2) - expr) == 0
    rts = sp.roots(sp.Poly(expr, x), extension=sp.I)
    assert rts.get(r) == mm and rts.get(z1) == 1 and rts.get(z2) == 1
    parts = [(f"Find all zeros of {m(F + '(x) = ' + shown)}.", zeros_txt),
             (f"Express {m(F + '(x)')} as a product of linear factors.", m(f"{F}(x) = " + factors) + ".")]
    return {"stem": "", "parts": parts, "figure": None}


def zeros_irrational_factor(rng):
    F = rng.choice(NAMES)
    r = _nonzero(rng, -4, 4)
    s = rng.choice([-3, -2, -1, 1, 2, 3])
    k = rng.choice([2, 3, 5, 6, 7, 10, 11])
    quad = sp.expand((x - s) ** 2 - k)
    expr = sp.expand((x - r) * quad)
    shown = lin(r) + "(" + _poly_tex(quad) + ")"
    z1, z2 = s + sp.sqrt(k), s - sp.sqrt(k)
    assert sp.expand((x - r) * (x - z1) * (x - z2) - expr) == 0 and sp.discriminant(quad, x) == 4 * k
    zeros_txt = f"{m(f'x = {r}')} and {m(f'x = {s} \\pm \\sqrt{{{k}}}')}."
    factors = lin(r) + _xminus(s, f" - \\sqrt{{{k}}}") + _xminus(s, f" + \\sqrt{{{k}}}")
    parts = [(f"Find all zeros of {m(F + '(x) = ' + shown)}. Give exact values.", zeros_txt),
             (f"Express {m(F + '(x)')} as a product of linear factors.", m(f"{F}(x) = " + factors) + ".")]
    return {"stem": "", "parts": parts, "figure": None}


def zeros_from_one_zero(rng):
    """Assessment: a cubic, one zero given. Divide, then solve the quadratic (complex or irrational)."""
    F = rng.choice(NAMES)
    r = _nonzero(rng, -3, 3)
    if rng.random() < 0.5:
        s, k = rng.choice([-2, -1, 1, 2]), rng.choice([1, 2, 3, 4])
        quad = sp.expand((x - s) ** 2 + k)
        z_txt, kind = f"{s} \\pm {_im(math.sqrt(k))}", "complex"
        zeros = [s + sp.I * sp.sqrt(k), s - sp.I * sp.sqrt(k)]
        lin_f = _xminus(s, " - " + _im(math.sqrt(k))) + _xminus(s, " + " + _im(math.sqrt(k)))
    else:
        s, k = rng.choice([-2, -1, 1, 2]), rng.choice([2, 3, 5, 6, 7])
        quad = sp.expand((x - s) ** 2 - k)
        z_txt, kind = f"{s} \\pm \\sqrt{{{k}}}", "irrational"
        zeros = [s + sp.sqrt(k), s - sp.sqrt(k)]
        lin_f = _xminus(s, f" - \\sqrt{{{k}}}") + _xminus(s, f" + \\sqrt{{{k}}}")
    expr = sp.expand((x - r) * quad)
    assert max(abs(co) for co in sp.Poly(expr, x).all_coeffs()) <= 30
    q, rem = sp.div(expr, x - r, x)
    assert rem == 0 and sp.expand(q - quad) == 0
    assert sp.expand((x - r) * (x - zeros[0]) * (x - zeros[1]) - expr) == 0
    rts = sp.roots(sp.Poly(expr, x), extension=sp.I)
    assert set(rts) == {r, *zeros}
    parts = [
        (f"Use long division to divide {m(F + '(x) = ' + _poly_tex(expr))} by {m(lin(r)[1:-1])}.",
         f"Quotient {m('q(x) = ' + tex(quad))}, remainder {m('0')}."),
        (f"Find all zeros of {m(F)}.", f"{m(f'x = {r}')} and, from the quadratic formula on {m(tex(quad) + ' = 0')}, {m('x = ' + z_txt)} ({kind})."),
        (f"Write {m(F + '(x)')} as a product of linear factors.", m(f"{F}(x) = " + lin(r) + lin_f) + "."),
    ]
    return {"stem": f"The number {m(r)} is a zero of {m(F)}.", "parts": parts, "figure": None}


# ============================================================================ PR6
def _x_text(q):
    return frac_tex(q)


def _check_sol(lhs, rhs, sol):
    """Substitute the claimed solution back into the original equation."""
    return sp.simplify(lhs.subs(x, sol) - rhs.subs(x, sol)) == 0


def rational_eq_single(rng):
    """Three one-denominator or two-denominator equations that clear to a linear equation."""
    p = _nonzero(rng, -5, 5)
    a_, c_ = rng.randint(2, 9), rng.randint(2, 6)
    s1 = sp.Rational(p) + sp.Rational(a_, c_)
    lhs1, rhs1 = a_ / (x - p), sp.Integer(c_)
    assert _check_sol(lhs1, rhs1, s1) and s1 != p
    # (b) a/(x+u) = b/(x-v)
    u, v = _nonzero(rng, -5, 5), _nonzero(rng, -5, 5)
    ab = rng.sample(range(2, 9), 2)
    a2, b2 = ab
    s2 = sp.Rational(a2 * v + b2 * u, a2 - b2)
    lhs2, rhs2 = a2 / (x + u), b2 / (x - v)
    assert _check_sol(lhs2, rhs2, s2) and s2 not in (-u, v)
    # (c) a/x + b = c
    a3, b3, c3 = rng.randint(2, 8), rng.randint(1, 5), rng.randint(6, 12)
    s3 = sp.Rational(a3, c3 - b3)
    assert _check_sol(a3 / x + b3, sp.Integer(c3), s3) and s3 != 0

    def eq_tex(l, r_):
        return tex(l) + " = " + tex(r_)

    def frac_expr(num_, den_):
        return rf"\dfrac{{{num_}}}{{{den_}}}"
    d1 = f"x - {p}" if p > 0 else f"x + {-p}"
    d2a = f"x + {u}" if u > 0 else f"x - {-u}"
    d2b = f"x - {v}" if v > 0 else f"x + {-v}"
    eqs = [
        (f"Solve {m(frac_expr(a_, d1) + f' = {c_}')}. Give the exact solution.",
         f"Multiply both sides by {m(d1)}: {m(f'{a_} = {c_}({d1})')}, so {m('x = ' + _x_text(s1))}. "
         f"Check: {m(d1)} is not zero at this value, so it is valid."),
        (f"Solve {m(frac_expr(a2, d2a) + ' = ' + frac_expr(b2, d2b))}. Give the exact solution.",
         f"Cross-multiply: {m(f'{a2}({d2b}) = {b2}({d2a})')}, so {m('x = ' + _x_text(s2))}. "
         f"Neither denominator is zero at this value, so it is valid."),
        (f"Solve {m(frac_expr(a3, 'x') + f' + {b3} = {c3}')}. Give the exact solution.",
         f"Subtract {m(b3)} from both sides: {m(frac_expr(a3, 'x') + f' = {c3 - b3}')}. So {m(f'{a3} = {_coef(c3 - b3)}x')} and {m('x = ' + _x_text(s3))}."),
    ]
    return {"stem": "", "parts": eqs, "figure": None}


def rational_eq_denominators(rng):
    """a/(x-p) + b/(x+p) = c/(x^2 - p^2): the common denominator is the product."""
    for _ in range(50):
        p = rng.randint(1, 4)
        a_, b_, c_ = rng.randint(1, 6), rng.randint(1, 6), rng.randint(-8, 8)
        if a_ + b_ == 0 or c_ == 0:
            continue
        s = sp.Rational(c_ - p * (a_ - b_), a_ + b_)
        if s not in (p, -p):
            break
    else:
        raise ValueError("no draw")
    lhs = a_ / (x - p) + b_ / (x + p)
    rhs = c_ / (x ** 2 - p ** 2)
    assert _check_sol(lhs, rhs, s) and s not in (p, -p)
    assert (a_, b_, p, c_) not in [(3, 2, 1, 1)]
    stem_eq = rf"\dfrac{{{a_}}}{{x - {p}}} + \dfrac{{{b_}}}{{x + {p}}} = \dfrac{{{c_}}}{{x^{{2}} - {p * p}}}"
    ans = (f"The common denominator is {m('(x - ' + str(p) + ')(x + ' + str(p) + ')')}. Multiplying through gives "
           f"{m(f'{a_}(x + {p}) + {b_}(x - {p}) = {c_}')}, so {m(f'{_coef(a_ + b_)}x = {c_ - p * (a_ - b_)}')} and {m('x = ' + _x_text(s))}. "
           f"This is not {m(p)} or {m(-p)}, so it is valid.")
    return {"stem": "", "parts": [(f"Solve {m(stem_eq)}. Give the exact solution.", ans)], "figure": None}


def rational_zero_numerator(rng):
    r, s = rng.sample([v for v in range(-6, 7) if v != 0], 2)
    num = sp.expand((x - r) * (x - s))
    expr = num / (x - r)
    assert sp.cancel(expr) == x - s
    d = f"x - {r}" if r > 0 else f"x + {-r}"
    eq = rf"\dfrac{{{_poly_tex(num)}}}{{{d}}} = 0"
    parts = [
        (f"Solve {m(eq)}.",
         f"Factor the numerator: {m(f'({lin(r)[1:-1]}){lin(s)}')}, so the numerator is {m(0)} at {m(f'x = {r}')} and {m(f'x = {s}')}. "
         f"But {m(f'x = {r}')} makes the denominator {m(0)}. The only solution is {m(f'x = {s}')}."),
        (f"Explain why {m(f'x = {r}')} is not a valid solution, even though it is a root of the numerator.",
         f"At {m(f'x = {r}')} the denominator {m(d)} equals {m(0)}, and division by {m(0)} is undefined. "
         f"A value that makes the original expression undefined cannot be a solution."),
    ]
    return {"stem": "", "parts": parts, "figure": None}


def rational_no_solution(rng):
    """Assessment: clearing denominators produces a value that is not allowed."""
    p = _nonzero(rng, -5, 5)
    c = rng.choice([-3, -2, 2, 3, 4])
    d = f"x - {p}" if p > 0 else f"x + {-p}"
    lhs = x / (x - p)
    rhs = p / (x - p) + c
    # route 2: the only candidate from the cleared equation is p, which is excluded
    cleared = sp.expand(x - (p + c * (x - p)))
    assert sp.solve(cleared, x) == [p]
    assert sp.simplify(lhs - rhs - (1 - c)) == 0 and c != 1   # the two sides differ by a nonzero constant wherever defined
    sg = "+" if c > 0 else "-"
    eq = rf"\dfrac{{x}}{{{d}}} = \dfrac{{{p}}}{{{d}}} {sg} {abs(c)}"
    ans = (f"Multiply both sides by {m(d)}: {m(f'x = {p} {sg} {abs(c)}({d})')}. This gives {m(f'{_coef(1 - c)}x = {p * (1 - c)}')}, so {m(f'x = {p}')}. "
           f"But {m(f'x = {p}')} makes the denominator {m(0)}, so it is extraneous. The equation has no solution.")
    parts = [(f"Solve {m(eq)}. Check each result in the original equation.", ans),
             ("How can you tell, before solving, that the value " + m(f"x = {p}") + " can never be a solution?",
              f"It makes the denominator {m(d)} equal to {m(0)}, so the original equation is undefined there. "
              f"List the excluded values first and compare your answer with them.")]
    return {"stem": "", "parts": parts, "figure": None}


# ============================================================================ PR7
def _features(num_, den_):
    """Independent description of num/den from SymPy's polynomial algebra (the factors are NOT auto-cancelled)."""
    num_, den_ = sp.expand(num_), sp.expand(den_)
    g = sp.gcd(sp.Poly(num_, x), sp.Poly(den_, x)).as_expr()
    holes = sorted(sp.roots(sp.Poly(g, x)).keys(), key=float) if sp.degree(g, x) > 0 else []
    red = sp.cancel(num_ / den_)
    rn, rd = sp.fraction(red)
    zeros = sorted([z for z in sp.roots(sp.Poly(rn, x)).keys()], key=float)
    vas = sorted(sp.roots(sp.Poly(rd, x)).keys(), key=float)
    ha = sp.limit(red, x, sp.oo)
    return holes, red, zeros, vas, ha


def rational_hole_features(rng):
    F = rng.choice(NAMES)
    a_, b_, c_ = rng.sample([v for v in range(-6, 7) if v != 0], 3)
    k = rng.choice([1, 1, 2, 3, -1, -2])
    num_, den_ = k * (x - a_) * (x - b_), (x - a_) * (x - c_)
    holes, red, zeros, vas, ha = _features(num_, den_)
    hole_y = sp.Rational(k * (a_ - b_), a_ - c_)
    yint = sp.Rational(k * b_, c_)
    assert holes == [a_] and zeros == [b_] and vas == [c_] and ha == k
    assert red.subs(x, a_) == hole_y and sp.Rational(num_.subs(x, 0), den_.subs(x, 0)) == yint
    rd_left = sp.cancel(den_ / (x - a_))                    # what is left of the denominator after the common factor is canceled
    assert rd_left == x - c_ and rd_left.subs(x, a_) != 0   # not zero at a: the factor canceled completely, so a is a hole and not an asymptote
    unfactored = rng.random() < 0.5
    cf = _coef(k)
    if unfactored:
        num_t = _poly_tex(k * (x - a_) * (x - b_))
        den_t = _poly_tex((x - a_) * (x - c_))
        shown = rf"\dfrac{{{num_t}}}{{{den_t}}}"
    else:
        shown = rf"\dfrac{{{cf}{lin(a_)}{lin(b_)}}}{{{lin(a_)}{lin(c_)}}}"
    parts = [
        ("Find any holes.", f"{m(f'x = {a_}')} is a factor of both the numerator and the denominator. After canceling it, the denominator that is left is "
                            f"{m(_poly_tex(rd_left))}, which is not {m(0)} at {m(f'x = {a_}')}, so the factor canceled completely and there is a hole at {m(f'x = {a_}')}. "
                            f"After canceling, the value there is {m(f'y = ' + frac_tex(hole_y))}, so the hole is at {m(f'({a_}, {frac_tex(hole_y)})')}."),
        ("Find the zeros.", f"The zero is {m(f'x = {b_}')} (the other numerator zero, {m(f'x = {a_}')}, is a hole, not a zero)."),
        ("Find the vertical asymptote.", f"{m(f'x = {c_}')}."),
        ("Find the horizontal asymptote.", f"The degrees are equal, so the horizontal asymptote is the ratio of the leading coefficients: {m(f'y = {k}')}."),
        (f"Find the {m('y')}-intercept.", f"{m(f'{F}(0) = ' + frac_tex(yint))}, so the {m('y')}-intercept is {m(f'(0, {frac_tex(yint)})')}."),
    ]
    stem = (f"Consider {m(F + '(x) = ' + shown)}. Find (a) any holes, (b) the zeros, (c) the vertical asymptote, "
            f"(d) the horizontal asymptote, and (e) the {m('y')}-intercept.")
    if unfactored:
        stem += " Start by factoring."
    return {"stem": stem, "parts": parts, "figure": None}


def rational_no_hole_features(rng):
    """No common factors: two vertical asymptotes; the horizontal asymptote depends on the degrees."""
    F = rng.choice(NAMES)
    c_, d_ = rng.sample([v for v in range(-5, 6) if v != 0], 2)
    deg_n = rng.choice([1, 2])
    zs = rng.sample([v for v in range(-6, 7) if v not in (c_, d_)], deg_n)
    k = rng.choice([1, 2, 3, -1, -2]) if deg_n == 2 else rng.choice([1, 2, 3, -1, -2, 4])
    e = rng.choice([1, 1, 2])
    num_ = k * sp.prod([(x - z) for z in zs])
    den_ = e * (x - c_) * (x - d_)
    holes, red, zeros, vas, ha = _features(num_, den_)
    assert holes == [] and sorted(zeros) == sorted(zs) and vas == sorted([c_, d_])
    ha_val = sp.Rational(k, e) if deg_n == 2 else 0
    assert ha == ha_val
    yint = sp.Rational(sp.expand(num_).subs(x, 0), sp.expand(den_).subs(x, 0))
    shown = rf"\dfrac{{{_coef(k)}{''.join(lin(z) for z in zs)}}}{{{_coef(e)}{lin(c_)}{lin(d_)}}}"
    ha_why = ("The numerator has the smaller degree, so the horizontal asymptote is " + m("y = 0") + "."
              if deg_n == 1 else
              f"The degrees are equal, so the horizontal asymptote is the ratio of the leading coefficients: {m('y = ' + frac_tex(ha_val))}.")
    parts = [
        ("Find any holes.", "There are no common factors, so there are no holes."),
        ("Find the zeros.", " and ".join(m(f"x = {z}") for z in sorted(zs)) + "."),
        ("Find the vertical asymptotes.", " and ".join(m(f"x = {z}") for z in sorted([c_, d_])) + "."),
        ("Find the horizontal asymptote.", ha_why),
        (f"Find the {m('y')}-intercept.", f"{m(f'{F}(0) = ' + frac_tex(yint))}, so the {m('y')}-intercept is {m(f'(0, {frac_tex(yint)})')}."),
    ]
    stem = (f"Consider {m(F + '(x) = ' + shown)}. Find (a) any holes, (b) the zeros, (c) the vertical asymptotes, "
            f"(d) the horizontal asymptote, and (e) the {m('y')}-intercept.")
    return {"stem": stem, "parts": parts, "figure": None}


# ============================================================================ PR8
OPS = {"<": (sp.StrictLessThan, "<"), "<=": (sp.LessThan, r"\le"), ">": (sp.StrictGreaterThan, ">"), ">=": (sp.GreaterThan, r"\ge")}


def _solve_ineq(expr, op):
    cls = OPS[op][0]
    S = sp.solveset(cls(expr, 0), x, sp.S.Reals)
    return S


def _sample_check(expr, op, S):
    """Test many points: membership in S must equal the truth of the inequality (independent of solveset)."""
    cls = OPS[op][0]
    pts = [sp.Rational(n, 4) for n in range(-60, 61)]
    for t in pts:
        try:
            val = expr.subs(x, t)
        except ZeroDivisionError:
            continue
        if val.has(sp.zoo) or val.has(sp.nan):
            assert not S.contains(t)
            continue
        truth = bool(cls(val, 0))
        assert truth == bool(S.contains(t)), (t, val)


def _quad_factors(rng):
    m1, m2 = rng.choice([1, 1, 1, 2]), rng.choice([1, 1, 2])
    n1, n2 = rng.randint(-6, 6), rng.randint(-6, 6)
    assert n1 != 0 and n2 != 0 and sp.Rational(n1, m1) != sp.Rational(n2, m2)
    return m1, n1, m2, n2


def quad_inequality(rng):
    m1, n1, m2, n2 = _quad_factors(rng)
    quad = sp.expand((m1 * x - n1) * (m2 * x - n2))
    if rng.random() < 0.25:
        quad = -quad
    op = rng.choice(list(OPS))
    S = _solve_ineq(quad, op)
    assert S not in (sp.S.EmptySet, sp.S.Reals)
    _sample_check(quad, op, S)
    crit = sorted([sp.Rational(n1, m1), sp.Rational(n2, m2)])
    roots_txt = " and ".join(m("x = " + frac_tex(c)) for c in crit)
    inclusive = op in ("<=", ">=")
    ans = (f"Solve {m(tex(quad) + ' = 0')}: {roots_txt}. These split the number line into three intervals. "
           f"Test a point in each interval to see where {m(tex(quad) + ' ' + OPS[op][1] + ' 0')} is true. "
           f"{'The endpoints are included because the inequality is not strict.' if inclusive else 'The endpoints are not included because the inequality is strict.'} "
           f"Solution: {m(iv_tex(S))}.")
    return {"stem": "", "parts": [(f"Solve {m(tex(quad) + ' ' + OPS[op][1] + ' 0')}. Express your answer in interval notation.", ans)], "figure": None}


def quad_inequality_rearranged(rng):
    """Assessment: terms on both sides, and a case with no real zeros (all reals or no solution)."""
    parts = []
    for kind in ("two", "none"):
        if kind == "two":
            m1, n1, m2, n2 = _quad_factors(rng)
            quad = sp.expand((m1 * x - n1) * (m2 * x - n2))
            k = rng.randint(-6, 6)
            # build  A x^2 + B x > C  with A x^2 + (B) x - C = quad shifted so rearranging is required
            A, B = quad.coeff(x, 2), quad.coeff(x, 1)
            C = -quad.coeff(x, 0)
            lhs, rhs = A * x ** 2 + B * x, sp.Integer(C)
            op = rng.choice(list(OPS))
            S = _solve_ineq(lhs - rhs, op)
            assert S not in (sp.S.EmptySet, sp.S.Reals)
            _sample_check(lhs - rhs, op, S)
            q = f"Solve {m(tex(lhs) + ' ' + OPS[op][1] + ' ' + tex(rhs))}. Express your answer in interval notation."
            step = f"Subtract {m(tex(rhs))} from both sides" if rhs > 0 else f"Add {m(tex(-rhs))} to both sides" if rhs < 0 else "Everything is already on one side"
            a_ = (f"{step} to get {m(tex(lhs - rhs) + ' ' + OPS[op][1] + ' 0')}, then factor and use a sign chart. "
                  f"Solution: {m(iv_tex(S))}.")
            parts.append((q, a_))
        else:
            s_, t_ = rng.randint(-4, 4), rng.randint(1, 4)
            pos = rng.random() < 0.5
            quad = sp.expand((x - s_) ** 2 + t_)           # never zero
            op = rng.choice(["<", "<=", ">", ">="])
            S = _solve_ineq(quad, op)
            _sample_check(quad, op, S)
            disc = sp.discriminant(quad, x)
            assert disc < 0 and S in (sp.S.EmptySet, sp.S.Reals)
            verdict = "every real number is a solution: " + m(r"(-\infty, \infty)") if S == sp.S.Reals else "there is no real solution"
            q = f"Solve {m(tex(quad) + ' ' + OPS[op][1] + ' 0')}. Express your answer in interval notation, or say there is no real solution."
            a_ = (f"The discriminant is {m(f'b^2 - 4ac = {disc}')}, which is negative, so the parabola never touches the {m('x')}-axis. "
                  f"It opens upward, so {m(tex(quad))} is always positive. Therefore {verdict}.")
            parts.append((q, a_))
    return {"stem": "", "parts": parts, "figure": None}


# ============================================================================ PR9
def _lin_text(a_, b_):
    return tex(a_ * x + b_)


def rational_inequality(rng):
    """(ax + b)/(cx + d) compared with 0."""
    m1, m2 = rng.choice([1, 1, 1, 2]), rng.choice([1, 1, 2, 3])
    n1, n2 = _nonzero(rng, -7, 7), _nonzero(rng, -7, 7)
    s1, s2 = sp.Rational(n1, m1), sp.Rational(n2, m2)
    assert s1 != s2
    sign = rng.choice([1, 1, -1])
    num_, den_ = sign * (m1 * x - n1), (m2 * x - n2)
    expr = num_ / den_
    op = rng.choice(list(OPS))
    S = _solve_ineq(expr, op)
    assert S not in (sp.S.EmptySet, sp.S.Reals)
    _sample_check(expr, op, S)
    # the zero of the denominator is never included; the zero of the numerator only for <= or >=
    assert not S.contains(s2) and (S.contains(s1) == (op in ("<=", ">=")))
    shown = rf"\dfrac{{{tex(num_)}}}{{{tex(den_)}}}"
    ans = (f"The numerator is {m(0)} at {m('x = ' + frac_tex(s1))} and the denominator is {m(0)} at {m('x = ' + frac_tex(s2))}. "
           f"Use these two values to split the number line, then test a point in each interval. "
           f"{m('x = ' + frac_tex(s2))} is never included because the expression is undefined there. "
           f"{m('x = ' + frac_tex(s1))} is {'included' if op in ('<=', '>=') else 'not included'} because the inequality is {'not ' if op in ('<=', '>=') else ''}strict. "
           f"Solution: {m(iv_tex(S))}.")
    return {"stem": "", "parts": [(f"Solve {m(shown + ' ' + OPS[op][1] + ' 0')}. Express your answer in interval notation.", ans)], "figure": None}


def rational_inequality_product(rng):
    """Assessment: three critical numbers, and a version with a constant on the right side."""
    parts = []
    # (a) (x - p)(x - q) / (x - r)  compared with 0
    p, q, r = rng.sample([v for v in range(-5, 6) if v != 0], 3)
    expr = (x - p) * (x - q) / (x - r)
    op = rng.choice(list(OPS))
    S = _solve_ineq(expr, op)
    _sample_check(expr, op, S)
    shown = rf"\dfrac{{{lin(p)}{lin(q)}}}{{{lin(r)[1:-1]}}}"
    crit = sorted([p, q, r])
    parts.append((f"Solve {m(shown + ' ' + OPS[op][1] + ' 0')}. Express your answer in interval notation.",
                  f"The critical numbers are {m(', '.join(str(c) for c in crit))}: {m(f'x = {p}')} and {m(f'x = {q}')} make the numerator {m(0)}, "
                  f"and {m(f'x = {r}')} makes the denominator {m(0)}. Test a point in each of the four intervals. "
                  f"{m(f'x = {r}')} is never included. Solution: {m(iv_tex(S))}."))
    # (b) (x + a)/(x - b) <= k : move everything to one side first
    for _ in range(40):
        a_, b_, k = _nonzero(rng, -6, 6), _nonzero(rng, -6, 6), rng.choice([-2, -1, 1, 2, 3])
        if k != 1 and a_ + k * b_ != 0 and -a_ != b_ and sp.Rational(a_ + k * b_, k - 1) != b_:
            break
    else:
        raise ValueError("no draw")
    op2 = rng.choice(list(OPS))
    lhs = (x + a_) / (x - b_)
    one_side = sp.together(lhs - k)
    S2 = _solve_ineq(one_side, op2)
    assert S2 not in (sp.S.EmptySet, sp.S.Reals)
    _sample_check(lhs - k, op2, S2)
    num_ = sp.expand((x + a_) - k * (x - b_))
    d2 = f"x - {b_}" if b_ > 0 else f"x + {-b_}"
    n2 = f"x + {a_}" if a_ > 0 else f"x - {-a_}"
    parts.append((f"Solve {m(rf'\dfrac{{{n2}}}{{{d2}}} ' + OPS[op2][1] + f' {k}')}. Express your answer in interval notation.",
                  f"Do not multiply by {m(d2)}, because its sign changes. Move everything to one side: "
                  f"{m(rf'\dfrac{{{n2}}}{{{d2}}} ' + (f'- {k}' if k > 0 else f'+ {-k}') + ' ' + OPS[op2][1] + ' 0')}, then combine over a common denominator: "
                  f"{m(rf'\dfrac{{{tex(num_)}}}{{{d2}}} ' + OPS[op2][1] + ' 0')}. Make a sign chart. Solution: {m(iv_tex(S2))}."))
    return {"stem": "", "parts": parts, "figure": None}


TEMPLATES = {
    "poly_zeros_multiplicity": poly_zeros_multiplicity,
    "poly_graph_behavior": poly_graph_behavior,
    "poly_long_division": poly_long_division,
    "poly_long_division_quadratic": poly_long_division_quadratic,
    "zeros_complex_factor": zeros_complex_factor,
    "zeros_irrational_factor": zeros_irrational_factor,
    "zeros_from_one_zero": zeros_from_one_zero,
    "rational_eq_single": rational_eq_single,
    "rational_eq_denominators": rational_eq_denominators,
    "rational_zero_numerator": rational_zero_numerator,
    "rational_no_solution": rational_no_solution,
    "rational_hole_features": rational_hole_features,
    "rational_no_hole_features": rational_no_hole_features,
    "quad_inequality": quad_inequality,
    "quad_inequality_rearranged": quad_inequality_rearranged,
    "rational_inequality": rational_inequality,
    "rational_inequality_product": rational_inequality_product,
}
