#!/usr/bin/env python3
"""
canon_extract.py - turns one of the original Canon PDFs (September 2026, ReportLab) into a Markdown draft.

    python3 tools/canon_extract.py ORIGINAL.pdf --scaffold > docs/canon/src/KEY.md
                                                                 a complete source that builds as it is: front matter
                                                                 taken from the cover and colophon, then the body
    python3 tools/canon_extract.py ORIGINAL.pdf > draft.md       draft body + the cover as comments (for inspection)
    python3 tools/canon_extract.py ORIGINAL.pdf --body           the body only

The old PDFs use a regular scheme of fonts, which this tool reads:

    Helvetica-Bold 15.5      section heading       ->  "# 1. Title"
    Helvetica-Bold 12.3      subsection heading    ->  "## 1.1 Title"
    Times-Roman 10.1         body text            (Times-Bold -> **bold**, Times-Italic -> *italic*, Courier -> `code`)
    Courier on a whole line  code block            ->  fenced block
    Times 8.6 / Helvetica-Bold 8.3   table cells / table header row  ->  a Markdown table
    Helvetica 7.7            running header and footer (dropped)

It is a draft generator, not a finished converter: the output must be read against the original and fixed by hand
(tables whose cells wrap oddly, lists, block quotes, emphasis the fonts did not carry). Then
`tools/canon_fidelity.py` proves that no word was lost, and a visual comparison of the rendered pages checks the tables.
"""
import argparse
import re
import sys

import pdfplumber

SECTION = ("Helvetica-Bold", 15.5)
SUBSECTION = ("Helvetica-Bold", 12.3)


def style(ch):
    f = ch["fontname"].split("+")[-1]
    if f.startswith("Courier"):
        return "code"
    if "Bold" in f:
        return "bold"
    if "Italic" in f or "Oblique" in f:
        return "italic"
    return "plain"


def line_font(line):
    chars = [c for c in line["chars"] if c["text"].strip()]
    if not chars:
        return ("", 0.0)
    c = chars[0]
    return (c["fontname"].split("+")[-1], round(c["size"], 1))


def inline(chars):
    """Markdown for a run of characters, with bold, italic and code markers where the font changes."""
    out, cur, buf = [], None, []

    def flush():
        nonlocal buf, cur
        if not buf:
            return
        text = "".join(buf)
        lead = len(text) - len(text.lstrip())
        trail = len(text) - len(text.rstrip())
        core = text.strip()
        if core:
            mark = {"code": "`", "bold": "**", "italic": "*"}.get(cur, "")
            out.append(text[:lead] + mark + core + mark + (text[len(text) - trail:] if trail else ""))
        else:
            out.append(text)
        buf = []

    prev = None
    for c in chars:
        s = style(c)
        if prev is not None and c["text"].strip() and prev["text"].strip() and c["x0"] - prev["x1"] > 1.0:
            buf.append(" ")                      # a gap wider than a letter space is a word space
        if s != cur and c["text"].strip():
            flush()
            cur = s
        buf.append(c["text"])
        prev = c
    flush()
    return "".join(out).replace("****", "").replace("**  **", " ")


def cover_fields(page):
    """The cover page's key/value table (Document, Version, Date, ...) as a dict-like list, plus title bits."""
    rows, quote, short, volume = [], "", "", ""
    for ln in page.extract_text_lines(return_chars=True):
        font, size = line_font(ln)
        t = ln["text"].strip()
        if size == 20.0 and font == "Helvetica-Bold" and re.match(r"^(Volume|Canon)", t):
            volume = t
        elif size >= 24:
            short = t
        elif size == 20.0 and not short:
            short = t
        elif font == "Times-Italic" and size >= 11:
            quote = t.strip("\u201c\u201d\"")
        elif font == "Helvetica-Bold" and size == 9.0:
            m = re.match(r"^(Document|Version|Date|Status|Part of|Depends on|Precedes|Feeds into|Audience|Author & Project Lead|Scope|Edition)\s+(.*)$", t)
            if m:
                rows.append((m.group(1), m.group(2)))
    return rows, quote, short, volume


