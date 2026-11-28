"""A small LaTeX-to-number evaluator used only by the verifier (verify_ch35.py).

It reads the math that the pool prints (fractions, roots, powers, degrees, trig and log functions) and returns a float,
so an answer can be re-computed from the printed text rather than from the generator that produced it.
Anything it does not understand raises ParseError; a symbol with no value raises FreeVar.
"""
import math
import re

DEG = math.pi / 180


class ParseError(Exception):
    pass


class FreeVar(Exception):
    pass


FUNCS = {"sin": math.sin, "cos": math.cos, "tan": math.tan,
         "cot": lambda a: 1 / math.tan(a), "sec": lambda a: 1 / math.cos(a), "csc": lambda a: 1 / math.sin(a)}
INV = {"sin": math.asin, "cos": math.acos, "tan": math.atan}
ARC = {"arcsin": math.asin, "arccos": math.acos, "arctan": math.atan}

TOKEN = re.compile(r"\s*(\\[A-Za-z]+|\d+\.?\d*|\.\d+|[A-Za-z]|[-+*/^_(){}\[\]|,=])")


def tokenize(s):
    s = s.replace(r"\left", "").replace(r"\right", "").replace(r"\dfrac", r"\frac").replace(r"\tfrac", r"\frac")
    s = s.replace(r"\,", " ").replace(r"\;", " ").replace(r"\!", " ").replace(r"\ ", " ")
    s = re.sub(r"\^\s*\{?\s*(\\circ|\\text\{°\}|°)\s*\}?", " DEGMARK ", s)
    s = s.replace(r"\text{°}", " DEGMARK ").replace("°", " DEGMARK ")
    s = s.replace("DEGMARK", "^\\circ").replace(r"\lt", "<").replace(r"\gt", ">")
    out, pos = [], 0
    s = s.strip()
    while pos < len(s):
        m = TOKEN.match(s, pos)
        if not m:
            raise ParseError(f"cannot tokenize {s[pos:pos + 12]!r}")
        out.append(m.group(1))
        pos = m.end()
    return out


