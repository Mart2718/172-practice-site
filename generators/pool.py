"""Export the bank to the student practice site.

    python3 generators/pool.py                    # all standards that have bank files, 12 versions each
    python3 generators/pool.py --only FN1,FN2     # just these
    python3 generators/pool.py --versions 20
    python3 generators/pool.py --check            # validate site/pool without regenerating

Writes
  site/pool/index.json          the 38 standards, with counts
  site/pool/<CODE>.json         families (hint, common slips, tier) and items (one per version)
  site/pool/figures/*.svg       graphs and mapping diagrams used by the items

Rules this script enforces (see SCHEMA.md, "Student site pool"):
  * Pool versions use seeds from 100000 up, so they never reuse a seed printed in the book.
  * A version whose text matches a book version, or an earlier pool version, is dropped.
  * Only `checked`, `audited` or `published` problems are exported. `draft` and `proposed` are skipped.
  * Items from bank/fixed/*.yaml (hand-written problems such as the Practice Exam 1 review set)
    are exported as written.
  * Math is normalised for MathJax + MathSpeak: degrees are \\text{°}, < and > inside math are
    \\lt and \\gt, and inline style attributes are removed (the site's CSP forbids them).
  * Every item is checked: balanced math delimiters, a non-empty answer for every part, alt text
    for every figure.
"""
import argparse
import glob
import importlib
import json
import os
import re
import shutil
import sys
import tempfile

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import common  # noqa: E402
from common import rng_for  # noqa: E402
from build import figures_of, table_meta  # noqa: E402

POOL = os.path.join(ROOT, "site", "pool")
FIGS = os.path.join(POOL, "figures")
SEED_BASE = 100_000
FROZEN_OK = ("checked", "audited", "published")   # "checked": passed the template asserts and verify_pool; awaiting an outside audit
CHECKIT = "https://tbil.org/preview/precalculus/exercises/#/bank/{code}/"
EXAM_OF_CHAPTER = {1: "Exam 1", 2: "Exam 1", 3: "Exam 2", 4: "Exam 2", 5: "Final only"}


# ---------------------------------------------------------------- normalising text
def _fix_math(s):
    """Apply MathJax/MathSpeak conventions inside \\( \\) and \\[ \\]."""
    def fix(body):
        body = re.sub(r"\^\s*\{\s*\\circ\s*\}|\^\s*\\circ(?![A-Za-z])", r"\\text{°}", body)
        body = body.replace("<", r"\lt ").replace(">", r"\gt ")
        # a list of ordered pairs may wrap between pairs on a narrow screen (WCAG 1.4.10 reflow)
        body = re.sub(r"\)\s*,\s*\(", r"), \\allowbreak (", body)
        return body
    s = re.sub(r"\\\((.*?)\\\)", lambda mt: r"\(" + fix(mt.group(1)) + r"\)", s, flags=re.S)
    s = re.sub(r"\\\[(.*?)\\\]", lambda mt: r"\[" + fix(mt.group(1)) + r"\]", s, flags=re.S)
    return s


def clean_html(s):
    """Normalise one HTML fragment from a template or a fixed item."""
    if s is None:
        return s
    # the 'A student's work' box: replace inline styles with a class
    s = re.sub(r"<div style=['\"][^'\"]*border-left[^'\"]*['\"]>", '<div class="work">', s)
    s = re.sub(r"\s+style=(['\"]).*?\1", "", s)
    s = s.replace("<br/>", "<br>")
    # tables from html_table(): modern markup, and numbers as math so a minus sign is a real minus
    def tbl(mt):
        inner = re.sub(r"<td>(-?\d+(?:\.\d+)?)</td>", r"<td>\\(\1\\)</td>", mt.group(1))
        return f'<div class="table-wrap"><table class="data">{inner}</table></div>'
    s = re.sub(r'<table border="1" cellpadding="8">(.*?)</table>', tbl, s, flags=re.S)
    return _fix_math(s)


