#!/usr/bin/env python3
"""
sync_sprite.py - copies the generated logo sprite (assets/logo/sprite.inc.html) into the site's pages
(index.html, survey/index.html, survey/relay-check.html), between the  <!-- sprite:start -->  and
<!-- sprite:end -->  markers.

Run it after tools/build_logo.py:   python3 tools/sync_sprite.py
Why inline: the logo then takes its colours from the page's CSS variables (--logo-ink, --logo-ember,
--logo-tag), which an <img> or an external SVG file cannot do. Exit status 1 if the markers are missing.
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the repository root; the site lives in public/
ROOT = os.path.join(REPO, "public")
PAGES = [os.path.join(ROOT, "index.html"), os.path.join(ROOT, "survey", "index.html"), os.path.join(ROOT, "survey", "relay-check.html")]
SPRITE = os.path.join(ROOT, "assets", "logo", "sprite.inc.html")


def main():
    sprite = open(SPRITE, encoding="utf-8").read().strip()
    pat = re.compile(r"(<!-- sprite:start -->)(.*?)(<!-- sprite:end -->)", re.S)
    status = 0
    for page_path in PAGES:
        name = os.path.relpath(page_path, ROOT)
        page = open(page_path, encoding="utf-8").read()
        if not pat.search(page):
            print("markers not found in %s" % name)
            status = 1
            continue
        new = pat.sub(lambda m: m.group(1) + "\n" + sprite + "\n" + m.group(3), page, count=1)
        if new != page:
            open(page_path, "w", encoding="utf-8").write(new)
        print("%s: sprite %s (%d bytes)" % (name, "updated" if new != page else "already current", len(sprite)))
    return status


if __name__ == "__main__":
    sys.exit(main())
