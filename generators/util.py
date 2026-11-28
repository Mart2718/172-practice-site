"""Small helpers shared by the chapter 3-5 templates (el.py, pr.py, te.py, pf.py).

Every template is  template(rng) -> {"stem", "parts": [(question_html, answer_html)], "figure": None}.
Templates ASSERT their own answers by a second route (substitute back, sample numerically) so a bad
parameter draw raises AssertionError and the pool simply skips that seed.
"""
import math
from fractions import Fraction

import sympy as sp

from common import x, m  # noqa: F401  (re-exported for the template modules)

OO = sp.oo


def sgn(n, first=False):
    """' + 3' / ' - 3' for building polynomials as text. first=True: no leading space or plus."""
    if first:
        return f"-{abs(n)}" if n < 0 else f"{n}"
    return f" - {abs(n)}" if n < 0 else f" + {n}"


def lin(r, power=1, var="x"):
    """The factor (x - r)^power as LaTeX."""
    if r == 0:
        return var + (f"^{{{power}}}" if power != 1 else "")
    inner = f"{var} - {r}" if r > 0 else f"{var} + {-r}"
    return f"({inner})" + (f"^{{{power}}}" if power != 1 else "")


def tex(e):
    return sp.latex(e, order="lex")


def frac_tex(q):
    """A rational as an integer or \\dfrac{p}{q}, with the sign out front."""
    q = sp.Rational(q)
    if q.q == 1:
        return str(q.p)
    sign = "-" if q < 0 else ""
    return f"{sign}\\dfrac{{{abs(q.p)}}}{{{q.q}}}"


# ---------------------------------------------------------------- interval notation
def iv_tex(S):
    """Interval notation for a SymPy subset of the reals (a union of intervals)."""
    S = sp.simplify(S) if not isinstance(S, sp.Set) else S
    if S == sp.S.Reals:
        return r"(-\infty, \infty)"
    if S == sp.S.EmptySet:
        return None
    pieces = list(S.args) if isinstance(S, sp.Union) else [S]
    for p in pieces:
        assert isinstance(p, sp.Interval), "unexpected isolated point in a solution set"
    pieces.sort(key=lambda I: float(I.start) if I.start != -OO else -1e18)
    out = []
    for I in pieces:
        lo = r"-\infty" if I.start == -OO else frac_tex(I.start)
        hi = r"\infty" if I.end == OO else frac_tex(I.end)
        lb = "(" if (I.left_open or I.start == -OO) else "["
        rb = ")" if (I.right_open or I.end == OO) else "]"
        out.append(f"{lb}{lo}, {hi}{rb}")
    return r" \cup ".join(out)


def in_set(S, v):
    return bool(S.contains(sp.nsimplify(v)))


# ---------------------------------------------------------------- numeric rounding guards
def safe_round(value, ndigits, margin=0.02):
    """Round, but refuse values so near a rounding boundary that a calculator might disagree."""
    frac = abs(value * 10 ** ndigits) % 1
    assert abs(frac - 0.5) > margin, "too close to a rounding boundary"
    return round(value, ndigits)


def fmt_dec(value, ndigits):
    """Decimal text with exactly ndigits places (trailing zeros kept) and a real minus sign handled by MathJax."""
    return f"{value:.{ndigits}f}"


def deg_tex(v, ndigits=0):
    return f"{fmt_dec(v, ndigits)}^\\circ"
