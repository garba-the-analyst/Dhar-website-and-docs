#!/usr/bin/env python3
"""
make_font.py: build the small Archivo subset that is embedded in index.html.

Why: the survey page must work with zero external requests (privacy, speed,
patchy mobile data), so the one typeface it uses is embedded as base64.
Archivo is a variable font with weight and width axes, which lets one file
cover the wide, heavy display type and the normal-width body text.

Input : the Latin variable woff2 from the npm package @fontsource-variable/archivo
Output: src/fonts/archivo-subset.woff2  (weights 400-800, widths 100-125, Basic Latin
        plus the punctuation the page actually uses)

Usage : python3 -I tools/make_font.py <input.woff2> <output.woff2>
License: Archivo is SIL OFL 1.1 (see src/fonts/OFL.txt).
"""
import sys
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset

src, dst = sys.argv[1], sys.argv[2]

font = TTFont(src)
axes = {a.axisTag: (a.minValue, a.defaultValue, a.maxValue) for a in font["fvar"].axes}
print("source axes:", axes)

# 1. Narrow the design space: body text needs 400-700, display needs up to 800;
#    widths from normal (100) to extra-expanded (125).
limits = {"wght": (400, 800)}
if "wdth" in axes:
    limits["wdth"] = (100, 125)
font = instancer.instantiateVariableFont(font, limits)

# 2. Keep only the characters the page uses (Basic Latin + typographic punctuation).
unicodes = list(range(0x20, 0x7F)) + [
    0x00A0, 0x00B7, 0x00D7, 0x00E9, 0x2013, 0x2014, 0x2018, 0x2019,
    0x201C, 0x201D, 0x2022, 0x2026, 0x2212,
]
opts = subset.Options()
opts.flavor = "woff2"
opts.layout_features = ["kern", "tnum", "lnum", "case", "ccmp", "locl"]
opts.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14]  # keep copyright + license strings
opts.notdef_outline = True
opts.hinting = False
sub = subset.Subsetter(opts)
sub.populate(unicodes=unicodes)
sub.subset(font)
font.flavor = "woff2"
font.save(dst)
print("wrote", dst)
