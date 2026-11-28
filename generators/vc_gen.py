"""Template-independent checks on the worked steps of an answer (run on every item in verify_ch35).

  steps      "E, so x = v" : v must satisfy the equation E printed just before it (also through a run of "x = a and x = b");
  zeros      "the denominator E equals 0" : E must be 0 at the nearest earlier "x = c";
  values     "f(c) = ... = v" : v must be the value of the f(x) given in the stem or a question, at c;
  identities in the identity templates, two neighbouring sides that both contain the variable must agree at random angles.
"""
import math
import random
import re

from texeval import FreeVar, ParseError, compile_tex, evaluate, split_top
from vbase import fail, maths

RAND = random.Random(11)
ERR = (FreeVar, ParseError, ZeroDivisionError, ValueError, OverflowError, IndexError, TypeError)
VAR = {r"\theta": "theta"}
TRIG_LHS = re.compile(r"^\\(sin|cos|tan|cot|sec|csc)\s*\\theta$")
CLAIM = re.compile(r"^\s*(\\theta|[A-Za-z]|\\(?:sin|cos|tan|cot|sec|csc)\\theta)\s*=\s*(.+)$", re.S)
CONNECT = [r", so ", r" and ", r", ", r": ", r" gives ", r", then ", r"\. Then ", r": the solutions? in one period (?:is|are) ", r", with solutions ", r", which gives "]
CONN_RE = re.compile(r"^(?:" + "|".join(CONNECT) + r")$")
SPAN = re.compile(r"\\\((.*?)\\\)", re.S)


def spans(text):
    return [(m.start(), m.end(), m.group(1)) for m in SPAN.finditer(text)]


def eq_parts(tex):
    parts, ops = split_top(tex)
    return (parts, ops) if len(parts) == 2 and ops == ["eq"] else None


def claim_of(tex):
    m = CLAIM.match(tex)
    if not m or r"\pm" in tex or "=" in m.group(2):
        return None
    lhs, rhs = m.group(1).strip(), m.group(2).strip()
    if r"\approx" in rhs:                      # "h = 69\tan 25 \approx 32.2": the exact expression is the claim
        pieces, ops = split_top(rhs)
        if ops != ["approx"] or not pieces[0].strip():
            return None
        rhs = pieces[0].strip()
    try:
        v = evaluate(rhs)
    except ERR:
        return None
    return lhs, v, rhs


def residual(eq_tex, lhs, rhs_tex, v):
    """E(v) for the equation E in the variable named by `lhs`; None when E uses other unknowns."""
    parts = eq_parts(eq_tex)
    if not parts:
        return None
    L, R = parts[0]
    if TRIG_LHS.match(lhs):
        fn = TRIG_LHS.match(lhs).group(1)
        def sub(s, fn=fn):
            s = re.sub(r"\\" + fn + r"\^\{(\d)\}\\theta", lambda m: "(" + rhs_tex + ")^{" + m.group(1) + "}", s)
            return re.sub(r"\\" + fn + r"\\theta", lambda m: "(" + rhs_tex + ")", s)
        L, R = sub(L), sub(R)
        env = {}
    else:
        env = {VAR.get(lhs, lhs): v}
    try:
        l, r = evaluate(L, env), evaluate(R, env)
    except ERR:
        return None
    return abs(l - r) / max(1.0, abs(l), abs(r))


def steps(item, text):
    fr = spans(text)
    for j, (s, e, tex) in enumerate(fr):
        c = claim_of(tex)
        if not c:
            continue
        lhs, v, rhs = c
        i = j - 1
        # walk back over "x = a and x = b" so that every root is tested against the equation before the first
        while i >= 0:
            prev = claim_of(fr[i][2])
            between = text[fr[i][1]:fr[i + 1][0]]
            if prev and prev[0] == lhs and CONN_RE.match(between):
                i -= 1
                continue
            break
        if i < 0 or i == j - 1 and False:
            continue
        between = text[fr[i][1]:fr[i + 1][0]]
        if not CONN_RE.match(between):
            continue
        if claim_of(fr[i][2]):
            continue
        res = residual(fr[i][2], lhs, rhs, v)
        if res is not None and res > 1e-7:
            fail(item, f"{lhs} = {rhs} does not satisfy the equation printed just before it: {fr[i][2].strip()}")


def zeros(item, ctx):
    fr = spans(ctx)
    for j, (s, e, tex) in enumerate(fr):
        try:
            target = evaluate(tex)
        except ERR:
            continue
        if j == 0:
            continue
        before = ctx[fr[j - 1][1]:s]
        if not re.search(r"\b(?:equals|equal to)\s*$", before):
            continue
        # which variable and value: nearest earlier "x = c"
        for k in range(j - 2, -1, -1):
            c = claim_of(fr[k][2])
            if c and re.fullmatch(r"[A-Za-z]", c[0]):
                try:
                    E = evaluate(fr[j - 1][2], {c[0]: c[1]})
                except ERR:
                    break
                if abs(E - target) > 1e-7:
                    fail(item, f"'{fr[j - 1][2].strip()} equals {tex.strip()}' is false at {c[0]} = {c[2]}")
                break


def definitions(item, part):
    out = {}
    for text in (part["q"], item["stem"]) + tuple(p["q"] for p in item["parts"]):
        for _, _, tex in spans(text):
            m = re.match(r"^\s*([A-Za-z])\(x\)\s*=\s*(.+)$", tex, re.S)
            if m and "=" not in m.group(2) and r"\ge" not in tex and m.group(1) not in out:
                out[m.group(1)] = m.group(2)
    return out


