#!/usr/bin/env python3
"""
build_canon.py - builds the Canon of Dhar documents, the amendments and the progress reports as PDFs.

    python3 tools/build_canon.py                 build every document
    python3 tools/build_canon.py spec0 pact      build only these (keys are the `key:` of each source)
    python3 tools/build_canon.py --list          list the sources: key, version, output file
    python3 tools/build_canon.py --verify        check, without rendering, that every PDF is up to date with its
                                                 source, the stylesheet, the template and the logo (used by tests)
    python3 tools/build_canon.py --html DIR      also write the intermediate HTML of each document to DIR

Where things are
    docs/canon/src/*.md        the sources of the Canon documents and of the amendments (kind: canon, amendment)
    docs/reports/src/*.md      the sources of the progress reports (kind: report)
    tools/canon/canon.css      the look: the website's six colours, Saira and JetBrains Mono, chamfered shapes, dark
    tools/canon/template.html  the page: cover, contents, body, colophon with the revision log
    docs/canon/pdf/*.pdf       output for kind canon and amendment      docs/reports/*.pdf   output for kind report
    docs/canon/pdf/MANIFEST.json   a hash of every input per PDF, so a test can tell that a PDF is out of date

A source is a Markdown file with a YAML front matter between two lines of `---`:

    key        short unique id used on the command line                 file       output file name (.pdf)
    kind       canon | amendment | report                               title      full title, e.g. "Spec0 - Overview & Vision"
    short      big cover title, e.g. SPEC0                              volume     cover label, e.g. "Volume I - Vision & Specification"
    quote      one-line epigraph under the cover title                  version    "1.1"          date   "October 26, 2026"
    status     "Ratified", "Proposed", ...                              cover      ordered extra rows of the cover table (list of one-key mappings)
    running    footer text, e.g. "DHAR - SPEC0"                         part_label top-left running header, e.g. "THE CANON OF DHAR - VOLUME I"
    contents   true to add a contents page with page numbers            colophon   optional text added to the closing line
    revisions  list of {v: "v1.0", date: "...", text: "..."}: the revision log (Master Index section 10)

The body is Markdown. `#` is a section heading, `##` a subsection, `###` below that (the document title is on the
cover, so the page has no level-one heading of its own). Tables, fenced code, `{: .class}` attribute lists and
`<div class="note" markdown="1">` blocks are available; classes: note, decision, warn (callouts), compact (on a
table's wrapping div: <div class="compact" markdown="1">), pagebreak, keep.

The Canon contains no status (Master Index section 2); this builder does not check that, tests/run_tests.py does.
"""
import argparse
import fcntl
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import tempfile

import markdown
import yaml
from jinja2 import Template
from pypdf import PdfReader, PdfWriter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON_SRC = os.path.join(ROOT, "docs", "canon", "src")
REPORT_SRC = os.path.join(ROOT, "docs", "reports", "src")
CANON_OUT = os.path.join(ROOT, "docs", "canon", "pdf")
REPORT_OUT = os.path.join(ROOT, "docs", "reports")
CSS_PATH = os.path.join(ROOT, "tools", "canon", "canon.css")
TEMPLATE_PATH = os.path.join(ROOT, "tools", "canon", "template.html")
FONTS_DIR = os.path.join(ROOT, "public", "assets", "fonts")
LOGO_PATH = os.path.join(ROOT, "public", "assets", "logo", "dhar-logo-on-dark.svg")
MONOGRAM_PATH = os.path.join(ROOT, "public", "assets", "logo", "dhar-monogram-on-dark.svg")
MANIFEST_PATH = os.path.join(CANON_OUT, "MANIFEST.json")
AUTHOR = "Abdullahi Baba Garba"
KINDS = ("canon", "amendment", "report")
REQUIRED = ("key", "file", "kind", "title", "short", "volume", "version", "date", "status", "running", "part_label")


# --------------------------------------------------------------------------------------------------------------------
# Sources
# --------------------------------------------------------------------------------------------------------------------
def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def parse_source(path):
    """Split a source file into (front matter dict, Markdown body). Raises ValueError on a malformed file."""
    text = read_text(path)
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError("%s: no front matter between two '---' lines" % path)
    meta = yaml.safe_load(m.group(1)) or {}
    missing = [k for k in REQUIRED if k not in meta]
    if missing:
        raise ValueError("%s: front matter lacks %s" % (path, ", ".join(missing)))
    if meta["kind"] not in KINDS:
        raise ValueError("%s: kind must be one of %s" % (path, ", ".join(KINDS)))
    meta["version"] = str(meta["version"])
    meta["date"] = str(meta["date"])
    meta["path"] = path
    return meta, m.group(2)


def source_paths():
    out = []
    for folder in (CANON_SRC, REPORT_SRC):
        if os.path.isdir(folder):
            out += sorted(os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".md"))
    return out


