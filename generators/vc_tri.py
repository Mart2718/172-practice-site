"""Checks for TE4-TE6: the givens are read back out of the printed problem, the triangle is solved again here
(law of sines / cosines on plain floats, no code shared with the generators), and every printed value is compared."""
import math
import re
from collections import Counter

from texeval import DEG, FreeVar, ParseError, evaluate, split_top
from vbase import Skip, check, fail, maths, strip_text
from vc_gen import env_chains

OPP = {"A": "a", "B": "b", "C": "c"}
UP = {"a": "A", "b": "B", "c": "C"}


# ---------------------------------------------------------------- independent triangle solver
def solve(angles, sides):
    """angles: {'A': radians}, sides: {'a': length}. Returns a list of complete triangles (dict with A,B,C in radians, a,b,c)."""
    def full(Ad, k):
        return {**Ad, **{OPP[L]: k * math.sin(Ad[L]) for L in "ABC"}}

    if len(angles) >= 2:
        Ad = dict(angles)
        missing = [L for L in "ABC" if L not in Ad]
        if missing:
            Ad[missing[0]] = math.pi - sum(Ad.values())
        if min(Ad.values()) <= 0:
            return []
        s = next(iter(sides))
        return [full(Ad, sides[s] / math.sin(Ad[UP[s]]))]
    if len(angles) == 1:
        X, = angles
        x = OPP[X]
        others = [s for s in sides if s != x]
        if x in sides:                                   # SSA
            y = others[0]
            Y = UP[y]
            r = sides[y] * math.sin(angles[X]) / sides[x]
            if r > 1 + 1e-12:
                return []
            r = min(r, 1.0)
            out = []
            for Yv in {round(math.asin(r), 12): math.asin(r), round(math.pi - math.asin(r), 12): math.pi - math.asin(r)}.values():
                Z = math.pi - angles[X] - Yv
                if Z > 1e-12:
                    Ad = {X: angles[X], Y: Yv}
                    Zl = next(L for L in "ABC" if L not in Ad)
                    Ad[Zl] = Z
                    out.append(full(Ad, sides[x] / math.sin(angles[X])))
            return out
        y, z = others                                    # SAS: the angle sits between sides y and z
        xv = math.sqrt(sides[y] ** 2 + sides[z] ** 2 - 2 * sides[y] * sides[z] * math.cos(angles[X]))
        Y = math.acos((xv ** 2 + sides[z] ** 2 - sides[y] ** 2) / (2 * xv * sides[z]))
        Z = math.acos((xv ** 2 + sides[y] ** 2 - sides[z] ** 2) / (2 * xv * sides[y]))
        Ad = {X: angles[X], UP[y]: Y, UP[z]: Z}
        t = dict(Ad)
        t.update({x: xv, y: sides[y], z: sides[z]})
        return [t]
    a, b, c = sides["a"], sides["b"], sides["c"]
    if a + b <= c or a + c <= b or b + c <= a:
        return []
    A = math.acos((b * b + c * c - a * a) / (2 * b * c))
    B = math.acos((a * a + c * c - b * b) / (2 * a * c))
    return [{"A": A, "B": B, "C": math.pi - A - B, "a": a, "b": b, "c": c}]


def givens(text_html):
    angles, sides = {}, {}
    for mt in maths(text_html):
        m = re.fullmatch(r"\s*([A-Za-z])\s*=\s*(\d+(?:\.\d+)?)\s*(\\text\{°\}|\^\\circ|°)?\s*", mt)
        if not m:
            continue
        L, v, deg = m.groups()
        if deg and L in "ABC":
            angles[L] = float(v) * DEG
        elif not deg and L in "abc":
            sides[L] = float(v)
    return angles, sides


# ---------------------------------------------------------------- reading what the answer prints
def half_unit(last_tex):
    m = re.search(r"(\d+)\.(\d+)\s*(?:\\text\{°\}|\^\\circ|°)?\s*$", last_tex.strip())
    if m:
        return 0.5 * 10 ** (-len(m.group(2))) + 1e-9
    if re.search(r"\d\s*(?:\\text\{°\}|\^\\circ|°)?\s*$", last_tex.strip()):
        return 0.5 + 1e-9
    return 1e-6


