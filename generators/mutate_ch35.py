"""Mutation test for verify_ch35.py: plant one small error in a printed answer and see whether the verifier notices.

Three kinds of plant, each on a copy of the item:
  final  the last number of the last chain in a random part goes up by one in its last digit;
  sign   one + or - in a random chain is flipped;
  any    a random number anywhere in a random part's math goes up by one in its last digit.
A plant is 'caught' when verify_ch35 records a failure (or cannot read the changed answer at all). A plant that survives is
either a gap in the checks or an edit to something the answer never claims (a step that no check re-derives); the list of
survivors is printed so each can be judged.

Run:  python3 generators/mutate_ch35.py [CODE ...] [--per-family N] [--seed S]
"""
import copy
import json
import os
import random
import re
import sys

import verify_ch35 as V
import vc_gen
from vbase import CHECKS, Skip, bad

NUM = re.compile(r"\d+(?:\.\d+)?")


def bump(tok):
    last = tok[-1]
    return tok[:-1] + str((int(last) + 1) % 10)


def frags(a):
    return [(m.start(1), m.end(1)) for m in re.finditer(r"\\\((.*?)\\\)", a, flags=re.S)]


def plant(a, mode, rng):
    spans = frags(a)
    if not spans:
        return None
    if mode == "final":
        cands = [(s, e) for s, e in spans if re.search(r"=|\\approx", a[s:e])]
        if not cands:
            return None
        s, e = cands[-1]
        ms = [m for m in NUM.finditer(a, s, e)]
        if not ms:
            return None
        m = ms[-1]
        return a[:m.start()] + bump(m.group()) + a[m.end():]
    if mode == "sign":
        sites = []
        for s, e in spans:
            for m in re.finditer(r"(?<=\s)[+-](?=\s)", a[s:e]):
                sites.append(s + m.start())
        if not sites:
            return None
        i = rng.choice(sites)
        return a[:i] + ("+" if a[i] == "-" else "-") + a[i + 1:]
    sites = []
    for s, e in spans:
        sites += list(NUM.finditer(a, s, e))
    if not sites:
        return None
    m = rng.choice(sites)
    return a[:m.start()] + bump(m.group()) + a[m.end():]


def run(item, tmpl):
    before = len(bad)
    try:
        for part in item["parts"]:
            V.g1(item, part["a"])
        vc_gen.generic(item, tmpl)
        fn = CHECKS.get(tmpl)
        if fn:
            fn(item)
    except Skip:
        pass
    except Exception as exc:                      # the verifier could not read the changed answer
        del bad[before:]
        return "unreadable", str(exc)[:60]
    caught = len(bad) > before
    msg = bad[before] if caught else ""
    del bad[before:]
    return ("caught" if caught else "survived"), msg


def main():
    args = sys.argv[1:]
    per = int(args[args.index("--per-family") + 1]) if "--per-family" in args else 3
    seed = int(args[args.index("--seed") + 1]) if "--seed" in args else 1
    codes = [a for a in args if a in V.CODES] or V.CODES
    rng = random.Random(seed)
    tmpl = V.family_templates()
    tally = {m: {"caught": 0, "unreadable": 0, "survived": 0} for m in ("final", "sign", "any")}
    survivors = []
    for code in codes:
        d = json.load(open(os.path.join(V.POOL, f"{code}.json")))
        by_family = {}
        for it in d["items"]:
            by_family.setdefault(it["family"], []).append(it)
        for fam, items in by_family.items():
            for it in rng.sample(items, min(per, len(items))):
                for mode in tally:
                    k = rng.randrange(len(it["parts"]))
                    a2 = plant(it["parts"][k]["a"], mode, rng)
                    if a2 is None or a2 == it["parts"][k]["a"]:
                        continue
                    mut = copy.deepcopy(it)
                    mut["parts"][k]["a"] = a2
                    res, msg = run(mut, tmpl[fam])
                    tally[mode][res] += 1
                    if res == "survived":
                        survivors.append((it["id"], tmpl[fam], mode, it["parts"][k]["a"], a2))
    print("mode    caught  unreadable  survived   kill rate")
    tot = {"caught": 0, "unreadable": 0, "survived": 0}
    for mode, t in tally.items():
        n = sum(t.values())
        print(f"{mode:6s} {t['caught']:7d} {t['unreadable']:11d} {t['survived']:9d}   {100 * (t['caught'] + t['unreadable']) / max(n, 1):5.1f}%")
        for k in tot:
            tot[k] += t[k]
    n = sum(tot.values())
    print(f"all    {tot['caught']:7d} {tot['unreadable']:11d} {tot['survived']:9d}   {100 * (tot['caught'] + tot['unreadable']) / max(n, 1):5.1f}%   ({n} plants)")
    by_t = {}
    for sid, t, mode, a, a2 in survivors:
        by_t.setdefault(t, []).append((sid, mode, a, a2))
    print("\nsurvivors by template:")
    for t, lst in sorted(by_t.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(lst):3d}  {t}")
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".mutation-survivors.json"), "w") as f:
        json.dump(survivors, f, indent=1)


if __name__ == "__main__":
    main()