def values(item, part):
    defs = definitions(item, part)
    for _, _, tex in spans(part["a"]):
        parts, ops = split_top(tex)
        m = re.match(r"^([A-Za-z])\((.+)\)$", parts[0].strip())
        if not m or m.group(1) not in defs or len(parts) < 2:
            continue
        try:
            arg = evaluate(m.group(2))
            want = compile_tex(defs[m.group(1)])({"x": arg})
        except ERR:
            continue
        for p, op in zip(parts[1:], ops):
            try:
                got = evaluate(p)
            except ERR:
                continue
            tol = 1e-7 if op == "eq" else 0.06 * max(1, abs(want)) * 0.01 + 0.05
            if abs(got - want) > tol * max(1.0, abs(want)) * (1 if op == "eq" else 0) + (tol if op != "eq" else 0):
                fail(item, f"{parts[0].strip()} printed as {p.strip()} but {m.group(1)}({m.group(2)}) = {want:.6g}")
                break


IDENTITY_TEMPLATES = {"power_reduce", "power_reduce_fourth", "double_angle_given", "half_angle_exact", "sum_difference_exact", "verify_identity_basic", "verify_identity_fractions", "pythagorean_quadrant"}


def identities(item, text):
    for _, _, tex in spans(text):
        parts, ops = split_top(tex)
        if len(parts) < 2 or any(o != "eq" for o in ops):
            continue
        for a, b in zip(parts, parts[1:]):
            if re.fullmatch(r"\s*(?:[A-Za-z]|\\theta)\s*", a):
                continue                       # a definition such as u = 4x, not an identity
            try:
                evaluate(a)
                continue                       # a number: not an identity in the variable
            except FreeVar:
                pass
            except ERR:
                continue
            try:
                evaluate(b)
                continue
            except FreeVar:
                pass
            except ERR:
                continue
            fa, fb = compile_tex(a), compile_tex(b)
            good = 0
            for _ in range(12):
                t = RAND.uniform(0.3, 2.8)
                env = {"x": t, "u": t, "t": t, "theta": t}
                try:
                    va, vb = fa(env), fb(env)
                except ERR:
                    continue
                good += 1
                if abs(va - vb) > 1e-8 * max(1.0, abs(va)):
                    fail(item, f"not an identity: {a.strip()} vs {b.strip()}")
                    return
                if good >= 5:
                    break


def generic(item, template):
    for p in item["parts"]:
        steps(item, p["a"])
        zeros(item, item["stem"] + " " + p["q"] + " " + p["a"])
        values(item, p)
        if template in IDENTITY_TEMPLATES:
            identities(item, p["a"])


# ------------------------------------------------------------------ chains that hold at known values of their letters
def approx_tol(tex):
    """Half a unit of the last printed digit (in radians when the number carries a degree mark)."""
    deg = r"(\^\{?\\circ\}?|\\text\{°\}|°)?"
    m = re.search(r"(\d+)\.(\d+)\s*" + deg + r"\s*$", tex.strip())
    if m:
        t = 0.5 * 10 ** (-len(m.group(2))) + 1e-9
        return t * math.pi / 180 if m.group(3) else t
    m = re.search(r"(\d+)\s*" + deg + r"\s*$", tex.strip())
    if m:
        t = 0.5 + 1e-9
        return t * math.pi / 180 if m.group(2) else t
    return 1e-7


def env_chains(item, text, envs, strict_domain=False):
    """Chains that need values for their letters (a, b, c, A, x, t, ...) are re-evaluated with the true values in `envs`.

    The chain has to hold for at least one of the environments (several when an equation has several solutions)."""
    for tex in maths(text):
        parts, ops = split_top(tex)
        if len(parts) < 2:
            continue
        try:
            for p in parts:
                evaluate(p)
            continue                            # nothing unknown: the plain chain check already covers it
        except FreeVar:
            pass
        except ERR:
            continue
        keys = {k for env in envs for k in env}
        if parts[0].strip() in keys:
            try:
                for p in parts[1:]:
                    evaluate(p)
                continue                        # "x = -16" restates a root; the answer checks cover it
            except ERR + (FreeVar,):
                pass
        verdicts = []
        for env in envs:
            vals = []
            bad_domain = False
            for p in parts:
                try:
                    vals.append(evaluate(p, env))
                except (FreeVar, ParseError, IndexError, TypeError):
                    vals.append(None)
                except (ValueError, ZeroDivisionError, OverflowError):
                    vals.append(None)
                    bad_domain = True
            compared, good = 0, True
            for i in range(len(parts) - 1):
                u, v = vals[i], vals[i + 1]
                if u is None or v is None:
                    continue
                compared += 1
                tol = approx_tol(parts[i + 1]) if ops[i] == "approx" else 1e-8 * max(1.0, abs(v))
                if abs(u - v) > tol * (1 if ops[i] == "approx" else 1):
                    good = False
            if strict_domain and bad_domain:
                good = False
            verdicts.append((compared, good))
        if verdicts and any(c > 0 or (strict_domain and not g) for c, g in verdicts) and not any(g and (c > 0 or not strict_domain) for c, g in verdicts):
            fail(item, f"this step does not hold at the true value: {tex.strip()}")
