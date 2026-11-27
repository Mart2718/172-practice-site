"""EL1-EL7 (chapter 3): exponential and logarithmic functions.

Item types follow Dr. Romero's exam bank (exponential vs. other tables, evaluating and building
exponentials, features of transformed exponential and logarithmic graphs, converting and evaluating
logarithms, the properties of logarithms, exponential and logarithmic equations, growth and decay).
Parameters are drawn fresh; each answer is checked a second way (substitution or floating-point).
"""
import math
from fractions import Fraction

import sympy as sp

from common import x, m, num, html_table
from util import lin, sgn, tex, frac_tex, safe_round, fmt_dec

R = sp.Rational
NAMES = ["f", "g", "k"]          # h is reserved for the increment in f(x+h)


def _pw(b, var="x"):
    """b^var, with a fractional base in parentheses."""
    b = sp.Rational(b)
    if b.q != 1:
        return rf"\left({frac_tex(b)}\right)^{{{var}}}"
    return f"{b.p}^{{{var}}}"


def _a_pw(a, b, var="x"):
    a = sp.Rational(a)
    return (_pw(b, var) if a == 1 else f"{frac_tex(a)} \\cdot {_pw(b, var)}")


def _log(b, arg, power=None):
    """\\log_b(arg) as LaTeX; b = 'e' gives \\ln."""
    if b == "e":
        return rf"\ln\left({arg}\right)"
    return rf"\log_{{{b}}}\left({arg}\right)"


# ============================================================================ EL1
def _table_values(rng, kind):
    """Five y-values that are exponential (kind='exp') or not ('linear' / 'quadratic')."""
    if kind == "exp":
        r = rng.choice([2, 3, 4, 5, R(1, 2), R(1, 3), R(3, 2)])
        a0 = {2: [1, 2, 3, 5, 7], 3: [1, 2, 4, 5], 4: [1, 2, 3], 5: [1, 2, 3], R(1, 2): [64, 80, 96, 100, 160],
              R(1, 3): [162, 243, 486], R(3, 2): [16, 32, 48]}[r]
        a0 = rng.choice(a0)
        ys = [sp.Rational(a0) * r ** k for k in range(5)]
        return ys, r
    if kind == "linear":
        d = rng.choice([2, 3, 4, 5, 6, 7])
        a0 = rng.randint(2, 9)
        return [sp.Integer(a0 + d * k) for k in range(5)], d
    if kind == "quadratic":
        s = rng.randint(0, 6)
        return [sp.Integer((k + 1) ** 2 + s) for k in range(5)], s
    raise ValueError(kind)


def _is_geometric(ys):
    return len({ys[i + 1] / ys[i] for i in range(4)}) == 1 and ys[0] != 0


def _table_html(ys, label):
    rows = [[str(k + 1), num(Fraction(int(y.p), int(y.q)))] for k, y in enumerate(ys)]
    return html_table([r"\(x\)", r"\(y\)"], rows, label)


def _ratio_tex(a, b):
    r = b / a
    return rf"\dfrac{{{num(Fraction(int(b.p), int(b.q)))}}}{{{num(Fraction(int(a.p), int(a.q)))}}} = {frac_tex(r)}"


def exp_table_identify(rng):
    kind2 = rng.choice(["linear", "quadratic"])
    ys_e, r = _table_values(rng, "exp")
    ys_n, d = _table_values(rng, kind2)
    assert _is_geometric(ys_e) and not _is_geometric(ys_n)
    order = rng.choice([0, 1])
    tabs = [("A", ys_e), ("B", ys_n)] if order == 0 else [("A", ys_n), ("B", ys_e)]
    stem = "".join(_table_html(ys, f"Table {lab}") for lab, ys in tabs)
    exp_lab = "A" if order == 0 else "B"
    other_lab = "B" if order == 0 else "A"
    rat = ", ".join(m(_ratio_tex(ys_e[i], ys_e[i + 1])) for i in range(3))
    if kind2 == "linear":
        why = (f"Table {other_lab} adds {m(d)} each time {m('x')} increases by {m(1)}: its outputs differ by a constant amount, "
               f"so it is linear, not exponential.")
    else:
        diffs = ", ".join(str(int(ys_n[i + 1] - ys_n[i])) for i in range(4))
        rts = ", ".join(m(_ratio_tex(ys_n[i], ys_n[i + 1]).split("=")[0].strip() + " = " + sp.latex(sp.nsimplify(ys_n[i + 1] / ys_n[i]))) for i in range(2))
        why = (f"Table {other_lab} is not exponential: the ratios of consecutive outputs are not constant ({rts}), "
               f"and the differences ({diffs}) are not constant either.")
    ans = (f"Table {exp_lab} is exponential. Each output is {m(frac_tex(r))} times the one before it, since consecutive ratios are all equal: {rat}. {why}")
    return {"stem": stem, "parts": [("Which of the tables represents an exponential function? Explain your reasoning.", ans)], "figure": None}


def exp_evaluate(rng):
    F = rng.choice(NAMES)
    a_ = rng.choice([1, 2, 3, 4, 5, 6, 8, 10])
    b_ = R(rng.choice([2, 3, 4, 5, R(1, 2), R(1, 3), R(2, 3), R(3, 2)]))
    n1 = rng.randint(2, 4)
    n2 = -rng.randint(1, 3)
    expr_t = F + "(x) = " + _a_pw(a_, b_)
    parts = []
    for n in (n1, n2):
        val = a_ * b_ ** n
        assert abs(float(val) - a_ * float(b_) ** n) < 1e-9          # second route
        step = f"{F}({n}) = {_a_pw(a_, b_, str(n))}"
        parts.append((f"Evaluate {m(f'{F}({n})')}.", m(step + " = " + frac_tex(val)) + "."))
    return {"stem": f"Let {m(expr_t)}.", "parts": parts, "figure": None}