def numeric_cell(c):
    """Bare numbers in tables become math so the minus sign is a real minus."""
    c = str(c)
    if "\\(" in c:
        return c
    if re.fullmatch(r"-?\d+(\.\d+)?", c):
        return rf"\({c}\)"
    return c


# ---------------------------------------------------------------- checks
def check_item(it):
    errs = []
    blob_parts = [it["stem"]] + [p["q"] for p in it["parts"]] + [p["a"] for p in it["parts"]]
    for s in blob_parts:
        if s.count(r"\(") != s.count(r"\)"):
            errs.append("unbalanced \\( \\)")
        if s.count(r"\[") != s.count(r"\]"):
            errs.append("unbalanced \\[ \\]")
        if re.search(r"\\\((?:(?!\\\)).)*[<>]", s, flags=re.S):
            errs.append("bare < or > inside math")
        if re.search(r"\bNone\b|\bnan\b|\{\{|\}\}\}", s):
            errs.append("placeholder text in item")
    if not it["parts"]:
        errs.append("no parts")
    for p in it["parts"]:
        if not p["q"].strip() or not re.sub(r"<[^>]+>|\s", "", p["a"]):
            errs.append("empty part or answer")
    for f in it.get("figures", []):
        if not f.get("alt", "").strip():
            errs.append("figure without alt text")
        if not os.path.exists(os.path.join(POOL, f["src"])):
            errs.append(f"missing figure file {f['src']}")
    if "style=" in json.dumps(it):
        errs.append("inline style attribute")
    return errs


# ---------------------------------------------------------------- figures and output shaping
def _copy_svg(tmpdir, rel_png, new_name):
    """Template wrote <tmp>/<ch>/<name>.png and .svg. Keep only the SVG, renamed."""
    src = os.path.join(tmpdir, os.path.splitext(rel_png)[0] + ".svg")
    if not os.path.exists(src):
        raise FileNotFoundError(src)
    svg = open(src, encoding="utf-8").read()
    svg = re.sub(r"\s*<dc:date>.*?</dc:date>", "", svg, flags=re.S)  # builds stay reproducible
    os.makedirs(FIGS, exist_ok=True)
    open(os.path.join(FIGS, new_name + ".svg"), "w", encoding="utf-8").write(svg)
    return f"figures/{new_name}.svg"


def shape(out, item_id, tmpdir):
    """Template output -> site item (without hint/slips; those live on the family)."""
    figs = []
    for k, f in enumerate(figures_of(out)):
        name = f"{item_id}" if len(figures_of(out)) == 1 else f"{item_id}-{k + 1}"
        d = {"src": _copy_svg(tmpdir, f["file"], name), "alt": clean_html(f["alt"])}
        if f.get("label"):
            d["label"] = f["label"]
        if f.get("table"):
            heads, caption, toggle = table_meta(f)
            d["table"] = {"caption": clean_html(caption), "toggle": toggle,
                          "headers": [clean_html(h) for h in heads],
                          "rows": [[clean_html(numeric_cell(c)) for c in r] for r in f["table"]]}
        figs.append(d)
    item = {"id": item_id, "stem": clean_html(out["stem"]),
            "parts": [{"q": clean_html(q), "a": clean_html(a)} for q, a in out["parts"]]}
    if figs:
        item["figures"] = figs
    return item


def signature(out):
    figs = [f["alt"] for f in figures_of(out)]
    return json.dumps({"s": clean_html(out["stem"]), "p": [[clean_html(q), clean_html(a)] for q, a in out["parts"]],
                       "f": figs}, sort_keys=True)


def run_template(gen, prob, seed, tag, tmpdir):
    fn = gen.TEMPLATES[prob["template"]]
    args = dict(prob.get("args") or {})
    if "fname_tag" in fn.__code__.co_varnames[:fn.__code__.co_argcount]:
        args["fname_tag"] = tag
    common.FIG_DIR = tmpdir
    return fn(rng_for(seed), **args)