def footer_subtitle(page, short):
    """The words after the dash in the middle of the running footer ("Security & Assurance")."""
    for ln in page.extract_text_lines(return_chars=False):
        t = ln["text"].strip()
        if t.upper().startswith("DHAR \u2014 ") and re.search(r"\d+$", t):
            mid = re.sub(r"^DHAR \u2014 .*?\b" + re.escape(short.split()[0].title()), short.split()[0].title(), t, count=1, flags=re.I)
            m = re.search(r"\u2014 (.+?)\s+\d+$", mid)
            if m:
                return m.group(1).strip()
    return ""


def table_markdown(header_line, rows):
    ncol = len(header_line)
    header_line = [h.replace("**", "") for h in header_line]
    md = ["| " + " | ".join(header_line) + " |", "| " + " | ".join(["---"] * ncol) + " |"]
    for r in rows:
        cells = [" ".join(r.get(i, [])).strip().replace("|", "\\|") for i in range(ncol)]
        md.append("| " + " | ".join(cells) + " |")
    return "\n".join(md)


def split_columns(line):
    """For a table header or body line: [(x0, text)] split where the horizontal gap is large."""
    words = line["chars"]
    cells, cur, last_x1 = [], [], None
    for c in words:
        if last_x1 is not None and c["x0"] - last_x1 > 9 and c["text"].strip() and cur:
            cells.append(cur)
            cur = []
        cur.append(c)
        last_x1 = c["x1"]
    if cur:
        cells.append(cur)
    out = []
    for cs in cells:
        first = next((c for c in cs if c["text"].strip()), None)
        if first:
            out.append((first["x0"], inline(cs).strip()))
    return out


