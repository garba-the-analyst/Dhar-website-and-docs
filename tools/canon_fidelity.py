#!/usr/bin/env python3
"""
canon_fidelity.py - shows exactly what changed in the words of a Canon document between two PDFs.

    python3 tools/canon_fidelity.py ORIGINAL.pdf NEW.pdf [--context N] [--max-removed N] [--quiet]

Converting a Canon document from its old PDF to the new Markdown source must lose nothing by accident. This tool
extracts the text of both PDFs, drops running headers, footers and page numbers, normalises quotes, dashes and
case, and compares the two as word sequences. It prints

    REMOVED   runs of words that are in the original and not in the new document
    ADDED     the number of words that are new (the amendments), and, with --added, the runs themselves
    a summary with the share of the original's words that survive unchanged

Every REMOVED run must have a reason: either it is a deliberate amendment (a sentence rewritten, a table row
changed, a version or date on the cover) or it is an error to fix. With --max-removed N the exit status is 1 when more
than N words were removed, so a script can gate on it.
"""
import argparse
import difflib
import re
import subprocess
import sys


def pdf_text(path):
    out = subprocess.run(["pdftotext", "-raw", path, "-"], capture_output=True, text=True, check=True).stdout
    keep = []
    for line in out.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("DHAR — ") or s.startswith("DHAR - "):            # running footer of both generations
            continue
        if re.fullmatch(r"\d+\s*/\s*\d+", s) or re.fullmatch(r"v\d+(\.\d+)*", s):
            continue
        if s.startswith("THE CANON OF DHAR ·") or s.startswith("THE CANON OF DHAR ·"):
            continue
        keep.append(s)
    # a compound word broken at its hyphen at the end of a line (supply-/chain) is one word
    return re.sub(r"(?<=[A-Za-z0-9])-\n(?=[A-Za-z0-9])", "-", "\n".join(keep))


def words(text):
    text = text.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    text = text.replace("—", "-").replace("–", "-").replace(" ", " ").replace("‑", "-")
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
    text = re.sub(r"\s*/\s*", "/", text)            # peek/poke, CWE-120 / 121: spacing around a slash is layout
    toks = re.findall(r"[A-Za-z0-9À-ɏ_$%.+#<>=/:-]+|[^\sA-Za-z0-9]", text)
    # drop pure punctuation tokens: layout changes (bullets, table borders) must not count as content
    return [t.lower().strip(".,;:()[]\"'") for t in toks if re.search(r"[A-Za-z0-9]", t)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("original")
    ap.add_argument("new")
    ap.add_argument("--context", type=int, default=6, help="words of context shown around a removed run")
    ap.add_argument("--max-removed", type=int, default=None)
    ap.add_argument("--added", action="store_true", help="also print the added runs")
    ap.add_argument("--quiet", action="store_true", help="summary only")
    args = ap.parse_args()

    a, b = words(pdf_text(args.original)), words(pdf_text(args.new))
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    removed = added = kept = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            kept += i2 - i1
            continue
        if i2 > i1:
            removed += i2 - i1
            if not args.quiet:
                before = " ".join(a[max(0, i1 - args.context):i1])
                gone = " ".join(a[i1:i2])
                after = " ".join(a[i2:i2 + args.context])
                print("REMOVED (%d words): ...%s [[ %s ]] %s..." % (i2 - i1, before, gone, after))
        if j2 > j1:
            added += j2 - j1
            if args.added and not args.quiet:
                print("ADDED   (%d words): %s" % (j2 - j1, " ".join(b[j1:j2])))
    total = len(a) or 1
    print("original %d words | kept unchanged %d (%.1f%%) | removed or replaced %d | new %d"
          % (len(a), kept, 100.0 * kept / total, removed, added))
    if args.max_removed is not None and removed > args.max_removed:
        print("FAIL: %d words removed or replaced, more than the allowed %d" % (removed, args.max_removed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