class P:
    def __init__(self, toks, env):
        self.t, self.i, self.env = toks, 0, env

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def take(self, want=None):
        tok = self.peek()
        if tok is None or (want is not None and tok != want):
            raise ParseError(f"expected {want!r}, got {tok!r}")
        self.i += 1
        return tok

    # --- grammar
    def expr(self):
        v = self.term()
        while self.peek() in ("+", "-"):
            op = self.take()
            w = self.term()
            v = v + w if op == "+" else v - w
        return v

    def starts_primary(self, tok):
        if tok is None:
            return False
        if tok in ("(", "{") or re.fullmatch(r"\d+\.?\d*|\.\d+|[A-Za-z]", tok):
            return True
        return tok in (r"\pi", r"\theta", r"\frac", r"\sqrt", r"\ln", r"\log") or tok[1:] in FUNCS or tok[1:] in ARC

    def term(self):
        v = self.unary()
        while True:
            tok = self.peek()
            if tok in ("*", r"\cdot", r"\times"):
                self.take()
                v = v * self.unary()
            elif tok == "/":
                self.take()
                v = v / self.unary()
            elif self.starts_primary(tok) or (tok and tok.startswith("\\") and tok[1:] in FUNCS):
                v = v * self.unary()       # implicit multiplication
            else:
                return v

    def unary(self):
        tok = self.peek()
        if tok == "-":
            self.take()
            return -self.unary()
        if tok == "+":
            self.take()
            return self.unary()
        return self.power()

    def power(self):
        base = self.primary()
        while self.peek() == "^":
            self.take()
            if self.peek() == r"\circ":
                self.take()
                base = base * DEG
                continue
            if self.peek() == "{":
                self.take("{")
                if self.peek() == r"\circ":
                    self.take()
                    self.take("}")
                    base = base * DEG
                    continue
                e = self.expr()
                self.take("}")
            else:
                e = self.atom_token()
            base = base ** e
        return base

    def atom_token(self):
        tok = self.take()
        if re.fullmatch(r"\d+\.?\d*", tok):
            return float(tok)
        return self.value_of(tok)

    def value_of(self, tok):
        if tok == r"\pi":
            return math.pi
        if tok == "e" and "e" not in self.env:
            return math.e
        if tok in self.env:
            return self.env[tok]
        if tok == r"\theta" and "theta" in self.env:
            return self.env["theta"]
        raise FreeVar(tok)

    def group(self):
        self.take("{")
        v = self.expr()
        self.take("}")
        return v

    def func_arg(self):
        """The argument of a function written without parentheses: one primary with its degree mark or power."""
        tok = self.peek()
        if tok == "(":
            return self.primary_power()
        v = self.primary_power()
        # a bare number followed by a letter, as in "2u": treat as a product
        while tok and re.fullmatch(r"\d+\.?\d*", tok) and self.peek() and (re.fullmatch(r"[A-Za-z]", self.peek()) or self.peek() in (r"\theta", r"\pi")):
            v = v * self.primary_power()
            tok = None
        return v

    def primary_power(self):
        base = self.primary()
        if self.peek() == "^" and self.t[self.i + 1:self.i + 2] in (["\\circ"], ["{"]):
            nxt = self.t[self.i + 1:self.i + 3]
            if nxt[0] == r"\circ" or (len(nxt) > 1 and nxt[1] == r"\circ"):
                self.take("^")
                if self.peek() == "{":
                    self.take("{")
                    self.take(r"\circ")
                    self.take("}")
                else:
                    self.take(r"\circ")
                return base * DEG
        return base

    def primary(self):
        tok = self.take()
        if re.fullmatch(r"\d+\.?\d*|\.\d+", tok):
            return float(tok)
        if tok == "(":
            v = self.expr()
            self.take(")")
            return v
        if tok == "[" :
            v = self.expr()
            self.take("]")
            return v
        if tok == "{":
            v = self.expr()
            self.take("}")
            return v
        if tok == "|":
            v = self.expr()
            self.take("|")
            return abs(v)
        if tok == r"\frac":
            a = self.group()
            b = self.group()
            return a / b
        if tok == r"\sqrt":
            if self.peek() == "[":
                self.take("[")
                n = self.expr()
                self.take("]")
                a = self.group()
                return math.copysign(abs(a) ** (1 / n), a) if round(n) % 2 == 1 else a ** (1 / n)
            return math.sqrt(self.group())
        if tok == r"\ln":
            return math.log(self.func_arg())
        if tok == r"\log":
            base = 10.0
            if self.peek() == "_":
                self.take("_")
                base = self.group() if self.peek() == "{" else self.atom_token()
            return math.log(self.func_arg(), base)
        if tok[1:] in ARC:
            return ARC[tok[1:]](self.func_arg())
        if tok.startswith("\\") and tok[1:] in FUNCS:
            name = tok[1:]
            power = 1
            if self.peek() == "^":
                self.take("^")
                self.take("{")
                neg = self.peek() == "-"
                if neg:
                    self.take("-")
                k = float(self.take())
                self.take("}")
                if neg and k == 1:
                    return INV[name](self.func_arg())
                power = k
            return FUNCS[name](self.func_arg()) ** power
        if tok == r"\pi":
            return math.pi
        if tok == r"\infty":
            raise ParseError("infinity")
        if tok.startswith("\\") and tok != r"\theta":
            raise ParseError(f"unsupported {tok}")
        return self.value_of(tok)


def evaluate(s, env=None):
    p = P(tokenize(s), env or {})
    v = p.expr()
    if p.peek() is not None:
        raise ParseError(f"left over {p.peek()!r} in {s!r}")
    return v


def split_top(s):
    """Split a math string on top-level = and \\approx. Returns (parts, ops)."""
    parts, ops, depth, cur, i = [], [], 0, "", 0
    while i < len(s):
        ch = s[i]
        if ch in "{([":
            depth += 1
        elif ch in "})]":
            depth -= 1
        if depth == 0 and s.startswith(r"\approx", i):
            parts.append(cur)
            ops.append("approx")
            cur, i = "", i + len(r"\approx")
            continue
        if depth == 0 and ch == "=":
            parts.append(cur)
            ops.append("eq")
            cur, i = "", i + 1
            continue
        cur += ch
        i += 1
    parts.append(cur)
    return parts, ops


def compile_tex(s):
    """Tokenise once; the returned function evaluates the expression for an environment (faster for scans)."""
    toks = tokenize(s)

    def run(env=None):
        p = P(toks, env or {})
        v = p.expr()
        if p.peek() is not None:
            raise ParseError(f"left over {p.peek()!r}")
        return v
    return run