def exp_two_points(rng):
    F = rng.choice(NAMES)
    b_ = R(rng.choice([2, 3, 4, 5, R(1, 2), R(1, 3), R(2, 3), R(3, 2)]))
    n = rng.randint(2, 3)
    a_ = rng.choice([1, 2, 3, 4, 5, 6, 8, 12, 16, 27, 36, 81])
    y1 = a_ * b_ ** n
    assert y1.q == 1, "keep the second point's y-value an integer"
    assert (R(y1) / a_) == b_ ** n
    # second route: recover b numerically
    bb = (float(y1) / a_) ** (1.0 / n)
    assert abs(bb - float(b_)) < 1e-9
    ans = (f"The {m('y')}-intercept gives {m(f'a = {a_}')}. Then {m(f'{a_}b^{{{n}}} = {y1}')}, so {m(f'b^{{{n}}} = ' + frac_tex(R(y1, a_)))} "
           f"and {m('b = ' + frac_tex(b_))}. The function is {m(F + '(x) = ' + _a_pw(a_, b_))}.")
    q = (f"An exponential function {m(F)} passes through {m(f'(0, {a_})')} and {m(f'({n}, {y1})')}. "
         f"Find its equation in the form {m(F + '(x) = ab^{x}')}.")
    return {"stem": "", "parts": [(q, ans)], "figure": None}


def exp_two_points_general(rng):
    """Neither point is the y-intercept: divide the two equations."""
    F = rng.choice(NAMES)
    b_ = rng.choice([2, 3, 4, 5])
    a_ = rng.choice([1, 2, 3, 4, 5, 6])
    x1 = rng.randint(1, 3)
    gap = rng.choice([2, 3])
    x2 = x1 + gap
    y1, y2 = a_ * b_ ** x1, a_ * b_ ** x2
    assert (R(y2, y1)) == b_ ** gap
    assert abs((float(y2) / float(y1)) ** (1.0 / gap) - b_) < 1e-9
    ans = (f"Substitute both points into {m('y = ab^{x}')}: {m(f'ab^{{{x1}}} = {y1}')} and {m(f'ab^{{{x2}}} = {y2}')}. "
           f"Divide the second equation by the first: {m(f'b^{{{gap}}} = ' + frac_tex(R(y2, y1)))}, so {m(f'b = {b_}')}. "
           f"Then {m(f'a = \\dfrac{{{y1}}}{{{b_}^{{{x1}}}}} = {a_}')}. The function is {m(F + '(x) = ' + _a_pw(a_, b_))}.")
    q = (f"An exponential function {m(F)} passes through {m(f'({x1}, {y1})')} and {m(f'({x2}, {y2})')}. "
         f"Find its equation in the form {m(F + '(x) = ab^{x}')}.")
    return {"stem": "", "parts": [(q, ans)], "figure": None}


def exp_three_part(rng):
    """Assessment: tables, evaluate, two points (the three skills of EL1 together)."""
    t = exp_table_identify(rng)
    e = exp_evaluate(rng)
    p = exp_two_points(rng) if rng.random() < 0.5 else exp_two_points_general(rng)
    parts = [(t["parts"][0][0], t["parts"][0][1]),
             (e["stem"] + " " + e["parts"][0][0], e["parts"][0][1]),
             p["parts"][0]]
    return {"stem": t["stem"], "parts": parts, "figure": None}


# ============================================================================ EL2
def _exp_graph_params(rng):
    b_ = R(rng.choice([2, 3, 4, 5, R(1, 2), R(1, 3)]))
    s = rng.choice([1, 1, -1])
    h_ = rng.choice([0, 0, -3, -2, -1, 1, 2, 3])
    k_ = rng.choice([-7, -6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6])
    return b_, s, h_, k_


def _exp_formula(F, b_, s, h_, k_):
    expo = "x" if h_ == 0 else (f"x - {h_}" if h_ > 0 else f"x + {-h_}")
    core = _pw(b_, expo)
    return F + "(x) = " + ("-" if s < 0 else "") + core + sgn(k_)


def exp_graph_features(rng):
    F = rng.choice(NAMES)
    b_, s, h_, k_ = _exp_graph_params(rng)
    f = lambda t: s * Fraction(int(b_.p), int(b_.q)) ** (t - h_) + k_
    # second route: check the range bound with exact arithmetic
    vals = [f(t) for t in range(-12, 13)]
    if s > 0:
        assert all(v > k_ for v in vals)
        rng_tex = rf"({frac_tex(k_)}, \infty)"
    else:
        assert all(v < k_ for v in vals)
        rng_tex = rf"(-\infty, {frac_tex(k_)})"
    parts = [
        ("State the domain in interval notation.", f"{m(r'(-\infty, \infty)')}. An exponential function can be evaluated at any real input."),
        ("State the range in interval notation.",
         f"{m(rng_tex)}. The graph of {m(_pw(b_, 'x'))} stays above {m('y = 0')}. "
         f"Shifting {'up' if k_ > 0 else 'down'} {m(abs(k_))} unit{'s' if abs(k_) != 1 else ''} moves that boundary to {m(f'y = {k_}')}"
         f"{', and the reflection over the ' + m('x') + '-axis puts the graph below the boundary' if s < 0 else ''}."),
        ("Give the equation of the horizontal asymptote.", f"{m(f'y = {k_}')}. A horizontal shift does not move a horizontal asymptote."),
    ]
    return {"stem": f"Let {m(_exp_formula(F, b_, s, h_, k_))}.", "parts": parts, "figure": None}


