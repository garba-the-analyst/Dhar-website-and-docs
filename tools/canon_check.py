#!/usr/bin/env python3
"""
canon_check.py - mechanical checks on the Canon of Dhar sources (docs/canon/src/*.md) and what is derived from them.

    python3 tools/canon_check.py            run every check, print one line each, exit 1 if any failed
    python3 tools/canon_check.py -q         print only the failures

tests/run_tests.py runs the same checks (CANON section). They catch the mistakes that are easy to make and hard to see:

  STATUS     A Canon source never says what exists or how well it works (Master Index section 2). The phrases
             rejected are listed in PHRASES below and in docs/canon/AUTHORING.md section 1.
  LISTS      A Markdown list must be preceded by a blank line, or it collapses into the paragraph above it in the PDF.
  XREF       Every "Document section N" citation names a section that exists in that document's source.
  VERSIONS   A source's version equals its latest revision-log entry; its status is Ratified or Proposed.
  README     docs/canon/README.md lists every document with its current version, standing and PDF file.
  INDEX      docs/canon/AMENDMENT-INDEX.md quotes every document's latest revision-log line word for word.
  LOOK       The stylesheet and the template use only the six brand colours, no rounded corners, one dark theme.
  PDFS       Every PDF named in the manifest exists, has the manifest's page count, and was built from the present
             sources and builder (python3 tools/build_canon.py --verify).

It reads files and runs the builder's own --verify; it changes nothing.
"""
import glob
import json
import os
import re
import subprocess
import sys

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "docs", "canon", "src")
PDF = os.path.join(REPO, "docs", "canon", "pdf")
PALETTE = {"#0B0B0D", "#FF5C00", "#4B5563", "#22D3EE", "#C2410C", "#F3F4F6"}

# Whole-phrase, case-insensitive. A design term such as "the system-interface stub" of a target is not a status and is
# not listed; "is implemented as a version bump" (the RFC process) is not listed either.
PHRASES = [r"currently implemented", r"already implemented", r"not yet implemented", r"has been implemented",
           r"is a stub", r"are stubs", r"\bTODO\b", r"\bFIXME\b", r"as of today", r"at the time of writing",
           r"tests pass", r"all tests", r"\b45/45\b", r"\b108\b", r"\b64 of 64\b"]
# A line quoting the rule itself is exempt: the Master Index states what a Canon document may not say.
EXEMPT_LINES = {"master_index": ("not a status report",)}

# How a document is named in a citation -> the source key that holds it.
NAMES = {
    "Spec0": "spec0", "Spec1": "spec1", "Stage-alpha": "stage_alpha", "Stage-beta": "stage_beta",
    "Stage-gamma": "stage_gamma", "Stage-delta": "stage_delta", "Stage-epsilon": "stage_epsilon",
    "Tempering Dhar": "tempering", "Tooling Dhar": "tooling", "Casting Dhar": "casting", "Fueling Dhar": "fueling",
    "The Hallmark of Dhar": "hallmark", "Hallmark of Dhar": "hallmark", "Hallmark": "hallmark",
    "The Guild of Dhar": "guild", "Guild of Dhar": "guild", "Guild": "guild",
    "The Pact of Developing Dhar": "pact", "The Pact": "pact", "Pact": "pact", "Master Index": "master_index",
    "Amendment A-1": "a1_direction", "Amendment A-2": "a2_stage0_targets", "A-1": "a1_direction", "A-2": "a2_stage0_targets",
}
# Citations that are deliberate and name no numbered section: (citing source, cited text). "Spec0 §0" is the author's own
# name for the unnumbered opening of Spec0 ("Philosophy & Naming"), where the names Dhar and Kun are explained.
XREF_EXEMPT = {("master_index", "Spec0 §0"), ("stage_delta", "Spec0 §0")}


def sources():
    """{key: (path, front matter dict, body text)} for every source."""
    out = {}
    for path in sorted(glob.glob(os.path.join(SRC, "*.md"))):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        parts = text.split("---", 2)
        out[os.path.basename(path)[:-3]] = (path, yaml.safe_load(parts[1]), parts[2])
    return out


def result(ok, what):
    return (bool(ok), what)


def check_status(src):
    bad = []
    for key, (_, _, body) in src.items():
        for i, line in enumerate(body.splitlines(), 1):
            if any(x in line for x in EXEMPT_LINES.get(key, ())):
                continue
            for pat in PHRASES:
                if re.search(pat, line, re.I):
                    bad.append("%s.md body line %d: %r" % (key, i, pat))
    return [result(not bad, "STATUS  no source says what exists or how well it works %s" % (bad[:5] or ""))]


def check_lists(src):
    bad = []
    for key, (_, _, body) in src.items():
        lines = body.split("\n")
        incode = False
        for i, line in enumerate(lines):
            if line.startswith("```"):
                incode = not incode
                continue
            if incode or not re.match(r"^(\s*[-*] |\s*\d+\. )", line):
                continue
            prev = lines[i - 1] if i else ""
            if prev.strip() and not re.match(r"^(\s*[-*] |\s*\d+\. |\s+\S|#)", prev):
                bad.append("%s.md body line %d" % (key, i + 1))
    return [result(not bad, "LISTS   every list has a blank line before it %s" % (bad[:5] or ""))]


def headings(body):
    found, incode = set(), False
    for line in body.splitlines():
        if line.startswith("```"):
            incode = not incode
        if incode:
            continue
        m = re.match(r"^#{1,4} (\d+(?:\.\d+)*)\.? ", line)
        if m:
            found.add(m.group(1))
    return found


