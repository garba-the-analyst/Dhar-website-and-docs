#!/usr/bin/env python3
"""
make_pdf_fonts.py: build assets/pdf-fonts.js, the fonts that go inside the PDF copy of a response.

WHY A SEPARATE FONT FILE
  The PDF is written by assets/pdf.js with no libraries. It embeds TrueType fonts directly,
  so it needs, for each font: the font file, a character -> glyph table and the glyph widths.
  This script produces all three. The file is loaded only when a respondent reaches the
  review step, so it does not slow down the survey itself.

THREE FACES
  archivo      Archivo Regular   survey wording (questions, hints, headings)  - the page's own look
  archivoBold  Archivo Bold      question text and headings
  dejavu       DejaVu Sans       what the respondent typed. It covers the letters used to write
                                 Yoruba, Igbo, Hausa and other Nigerian languages (for example
                                 e with a dot below, o with a dot below, hooked b, d and k),
                                 the naira sign, combining tone marks, Greek and common symbols.
  A character that neither font has is shown as "?" in the PDF (the emailed text keeps it).

INPUTS
  --archivo  the Latin variable woff2 from the npm package @fontsource-variable/archivo
             (files/archivo-latin-wdth-normal.woff2)
  --dejavu   DejaVuSans.ttf  (Debian/Ubuntu: /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf)
  --out      the .js file to write

USAGE
  python3 -I tools/make_pdf_fonts.py \\
      --archivo node_modules/@fontsource-variable/archivo/files/archivo-latin-wdth-normal.woff2 \\
      --dejavu /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf \\
      --out assets/pdf-fonts.js

LICENCES
  Archivo: SIL Open Font License 1.1 (assets/fonts/OFL.txt).
  DejaVu : Bitstream Vera licence with public-domain additions (assets/fonts/DEJAVU-LICENSE.txt).
  Both allow embedding in documents and redistribution of subsets.
"""
import argparse
import base64
import io
import json
import sys

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

# Unicode ranges kept from DejaVu Sans. Each is intersected with what the font actually has.
DEJAVU_RANGES = [
    (0x0020, 0x007E),   # Basic Latin
    (0x00A0, 0x00FF),   # Latin-1 Supplement
    (0x0100, 0x017F),   # Latin Extended-A
    (0x0180, 0x024F),   # Latin Extended-B (hooked b, d, k, y; Hausa)
    (0x0250, 0x02AF),   # IPA Extensions (open e and o; Yoruba, Igbo, Hausa, Akan)
    (0x02B0, 0x02FF),   # Spacing modifier letters
    (0x0300, 0x036F),   # Combining diacritical marks (tone marks, dot below)
    (0x0370, 0x03FF),   # Greek and Coptic
    (0x1E00, 0x1EFF),   # Latin Extended Additional (dot-below vowels, s with dot below)
    (0x2000, 0x206F),   # General punctuation
    (0x2070, 0x209F),   # Superscripts and subscripts
    (0x20A0, 0x20CF),   # Currency symbols (naira sign U+20A6)
    (0x2100, 0x214F),   # Letterlike symbols
    (0x2190, 0x21FF),   # Arrows
    (0x2200, 0x22FF),   # Mathematical operators
    (0x25A0, 0x25FF),   # Geometric shapes
    (0x2713, 0x2717),   # Check and cross marks
]

# What the survey's own wording needs from Archivo (everything else falls back to DejaVu).
ARCHIVO_RANGES = [
    (0x0020, 0x007E),
    (0x00A0, 0x00FF),
    (0x2013, 0x2014), (0x2018, 0x2019), (0x201C, 0x201D), (0x2022, 0x2022),
    (0x2026, 0x2026), (0x2212, 0x2212),
]

STEMV = {"archivo": 80, "archivoBold": 140, "dejavu": 80}
PS_NAME = {"archivo": "Archivo-Regular", "archivoBold": "Archivo-Bold", "dejavu": "DejaVuSans"}


def unicodes_from(ranges, cmap):
    out = []
    for lo, hi in ranges:
        out.extend(cp for cp in range(lo, hi + 1) if cp in cmap)
    return out