def body_markdown(pdf, title_guess="", colophon_out=None):
    colophon = None
    blocks = []                      # finished Markdown blocks
    para, code = [], []
    table = None                     # {"cols": [x0...], "head": [...], "rows": [ {col: [text]} ], "last_top": float}
    last_top, last_bottom = None, None

    def flush_para():
        nonlocal para
        if para:
            joined = ""
            for piece in para:
                if joined and re.search(r"[A-Za-z0-9]-$", joined) and re.match(r"[A-Za-z0-9]", piece):
                    joined += piece              # a compound broken at its hyphen at the end of a line
                else:
                    joined += (" " if joined else "") + piece
            blocks.append(joined.strip())
            para = []

    def flush_code():
        nonlocal code
        if code:
            blocks.append("```\n" + "\n".join(code) + "\n```")
            code = []

    def flush_table():
        nonlocal table
        if table:
            blocks.append(table_markdown(table["head"], table["rows"]))
            table = None

    new_page = False
    for pi, page in enumerate(pdf.pages):
        if pi == 0:
            continue                 # cover
        new_page = True
        lines = page.extract_text_lines(return_chars=True)
        for ln in lines:
            bullet_glyph = any(c["text"].startswith("(cid:") for c in ln["chars"][:2])
            if bullet_glyph:
                ln = dict(ln)
                ln["chars"] = [c for c in ln["chars"] if not c["text"].startswith("(cid:")]
                ln["text"] = re.sub(r"(\(cid:\d+\))+\s*", "", ln["text"])
            font, size = line_font(ln)
            text = ln["text"].strip()
            if not text:
                continue
            if colophon is not None or (text.startswith(title_guess) and "· v" in text):
                if all(style(c) == "italic" for c in ln["chars"] if c["text"].strip()):
                    if colophon is None:
                        colophon = []
                    colophon.append(inline(ln["chars"]).strip().strip("*"))
                    continue
            if font == "Helvetica" and size == 7.7:                  # running footer
                continue
            if re.match(r"^DHAR —", text) and re.search(r"\d+$", text):
                continue
            top = ln["top"]
            if (font, size) in (SECTION, SUBSECTION):
                flush_para(); flush_code(); flush_table()
                blocks.append(("# " if (font, size) == SECTION else "## ") + inline(ln["chars"]).replace("**", "").strip())
                last_top = None
                continue
            if font == "Helvetica-Bold" and size == 8.3:             # table header row
                flush_para(); flush_code(); flush_table()
                cols = split_columns(ln)
                table = {"cols": [x for x, _ in cols], "head": [t for _, t in cols], "rows": [], "last_top": top, "cur": None}
                continue
            if table is not None and size in (8.6, 8.3, 9.0) and not font.startswith("Helvetica-Bold"):
                gap = top - table["last_top"]
                table["last_top"] = top
                cells = split_columns(ln)
                if table["cur"] is None or gap > 14:
                    table["cur"] = {}
                    table["rows"].append(table["cur"])
                for x, t in cells:
                    ci = max([i for i, cx in enumerate(table["cols"]) if cx <= x + 4] or [0])
                    table["cur"].setdefault(ci, []).append(t)
                continue
            if table is not None:
                flush_table()
            if font.startswith("Courier") and all(style(c) == "code" for c in ln["chars"] if c["text"].strip()):
                flush_para()
                indent = max(0, int((ln["x0"] - 71) / 4.5))
                code.append(" " * indent + text)
                continue
            flush_code()
            md = inline(ln["chars"]).strip()
            if bullet_glyph or re.match(r"^(•|▪|-)\s", md) or md.startswith("•"):
                flush_para()
                para.append("- " + md.lstrip("•▪- ").strip())
                last_top = top
                new_page = False
                continue
            if re.match(r"^\*\*\d+\.", md) or re.match(r"^\d+\.\s", md):
                flush_para()
                para.append(md)
                last_top = top
                new_page = False
                continue
            if new_page and para and re.search(r"[.:?!”)\]*]$", para[-1]) is None:
                pass                                                   # a paragraph running on across the page break
            elif new_page and para:
                flush_para()
            elif last_top is not None and top - last_top > 19 and para:             # paragraph gap
                flush_para()
            new_page = False
            para.append(md)
            last_top = top
        last_top = None
    flush_para(); flush_code(); flush_table()
    # list items were collected one per paragraph entry; blank lines between list items are removed
    if colophon_out is not None and colophon:
        colophon_out.extend(colophon)
    text = "\n\n".join(b for b in blocks if b)
    text = re.sub(r"(?m)^\*\*(\d+)\.\*\*\s*", r"\1. ", text)
    text = re.sub(r"(?m)^\*\*(\d+)\.\s*([^*]+?)\*\*\s*", r"\1. **\2** ", text)
    text = re.sub(r"\n\n(- )", r"\n\1", text)
    text = re.sub(r"\n\n(\d+\. )", r"\n\1", text)
    return text + "\n"


ROMAN = {"I": "Volume I", "II": "Volume II", "III": "Volume III", "IV": "Volume IV"}

KEYS = {   # original file stem -> (key, new short title)
    "Canon_of_Dhar_Master_Index": ("master_index", "Master Index"),
    "Spec0_Overview_and_Vision": ("spec0", "Spec0"),
    "Spec1_Language_Specification": ("spec1", "Spec1"),
    "StageAlpha_Forge_of_Dhar": ("stage_alpha", "Stage-alpha"),
    "6_StageBeta_Honing_Dhar": ("stage_beta", "Stage-beta"),
    "7_StageGamma_Optimizing_Dhar": ("stage_gamma", "Stage-gamma"),
    "8_StageDelta_Gearing_Dhar": ("stage_delta", "Stage-delta"),
    "9_StageEpsilon_Deploying_Dhar": ("stage_epsilon", "Stage-epsilon"),
    "11_GuildOfDhar_Governance": ("guild", "The Guild of Dhar"),
    "12_TemperingDhar_Security_Assurance": ("tempering", "Tempering Dhar"),
    "13_CastingDhar_Adoption_Education": ("casting", "Casting Dhar"),
    "14_FuelingDhar_Business_Funding": ("fueling", "Fueling Dhar"),
    "15_HallmarkOfDhar_Legal": ("hallmark", "The Hallmark of Dhar"),
    "ThePact_Program_Management": ("pact", "The Pact of Developing Dhar"),
}