# ---------------------------------------------------------------- one standard
def export_bank(std, path, n_versions, report):
    bank = yaml.safe_load(open(path))
    gen = importlib.import_module(bank["generator"])
    tmp = tempfile.mkdtemp(prefix="pool_")
    try:
        # every printed book version, for dedupe
        book_sigs = set()
        for p in bank["problems"]:
            try:
                book_sigs.add(signature(run_template(gen, p, p["seed"], p["id"] + "-book", tmp)))
            except Exception as e:  # a book problem failing is a bank bug; surface it
                raise SystemExit(f"{p['id']}: book version does not build: {e}")
        families, items = {}, []
        for fi, p in enumerate(bank["problems"]):
            if p["status"] not in FROZEN_OK:
                report.append(f"  skip {p['id']} (status {p['status']})")
                continue
            types = p["item_type"] if isinstance(p["item_type"], list) else [p["item_type"]]
            fam = {"tier": p["tier"], "types": types, "hint": p.get("hint", ""), "slips": p.get("slips", [])}
            if not fam["hint"]:
                report.append(f"  warn {p['id']}: no hint")
            if p.get("bridge_note"):
                fam["bridge_note"] = p["bridge_note"]
            families[p["id"]] = fam
            seen, made, tries, failed = set(book_sigs), 0, 0, 0
            while made < n_versions and tries < 400:
                seed = SEED_BASE + 1000 * fi + tries
                tries += 1
                tag = f"{p['id']}.v{made + 1:02d}"
                try:
                    out = run_template(gen, p, seed, tag, tmp)
                except (AssertionError, ValueError, ZeroDivisionError, KeyError, IndexError, TypeError):
                    failed += 1
                    continue
                sig = signature(out)
                if sig in seen:
                    continue
                item = shape(out, tag, tmp)
                item["family"] = p["id"]
                item["seed"] = seed
                errs = check_item(item)
                if errs:
                    raise SystemExit(f"{tag} (seed {seed}): {'; '.join(sorted(set(errs)))}")
                seen.add(sig)
                items.append(item)
                made += 1
            if fam.get("bridge_note") is None:
                fam.pop("bridge_note", None)
            report.append(f"  {p['id']:<10} {p['tier']:<10} {made} versions  ({failed} draws rejected by the template's own asserts)")
        return families, items
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def export_fixed(code_to_items, report):
    """Hand-written items: bank/fixed/*.yaml. Each item names its standard."""
    n = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "bank", "fixed", "*.yaml"))):
        data = yaml.safe_load(open(path))
        src = data.get("source", os.path.basename(path))
        for raw in data["items"]:
            figs = []
            for k, f in enumerate(raw.get("figures") or []):
                src_file = os.path.join(os.path.dirname(path), "assets", f["file"])
                ext = os.path.splitext(f["file"])[1]
                dst = f"{raw['id']}" + (f"-{k + 1}" if len(raw["figures"]) > 1 else "") + ext
                os.makedirs(FIGS, exist_ok=True)
                shutil.copyfile(src_file, os.path.join(FIGS, dst))
                d = {"src": f"figures/{dst}", "alt": clean_html(f["alt"])}
                if f.get("label"):
                    d["label"] = f["label"]
                if f.get("table"):
                    t = f["table"]
                    d["table"] = {"caption": clean_html(t["caption"]), "toggle": t.get("toggle", "Table of the labeled points"),
                                  "headers": [clean_html(h) for h in t["headers"]],
                                  "rows": [[clean_html(numeric_cell(c)) for c in r] for r in t["rows"]]}
                figs.append(d)
            stem = clean_html(raw["stem"])
            if raw.get("table"):
                stem += "\n" + data_table(raw["table"])
            item = {"id": raw["id"], "family": raw["id"], "stem": stem,
                    "parts": [{"q": clean_html(p["q"]), "a": clean_html(p["a"])} for p in raw["parts"]]}
            if figs:
                item["figures"] = figs
            errs = check_item(item)
            if errs:
                raise SystemExit(f"{raw['id']}: {'; '.join(sorted(set(errs)))}")
            fam = {"tier": "review", "types": [raw.get("item_type", raw["standard"])], "hint": raw.get("hint", ""),
                   "slips": raw.get("slips", []), "source": src}
            code_to_items.setdefault(raw["standard"], ([], {}))
            code_to_items[raw["standard"]][1][raw["id"]] = fam
            code_to_items[raw["standard"]][0].append(item)
            n += 1
    report.append(f"  fixed items: {n}")


