"""Shared helpers for the Chapter 3-5 verifier: the registry of per-template checks and small parsing tools."""
import math
import re
from collections import Counter

import sympy as sp

from texeval import DEG, FreeVar, ParseError, evaluate, split_top

ok, skipped, bad = Counter(), Counter(), []
CHECKS = {}


class Skip(Exception):
    pass


def check(*names):
    def deco(fn):
        for n in names:
            CHECKS[n] = fn
        return fn
    return deco


def maths(s):
    return re.findall(r"\\\((.*?)\\\)", s, flags=re.S)


def fail(item, msg):
    bad.append(f"{item['id']}: {msg}")


def strip_text(s):
    """Plain words of an answer, with the math removed."""
    return re.sub(r"\\\(.*?\\\)", " ", s, flags=re.S)


def val(tex, env=None):
    return evaluate(tex, env)


def last_value(a_html):
    """The value on the right-hand end of the last chain in the answer that can be evaluated."""
    for mt in reversed(maths(a_html)):
        parts, ops = split_top(mt)
        for p in reversed(parts):
            try:
                return val(p)
            except (FreeVar, ParseError, ZeroDivisionError, ValueError):
                continue
    raise Skip()


def close(u, v, tol=1e-6):
    return abs(u - v) <= tol * max(1.0, abs(v))


def sym(tex):
    """LaTeX to a SymPy expression in x (reuses the FN1/FN2 verifier's reader)."""
    from verify_pool import tex2sym
    return tex2sym(tex)


X = sp.symbols("x")