def yaml_str(v):
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def scaffold(path, pdf):
    """A complete, buildable source for the document: v-same-as-original front matter and the extracted body."""
    import os
    stem = os.path.splitext(os.path.basename(path))[0]
    key, short = KEYS.get(stem, (re.sub(r"\W+", "_", stem).lower(), stem))
    rows, quote, _, volume = cover_fields(pdf.pages[0])
    cov = dict(rows)
    title = cov.get("Document", short)
    colophon = []
    body = body_markdown(pdf, title.split(" \u2014 ")[0], colophon)
    col = " ".join(colophon)
    note = ""
    revisions = []
    m = re.search(r"Revision log:\s*(.*)$", col)
    if m:
        rest = m.group(1).strip()
        mm = re.match(r"(v[\d.]+)\s*[\u2014-]\s*(.*)$", rest)
        revisions = [(mm.group(1), mm.group(2).strip()) if mm else ("v" + cov.get("Version", "1.0"), rest)]
        col = col[:m.start()].strip()
    m = re.search(r"(Ratified|Proposed|Draft)\.\s*(.*)$", col)
    if m:
        note = m.group(2).strip()
    vol_no = ""
    mv = re.search(r"Volume (I{1,3}|IV)\b", volume or cov.get("Part of", ""))
    if mv:
        vol_no = mv.group(1)
    part_label = "THE CANON OF DHAR \u00b7 " + ROMAN.get(vol_no, "VOLUME").upper() if vol_no else "THE CANON OF DHAR"
    sub = footer_subtitle(pdf.pages[1], short) if len(pdf.pages) > 1 else ""
    running = "DHAR \u2014 " + short.upper() + (" \u00b7 " + sub if sub else "")
    nheads = len(re.findall(r"(?m)^#{1,2} ", body))
    out = ["---", "key: " + key, "file: " + os.path.basename(path).replace(".pdf", "") + ".pdf", "kind: canon",
           "volume: " + yaml_str(volume), "short: " + yaml_str(short), "title: " + yaml_str(title),
           "quote: " + yaml_str(quote), "version: " + yaml_str(cov.get("Version", "1.0")),
           "date: " + yaml_str(cov.get("Date", "")), "status: " + yaml_str(cov.get("Status", "Ratified")),
           "running: " + yaml_str(running), "part_label: " + yaml_str(part_label)]
    if nheads >= 9:
        out.append("contents: true")
    extra = [(k, v) for k, v in rows if k not in ("Document", "Version", "Date", "Status")]
    if extra:
        out.append("cover:")
        out += ["  - %s: %s" % (yaml_str(k), yaml_str(v)) for k, v in extra]
    if note:
        out.append("colophon: " + yaml_str(note))
    out.append("revisions:")
    for v, text in revisions or [("v" + cov.get("Version", "1.0"), "First ratified edition.")]:
        out += ["  - v: " + yaml_str(v), "    date: " + yaml_str(cov.get("Date", "")), "    text: " + yaml_str(text)]
    out += ["---", ""]
    return "\n".join(out) + "\n" + body


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--body", action="store_true")
    ap.add_argument("--scaffold", action="store_true")
    args = ap.parse_args()
    if args.scaffold:
        with pdfplumber.open(args.pdf) as pdf:
            sys.stdout.write(scaffold(args.pdf, pdf))
        return 0
    with pdfplumber.open(args.pdf) as pdf:
        rows, quote, short, volume = cover_fields(pdf.pages[0])
        title = dict(rows).get("Document", "")
        colophon = []
        body = body_markdown(pdf, title.split(" — ")[0] if title else "", colophon)
        if args.body:
            sys.stdout.write(body)
            return 0
        sys.stdout.write("---\n# cover of the original (fill the real front matter from this)\n")
        sys.stdout.write("# short: %s\n# volume: %s\n# quote: %s\n" % (short, volume, quote))
        for k, v in rows:
            sys.stdout.write("# %s: %s\n" % (k, v))
        for c in colophon:
            sys.stdout.write("# colophon: %s\n" % c)
        sys.stdout.write("---\n\n")
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