def data_table(t):
    """Accessible HTML table for a fixed item. t: caption, headers, rows; row_headers: true makes column 1 <th scope=row>."""
    th = "".join(f'<th scope="col">{clean_html(h)}</th>' for h in t["headers"])
    rows = []
    for r in t["rows"]:
        cells = [clean_html(numeric_cell(c)) for c in r]
        if t.get("row_headers"):
            first = f'<th scope="row">{cells[0]}</th>'
            rest = "".join(f"<td>{c}</td>" for c in cells[1:])
            rows.append(f"<tr>{first}{rest}</tr>")
        else:
            rows.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
    return (f'<div class="table-wrap"><table class="data"><caption>{clean_html(t["caption"])}</caption>'
            f"<thead><tr>{th}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--versions", type=int, default=12)
    ap.add_argument("--only", default="")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    standards = yaml.safe_load(open(os.path.join(ROOT, "bank", "standards.yaml")))["standards"]
    codes = [s["code"] for s in standards]
    if a.check:
        bad = 0
        for c in codes:
            p = os.path.join(POOL, f"{c}.json")
            if not os.path.exists(p):
                continue
            d = json.load(open(p))
            for it in d["items"]:
                errs = check_item(it)
                if errs:
                    bad += 1
                    print(f"{it['id']}: {'; '.join(sorted(set(errs)))}")
        print("pool check:", "FAILED" if bad else "ok")
        sys.exit(1 if bad else 0)

    only = [c for c in a.only.split(",") if c]
    report = []
    if not only:  # a full rebuild starts clean so no stale figures remain
        shutil.rmtree(POOL, ignore_errors=True)
    os.makedirs(FIGS, exist_ok=True)

    fixed = {}
    export_fixed(fixed, report)
    index = []
    for s in standards:
        code = s["code"]
        if only and code not in only:
            continue
        found = glob.glob(os.path.join(ROOT, "bank", "ch*", f"{code}.yaml"))
        families, items = {}, []
        if found:
            report.append(f"{code}: {found[0].split('bank/')[1]}")
            families, items = export_bank(s, found[0], a.versions, report)
        fx_items, fx_fams = fixed.get(code, ([], {}))
        families.update(fx_fams)
        items += fx_items
        doc = {"code": code, "title": s["title"], "families": families, "items": items}
        os.makedirs(POOL, exist_ok=True)
        with open(os.path.join(POOL, f"{code}.json"), "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, separators=(",", ":"))
        if not only or True:
            report.append(f"{code}: {len(items)} items in {len(families)} families")

    # index covers every standard, including the ones with no items yet
    for s in standards:
        code = s["code"]
        p = os.path.join(POOL, f"{code}.json")
        n_items = n_fam = 0
        if os.path.exists(p):
            d = json.load(open(p))
            n_items, n_fam = len(d["items"]), len(d["families"])
        else:
            json.dump({"code": code, "title": s["title"], "families": {}, "items": []}, open(p, "w"), separators=(",", ":"))
        index.append({"code": code, "title": s["title"], "chapter": s["chapter"], "section": s.get("section", ""),
                      "blurb": s.get("blurb", ""), "exam": EXAM_OF_CHAPTER[s["chapter"]],
                      "items": n_items, "families": n_fam, "checkit": CHECKIT.format(code=code)})
    json.dump({"standards": index}, open(os.path.join(POOL, "index.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n".join(report))
    print(f"\nwrote {len(index)} standards; {sum(i['items'] for i in index)} items")


if __name__ == "__main__":
    main()
