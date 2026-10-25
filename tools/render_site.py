#!/usr/bin/env python3
"""
render_site.py - writes everything on the website that states what Dhar can do, from three data files:

    data/status.json       what works, what is designed, milestones, direction tracks
    data/benchmarks/*.json the hyperfine results
    data/site.json         where the site and the survey are hosted (the only settings)

    python3 tools/render_site.py            rewrite the generated blocks in public/index.html
    python3 tools/render_site.py --check    change nothing; exit 1 if the page is out of date

The data files are copies. Their source of truth is the forge-of-dhar repository (status/status.json and
benchmarks/results/), because status is a statement about code and the code lives there. Refresh the copies with

    python3 tools/sync_from_forge.py ../forge-of-dhar

which also records which forge-of-dhar commit they came from (data/SOURCE.json). Never edit data/status.json or
data/benchmarks by hand: the next sync overwrites it. Edit data/site.json by hand; it belongs to this repository.

Generated blocks in public/index.html sit between markers such as <!-- status:board:start --> ... <!-- status:board:end -->
and <!--asof-short-->...<!--/asof-short-->. Do not edit inside them.
"""
import argparse
import html
import json
import os
import re
import sys
from datetime import date

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(REPO, "public", "index.html")
SURVEY_PAGE = os.path.join(REPO, "public", "survey", "index.html")
LABEL = {"works": "Works", "partly": "Partly", "designed": "Designed", "notyet": "Not yet"}
DOCS_URL = "https://github.com/garba-the-analyst/dhar-website-and-docs"

BENCH_FILES = [  # (display name, result file, group)
    ("C (raw, -O3)", "c_raw__nostdlib", "Compiled ahead of time"),
    ("C++ (-O3)", "cpp_optimized", "Compiled ahead of time"),
    ("Rust (release)", "rust_release", "Compiled ahead of time"),
    ("Dhar", "dhar_native", "Compiled ahead of time"),
    ("Node.js", "node.js_javascript", "Runtimes"),
    ("PHP 8.3", "php", "Runtimes"),
    ("Java (OpenJDK)", "java_openjdk", "Runtimes"),
    ("Python 3", "python", "Runtimes"),
]


def jload(*parts):
    with open(os.path.join(REPO, *parts), encoding="utf-8") as f:
        return json.load(f)


def load_bench():
    out = []
    for name, fn, group in BENCH_FILES:
        r = jload("data", "benchmarks", fn + ".json")["results"][0]
        out.append({"name": name, "group": group, "median": round(r["median"] * 1000, 2),
                    "mean": round(r["mean"] * 1000, 2), "sd": round(r["stddev"] * 1000, 2), "us": name == "Dhar"})
    return out


def ratios(bench):
    by = {b["name"]: b for b in bench}
    d, c = by["Dhar"], by["C (raw, -O3)"]
    rt = [by[n] for n in ("Node.js", "PHP 8.3", "Java (OpenJDK)", "Python 3")]
    res = {}
    for k in ("median", "mean"):
        f = [r[k] / d[k] for r in rt]
        res[k] = (d[k] / c[k], min(f), max(f))
    return res


def subst(text, st):
    return re.sub(r"\{(\w+)\}", lambda m: str(st["facts"].get(m.group(1), m.group(0))), text)


def code_html(text):
    return re.sub(r"`([^`]+)`", lambda m: "<code>%s</code>" % m.group(1), html.escape(text, quote=False))


def long_date(iso):
    d = date.fromisoformat(iso)
    return "%d %s %d" % (d.day, d.strftime("%B"), d.year)


def short_date(iso):
    d = date.fromisoformat(iso)
    return "%d %s %d" % (d.day, d.strftime("%b"), d.year)


def html_board(st):
    return "\n".join('      <li data-status="%s">\n        <span class="chip %s">%s</span>\n        <div><h3>%s</h3>\n        <p>%s</p></div>\n      </li>'
                     % (c["status"], c["status"], LABEL[c["status"]], code_html(c["title"]), code_html(subst(c["text"], st)))
                     for c in st["components"])


def html_rail(st):
    return "\n".join('      <li class="%s"><span class="node" aria-hidden="true">%s</span><div><h3>%s <span class="chip %s">%s</span></h3>\n        <p>%s</p></div></li>'
                     % (p["status"], p["n"], code_html(p["title"]), p["status"], LABEL[p["status"]], code_html(p["text"]))
                     for p in st["pipeline"])


def html_backends(st):
    return "\n".join('<li><span class="chip %s">%s</span></li>' % (b["status"], html.escape(b["name"])) for b in st["backends"])


def html_milestones(st):
    return "\n".join('      <li><time datetime="%s">%s</time><div><h3>%s</h3><p>%s</p></div></li>'
                     % (m["date"], short_date(m["date"]), code_html(m["title"]), code_html(subst(m["text"], st)))
                     for m in st["milestones"])