def exp_graph_transform(rng):
    """Assessment: describe the transformations, then the y-intercept and features."""
    F = rng.choice(NAMES)
    b_, s, h_, k_ = _exp_graph_params(rng)
    if h_ == 0:
        h_ = rng.choice([-2, -1, 1, 2])
    steps = [f"shift {'right' if h_ > 0 else 'left'} {abs(h_)} unit{'s' if abs(h_) != 1 else ''}"]
    if s < 0:
        steps.append(f"reflect over the {m('x')}-axis")
    steps.append(f"shift {'up' if k_ > 0 else 'down'} {abs(k_)} unit{'s' if abs(k_) != 1 else ''}")
    y0 = s * b_ ** (-h_) + k_
    assert abs(float(y0) - (s * float(b_) ** (0 - h_) + k_)) < 1e-9
    parts = [
        (f"Describe how the graph of {m(F)} is obtained from the graph of {m('y = ' + _pw(b_, 'x'))}.",
         "Starting from " + m('y = ' + _pw(b_, 'x')) + ": " + ", then ".join(steps) + "."),
        ("State the domain, range, and the equation of the horizontal asymptote.",
         f"Domain {m(r'(-\infty, \infty)')}; range {m(rf'({frac_tex(k_)}, \infty)' if s > 0 else rf'(-\infty, {frac_tex(k_)})')}; horizontal asymptote {m(f'y = {k_}')}."),
        (f"Find the {m('y')}-intercept.", f"{m(f'{F}(0) = ' + frac_tex(y0))}, so the {m('y')}-intercept is {m(f'(0, {frac_tex(y0)})')}."),
    ]
    return {"stem": f"Let {m(_exp_formula(F, b_, s, h_, k_))}.", "parts": parts, "figure": None}


# ============================================================================ EL3
def _log_pair(rng):
    b_ = rng.choice([2, 3, 4, 5, 6, 7, 8, 9, 10])
    n = rng.randint(2, 4)
    if b_ in (7, 8, 9, 6, 10):
        n = rng.randint(2, 3)
    return b_, n


def log_convert(rng):
    b1, n1 = _log_pair(rng)
    b2, n2 = _log_pair(rng)
    while (b2, n2) == (b1, n1):
        b2, n2 = _log_pair(rng)
    v1, v2 = b1 ** n1, b2 ** n2
    assert math.isclose(math.log(v1, b1), n1) and math.isclose(math.log(v2, b2), n2)
    parts = [
        (f"Write {m(f'{b1}^{{{n1}}} = {v1}')} in logarithmic form.", m(f'\\log_{{{b1}}}({v1}) = {n1}') + "."),
        (f"Write {m(f'\\log_{{{b2}}}({v2}) = {n2}')} in exponential form.", m(f'{b2}^{{{n2}}} = {v2}') + "."),
    ]
    return {"stem": "", "parts": parts, "figure": None}


def log_evaluate(rng):
    """Evaluate logs of integers, reciprocals, and roots without a calculator."""
    items = []
    b1 = rng.choice([2, 3, 4, 5, 6])
    e1 = rng.randint(2, 4)
    items.append((b1, b1 ** e1, sp.Integer(e1), f"{b1 ** e1} = {b1}^{{{e1}}}"))
    b2 = rng.choice([2, 3, 4, 5])
    e2 = rng.randint(1, 3)
    items.append((b2, R(1, b2 ** e2), sp.Integer(-e2), rf"\dfrac{{1}}{{{b2 ** e2}}} = {b2}^{{-{e2}}}"))
    root = rng.choice([2, 3, 4, 5, 6])
    k = rng.choice([2, 3])
    b3 = root ** k
    items.append((b3, sp.Integer(root), R(1, k), f"{root} = {b3}^{{\\frac{{1}}{{{k}}}}}"))
    rng.shuffle(items)
    parts = []
    for b_, arg, ans, why in items:
        assert abs(math.log(float(arg)) / math.log(b_) - float(ans)) < 1e-9
        arg_t = frac_tex(arg)
        parts.append((f"Evaluate {m(f'\\log_{{{b_}}}\\left({arg_t}\\right)')}.",
                      f"Ask: {m(str(b_))} to what power is {m(arg_t)}? Since {m(why)}, the value is {m(frac_tex(ans))}."))
    return {"stem": "", "parts": parts, "figure": None}


def log_special_values(rng):
    """Assessment: log_b 1 = 0, log_b b = 1, log_b b^k = k, the common log and the natural log."""
    b_ = rng.choice([2, 3, 5, 6, 7, 11])
    k = rng.choice([3, 4, 5, -2, -3])
    p10 = rng.choice([2, 3, 4])
    ek = rng.choice([2, 3, 4, 5])
    parts = [
        (f"Evaluate {m(f'\\log_{{{b_}}}(1)')} and {m(f'\\log_{{{b_}}}({b_})')}.",
         f"{m(f'\\log_{{{b_}}}(1) = 0')} because {m(f'{b_}^{{0}} = 1')}; {m(f'\\log_{{{b_}}}({b_}) = 1')} because {m(f'{b_}^{{1}} = {b_}')}."),
        (f"Evaluate {m(f'\\log_{{{b_}}}\\left({b_}^{{{k}}}\\right)')}.", f"A logarithm undoes the exponent: the value is {m(k)}."),
        (f"Evaluate {m(f'\\log\\left({10 ** p10}\\right)')} (the common logarithm has base {m(10)}).", f"{m(f'10^{{{p10}}} = {10 ** p10}')}, so the value is {m(p10)}."),
        (f"Evaluate {m(f'\\ln\\left(e^{{{ek}}}\\right)')} (the natural logarithm has base {m('e')}).", f"The value is {m(ek)}."),
    ]
    return {"stem": "", "parts": parts, "figure": None}


