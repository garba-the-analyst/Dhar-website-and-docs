# Dhar: website and documents

The public face and the written record of the [Dhar](https://github.com/garba-the-analyst/forge-of-dhar) systems
language, by Abdullahi Baba Garba (*Garba the Analyst*), for Nigerian and African independence in systems software.

One branch, `main`, holds everything: the **website** (`public/`, including the survey as the page `public/survey/`), the
**Canon of Dhar** and its amendments (`docs/canon/`), the **progress reports** (`docs/reports/`), the rules for honest
claims, the database definition (`supabase/`), and the tools and tests that keep the site true.

The compilers live elsewhere: [forge-of-dhar](https://github.com/garba-the-analyst/forge-of-dhar) (Stage 0, in assembly)
and [honing-dhar](https://github.com/garba-the-analyst/honing-dhar) (Stage 1, in Dhar). What Dhar can do *today* is a
statement about that code, so its source of truth, `status/status.json`, stays in forge-of-dhar next to the tests that
check it. This repository holds a copy (see "Keeping it true").

## What is here

```
public/                    the website, deployable as it stands (index.html, assets/, site.webmanifest)
docs/canon/                Canon Amendment A-1 (direction) and the amendment index
docs/canon/pdf/            the Canon of Dhar as PDFs: master index, Spec0, Spec1, Stage-alpha to epsilon, Volume III, the Pact
docs/reports/              progress reports (PR-001 ...) and the live progress log
docs/HONESTY.md            the rules for what may be claimed
docs/MULTI-ISA-PLAN.md     the plan for the processors other than x86-64
docs/BRAND.md              colour, type and logo rules (fixed)
data/                      copies of status.json and the benchmark JSON, plus site.json (hosting settings)
brand/                     the reference banner the logo was traced from (not deployed)
tools/                     render_site.py, sync_from_forge.py, and the logo tools
tests/run_tests.py         the site's tests
render.yaml                Render blueprint: this site and the survey
```

The Canon has 14 documents in four volumes. `docs/canon/pdf/` holds 14 files: the master index and 13 of the 14
documents the index lists. **Tooling Dhar (document 10) is not among them**; it was never in the Canon files and needs to
be written (see the amendment index).

## Host it on Render

Render dashboard, **New, Blueprint**, pick this repository and the `main` branch. `render.yaml` creates one static site
(`dhar`) that publishes `public/`. It redeploys on every push to `main`. There is nothing to build.

(To do it by hand instead: **New, Static Site**, pick this repository and `main`, build command empty or
`echo static`, publish directory `public`.)

Then tell the website where it is, once. Render shows the site's address after the first deploy. Put it in
`data/site.json` and re-render:

```json
{ "site_url": "https://<the dhar site>.onrender.com" }
```
```
python3 tools/render_site.py
```
`site_url` makes link previews work. Commit and push, and the site updates.

## Keeping it true

Everything on the site that states what works, what changed and what is planned is generated, not typed:

```
python3 tools/sync_from_forge.py ../forge-of-dhar     # copy status.json, the benchmark JSON and PROGRESS.md, then re-render
python3 tools/render_site.py                          # re-render after editing data/site.json
python3 tests/run_tests.py --dharc ../forge-of-dhar/build/dharc --forge-repo ../forge-of-dhar
```
The test fails if the page differs from the data, if the data differs from the forge-of-dhar checkout, if a number on
the page differs from the benchmark JSON, if a code sample no longer compiles and runs as shown, and on any palette,
logo, layout or accessibility regression. The rules are in [docs/HONESTY.md](docs/HONESTY.md). Needs Python 3,
Playwright with Chromium, `nasm` and `ld` (for the samples), and for the logo tools Pillow, OpenCV, shapely and fontTools.

## Licence

MIT, copyright 2026 Abdullahi Baba Garba. Fonts (Saira, JetBrains Mono, Noto Naskh Arabic): SIL Open Font License.