def check_xrefs(src):
    heads = {k: headings(v[2]) for k, v in src.items()}
    names = "|".join(sorted(map(re.escape, NAMES), key=len, reverse=True))
    pat = re.compile(r"(%s)\s+((?:§\s?\d+(?:\.\d+)*(?:\s?[–-]\s?\d+(?:\.\d+)*)?(?:\s*(?:,|and|to)\s*)?)+)" % names)
    bad, total = [], 0
    for key, (_, _, body) in src.items():
        for m in pat.finditer(body):
            target = NAMES[m.group(1)]
            if target == key:
                continue
            first = re.search(r"§\s?(\d+(?:\.\d+)*)", m.group(2)).group(0)
            if (key, "%s %s" % (m.group(1), first.replace(" ", ""))) in XREF_EXEMPT:
                continue
            for a, b in re.findall(r"§\s?(\d+(?:\.\d+)*)(?:\s?[–-]\s?(\d+(?:\.\d+)*))?", m.group(2)):
                for s in [a] + ([b] if b else []):
                    total += 1
                    if s not in heads[target]:
                        bad.append("%s.md cites %s §%s" % (key, m.group(1), s))
    return [result(not bad and total > 100, "XREF    %d section citations between documents, all to sections that exist %s" % (total, bad[:6] or ""))]


def check_versions(src):
    bad = []
    for key, (_, meta, _) in src.items():
        last = meta["revisions"][-1]["v"]
        if last != "v" + str(meta["version"]):
            bad.append("%s: version %s but latest revision %s" % (key, meta["version"], last))
        if meta["status"].split(" — ")[0] not in ("Ratified", "Proposed"):
            bad.append("%s: status %r" % (key, meta["status"]))
        if not meta["file"].endswith(".pdf"):
            bad.append("%s: file %r" % (key, meta["file"]))
    return [result(not bad and len(src) == 17, "VERSIONS 17 sources; each version equals its latest revision-log entry, each standing is Ratified or Proposed %s" % (bad or ""))]


def check_readme(src):
    with open(os.path.join(REPO, "docs", "canon", "README.md"), encoding="utf-8") as f:
        rows = [l for l in f.read().splitlines() if l.startswith("|")]
    bad = []
    for key, (_, meta, _) in src.items():
        row = [r for r in rows if "(pdf/%s)" % meta["file"] in r]
        if len(row) != 1:
            bad.append("%s: %d rows name %s" % (key, len(row), meta["file"]))
            continue
        cells = [c.strip().strip("*") for c in row[0].strip("|").split("|")]
        if cells[-3] != str(meta["version"]) or cells[-2] != meta["status"].split(" — ")[0]:
            bad.append("%s: README says %s %s, source says %s %s" % (key, cells[-3], cells[-2], meta["version"], meta["status"]))
    return [result(not bad, "README  docs/canon/README.md lists every document with its current version and standing %s" % (bad or ""))]


def check_index(src):
    with open(os.path.join(REPO, "docs", "canon", "AMENDMENT-INDEX.md"), encoding="utf-8") as f:
        index = f.read()
    missing = [k for k, (_, meta, _) in src.items() if meta["revisions"][-1]["text"] not in index]
    return [result(not missing, "INDEX   the amendment index quotes every document's latest revision-log line %s" % (missing or ""))]


def check_look():
    out = []
    for name in ("canon.css", "template.html"):
        with open(os.path.join(REPO, "tools", "canon", name), encoding="utf-8") as f:
            text = f.read()
        colours = {h.upper() for h in re.findall(r"#[0-9a-fA-F]{6}(?![0-9a-zA-Z])", text)}
        bad = []
        if colours - PALETTE:
            bad.append("colours %s" % sorted(colours - PALETTE))
        if re.search(r"\brgba?\(|\bhsla?\(|\blab\(|\blch\(|oklch\(", text):
            bad.append("rgb()/hsl()/lab() literals")
        if re.search(r"border-radius\s*:\s*[1-9]", text):
            bad.append("rounded corners")
        if "prefers-color-scheme" in text:
            bad.append("a light-theme switch")
        out.append(result(not bad, "LOOK    %s uses only the six brand colours, no rounded corners, one dark theme %s" % (name, bad or "")))
    return out


def check_pdfs(src):
    out = []
    manifest_path = os.path.join(PDF, "MANIFEST.json")
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    bad = []
    try:
        from pypdf import PdfReader
    except ImportError:
        PdfReader = None
    for key in src:
        short = {"a1_direction": "a1", "a2_stage0_targets": "a2"}.get(key, key)
        entry = manifest.get(short)
        if not entry:
            bad.append("%s not in the manifest" % key)
            continue
        path = os.path.join(REPO, entry["file"])
        if not os.path.exists(path):
            bad.append("%s: %s missing" % (key, entry["file"]))
        elif PdfReader and len(PdfReader(path).pages) != entry["pages"]:
            bad.append("%s: %d pages, manifest says %d" % (key, len(PdfReader(path).pages), entry["pages"]))
    out.append(result(not bad, "PDFS    every PDF exists and has the manifest's page count %s" % (bad or "")))
    r = subprocess.run([sys.executable, os.path.join(REPO, "tools", "build_canon.py"), "--verify"], capture_output=True, text=True)
    out.append(result(r.returncode == 0, "PDFS    every PDF was built from the present sources and builder (%s)" % (r.stdout + r.stderr).strip().splitlines()[-1][:120]))
    return out


def run_all():
    src = sources()
    results = []
    for fn in (check_status, check_lists, check_xrefs, check_versions, check_readme, check_index, check_pdfs):
        results += fn(src)
    results += check_look()
    return results


def main():
    quiet = "-q" in sys.argv[1:]
    results = run_all()
    for ok, what in results:
        if not quiet or not ok:
            print(("  ok   " if ok else "  FAIL ") + what)
    failed = [w for ok, w in results if not ok]
    print("\n%d checks, %d failed" % (len(results), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