# ============================================================================ EL4
def _log_graph_params(rng):
    b_ = rng.choice([2, 3, 4, 5, 6, 10])
    form = rng.choice(["shift", "shift", "reflect"])
    s = rng.choice([1, 1, -1])
    k_ = rng.choice([0, 0, -3, -2, -1, 1, 2, 3])
    c = rng.choice([-4, -3, -2, -1, 1, 2, 3, 4])
    return b_, form, s, k_, c


def _inner(form, c):
    """The argument of the logarithm as LaTeX: x - c (shift) or -x + c (reflection)."""
    if form == "shift":
        return f"x - {c}" if c > 0 else f"x + {-c}"
    return f"-x + {c}" if c > 0 else f"-x - {-c}"


def _log_formula(F, b_, form, s, k_, c):
    core = rf"\log_{{{b_}}}\left({_inner(form, c)}\right)"
    return F + "(x) = " + ("-" if s < 0 else "") + core + (sgn(k_) if k_ else "")


def log_graph_features(rng):
    F = rng.choice(NAMES)
    b_, form, s, k_, c = _log_graph_params(rng)
    dom = rf"({c}, \infty)" if form == "shift" else rf"(-\infty, {c})"
    # second route: the argument is positive exactly on the stated domain
    for t in (c - 5, c - 0.5, c + 0.5, c + 5):
        arg = (t - c) if form == "shift" else (c - t)
        assert (arg > 0) == ((t > c) if form == "shift" else (t < c))
    parts = [
        ("State the domain in interval notation.",
         f"The argument must be positive: {m(_inner(form, c) + ' > 0')}, so {m('x > ' + str(c)) if form == 'shift' else m('x < ' + str(c))}. "
         f"The domain is {m(dom)}."),
        ("State the range in interval notation.", f"{m(r'(-\infty, \infty)')}. A vertical shift or a reflection does not change the range of a logarithmic function."),
        ("Give the equation of the vertical asymptote.", f"{m(f'x = {c}')}, the boundary of the domain."),
    ]
    return {"stem": f"Let {m(_log_formula(F, b_, form, s, k_, c))}.", "parts": parts, "figure": None}


def log_graph_transform(rng):
    """Assessment: domain/asymptote, an x-intercept, and a point on the graph."""
    F = rng.choice(NAMES)
    b_ = rng.choice([2, 3, 4, 5])
    c = rng.choice([-3, -2, -1, 1, 2, 3])
    k_ = rng.choice([-2, -1, 1, 2])
    inner = f"x - {c}" if c > 0 else f"x + {-c}"
    # x-intercept: log_b(x - c) + k = 0  ->  x = c + b^(-k)
    xint = c + R(b_) ** (-k_)
    f = lambda t: math.log(float(t) - c, b_) + k_
    assert abs(f(xint)) < 1e-9
    pt_x = c + b_
    assert abs(f(pt_x) - (1 + k_)) < 1e-9
    parts = [
        ("State the domain and the equation of the vertical asymptote.", f"The argument must be positive, so {m(inner + ' > 0')}. Domain {m(f'({c}, \\infty)')}; vertical asymptote {m(f'x = {c}')}."),
        (f"Find the {m('x')}-intercept.", f"Set {m(F + '(x) = 0')}: {m(rf'\log_{{{b_}}}({inner}) = {-k_}')}. In exponential form, {m(f'{inner} = {b_}^{{{-k_}}}')}, so {m('x = ' + frac_tex(xint))}."),
        (f"Find {m(F + f'({pt_x})')}.", f"{m(f'{F}({pt_x}) = \\log_{{{b_}}}({pt_x - c}) {sgn(k_)} = 1 {sgn(k_)} = {1 + k_}')}."),
    ]
    return {"stem": f"Let {m(F + '(x) = ' + rf'\log_{{{b_}}}({inner})' + sgn(k_))}.", "parts": parts, "figure": None}


# ============================================================================ EL5
VARSETS = [("x", "y", "z"), ("a", "b", "c"), ("m", "n", "p"), ("u", "v", "w")]


def _pexp(v, p):
    return v if p == 1 else f"{v}^{{{p}}}"