def subset_to_bytes(font, unicodes):
    opts = subset.Options()
    opts.layout_features = []          # the PDF writer does no text shaping
    opts.hinting = False               # smaller; PDF viewers render unhinted outlines fine
    opts.glyph_names = False
    opts.notdef_outline = True
    opts.name_IDs = [0, 1, 2, 3, 4, 6, 13, 14]
    opts.drop_tables += ["GSUB", "GPOS", "GDEF", "STAT", "DSIG", "kern", "LTSH", "VDMX", "hdmx"]
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=unicodes)
    sub.subset(font)
    font.flavor = None
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


def describe(key, data):
    """Reads the subset back and returns the metrics pdf.js needs."""
    font = TTFont(io.BytesIO(data))
    upm = font["head"].unitsPerEm
    order = font.getGlyphOrder()
    hmtx = font["hmtx"]
    adv = [hmtx[name][0] for name in order]
    cmap = {str(cp): order.index(name) for cp, name in font.getBestCmap().items()}
    os2 = font["OS/2"]
    cap = getattr(os2, "sCapHeight", 0) or int(upm * 0.7)
    head = font["head"]
    return {
        "ps": PS_NAME[key],
        "upm": upm,
        "ascent": font["hhea"].ascent,
        "descent": font["hhea"].descent,
        "cap": cap,
        "bbox": [head.xMin, head.yMin, head.xMax, head.yMax],
        "italic": 0,
        "stemv": STEMV[key],
        "cmap": cmap,
        "adv": adv,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archivo", required=True)
    ap.add_argument("--dejavu", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    faces = {}

    variable = TTFont(args.archivo)
    for key, weight in (("archivo", 400), ("archivoBold", 700)):
        font = instancer.instantiateVariableFont(TTFont(args.archivo), {"wght": weight, "wdth": 100})
        cmap = font.getBestCmap()
        data = subset_to_bytes(font, unicodes_from(ARCHIVO_RANGES, cmap))
        faces[key] = (data, describe(key, data))
    del variable

    font = TTFont(args.dejavu)
    data = subset_to_bytes(font, unicodes_from(DEJAVU_RANGES, font.getBestCmap()))
    faces["dejavu"] = (data, describe("dejavu", data))

    parts = [
        "/*\n"
        " * pdf-fonts.js: fonts for the PDF copy of a response. GENERATED by tools/make_pdf_fonts.py. Do not edit.\n"
        " *\n"
        " * archivo, archivoBold : Archivo, SIL Open Font License 1.1 (see assets/fonts/OFL.txt)\n"
        " * dejavu               : DejaVu Sans, Bitstream Vera licence (see assets/fonts/DEJAVU-LICENSE.txt)\n"
        " * Each face holds: the TrueType subset (base64), a character -> glyph table (cmap) and the\n"
        " * glyph advance widths (adv, in font units), which assets/pdf.js needs to lay out text.\n"
        " */\n"
        "window.DHAR_PDF_FONTS = {\n"
    ]
    for i, key in enumerate(("archivo", "archivoBold", "dejavu")):
        data, meta = faces[key]
        b64 = base64.b64encode(data).decode("ascii")
        wrapped = "\n".join(b64[j:j + 100] for j in range(0, len(b64), 100))
        meta = dict(meta)
        parts.append("  " + json.dumps(key) + ": {\n")
        for k in ("ps", "upm", "ascent", "descent", "cap", "bbox", "italic", "stemv"):
            parts.append("    " + k + ": " + json.dumps(meta[k]) + ",\n")
        parts.append("    cmap: " + json.dumps(meta["cmap"], separators=(",", ":")) + ",\n")
        parts.append("    adv: " + json.dumps(meta["adv"], separators=(",", ":")) + ",\n")
        parts.append("    ttf: `\n" + wrapped + "\n`\n")
        parts.append("  }" + ("," if i < 2 else "") + "\n")
    parts.append("};\n")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("".join(parts))

    for key in ("archivo", "archivoBold", "dejavu"):
        data, meta = faces[key]
        print("%-12s %7d bytes ttf, %5d characters, %5d glyphs" % (key, len(data), len(meta["cmap"]), len(meta["adv"])))
    print("wrote", args.out)


if __name__ == "__main__":
    sys.exit(main())