def printed(a):
    """[(label, value, tolerance, is_degree)] for every chain in the answer whose left end is a plain label."""
    out = []
    for mt in maths(a):
        parts, ops = split_top(mt)
        if len(parts) < 2:
            continue
        label = parts[0].strip()
        if not re.fullmatch(r"[A-Za-z]|[a-z]\^\{2\}|\\(?:sin|cos|tan)\s*[A-Z]", label):
            continue
        last = parts[-1]
        try:
            v = evaluate(last)
        except (FreeVar, ParseError, ZeroDivisionError, ValueError):
            continue
        is_deg = bool(re.fullmatch(r"[A-Z]", label)) and bool(re.search(r"\\text\{°\}|\^\\circ|°", last))
        tol = half_unit(last) if "approx" in ops else 1e-6
        if is_deg:
            v /= DEG
        out.append((label, v, tol, is_deg))
    return out


def truth_for(label, tri):
    m = re.fullmatch(r"\\(sin|cos|tan)\s*([A-Z])", label)
    if m:
        return getattr(math, m.group(1))(tri[m.group(2)]), False
    m = re.fullmatch(r"([a-z])\^\{2\}", label)
    if m:
        return tri[m.group(1)] ** 2, False
    if label in "ABC":
        return tri[label] / DEG, True
    return tri[label], False


def compare(item, a, tris, unknown):
    seen = Counter()
    labels_done = set()
    for label, v, tol, is_deg in printed(a):
        k = seen[label]
        seen[label] += 1
        if k >= len(tris):
            fail(item, f"{label} is printed {k + 1} times but only {len(tris)} triangle(s) exist")
            continue
        want, deg = truth_for(label, tris[k])
        if label in "ABC" and len(label) == 1 and not is_deg:
            fail(item, f"{label} is printed without a degree mark")
        if abs(v - want) > max(tol, 1e-6 if tol < 1e-3 else tol) and abs(v - want) > tol * max(1, abs(want)) * (1 if tol < 1e-3 else 0):
            fail(item, f"{label} printed {v:.6g} but the triangle gives {want:.6g}")
        labels_done.add(label)
    for u in unknown:
        if seen[u] < len(tris):
            fail(item, f"the answer never gives {u}" + ("" if len(tris) == 1 else f" for every triangle ({seen[u]} of {len(tris)})"))


def unknowns(tris0, angles, sides):
    return [L for L in "ABC" if L not in angles] + [s for s in "abc" if s not in sides]


def envs_of(tris):
    return [{**{L: t[L] for L in "ABC"}, **{s: t[s] for s in "abc"}} for t in tris]


def gather(item):
    html = item["stem"] + " " + " ".join(p["q"] for p in item["parts"])
    return givens(html)


# ---------------------------------------------------------------- TE4
@check("right_triangle_angle_given", "right_triangle_sides_given")
def te4(item):
    angles, sides = gather(item)
    if angles.get("C") != math.pi / 2:
        fail(item, "the right angle C = 90 is not stated")
        return
    tris = solve(angles, sides)
    if len(tris) != 1:
        fail(item, "the givens do not make one triangle")
        return
    compare(item, item["parts"][0]["a"], tris, [u for u in unknowns(tris, angles, sides)])
    env_chains(item, item["parts"][0]["a"], envs_of(tris), strict_domain=True)


# ---------------------------------------------------------------- TE5
@check("law_sines_aas", "law_cosines_sss", "law_cosines_sas")
def te5_single(item, ):
    angles, sides = gather(item)
    tris = solve(angles, sides)
    if len(tris) != 1:
        fail(item, "the givens do not make exactly one triangle")
        return
    a = item["parts"][0]["a"]
    compare(item, a, tris, unknowns(tris, angles, sides))
    env_chains(item, a, envs_of(tris), strict_domain=True)
    first_law = "Law of Sines" if len(angles) >= 2 else "Law of Cosines"
    if first_law not in a:
        fail(item, f"the first law named should be the {first_law}")
    if len(angles) >= 2 and "Law of Cosines" in a:
        fail(item, "the Law of Cosines is named for an angle-angle-side problem")