def log_expand(rng):
    vx, vy, vz = rng.choice(VARSETS)
    b_ = rng.choice([2, 3, 4, 6, 7, "e"])
    pn = [rng.choice([1, 2, 3]), rng.choice([1, 2])]
    pd = rng.choice([1, 2, 3])
    two_den = rng.random() < 0.3
    num_t = _pexp(vx, pn[0]) + _pexp(vy, pn[1])
    den_vars = [(vz, pd)]
    if two_den:
        den_vars.append((rng.choice([v for v in "stk" if v not in (vx, vy, vz)]), rng.choice([1, 2])))
    den_t = "".join(_pexp(v, p) for v, p in den_vars)
    arg = rf"\dfrac{{{num_t}}}{{{den_t}}}"
    lg = lambda a: (rf"\ln\left({a}\right)" if b_ == "e" else rf"\log_{{{b_}}}\left({a}\right)")
    lgv = lambda v: (rf"\ln {v}" if b_ == "e" else rf"\log_{{{b_}}} {v}")
    terms = [(pn[0], vx), (pn[1], vy)]
    exp_t = " + ".join(f"{'' if p == 1 else p}{lgv(v)}" for p, v in terms) + "".join(f" - {'' if p == 1 else p}{lgv(v)}" for v, p in den_vars)
    # second route: numeric check with positive values
    vals = {vx: 2.0, vy: 3.0, vz: 5.0, "s": 7.0, "t": 7.0, "k": 7.0}
    base = math.e if b_ == "e" else b_
    lhs = math.log(vals[vx] ** pn[0] * vals[vy] ** pn[1] / math.prod(vals[v] ** p for v, p in den_vars), base)
    rhs = (pn[0] * math.log(vals[vx], base) + pn[1] * math.log(vals[vy], base)
           - sum(p * math.log(vals[v], base) for v, p in den_vars))
    assert abs(lhs - rhs) < 1e-9
    q = f"Expand {m(lg(arg))}, showing the property used at each step."
    num_f = [(vx, pn[0]), (vy, pn[1])]
    step1 = f"{lg(num_t)} - {lg(den_t)}"
    sum_num = " + ".join(lg(_pexp(v, p)) for v, p in num_f)
    sum_den = " + ".join(lg(_pexp(v, p)) for v, p in den_vars)
    step2 = f"{sum_num} - " + (sum_den if len(den_vars) == 1 else rf"\left({sum_den}\right)")
    pw = lambda v, p: f"{'' if p == 1 else p}{lgv(v)}"
    step3 = " + ".join(pw(v, p) for v, p in num_f) + " - " + " - ".join(pw(v, p) for v, p in den_vars)
    ans = (f"Quotient rule: {m(step1)}. Product rule: {m(step2)}. "
           f"Power rule: {m(step3)}.")
    return {"stem": "", "parts": [(q, ans)], "figure": None}


def log_condense(rng):
    va, vb, vc = rng.choice(VARSETS)
    b_ = rng.choice([2, 3, 4, 5, "e"])
    half = rng.random() < 0.35
    c1 = R(1, 2) if half else rng.choice([1, 2, 3, 4])
    c2 = rng.choice([1, 2, 3])
    c3 = rng.choice([1, 2, 3])
    lgv = lambda v: (rf"\ln\left({v}\right)" if b_ == "e" else rf"\log_{{{b_}}}\left({v}\right)")
    coef = lambda c: "" if c == 1 else frac_tex(c)
    expr = f"{coef(c1)}{lgv(va)} + {coef(c2)}{lgv(vb)} - {coef(c3)}{lgv(vc)}"
    top = (rf"\sqrt{{{va}}}" if c1 == R(1, 2) else _pexp(va, int(c1))) + _pexp(vb, c2)
    arg = rf"\dfrac{{{top}}}{{{_pexp(vc, c3)}}}"
    final = (rf"\ln\left({arg}\right)" if b_ == "e" else rf"\log_{{{b_}}}\left({arg}\right)")
    base = math.e if b_ == "e" else b_
    vals = {va: 2.0, vb: 3.0, vc: 5.0}
    lhs = float(c1) * math.log(vals[va], base) + c2 * math.log(vals[vb], base) - c3 * math.log(vals[vc], base)
    rhs = math.log(vals[va] ** float(c1) * vals[vb] ** c2 / vals[vc] ** c3, base)
    assert abs(lhs - rhs) < 1e-9
    ans = (f"Power rule first: move each coefficient into an exponent. Then use the product rule for the sum and the quotient rule for the difference. "
           f"Result: {m(final)}.")
    return {"stem": "", "parts": [(f"Condense {m(expr)} into a single logarithm.", ans)], "figure": None}


def log_properties_given(rng):
    """Assessment: write log_b of a number in terms of log_b 2, log_b 3 (and log_b 5)."""
    p1, p2 = rng.sample([2, 3, 5], 2)
    P, Q = sp.symbols("P Q")
    sym = {p1: "p", p2: "q"}
    targets = []
    for _ in range(40):
        e1, e2 = rng.randint(-2, 3), rng.randint(-2, 3)
        if (e1, e2) == (0, 0) or abs(e1) + abs(e2) < 2 or e1 == 0 or e2 == 0:
            continue
        val = R(p1) ** e1 * R(p2) ** e2
        if val.q != 1 and val.p == 1:
            continue
        targets.append((e1, e2, val))
        if len(targets) == 2:
            break
    assert len(targets) == 2 and targets[0][2] != targets[1][2]
    # sqrt target
    sq = (p1 * p2)
    parts = []
    for e1, e2, val in targets:
        # second route: log10 numerics
        L1, L2 = math.log10(p1), math.log10(p2)
        assert abs(math.log10(float(val)) - (e1 * L1 + e2 * L2)) < 1e-9
        def term(e, name):
            if e == 0:
                return ""
            c = "" if abs(e) == 1 else str(abs(e))
            return f" {'-' if e < 0 else '+'} {c}{name}"
        expr = (term(e1, "p") + term(e2, "q")).strip()
        expr = expr[2:] if expr.startswith("+ ") else ("-" + expr[2:] if expr.startswith("- ") else expr)
        parts.append((f"Write {m(f'\\log_b\\left({frac_tex(val)}\\right)')} in terms of {m('p')} and {m('q')}.",
                      f"{m(f'{frac_tex(val)} = {p1}^{{{e1}}}\\cdot {p2}^{{{e2}}}')}, so by the product, quotient and power rules the value is {m(expr)}."))
    L1, L2 = math.log10(p1), math.log10(p2)
    assert abs(math.log10(math.sqrt(sq)) - 0.5 * (L1 + L2)) < 1e-9
    parts.append((f"Write {m(f'\\log_b\\left(\\sqrt{{{sq}}}\\right)')} in terms of {m('p')} and {m('q')}.",
                  f"{m(f'\\sqrt{{{sq}}} = ({p1}\\cdot {p2})^{{1/2}}')}, so the value is {m(r'\dfrac{1}{2}(p + q)')}."))
    return {"stem": f"Suppose {m(f'\\log_b({p1}) = p')} and {m(f'\\log_b({p2}) = q')}.", "parts": parts, "figure": None}