def html_tracks(st):
    out = []
    for tr in st["tracks"]:
        gates = "\n".join('          <li><span class="chip %s">%s</span><p><b>%s</b> %s</p></li>'
                          % (g["status"], LABEL[g["status"]], g["id"], code_html(g["text"])) for g in tr["gates"])
        out.append('      <article class="track cut">\n        <p class="ord" aria-hidden="true">%d</p>\n        <h3>%s</h3>\n        <p class="why">%s</p>\n        <ul class="gates">\n%s\n        </ul>\n      </article>'
                   % (tr["order"], html.escape(tr["name"]), code_html(tr["why"]), gates))
    return "\n".join(out)


def bench_json(bench):
    groups = []
    for g in ("Compiled ahead of time", "Runtimes"):
        rows = []
        for b in bench:
            if b["group"] == g:
                row = {"name": b["name"], "median": b["median"], "mean": b["mean"], "sd": b["sd"]}
                if b["us"]:
                    row["us"] = True
                rows.append(row)
        groups.append({"label": g, "rows": rows})
    data = {"source": "forge-of-dhar benchmarks/results/*.json (hyperfine, 100 runs, 3 warm-ups, taskset -c 1)", "groups": groups}
    return "\n    " + json.dumps(data, indent=1).replace("\n", "\n    ") + "\n    "


def survey_pieces(site):
    """The survey is a page of this website (public/survey/), served from the same address, so the links
    are relative and always shown. There is no separate host and no setting to leave empty."""
    return {
        "survey-hero": '<a class="btn quiet" href="survey/">Shape Dhar: take the survey</a>',
        "survey-call": '<a class="btn primary" href="survey/">Take the survey</a>',
        "survey-foot": '<li><a href="survey/">The survey</a></li>',
    }


def meta_block(site):
    base = (site.get("site_url") or "").strip().rstrip("/")
    if base:
        return ('<meta property="og:image" content="%s/assets/brand/og-image.jpg">\n<meta property="og:url" content="%s/">'
                % (html.escape(base, quote=True), html.escape(base, quote=True)))
    return '<meta property="og:image" content="assets/brand/og-image.jpg">'


def survey_meta_block(site):
    """The same, for the survey page (public/survey/index.html): link previews need absolute addresses."""
    base = (site.get("site_url") or "").strip().rstrip("/")
    if base:
        return ('<meta property="og:image" content="%s/assets/brand/og-image.jpg">\n<meta property="og:url" content="%s/survey/">'
                % (html.escape(base, quote=True), html.escape(base, quote=True)))
    return '<meta property="og:image" content="../assets/brand/og-image.jpg">'


def replace_block(text, name, body):
    start, end = "<!-- %s:start -->" % name, "<!-- %s:end -->" % name
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pat.search(text):
        raise SystemExit("marker %s missing in public/index.html" % start)
    return pat.sub(lambda m: start + "\n" + body + "\n" + end, text, count=1)


def replace_inline(text, name, value):
    pat = re.compile(r"<!--%s-->.*?<!--/%s-->" % (name, name), re.S)
    if not pat.search(text):
        raise SystemExit("inline marker %s missing in public/index.html" % name)
    return pat.sub(lambda m: "<!--%s-->%s<!--/%s-->" % (name, value, name), text, count=1)


def render(page, st, bench, site, src):
    t = page
    t = replace_block(t, "status:board", html_board(st))
    t = replace_block(t, "status:rail", html_rail(st))
    t = replace_block(t, "status:backends", html_backends(st))
    t = replace_block(t, "status:milestones", html_milestones(st))
    t = replace_block(t, "status:tracks", html_tracks(st))
    t = replace_block(t, "site:meta", meta_block(site))
    t = replace_inline(t, "tracks-intro", code_html(st["tracks_intro"]))
    t = replace_inline(t, "asof-short", short_date(st["as_of"]))
    t = replace_inline(t, "asof-long", long_date(st["as_of"]))
    t = replace_inline(t, "commit-forge", src["forge_code_commit"])
    t = replace_inline(t, "commit-honing", st["repos"]["honing_dhar"]["checked_commit"])
    for k, v in survey_pieces(site).items():
        t = replace_inline(t, k, v)
    t = re.sub(r'(<script type="application/json" id="bench-data">).*?(</script>)',
               lambda m: m.group(1) + bench_json(bench) + m.group(2), t, count=1, flags=re.S)
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    st, site, src = jload("data", "status.json"), jload("data", "site.json"), jload("data", "SOURCE.json")
    pages = [
        (PAGE, "public/index.html", lambda t: render(t, st, load_bench(), site, src)),
        (SURVEY_PAGE, "public/survey/index.html", lambda t: replace_block(t, "site:meta", survey_meta_block(site))),
    ]
    status = 0
    for path, name, make in pages:
        old = open(path, encoding="utf-8").read()
        new = make(old)
        if a.check:
            if old != new:
                print("%s is out of date. Run: python3 tools/render_site.py" % name)
                status = 1
            else:
                print("%s is up to date" % name)
        elif old != new:
            open(path, "w", encoding="utf-8").write(new)
            print("updated %s" % name)
        else:
            print("%s already current" % name)
    return status


if __name__ == "__main__":
    sys.exit(main())