def load_all(strict=True):
    """All sources by key. With strict=False a malformed source (somebody else's unfinished draft) is skipped and
    reported in the second return value instead of stopping the run."""
    docs, errors = {}, []
    for p in source_paths():
        try:
            meta, body = parse_source(p)
            if meta["key"] in docs:
                raise ValueError("duplicate key %r (%s and %s)" % (meta["key"], docs[meta["key"]][0]["path"], p))
        except ValueError as e:
            if strict:
                raise
            errors.append(str(e))
            continue
        docs[meta["key"]] = (meta, body)
    return docs, errors


def out_path(meta):
    return os.path.join(REPORT_OUT if meta["kind"] == "report" else CANON_OUT, meta["file"])


# --------------------------------------------------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------------------------------------------------
def render_markdown(body):
    """Markdown to HTML. Headings are shifted down one level (the cover carries the document title)."""
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "attr_list", "md_in_html", "sane_lists", "toc"],
        extension_configs={"toc": {"baselevel": 2, "permalink": False, "anchorlink": False}},   # "#" becomes <h2>
    )
    out = md.convert(body)
    heads = []
    for m in re.finditer(r'<h([23]) id="([^"]+)">(.*?)</h\1>', out, re.S):
        text = html.unescape(re.sub(r"<[^>]+>", "", m.group(3))).strip()
        heads.append({"level": int(m.group(1)) - 1, "id": m.group(2), "text": text})
    return out, heads


def css_string(s):
    """A value for a CSS string token."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def cover_rows(meta):
    rows = [("Document", meta["title"]), ("Version", meta["version"]), ("Date", meta["date"]), ("Status", meta["status"])]
    for item in meta.get("cover") or []:
        for k, v in item.items():
            rows.append((str(k), str(v)))
    return rows


def render_html(meta, body, pages=None):
    """Complete HTML for one document. `pages` maps heading id to page number for the contents page."""
    body_html, heads = render_markdown(body)
    # a short first cell (a label such as "Stage-alpha") must not wrap at its hyphen
    def nowrap_first(m):
        return '<tr>%s<td class="nw">%s</td>' % (m.group(1), m.group(2)) if len(re.sub(r"<[^>]+>", "", m.group(2))) <= 26 else m.group(0)
    body_html = re.sub(r"<tr>(\s*)<td>((?:<code>[^<]*</code>|[^<>])+)</td>", nowrap_first, body_html)
    css = read_text(CSS_PATH).replace("{{FONTS}}", "file://" + FONTS_DIR)
    tpl = Template(read_text(TEMPLATE_PATH))
    logo = "file://" + LOGO_PATH
    mono = "file://" + MONOGRAM_PATH
    colophon_line = "%s \u00b7 v%s \u00b7 %s \u00b7 %s." % (meta["title"], meta["version"], meta["date"], meta["status"])
    if meta.get("colophon"):
        colophon_line += " " + str(meta["colophon"]).strip()
    toc = []
    if meta.get("contents"):
        for h in heads:
            if h["level"] <= 2:
                toc.append({"level": h["level"], "id": h["id"], "text": h["text"], "page": (pages or {}).get(h["id"], "")})
    return tpl.render(
        meta=meta, body=body_html, css=css, logo=logo, monogram=mono,
        cover_rows=cover_rows(meta), colophon_line=colophon_line, toc=toc,
        revisions=meta.get("revisions") or [], e=html.escape,
        run_top_left=css_string(meta["part_label"]), run_top_right=css_string("v" + meta["version"]),
        run_bottom_left=css_string(meta["running"].upper()),
        has_dates=any((r or {}).get("date") for r in (meta.get("revisions") or [])),
    ), heads


class Renderer:
    """One Chromium for the whole run."""

    def __init__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch()

    def pdf(self, html_text, pdf_path):
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
            f.write(html_text)
            tmp = f.name
        try:
            page = self._browser.new_page()
            page.goto("file://" + tmp)
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(250)
            page.pdf(path=pdf_path, prefer_css_page_size=True, print_background=True, outline=True, tagged=True)
            page.close()
        finally:
            os.unlink(tmp)

    def close(self):
        self._browser.close()
        self._pw.stop()


def norm(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def find_pages(pdf_path, heads):
    """Page number (1-based) of each heading. Chromium writes the headings into the PDF outline (bookmarks) with
    their pages, which is exact; a heading the outline lacks is searched for by its text, forward only."""
    reader = PdfReader(pdf_path)
    outline = []

    def walk(items):
        for it in items:
            if isinstance(it, list):
                walk(it)
            else:
                try:
                    outline.append((norm(it.title), reader.get_destination_page_number(it) + 1))
                except Exception:
                    pass
    walk(reader.outline)
    pages, pos = {}, 0
    for h in heads:                                   # the outline lists headings in document order
        key = norm(h["text"])
        for j in range(pos, len(outline)):
            if outline[j][0] == key and outline[j][1] > 1:
                pages[h["id"]] = outline[j][1]
                pos = j + 1
                break
    texts = [norm(p.extract_text() or "") for p in reader.pages]
    last = 1
    for h in heads:
        if h["id"] in pages:
            last = pages[h["id"]] - 1
            continue
        key = norm(h["text"])[:60]
        for i in range(max(last, 1), len(texts)):
            if key and key in texts[i]:
                pages[h["id"]] = i + 1
                last = i
                break
    return pages


def set_metadata(pdf_path, meta):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    writer.append(reader)
    writer.add_metadata({
        "/Title": meta["title"], "/Author": AUTHOR,
        "/Subject": "%s, version %s" % (meta["volume"], meta["version"]),
        "/Keywords": "Dhar, Canon of Dhar, %s" % meta["short"],
        "/Creator": "tools/build_canon.py",
    })
    with open(pdf_path, "wb") as f:
        writer.write(f)


def input_hash(meta, body):
    h = hashlib.sha256()
    for blob in (read_bytes(meta["path"]), read_bytes(CSS_PATH), read_bytes(TEMPLATE_PATH),
                 read_bytes(LOGO_PATH), read_bytes(MONOGRAM_PATH), read_bytes(os.path.abspath(__file__))):
        h.update(hashlib.sha256(blob).digest())
    return h.hexdigest()


def build_one(renderer, meta, body, html_dir=None):
    pdf_path = out_path(meta)
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    html1, heads = render_html(meta, body)
    if html_dir:
        os.makedirs(html_dir, exist_ok=True)
        with open(os.path.join(html_dir, meta["key"] + ".html"), "w", encoding="utf-8") as f:
            f.write(html1)
    renderer.pdf(html1, pdf_path)
    if meta.get("contents"):                                  # second pass: put page numbers in the contents page
        pages = find_pages(pdf_path, [h for h in heads if h["level"] <= 2])
        html2, _ = render_html(meta, body, pages)
        renderer.pdf(html2, pdf_path)
        missing = [h["text"] for h in heads if h["level"] <= 2 and h["id"] not in pages]
        if missing:
            print("  warning: no page found for: %s" % "; ".join(missing[:5]))
    set_metadata(pdf_path, meta)
    n = len(PdfReader(pdf_path).pages)
    return pdf_path, n


def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def update_manifest(entries):
    """Merge `entries` into MANIFEST.json under a file lock, so that several builds running at the same time (one per
    author or agent) never overwrite one another's entries. The write is atomic (temporary file, then rename)."""
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH + ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        m = load_manifest()
        m.update(entries)
        tmp = MANIFEST_PATH + ".tmp.%d" % os.getpid()
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(m, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp, MANIFEST_PATH)