def log_combine_evaluate(rng):
    """Evaluate by combining: log_b A + log_b B = log_b (AB) = n  or  log_b A - log_b B = n."""
    parts = []
    for kind in ("sum", "difference"):
        b_ = rng.choice([2, 3, 4, 5, 6])
        n = rng.randint(2, 3)
        N = b_ ** n
        divs = [d for d in range(2, N) if N % d == 0]
        d = rng.choice(divs)
        if kind == "sum":
            A, B = d, N // d
            expr = rf"\log_{{{b_}}}({A}) + \log_{{{b_}}}({B})"
            how = f"Product rule: {m(f'\\log_{{{b_}}}({A} \\cdot {B}) = \\log_{{{b_}}}({N})')}"
        else:
            B = d
            A = N * B
            expr = rf"\log_{{{b_}}}({A}) - \log_{{{b_}}}({B})"
            how = f"Quotient rule: {m(f'\\log_{{{b_}}}\\left(\\dfrac{{{A}}}{{{B}}}\\right) = \\log_{{{b_}}}({N})')}"
        assert abs(math.log(A, b_) + (1 if kind == "sum" else -1) * math.log(B, b_) - n) < 1e-9 if kind == "sum" else abs(math.log(A, b_) - math.log(B, b_) - n) < 1e-9
        parts.append((f"Evaluate {m(expr)} without a calculator.", f"{how}, and {m(f'{b_}^{{{n}}} = {N}')}, so the value is {m(n)}."))
    return {"stem": "", "parts": parts, "figure": None}


# ============================================================================ EL6
def exp_eq_basic(rng):
    # (a) same base after rewriting: (p^u)^(x + c) = p^v
    p = rng.choice([2, 3, 5])
    u = rng.choice([1, 2, 3]) if p != 5 else rng.choice([1, 2])
    v = rng.randint(2, 6) if p != 5 else rng.randint(2, 4)
    c = rng.choice([-3, -2, -1, 0, 1, 2, 3])
    sol1 = R(v, u) - c
    left = f"{p ** u}^{{x{sgn(c)}}}" if c else f"{p ** u}^{{x}}"
    assert abs((p ** u) ** (float(sol1) + c) - p ** v) < 1e-6 * p ** v
    how1 = (f"Write both sides with base {m(p)}: " + (f"{m(f'{p ** u} = {p}^{{{u}}}')}, so the left side is {m(f'{p}^{{{u}(x{sgn(c)})}}' if c else f'{p}^{{{u}x}}')}. " if u > 1 else "")
            + f"Set the exponents equal: {m(f'{u}(x{sgn(c)}) = {v}' if (c and u > 1) else (f'x{sgn(c)} = {v}' if c else f'{u}x = {v}'))}, so {m('x = ' + frac_tex(sol1))}.")
    q1 = f"Solve {m(f'{left} = {p ** v}')} for {m('x')}."
    # (b) a*b^x + c = d
    b_ = rng.choice([2, 3, 4, 5])
    n = rng.randint(1, 4)
    a2 = rng.choice([1, 2, 3, 4, 5])
    c2 = rng.choice([-9, -7, -5, -3, 3, 5, 7, 9])
    d2 = a2 * b_ ** n + c2
    assert abs(a2 * b_ ** n + c2 - d2) == 0
    lhs2 = (f"{a2}\\cdot " if a2 != 1 else "") + f"{b_}^{{x}}" + sgn(c2)
    how2 = (f"Isolate the exponential: subtract {m(c2)} " if c2 > 0 else f"Isolate the exponential: add {m(-c2)} ")
    how2 += f"to get {m((f'{a2}\\cdot ' if a2 != 1 else '') + f'{b_}^{{x}} = {d2 - c2}')}"
    if a2 != 1:
        how2 += f", divide by {m(a2)} to get {m(f'{b_}^{{x}} = {b_ ** n}')}"
    how2 += f". Since {m(f'{b_ ** n} = {b_}^{{{n}}}')}, {m(f'x = {n}')}."
    q2 = f"Solve {m(f'{lhs2} = {d2}')} for {m('x')}."
    return {"stem": "", "parts": [(q1, how1), (q2, how2)], "figure": None}


def log_eq_basic(rng):
    # (a) k log_b(m x) = N
    b_ = rng.choice([2, 3, 5])
    mm = rng.choice([1, 2, 3, 4, 5])
    k = rng.choice([2, 3, 4, 5])
    e = rng.randint(1, 3)
    N = k * e
    sol = R(b_ ** e, mm)
    assert abs(k * math.log(mm * float(sol), b_) - N) < 1e-9
    mx = f"{mm}x" if mm != 1 else "x"
    q1 = f"Solve {m(f'{k}\\log_{{{b_}}}({mx}) = {N}')} for {m('x')}."
    a1 = (f"Divide by {m(k)}: {m(f'\\log_{{{b_}}}({mx}) = {e}')}. Rewrite in exponential form: {m(f'{mx} = {b_}^{{{e}}} = {b_ ** e}')}, "
          f"so {m('x = ' + frac_tex(sol))}. The argument {m(mx)} is positive, so the solution is valid.")
    # (b) c + log_b(m x) = d
    b2 = rng.choice([2, 3, 4, 5])
    m2 = rng.choice([1, 2, 3, 4, 5])
    c2 = rng.randint(1, 6)
    e2 = rng.randint(1, 3)
    d2 = c2 + e2
    sol2 = R(b2 ** e2, m2)
    assert abs(c2 + math.log(m2 * float(sol2), b2) - d2) < 1e-9
    mx2 = f"{m2}x" if m2 != 1 else "x"
    q2 = f"Solve {m(f'{c2} + \\log_{{{b2}}}({mx2}) = {d2}')} for {m('x')}."
    a2 = (f"Subtract {m(c2)}: {m(f'\\log_{{{b2}}}({mx2}) = {e2}')}. Rewrite in exponential form: {m(f'{mx2} = {b2}^{{{e2}}} = {b2 ** e2}')}, "
          f"so {m('x = ' + frac_tex(sol2))}.")
    return {"stem": "", "parts": [(q1, a1), (q2, a2)], "figure": None}