@check("ambiguous_ssa")
def te5_ssa(item):
    angles, sides = gather(item)
    tris = solve(angles, sides)
    a = item["parts"][0]["a"]
    words = strip_text(a).lower()
    said = 2 if "two triangles" in words else 1 if "one triangle" in words else 0 if (re.search(r"no triangle|zero triangle", words) or r"\(0\) triangles" in a) else None
    if said != len(tris):
        fail(item, f"the answer says {said} triangle(s); the givens make {len(tris)}")
    if not tris:
        return
    tris.sort(key=lambda t: t["B"] if "B" in t else 0)
    # acute second angle first, as the answer lists it
    yL = next(s for s in sides if s != next(iter(angles)).lower())
    Y = UP[yL]
    tris.sort(key=lambda t: t[Y])
    compare(item, a, tris, [L for L in "ABC" if L not in angles] + [s for s in "abc" if s not in sides])
    env_chains(item, a, envs_of(tris))
    for mt in maths(a):                                   # the 'x \lt y \lt z' claim that decides the case
        if r"\lt" in mt:
            vals = [evaluate(t) for t in mt.split(r"\lt")]
            if any(u >= v for u, v in zip(vals, vals[1:])):
                fail(item, f"the printed inequality {mt} is false")
    if "Law of Sines" not in a:
        fail(item, "the Law of Sines is not named")


# ---------------------------------------------------------------- TE6
def tail(a):
    """(value, tolerance, is_degree) at the right end of the last chain that has an approximation sign."""
    for mt in reversed(maths(a)):
        parts, ops = split_top(mt)
        if "approx" in ops:
            last = parts[-1]
            v = evaluate(last)
            is_deg = bool(re.search(r"\\text\{°\}|\^\\circ|°", last))
            return (v / DEG if is_deg else v), half_unit(last), is_deg
    raise Skip()


def expect(item, a, want, label, angle=False):
    v, tol, is_deg = tail(a)
    if abs(v - want) > tol:
        fail(item, f"{label}: the answer ends at {v:.6g} but the situation gives {want:.6g}")
    env_chains(item, a, [{"h": want, "d": want, "theta": want * DEG if angle else want}])


@check("right_triangle_application")
def te6_right(item):
    p = item["parts"][0]
    q, a = p["q"], p["a"]
    if m := re.search(r"A (\d+)-foot ladder .*? height of (\d+) feet", q):
        L, h = map(float, m.groups())
        expect(item, a, math.degrees(math.asin(h / L)), "ladder angle", angle=True)
    elif m := re.search(r"From a point (\d+) feet from the base of a \w+, the angle of elevation to its top is (\d+)°", q):
        d, th = map(float, m.groups())
        expect(item, a, d * math.tan(th * DEG), "height")
    elif m := re.search(r"From the top of a (\d+)-foot cliff, the angle of depression to a boat is (\d+)°", q):
        H, th = map(float, m.groups())
        expect(item, a, H / math.tan(th * DEG), "distance from the base")
    else:
        fail(item, "scenario not recognised")


@check("law_of_cosines_application")
def te6_cos(item):
    p = item["parts"][0]
    m = re.search(r"angle of (\d+)°\. One \w+ \w+ (\d+) \w+ and the other \w+ \w+ (\d+) \w+", p["q"])
    if not m:
        fail(item, "scenario not recognised")
        return
    th, u, v = map(float, m.groups())
    expect(item, p["a"], math.sqrt(u * u + v * v - 2 * u * v * math.cos(th * DEG)), "distance apart")


@check("law_of_sines_application")
def te6_sin(item):
    q0 = item["parts"][0]["q"]
    m = re.search(r"stand (\d+(?:\.\d+)?) \w+ apart.*? is (\d+)° at the first observer and (\d+)° at the second", q0)
    if not m:
        fail(item, "scenario not recognised")
        return
    D, al, be = map(float, m.groups())
    ga = math.pi - (al + be) * DEG
    want = {"first": D * math.sin(be * DEG) / math.sin(ga), "second": D * math.sin(al * DEG) / math.sin(ga)}
    for p in item["parts"]:
        who = re.search(r"from the (first|second) observer", p["q"])
        if not who:
            fail(item, "part not recognised")
            continue
        expect(item, p["a"], want[who.group(1)], f"distance from the {who.group(1)} observer")


import vc_trig  # noqa: E402
from vbase import CHECKS  # noqa: E402

_ssa = CHECKS["ambiguous_ssa"]


def _ssa_with_static(item):
    _ssa(item)
    vc_trig.ssa_static(item)


CHECKS["ambiguous_ssa"] = _ssa_with_static