def verify(docs):
    """Return a list of problems: missing PDF, PDF built from other inputs than the present ones."""
    manifest = load_manifest()
    problems = []
    for key, (meta, body) in sorted(docs.items()):
        p = out_path(meta)
        if not os.path.exists(p):
            problems.append("%s: %s does not exist (run tools/build_canon.py %s)" % (key, os.path.relpath(p, ROOT), key))
        elif manifest.get(key, {}).get("input") != input_hash(meta, body):
            problems.append("%s: %s is out of date with its source (run tools/build_canon.py %s)" % (key, os.path.relpath(p, ROOT), key))
    for key in manifest:
        if key not in docs:
            problems.append("%s: in MANIFEST.json but there is no source" % key)
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keys", nargs="*", help="document keys to build (default: all)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--html", metavar="DIR")
    args = ap.parse_args()

    docs, errors = load_all(strict=not args.keys)
    for e in errors:
        print("  skipped (not the document being built): %s" % e)
    if args.list:
        for key, (meta, _) in sorted(docs.items(), key=lambda kv: kv[1][0]["path"]):
            print("%-14s %-9s v%-5s %s" % (key, meta["kind"], meta["version"], os.path.relpath(out_path(meta), ROOT)))
        return 0
    if args.verify:
        problems = verify(docs)
        for p in problems:
            print("  " + p)
        print("canon PDFs: %s" % ("all %d up to date" % len(docs) if not problems else "%d problem(s)" % len(problems)))
        return 1 if problems else 0

    keys = args.keys or sorted(docs)
    unknown = [k for k in keys if k not in docs]
    if unknown:
        print("unknown key(s): %s (known: %s)" % (", ".join(unknown), ", ".join(sorted(docs))))
        return 2
    renderer = Renderer()
    try:
        for key in keys:
            meta, body = docs[key]
            pdf_path, n = build_one(renderer, meta, body, args.html)
            update_manifest({key: {"file": os.path.relpath(pdf_path, ROOT), "version": meta["version"], "pages": n,
                                   "input": input_hash(meta, body)}})
            print("  built %-14s v%-5s %2d pages  %s" % (key, meta["version"], n, os.path.relpath(pdf_path, ROOT)))
    finally:
        renderer.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