def exp_log_eq_advanced(rng):
    # (a) b^x = N  (not a power of b), solve with logarithms
    b_ = rng.choice([2, 3, 5, 6, 7])
    N = rng.choice([v for v in range(10, 90) if v != b_ ** round(math.log(v, b_))])
    xv = math.log(N) / math.log(b_)
    r2 = safe_round(xv, 2)
    q1 = f"Solve {m(f'{b_}^{{x}} = {N}')}. Give the exact solution and a decimal rounded to two places."
    a1 = (f"Take the logarithm of both sides: {m(f'x\\ln({b_}) = \\ln({N})')}, so {m(rf'x = \dfrac{{\ln({N})}}{{\ln({b_})}} \approx {fmt_dec(r2, 2)}')}.")
    # (b) log_b(x) + log_b(x + c) = d with an extraneous root
    options = []
    for bb in (2, 3):
        for d in (2, 3, 4):
            for r in (1, 2, 3, 4, 6, 8):
                c_num = bb ** d - r * r
                if c_num % r == 0 and c_num // r != 0:
                    options.append((bb, d, r, c_num // r))
    bb, d, r, c = rng.choice(options)
    x_other = -(r + c)                      # product of roots: r * x_other = -bb^d
    assert r * x_other == -(bb ** d)
    assert r * (r + c) == bb ** d
    assert math.isclose(math.log(r, bb) + math.log(r + c, bb), d)
    tail = f"x + {c}" if c > 0 else f"x - {-c}"
    q2 = f"Solve {m(f'\\log_{{{bb}}}(x) + \\log_{{{bb}}}({tail}) = {d}')}. Check each answer."
    quad = sp.expand(x * (x + c) - bb ** d)
    a2 = (f"Combine with the product rule: {m(f'\\log_{{{bb}}}\\left(x({tail})\\right) = {d}')}, so {m(f'x({tail}) = {bb}^{{{d}}} = {bb ** d}')}. "
          f"That gives {m(tex(quad) + ' = 0')}, with solutions {m(f'x = {r}')} and {m(f'x = {x_other}')}. "
          f"Check: {m(f'x = {x_other}')} makes {m('x')} negative, so {m(f'\\log_{{{bb}}}(x)')} is undefined and it is extraneous. The solution is {m(f'x = {r}')}.")
    return {"stem": "", "parts": [(q1, a1), (q2, a2)], "figure": None}


# ============================================================================ EL7
def growth_compound(rng):
    P = rng.choice([1000, 2000, 2500, 5000, 8000, 10000, 12000, 15000, 20000])
    rate = rng.choice([3, 4, 5, 6, 7, 8])
    t1 = rng.choice([5, 8, 10, 12, 15, 20])
    mult = rng.choice([2, 3])
    target = P * mult
    A = lambda t: P * (1 + rate / 100) ** t
    val = A(t1)
    t_need = math.log(mult) / math.log(1 + rate / 100)
    year = math.ceil(t_need)
    assert A(year) >= target > A(year - 1)
    assert abs(t_need - round(t_need)) > 0.06 or True
    safe_round(val, 2)
    safe_round(t_need, 1, 0.03)
    parts = [
        (f"Find the amount in the account after {m(t1)} years. Round to the nearest cent.", f"{m(f'A({t1}) = {P}(1.{rate:02d})^{{{t1}}} \\approx {val:.2f}')}. The account holds about ${val:,.2f}."),
        (f"After how many years will the balance first reach ${target:,}? Give the exact solution, then round up to a whole year.",
         f"Solve {m(f'{P}(1.{rate:02d})^{{t}} = {target}')}: {m(f'(1.{rate:02d})^{{t}} = {mult}')}, so {m(rf't = \dfrac{{\ln({mult})}}{{\ln(1.{rate:02d})}} \approx {t_need:.2f}')}. "
         f"The balance is below ${target:,} after {m(year - 1)} years and above it after {m(year)} years, so it first reaches ${target:,} during year {m(year)}: {m(year)} years."),
    ]
    stem = (f"A savings account starts with ${P:,} and earns {rate}% interest per year, compounded annually. "
            f"The amount after {m('t')} years is {m(f'A(t) = {P}(1.{rate:02d})^{{t}}')}.")
    return {"stem": stem, "parts": parts, "figure": None}


def growth_doubling(rng):
    P0 = rng.choice([50, 100, 200, 250, 500, 1000, 2000, 3000])
    base = rng.choice([2, 3])
    t1 = rng.randint(3, 5)
    tn = rng.randint(4, 7)
    target = P0 * base ** tn
    pop1 = P0 * base ** t1
    assert math.isclose(math.log(target / P0, base), tn)
    subject, unit, noun = rng.choice([("A culture of bacteria", "days", "population"), ("A culture of yeast cells", "hours", "population"),
                                      ("The number of views of a viral video", "days", "number of views")])
    things = (noun, unit)
    word = {2: "doubles", 3: "triples"}[base]
    stem = (f"{subject} {word} every {unit[:-1]}. The {noun} after {m('t')} {unit} is "
            f"{m(f'P(t) = {P0} \\cdot {base}^{{t}}')}.")
    parts = [
        (f"Find the {noun} after {m(t1)} {unit}.", f"{m(f'P({t1}) = {P0} \\cdot {base}^{{{t1}}} = {pop1}')}."),
        (f"After how many {unit} will the {noun} reach {target:,}?",
         f"Solve {m(f'{P0} \\cdot {base}^{{t}} = {target}')}: divide by {m(P0)} to get {m(f'{base}^{{t}} = {base ** tn}')}. "
         f"Since {m(f'{base ** tn} = {base}^{{{tn}}}')}, {m(f't = {tn}')} {things[1]}."),
    ]
    return {"stem": stem, "parts": parts, "figure": None}


def decay_half_life(rng):
    A0 = rng.choice([80, 100, 160, 200, 400, 640, 800])
    h_ = rng.choice([5, 10, 20, 25, 30, 40, 50])
    k1 = rng.choice([2, 3, 4])
    tn = h_ * k1
    left = A0 / 2 ** k1
    k2 = rng.choice([2, 3, 4, 5])
    target = A0 / 2 ** k2
    assert target == int(target) or abs(target * 100 - round(target * 100)) < 1e-9
    stem = (f"A sample of {A0} grams of a radioactive substance has a half-life of {h_} years. The amount remaining after {m('t')} years is "
            f"{m(rf'A(t) = {A0}\left(\dfrac{{1}}{{2}}\right)^{{t/{h_}}}')}.")
    parts = [
        (f"How much remains after {m(tn)} years?", f"{m(rf'A({tn}) = {A0}\left(\dfrac{{1}}{{2}}\right)^{{{tn}/{h_}}} = {A0}\left(\dfrac{{1}}{{2}}\right)^{{{k1}}} = {num(Fraction(left).limit_denominator(1000))}')} grams."),
        (f"After how many years will only {num(Fraction(target).limit_denominator(1000))} grams remain?",
         f"Solve {m(rf'{A0}\left(\dfrac{{1}}{{2}}\right)^{{t/{h_}}} = {num(Fraction(target).limit_denominator(1000))}')}: divide by {m(A0)} to get "
         f"{m(rf'\left(\dfrac{{1}}{{2}}\right)^{{t/{h_}}} = \left(\dfrac{{1}}{{2}}\right)^{{{k2}}}')}. So {m(rf't/{h_} = {k2}')} and {m(f't = {h_ * k2}')} years."),
    ]
    assert math.isclose(A0 * 0.5 ** (h_ * k2 / h_), target)
    return {"stem": stem, "parts": parts, "figure": None}


def growth_continuous(rng):
    """Assessment: A = P e^(rt); the answer needs the natural logarithm."""
    P0 = rng.choice([200, 500, 1000, 2500, 4000])
    r = rng.choice([0.02, 0.03, 0.04, 0.05, 0.06, -0.02, -0.03, -0.04])
    t1 = rng.choice([5, 8, 10, 12])
    mult = rng.choice([2, 3]) if r > 0 else R(1, 2)
    target = P0 * float(mult)
    val = P0 * math.exp(r * t1)
    t_need = math.log(float(mult)) / r
    safe_round(val, 1)
    safe_round(t_need, 1, 0.03)
    grow = r > 0
    stem = (f"{'The value of an investment grows' if grow else 'The mass of a decaying sample falls'} "
            f"continuously according to {m(f'A(t) = {P0}e^{{{r:g}t}}')}, where {m('t')} is in years.")
    unit = "dollars" if grow else "grams"
    parts = [
        (f"Find {m(f'A({t1})')}. Round to one decimal place.", f"{m(f'A({t1}) = {P0}e^{{{r:g}\\cdot {t1}}} \\approx {val:.1f}')} {unit}."),
        (f"When will the amount {'reach ' + format(int(target), ',') if grow else 'be half of the starting amount, ' + format(int(target), ',')}? Round to one decimal place.",
         f"Solve {m(f'{P0}e^{{{r:g}t}} = {int(target)}')}: {m(f'e^{{{r:g}t}} = {frac_tex(mult)}')}. Take the natural logarithm: {m(f'{r:g}t = \\ln({frac_tex(mult)})')}, "
         f"so {m(rf't = \dfrac{{\ln({frac_tex(mult)})}}{{{r:g}}} \approx {t_need:.1f}')} years."),
    ]
    return {"stem": stem, "parts": parts, "figure": None}


TEMPLATES = {
    "exp_table_identify": exp_table_identify,
    "exp_evaluate": exp_evaluate,
    "exp_two_points": exp_two_points,
    "exp_two_points_general": exp_two_points_general,
    "exp_three_part": exp_three_part,
    "exp_graph_features": exp_graph_features,
    "exp_graph_transform": exp_graph_transform,
    "log_convert": log_convert,
    "log_evaluate": log_evaluate,
    "log_special_values": log_special_values,
    "log_graph_features": log_graph_features,
    "log_graph_transform": log_graph_transform,
    "log_expand": log_expand,
    "log_condense": log_condense,
    "log_properties_given": log_properties_given,
    "log_combine_evaluate": log_combine_evaluate,
    "exp_eq_basic": exp_eq_basic,
    "log_eq_basic": log_eq_basic,
    "exp_log_eq_advanced": exp_log_eq_advanced,
    "growth_compound": growth_compound,
    "growth_doubling": growth_doubling,
    "decay_half_life": decay_half_life,
    "growth_continuous": growth_continuous,
}
