#!/usr/bin/env python3
"""
run_tests.py: end-to-end tests for the "Shaping Dhar" survey page.

It serves the site from a throw-away local web server, drives it in headless
Chromium exactly as a respondent would (clicks, typing, keyboard), and checks:

  - every combination of the four roles shows exactly the right steps
  - validation, the "up to N" limits, "Other" boxes and the exclusive "None" option
  - answers hidden by branching are left out of the report but are not lost
  - the report text, the mailto: link, the webmail links, the download and the clipboard
  - long answers are cut safely (Windows vs other platforms) and the cut is marked
  - drafts are saved on the device, restored on reload, and can be cleared
  - the page makes no request to any other site and raises no JavaScript errors
  - the page never scrolls sideways at phone, tablet and desktop widths
  - accessibility (axe-core) in light and dark, if axe.min.js is available
  - the parser in tools/parse_responses.py can read what the page produces
  - the PDF copy: valid file, every question and answer in it, text selectable, Nigerian-language
    letters intact, nothing outside the margins, share-sheet button, and a clean fall-back to a
    text-only email when the PDF cannot be made or is switched off (needs qpdf and poppler's
    pdftotext/pdffonts for the file checks; without them those checks are reported as skipped)

Usage
  pip install playwright            # and a Chromium for it (see README)
  python3 tests/run_tests.py [--site DIR] [--shots DIR] [--chromium PATH] [--axe PATH]

Environment: CHROMIUM (browser path), AXE_JS (path to axe.min.js, from `npm pack axe-core`).
Exit status is 0 only if every check passed.
"""
import argparse
import functools
import http.server
import itertools
import json
import os
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import unicodedata
import urllib.parse

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

ap = argparse.ArgumentParser()
ap.add_argument("--site", default=ROOT, help="folder that contains index.html")
ap.add_argument("--shots", default=None, help="folder for screenshots (optional)")
ap.add_argument("--chromium", default=os.environ.get("CHROMIUM"), help="path to a Chromium/Chrome binary")
ap.add_argument("--axe", default=os.environ.get("AXE_JS"), help="path to axe.min.js")
ARGS = ap.parse_args()

RESULTS = []          # (name, ok, detail)
CURRENT = {"name": ""}


def check(cond, message):
    """Records one assertion. A failed check does not stop the test; it is reported at the end."""
    RESULTS.append((CURRENT["name"], bool(cond), message))
    if not cond:
        print("    FAIL:", message)
    return bool(cond)


def test(fn):
    TESTS.append(fn)
    return fn


TESTS = []

# --------------------------------------------------------------------------- server

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def start_server():
    handler = functools.partial(QuietHandler, directory=ARGS.site)
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


# --------------------------------------------------------------------------- page helpers

MAILTO_HOOK = """
window.__mailto = null;
document.addEventListener('click', function (e) {
  var a = e.target && e.target.closest && e.target.closest('a[href^="mailto:"]');
  if (a) { window.__mailto = a.href; e.preventDefault(); }
}, true);
"""

ALL_ROLES = ["prof", "researcher", "student", "dev"]
STEP_TITLE = {"prof": "Teaching", "researcher": "Research", "student": "Learning", "dev": "Building"}


class Run:
    """One browser context + page, with the error and request watchers attached."""

    def __init__(self, browser, base, viewport=None, scheme="light", ua=None, permissions=True):
        opts = {"viewport": viewport or {"width": 1280, "height": 900}, "color_scheme": scheme}
        if ua:
            opts["user_agent"] = ua
        self.ctx = browser.new_context(**opts)
        if permissions:
            self.ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=base)
        self.page = self.ctx.new_page()
        self.base = base
        self.errors = []
        self.external = []
        self.page.on("console", lambda m: self.errors.append("console." + m.type + ": " + m.text) if m.type in ("error", "warning") else None)
        self.page.on("pageerror", lambda e: self.errors.append("pageerror: " + str(e)))
        self.page.on("request", lambda r: self.external.append(r.url) if not (r.url.startswith(base) or r.url.startswith("data:") or r.url.startswith("blob:")) else None)
        self.page.add_init_script(MAILTO_HOOK)

    def open(self, path="/index.html"):
        self.page.goto(self.base + path)
        self.page.wait_for_selector("html[data-ready=true]")
        return self

    def close(self):
        self.ctx.close()

    # ---- reading the page
    def title(self):
        return self.page.evaluate("document.querySelector('.step:not([hidden]) .step-title').textContent")

    def step_ids(self):
        return self.page.evaluate("[...document.querySelectorAll('.step')].filter(s => !s.hidden).map(s => s.dataset.step)")

    def visible_questions(self):
        return self.page.evaluate("""() => {
          const S = window.DHAR_SURVEY, out = [];
          const step = document.querySelector('.step:not([hidden])');
          const all = {}; S.sections.forEach(s => s.questions.forEach(q => all[q.code] = q));
          step.querySelectorAll('.q').forEach(el => {
            if (el.hidden || el.closest('[hidden]')) return;
            const q = all[el.dataset.code];
            out.push({code: q.code, type: q.type, required: !!q.required, rows: q.rows ? q.rows.length : 0, max: q.max || 0,
                      collapsed: !!el.closest('details:not([open])')});
          });
          return out;
        }""")

    def error_text(self, code):
        loc = self.page.locator(f"#err-{code}")
        return loc.inner_text() if loc.count() and loc.is_visible() else ""

    # ---- acting on the page
    def pick_roles(self, roles):
        for r in roles:
            self.page.check(f"#in-ROLE-{r}")

    def next(self):
        self.page.click(".nav button[type=submit]")

    def back(self):
        self.page.click(".nav button:has-text('Back')")

    def is_filled(self, code):
        """True when the question already shows an answer (so a helper does not overwrite a deliberate one)."""
        return self.page.evaluate("""code => {
          const el = document.getElementById('q-' + code);
          if (el.querySelector('input:checked')) return true;
          return [...el.querySelectorAll('input[type=text],input[type=email],textarea')].some(i => !i.classList.contains('other') && i.value.trim() !== '');
        }""", code)

    def fill_default(self, q, skip=()):
        code, kind, p = q["code"], q["type"], self.page
        if code in skip or self.is_filled(code):
            return
        if kind == "radio":
            p.locator(f"#q-{code} label.opt").first.click()
        elif kind == "checkbox":
            p.locator(f"#q-{code} label.opt").first.click()
        elif kind in ("likert", "scale"):
            p.locator(f"#q-{code} .seg-item").nth(2).click()
        elif kind == "grid":
            for i in range(q["rows"]):
                p.locator(f"#q-{code} .grid-row").nth(i).locator(".seg-item").nth(2).click()
        elif kind in ("text", "email"):
            p.fill(f"#in-{code}", "Test answer")
        elif kind == "textarea":
            p.fill(f"#in-{code}", "Test answer")

    def fill_step(self, only_required=True, skip=(), long_text=0):
        """Answers the visible questions of the current step. Questions that appear as a result of an
        earlier answer (for example the contact box) are picked up on the next pass."""
        done = set()
        for _ in range(3):
            todo = [q for q in self.visible_questions() if q["code"] not in done and not q["collapsed"]]
            if not todo:
                break
            for q in todo:
                done.add(q["code"])
                if q["type"] == "textarea" and long_text:
                    self.page.fill(f"#in-{q['code']}", ("Considered answer with several words in it. " * 8)[:long_text])
                elif q["required"] or not only_required:
                    self.fill_default(q, skip)

    def walk(self, on_step=None, overrides=None, long_text=0, only_required=True):
        """Fills every required question and presses Next until the review step."""
        overrides = overrides or {}
        titles = []
        for _ in range(14):
            t = self.title()
            titles.append(t)
            if on_step:
                on_step(t)
            if t == "Review and send":
                break
            step = self.step_ids()[0]
            if step in overrides:
                overrides[step](self)
            self.fill_step(only_required=only_required, skip=overrides.get("skip", ()), long_text=long_text)
            self.next()
        return titles

    def mailto(self):
        return self.page.evaluate("window.__mailto")

    def report(self):
        return self.page.input_value("#report-text")

    def shot(self, name, full=True):
        if ARGS.shots:
            os.makedirs(ARGS.shots, exist_ok=True)
            self.page.screenshot(path=os.path.join(ARGS.shots, name + ".png"), full_page=full)


def expected_titles(roles, with_areas=False):
    t = ["Start", "About you"] + [STEP_TITLE[r] for r in ALL_ROLES if r in roles]
    if with_areas:
        t.append("Your areas in detail")
    return t + ["Your view of Dhar", "Stay in touch", "Review and send"]


def set_areas(ids):
    """Override for the 'about' step: tick the given A3 options (and nothing else)."""
    def _do(run):
        for i in ids:
            run.page.check(f"#in-A3-{i}")
    return _do


def about_step(areas=()):
    def _do(run):
        run.page.fill("#in-A1", "Nigeria")
        run.page.check("#in-A2-o3")
        for i in areas or ["none"]:
            run.page.check(f"#in-A3-{i}")
        run.page.check("#in-A4-o5")
        run.page.check("#in-A5-o1")
    return _do


# --------------------------------------------------------------------------- tests

@test
def t_first_load(env):
    r = Run(env.browser, env.base).open()
    check(r.title() == "Start", "first step is 'Start'")
    check(r.page.is_hidden(".nav button:has-text('Back')"), "no Back button on the first step")
    check(r.page.locator("#in-ROLE-prof").count() == 1 and r.page.locator("input[name=ROLE]").count() == 4, "four role options are shown")
    check(r.page.evaluate("getComputedStyle(document.querySelector('.hero .code')).display") != "none", "code sample is shown on desktop")
    r.close()
    m = Run(env.browser, env.base, viewport={"width": 375, "height": 780}).open()
    check(m.page.evaluate("getComputedStyle(document.querySelector('.hero .code')).display") == "none", "code sample is hidden on phones")
    check(m.errors == [] and m.external == [], f"no errors / external requests on phone load: {m.errors} {m.external}")
    m.close()


@test
def t_role_required(env):
    r = Run(env.browser, env.base).open()
    r.next()
    check(r.title() == "Start", "Next without a role stays on the first step")
    check("Choose at least one option" in r.error_text("ROLE"), "role error says what to do")
    check(r.page.evaluate("document.activeElement.name") == "ROLE", "focus moves to the first role option")
    check("needs an answer" in r.page.inner_text(".nav-err"), "summary message appears near Next")
    r.pick_roles(["student"])
    check(r.error_text("ROLE") == "", "error clears once a role is ticked")
    r.next()
    check(r.title() == "About you", "Next works after a role is ticked")
    check(r.page.is_visible(".nav button:has-text('Back')"), "Back appears after the first step")
    r.close()


@test
def t_all_role_combinations(env):
    combos = [list(c) for n in range(1, 5) for c in itertools.combinations(ALL_ROLES, n)]
    check(len(combos) == 15, "15 non-empty role combinations")
    for combo in combos:
        r = Run(env.browser, env.base, permissions=False).open()
        r.pick_roles(combo)
        titles = r.walk(overrides={"about": about_step()})
        check(titles == expected_titles(combo), f"roles {combo}: steps {titles}")
        check(r.errors == [] and r.external == [], f"roles {combo}: no errors {r.errors} {r.external}")
        r.close()


@test
def t_about_and_limits(env):
    r = Run(env.browser, env.base).open()
    r.pick_roles(["student", "dev", "prof"])
    r.next()
    # required fields on 'About you'
    r.next()
    for code in ("A1", "A2", "A3", "A4", "A5"):
        check(r.error_text(code) != "", f"{code} reports a problem when empty")
    # exclusive "None of these yet"
    r.page.check("#in-A3-web"); r.page.check("#in-A3-security")
    r.page.check("#in-A3-none")
    check(not r.page.is_checked("#in-A3-web") and not r.page.is_checked("#in-A3-security"), "'None' clears the other A3 choices")
    r.page.check("#in-A3-web")
    check(not r.page.is_checked("#in-A3-none"), "ticking a real choice clears 'None'")
    # Other with no text
    r.page.check("#in-A4-other")
    check(r.page.is_visible("#in-A4-other-text"), "'Other' reveals a text box")
    r.page.fill("#in-A1", "Nigeria"); r.page.check("#in-A2-o2"); r.page.check("#in-A5-o2")
    r.next()
    check("Say what" in r.error_text("A4"), "'Other' with no text is rejected when required")
    r.page.fill("#in-A4-other-text", "Zig")
    r.next()
    check(r.title() == "Teaching", "About you passes with a filled 'Other' (next step is Teaching)")
    # P4 allows 3
    for o in ("o1", "o2", "o3"):
        r.page.check(f"#in-P4-{o}")
    check(r.page.is_disabled("#in-P4-o4"), "a 4th choice is disabled once 3 are ticked")
    check("3 of 3 chosen" in r.page.inner_text("#q-P4 .q-count"), "counter reads '3 of 3 chosen'")
    r.page.uncheck("#in-P4-o2")
    check(r.page.is_enabled("#in-P4-o4"), "unticking re-enables the others")
    # likert / radio / grid validation on the right steps
    r.next()
    check(r.error_text("P3") != "" and "1 to 5" in r.error_text("P3"), "likert error names the range")
    r.close()


@test
def t_grid_and_scale(env):
    r = Run(env.browser, env.base).open()
    r.pick_roles(["dev"])
    r.next(); about_step()(r); r.next()
    check(r.title() == "Building", "reached the developer step")
    for q in r.visible_questions():
        if q["code"] != "D5":
            r.fill_default(q)
    for i in range(10):                 # rate 10 of the 11 rows
        r.page.locator("#q-D5 .grid-row").nth(i).locator(".seg-item").nth(3).click()
    r.next()
    check("1 line is still unrated" in r.error_text("D5"), f"grid reports the missing row: {r.error_text('D5')!r}")
    r.page.locator("#q-D5 .grid-row").nth(10).locator(".seg-item").nth(4).click()
    check(r.error_text("D5") == "", "grid error clears when the last row is rated")
    r.next()
    check(r.title() == "Your view of Dhar", "developer step passes after the grid is complete")
    r.next()
    check("Pick a number from 0 to 10" in r.error_text("X3"), "0-10 scale error names the range")
    r.fill_step()
    check(r.page.evaluate("document.querySelectorAll('#q-X3 .seg-item').length") == 11, "0-10 scale has eleven choices")
    r.close()


@test
def t_areas_branching(env):
    r = Run(env.browser, env.base).open()
    r.pick_roles(["student"])
    t = r.walk(overrides={"about": about_step(areas=["security", "blockchain"])})
    check("Your areas in detail" in t, "areas step appears when a niche is ticked")
    r.close()

    r = Run(env.browser, env.base).open()
    r.pick_roles(["student"])
    r.next(); about_step(areas=["security", "blockchain", "web"])(r); r.next()
    r.fill_step(); r.next()                       # student step
    check(r.title() == "Your areas in detail", "areas step follows the role steps")
    groups = r.page.evaluate("[...document.querySelectorAll('.deep')].filter(d => !d.hidden).map(d => d.dataset.group)")
    check(sorted(groups) == ["blockchain", "security", "webmobile"], f"one block per ticked area (web counts as web and mobile): {groups}")
    check(r.page.evaluate("document.querySelectorAll('.deep[open]').length") == 0, "blocks start closed when several apply")
    r.page.click(".deep[data-group=security] summary")
    r.page.check("#in-SE1-o5")
    r.page.fill("#in-SE2", "Wireshark, Burp Suite")
    check("1 of 3 answered" not in r.page.inner_text(".deep[data-group=security] .deep-meta") and "2 of 3 answered" in r.page.inner_text(".deep[data-group=security] .deep-meta"), "block summary counts answered questions")
    r.next()
    check(r.title() == "Your view of Dhar", "areas are optional: Next passes with only some answered")
    # a lone niche opens by itself
    r.close()
    r = Run(env.browser, env.base).open()
    r.pick_roles(["student"]); r.next(); about_step(areas=["data"])(r); r.next(); r.fill_step(); r.next()
    check(r.page.evaluate("document.querySelectorAll('.deep[open]').length") == 1, "a lone area block opens itself")
    r.close()
    # no niche ticked -> no areas step
    r = Run(env.browser, env.base).open()
    r.pick_roles(["student"]); t = r.walk(overrides={"about": about_step(areas=["cloud"])})
    check("Your areas in detail" not in t, "cloud/DevOps alone has no area step")
    r.close()


@test
def t_hidden_answers_not_reported_but_kept(env):
    r = Run(env.browser, env.base).open()
    r.pick_roles(["prof", "student"])
    titles = r.walk(overrides={"about": about_step()}, only_required=False)     # answer everything, optional too
    check(titles[-1] == "Review and send", f"reached review with two roles: {titles}")
    steps_back = len(titles) - 1
    rep = r.report()
    check("[P3]" in rep and "[S1]" in rep, "both role sections are in the report")
    for _ in range(steps_back):
        r.back()
    check(r.title() == "Start", "Back returns to the first step")
    r.page.uncheck("#in-ROLE-student")
    titles2 = r.walk()
    rep2 = r.report()
    check("Learning" not in titles2, "the student step disappears when the role is unticked")
    check("[S1]" not in rep2 and "[P3]" in rep2, "student answers drop out of the report once the role is unticked")
    check(rep2.split("\n")[3] == "Roles: Academic (professor or lecturer)", f"roles line follows the ticks: {rep2.split(chr(10))[3]!r}")
    for _ in range(len(titles2) - 1):
        r.back()
    r.page.check("#in-ROLE-student")
    r.walk()
    check("[S1] What best describes your current stage?" in r.report(), "earlier student answers come back when the role is re-ticked")
    r.close()


@test
def t_contact_branch(env):
    r = Run(env.browser, env.base).open()
    r.pick_roles(["student"])
    r.next(); about_step()(r); r.next(); r.fill_step(); r.next(); r.fill_step(); r.next()
    check(r.title() == "Stay in touch", "reached the closing step")
    check(r.page.is_hidden("#q-C2"), "contact box is hidden before an answer")
    r.page.check("#in-C1-yes")
    check(r.page.is_visible("#q-C2"), "contact box appears for 'Yes'")
    r.next()
    check(r.title() == "Stay in touch" and r.error_text("C2") != "", "contact is required once 'Yes' is chosen")
    r.page.check("#in-C1-no")
    check(r.page.is_hidden("#q-C2"), "contact box hides again for 'No'")
    r.next()
    check(r.title() == "Review and send", "Next passes with 'No'")
    check("[C2]" not in r.report(), "hidden contact question is not in the report")
    r.back(); r.page.check("#in-C1-yes"); r.page.fill("#in-C2", "student@example.edu"); r.next()
    check("[C2]" in r.report() and "student@example.edu" in r.report(), "contact appears in the report when given")
    rep = r.report()
    check(rep.index("[C2]") < rep.index("[A1]"), "contact is the first thing in the report")
    r.close()


def mail_parts(mt):
    """Splits a mailto: link into (to, subject, body-with-LF)."""
    parsed = urllib.parse.urlparse(mt)
    q = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    return parsed.path, q["subject"][0], q["body"][0].replace("\r\n", "\n"), q["body"][0]


def codes_in(text):
    import re
    return re.findall(r"^\[([A-Z]+[0-9]+[a-z]?)\]", text, re.M)


@test
def t_report_and_mailto_short(env):
    r = Run(env.browser, env.base, ua="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 Safari/605.1.15").open()
    r.pick_roles(["student"])
    r.walk(overrides={"about": about_step()})
    rep = r.report()
    lines = rep.split("\n")
    check(lines[0] == "SHAPING DHAR SURVEY RESPONSE", "report starts with the marker line")
    check(lines[1] == "Survey version: 1.0", "report carries the survey version")
    check(lines[2].startswith("Submitted: "), "report carries a timestamp")
    check(lines[3] == "Roles: Student", f"roles line: {lines[3]!r}")
    check(lines[5] == "Question wording: full", f"wording line: {lines[5]!r}")
    check(lines[-1] == "== END OF RESPONSE ==", "report ends with the end marker")
    check("[A1] Which country or region are you currently based in?\n  Nigeria" in rep, "question text and answer appear together")
    check("[A3] Which of the following are you currently involved in, in any capacity? (Select all that apply." in rep, "hint is part of the question text in the report")
    check("\n  - None of these yet" in rep, "checkbox answers are listed with '- '")
    check("[ROLE]" not in rep, "the role question is not repeated in the body (roles are in the header)")
    order = [rep.index(t) for t in ("== CONTACT ==", "== ABOUT YOU ==", "== SENTIMENT AND PRIORITIES ==", "== STUDENT ==")]
    check(order == sorted(order), f"essentials come first: contact, about, sentiment, then the role section {order}")
    r.page.click("#btn-send")
    r.page.wait_for_selector("#sent:not([hidden])")
    mt = r.mailto()
    check(mt is not None and mt.startswith("mailto:garbaabdullahi344@gmail.com?subject="), f"mailto goes to the owner: {str(mt)[:70]}")
    to, subject, body, raw = mail_parts(mt)
    check(subject == "Shaping Dhar survey response: Student", f"subject: {subject!r}")
    check("\r\n" in raw and "\n" not in raw.replace("\r\n", ""), "mailto body uses CRLF line breaks (RFC 6068)")
    check(len(mt) <= 7500, f"link within the limit ({len(mt)})")
    if "Question wording: full" in body:
        check(body == rep, "tier full: the mailto body is the complete report")
    else:
        check(body.rstrip().endswith("== END OF RESPONSE ==") and "Question wording: shortened" in body, "tier compact: ends cleanly and says the wording is shortened")
        check(codes_in(body) == codes_in(rep), "tier compact: carries every answered question")
        check("shortened" in r.page.inner_text("#sent"), "tier compact: the panel says the wording was shortened")
    clip = r.page.evaluate("navigator.clipboard.readText()")
    check(clip == rep, "the full report is on the clipboard")
    check("Your email is ready" in r.page.inner_text("#sent"), "confirmation panel is shown")
    check("garbaabdullahi344@gmail.com" in r.page.inner_text("#sent"), "panel shows where the answers go")
    r.close()


@test
def t_tiers_full_compact_cut(env):
    """A tiny response goes out in full; a big one with long answers is never silently cut."""
    # 1. very short response on a roomy platform: full text
    ua_mac = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 Safari/605.1.15"
    r = Run(env.browser, env.base, ua=ua_mac).open()
    r.pick_roles(["student"])
    r.walk(overrides={"about": about_step()})
    rep = r.report()
    r.page.click("#btn-send"); r.page.wait_for_selector("#sent:not([hidden])")
    _, _, body, _ = mail_parts(r.mailto())
    full_enc = len(urllib.parse.quote(rep.replace("\n", "\r\n")))
    check((full_enc + 120 <= 7500) == ("Question wording: full" in body) or full_enc + 120 > 7500, f"student response ({full_enc} chars encoded) is sent in full when it fits")
    r.close()

    # 2. long answers on Windows (strict limit) and Android (roomy)
    cases = [
        ("Windows", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36", 1900),
        ("Android", "Mozilla/5.0 (Linux; Android 13; SM-A135F) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36", 7500),
    ]
    for name, ua, limit in cases:
        r = Run(env.browser, env.base, ua=ua).open()
        r.pick_roles(ALL_ROLES)
        r.walk(overrides={"about": about_step(areas=["software", "ai"])}, long_text=380)
        rep = r.report()
        r.page.click("#btn-send"); r.page.wait_for_selector("#sent:not([hidden])")
        mt = r.mailto()
        _, _, body, raw = mail_parts(mt)
        check(len(mt) <= limit, f"{name}: mailto link is {len(mt)} chars, limit {limit}")
        check(body.startswith("SHAPING DHAR SURVEY RESPONSE\nSurvey version"), f"{name}: the header always survives")
        ended = body.rstrip().endswith("== END OF RESPONSE ==")
        if ended:
            check(codes_in(body) == codes_in(rep), f"{name}: compact tier carries every answered question ({len(codes_in(body))})")
            check("Question wording: shortened" in body, f"{name}: compact tier says so")
        else:
            check(body.rstrip().endswith("select all of this message, paste, and send.]"), f"{name}: a cut message says it was cut")
            check("== CONTACT ==" in body and "== ABOUT YOU ==" in body, f"{name}: even a cut message keeps contact and basics")
            check("Your email may be cut short" in r.page.inner_text("#sent"), f"{name}: panel warns about the cut")
            check("[C2]" in body, f"{name}: the contact answer survives the cut")
        check(r.page.evaluate("navigator.clipboard.readText()") == rep, f"{name}: clipboard holds the complete report ({len(rep)} chars)")
        links = r.page.evaluate("[...document.querySelectorAll('#sent a[target=_blank]')].map(a => ({t: a.textContent, h: a.href}))")
        check([l["t"] for l in links] == ["Open Gmail", "Open Outlook", "Open Yahoo Mail"], f"{name}: three webmail links: {[l['t'] for l in links]}")
        gm = [l for l in links if l["t"] == "Open Gmail"][0]["h"]
        check(gm.startswith("https://mail.google.com/mail/?view=cm&fs=1&to=garbaabdullahi344%40gmail.com&su="), f"{name}: Gmail link addressed correctly")
        check(all(len(l["h"]) <= 7000 for l in links), f"{name}: webmail links within 7000 chars ({[len(l['h']) for l in links]})")
        gbody = urllib.parse.parse_qs(urllib.parse.urlparse(gm).query)["body"][0]
        check(gbody.startswith("SHAPING DHAR SURVEY RESPONSE"), f"{name}: Gmail body starts with the header")
        check(r.errors == [] and r.external == [], f"{name}: no errors / external requests {r.errors} {r.external}")
        r.close()


@test
def t_compact_text_parses(env):
    """The shortened wording must still be read correctly by the parser."""
    import csv
    parser = os.path.join(ROOT, "tools", "parse_responses.py")
    r = Run(env.browser, env.base, ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36").open()
    r.pick_roles(["dev", "student"])
    r.walk(overrides={"about": about_step()}, long_text=100)
    r.page.click("#btn-send"); r.page.wait_for_selector("#sent:not([hidden])")
    _, _, body, _ = mail_parts(r.mailto())
    r.close()
    check("Question wording: shortened" in body or "[Shortened by the survey page" in body, "Windows limit forces the shortened or cut form for this response")
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "m.txt")
        open(src, "w", encoding="utf-8").write(body)
        out = os.path.join(d, "o.csv")
        res = subprocess.run([sys.executable, "-I", parser, src, "-o", out], capture_output=True, text=True)
        check(res.returncode == 0, f"parser reads the short form: {res.stderr[-200:]}")
        rows = list(csv.DictReader(open(out, encoding="utf-8")))
        check(len(rows) == 1 and rows[0]["A1"] == "Nigeria" and rows[0]["roles"] == "Student; Developer or engineer", f"core fields parsed: {rows[0] if rows else rows}")
        check(rows[0].get("wording") in ("shortened", "full"), f"wording column filled: {rows[0].get('wording')!r}")


@test
def t_download(env):
    r = Run(env.browser, env.base).open()
    r.pick_roles(["dev"])
    r.walk(overrides={"about": about_step()})
    rep = r.report()
    r.page.click("#btn-send"); r.page.wait_for_selector("#sent:not([hidden])")
    with r.page.expect_download() as dl:
        r.page.click("text=Download as a text file")
    d = dl.value
    check(d.suggested_filename.startswith("dhar-survey-response-") and d.suggested_filename.endswith(".txt"), f"download name: {d.suggested_filename}")
    data = open(d.path(), encoding="utf-8").read()
    check(data.replace("\r\n", "\n") == rep, "downloaded file holds the complete report")
    r.close()


@test
def t_draft_saved_and_restored(env):
    r = Run(env.browser, env.base).open()
    r.pick_roles(["student"])
    r.next(); r.page.fill("#in-A1", "Kenya"); r.page.check("#in-A2-o4")
    r.page.wait_for_timeout(500)
    r.page.reload(); r.page.wait_for_selector("html[data-ready=true]")
    check(r.title() == "About you", f"reload returns to the same step: {r.title()}")
    check(r.page.input_value("#in-A1") == "Kenya" and r.page.is_checked("#in-A2-o4"), "answers are restored")
    r.back()
    check(r.page.is_checked("#in-ROLE-student"), "roles are restored")
    check(r.page.is_visible("#restored"), "the 'welcome back' notice is shown on the first step")
    with r.page.expect_navigation():
        r.page.click("#restart")
    r.page.wait_for_selector("html[data-ready=true]")
    check(r.title() == "Start" and not r.page.is_checked("#in-ROLE-student") and r.page.is_hidden("#restored"), "Start over clears the draft")
    r.close()
    # storage that throws must not break the page
    r2 = Run(env.browser, env.base)
    r2.page.add_init_script("Object.defineProperty(window, 'localStorage', {get() { throw new Error('blocked'); }});")
    r2.open()
    r2.pick_roles(["student"]); r2.next()
    check(r2.title() == "About you", "page works when localStorage is blocked")
    check(not [e for e in r2.errors if "blocked" in e], f"blocked storage raises no page error: {r2.errors}")
    r2.close()


@test
def t_clear_after_send(env):
    r = Run(env.browser, env.base).open()
    r.pick_roles(["student"]); r.walk(overrides={"about": about_step()})
    r.page.click("#btn-send"); r.page.wait_for_selector("#sent:not([hidden])")
    with r.page.expect_navigation():
        r.page.click("text=I have sent it")
    r.page.wait_for_selector("html[data-ready=true]")
    check(r.title() == "Start" and r.page.is_hidden("#restored"), "'I have sent it' clears the draft and starts fresh")
    r.close()


@test
def t_keyboard(env):
    r = Run(env.browser, env.base).open()
    r.page.focus("#in-ROLE-dev")
    r.page.keyboard.press("Space")
    check(r.page.is_checked("#in-ROLE-dev"), "Space ticks a role")
    r.page.focus(".nav button[type=submit]")
    r.page.keyboard.press("Enter")
    check(r.title() == "About you", "Enter on Next moves on")
    check(r.page.evaluate("document.activeElement.classList.contains('step-title')"), "focus moves to the new step heading")
    r.page.fill("#in-A1", "Ghana")
    r.page.keyboard.press("Enter")
    check(r.title() == "About you" and r.error_text("A2") != "", "Enter inside a text box runs validation instead of submitting")
    r.close()


@test
def t_no_horizontal_scroll(env):
    for w, h in [(320, 640), (375, 780), (768, 1024), (1024, 768), (1440, 900)]:
        r = Run(env.browser, env.base, viewport={"width": w, "height": h}, permissions=False).open()
        r.pick_roles(ALL_ROLES)
        over = []

        def on_step(t, r=r, over=over):
            sw = r.page.evaluate("document.documentElement.scrollWidth")
            if sw > w:
                over.append((t, sw))
            if ARGS.shots and w in (375, 1440):
                r.shot(f"flow-{w}-{t.lower().replace(' ', '-')}")
        r.walk(on_step=on_step, overrides={"about": about_step(areas=["security", "blockchain"])})
        r.page.click("#btn-send"); r.page.wait_for_selector("#sent:not([hidden])")
        if r.page.evaluate("document.documentElement.scrollWidth") > w:
            over.append(("sent panel", r.page.evaluate("document.documentElement.scrollWidth")))
        if ARGS.shots and w in (375, 1440):
            r.shot(f"flow-{w}-review-sent")
        check(not over, f"{w}px wide: no sideways scrolling ({over})")
        r.close()


@test
def t_error_states_screenshots(env):
    if not ARGS.shots:
        return
    for w, name in [(1280, "desktop"), (375, "mobile")]:
        r = Run(env.browser, env.base, viewport={"width": w, "height": 900 if w > 500 else 780}, permissions=False).open()
        r.pick_roles(["dev"]); r.next(); r.next()
        r.shot(f"errors-{name}-about")
        about_step()(r); r.next()
        r.next()
        r.shot(f"errors-{name}-developer")
        r.close()


@test
def t_file_protocol(env):
    r = Run(env.browser, env.base, permissions=False)
    r.page.goto("file://" + os.path.join(os.path.abspath(ARGS.site), "index.html"))
    r.page.wait_for_selector("html[data-ready=true]")
    r.pick_roles(["student"]); r.next()
    check(r.title() == "About you", "page works when index.html is opened straight from disk")
    # Browsers refuse to load a font file from file:// (a cross-origin rule), so the page falls back to a
    # system font there. That is the only expected message; anything else is a real error.
    other = [e for e in r.errors if "font" not in e.lower() and "preload" not in e.lower() and "ERR_FAILED" not in e]
    check(not other, f"no errors from file:// apart from the blocked font: {other}")
    r.close()


@test
def t_parser_round_trip(env):
    parser = os.path.join(ROOT, "tools", "parse_responses.py")
    if not os.path.exists(parser):
        check(False, "tools/parse_responses.py is missing")
        return
    r = Run(env.browser, env.base).open()
    r.pick_roles(["student", "dev"])
    r.walk(overrides={"about": about_step(areas=["security"])}, long_text=60)
    rep = r.report()
    r.close()
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "mail.txt")
        # two copies, one of them quoted the way a reply or forward would quote it
        open(src, "w", encoding="utf-8").write("From: someone\nSubject: x\n\n" + rep + "\n\n> " + rep.replace("\n", "\n> ") + "\n")
        out = os.path.join(d, "out.csv")
        res = subprocess.run([sys.executable, "-I", parser, src, "-o", out], capture_output=True, text=True)
        check(res.returncode == 0, f"parser exits cleanly: {res.stderr[-300:]}")
        import csv
        rows = list(csv.DictReader(open(out, encoding="utf-8")))
        check(len(rows) == 2, f"parser finds both responses ({len(rows)})")
        if rows:
            row = rows[0]
            check(row.get("A1") == "Nigeria" and row.get("roles") == "Student; Developer or engineer", f"A1/roles parsed: {row.get('A1')!r} {row.get('roles')!r}")
            check(row.get("D5", "").count("|") == 10, f"grid answer has 11 rows: {row.get('D5')!r}")
            check(row.get("S1") and row.get("X3") == "2", f"other codes parsed: S1={row.get('S1')!r} X3={row.get('X3')!r}")
            check(row.get("complete") == "yes", "complete marker detected")
            check(re.match(r"^shaping-dhar-response-\d{8}-\d{4}\.pdf$", row.get("pdf_copy", "")) is not None, f"pdf_copy column holds the attachment name: {row.get('pdf_copy')!r}")


@test
def t_accessibility(env):
    axe = ARGS.axe
    if not axe or not os.path.exists(axe):
        print("    (skipped: pass --axe /path/to/axe.min.js, from `npm pack axe-core`)")
        return
    src = open(axe, encoding="utf-8").read()
    for scheme in ("light", "dark"):
        r = Run(env.browser, env.base, scheme=scheme, permissions=True).open()
        r.page.add_script_tag(content=src)
        seen = []

        def run_axe(label, r=r, scheme=scheme):
            res = r.page.evaluate("""async () => {
              const out = await axe.run(document, {resultTypes: ['violations']});
              return out.violations.map(v => ({id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.slice(0, 3).map(n => n.target.join(' ') + ' :: ' + (n.failureSummary || '').split('\\n').slice(0, 3).join(' / '))}));
            }""")
            check(res == [], f"axe ({scheme}) on '{label}': {json.dumps(res)[:900]}")

        r.pick_roles(ALL_ROLES)
        run_axe("start")
        # validation state
        r.next()
        r.next(); run_axe("about with errors")
        about_step(areas=["security", "web"])(r); r.next()

        def on_step(t):
            if t not in seen:
                seen.append(t)
                if t != "Start":
                    run_axe(t)
        r.walk(on_step=on_step, long_text=0)
        r.page.click("#btn-send"); r.page.wait_for_selector("#sent:not([hidden])")
        run_axe("review with confirmation panel")
        r.close()


# --------------------------------------------------------------------------- main

# --------------------------------------------------------------------------- PDF copy

PAGE_W, PAGE_H, MARGIN_X = 595.28, 841.89, 54.0
SKIPPED = []


def tool(name):
    return shutil.which(name)


def squash(text):
    """Whitespace-free, NFC form: PDF text wraps anywhere, so compare without spaces and line breaks."""
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", text))


def report_blocks(rep):
    """[(code, [answer lines])] from the emailed text."""
    blocks, cur = [], None
    for line in rep.split("\n"):
        m = re.match(r"^\[([A-Z]+[0-9]+[a-z]?)\] ", line)
        if m:
            cur = (m.group(1), [])
            blocks.append(cur)
        elif line.startswith("== "):
            cur = None
        elif cur is not None and line.startswith("  "):
            cur[1].append(line[2:])
    return blocks


def survey_questions(run):
    data = run.page.evaluate("window.DHAR_SURVEY")
    out = {}
    for sec in data["sections"]:
        for q in sec["questions"]:
            out[q["code"]] = q
    return out


def press_send_and_save_pdf(run, folder):
    """Waits for the PDF to be ready, presses Send, returns (file name, saved path)."""
    run.page.wait_for_function("document.getElementById('btn-send').textContent.indexOf('Download PDF') === 0", timeout=30000)
    with run.page.expect_download() as dl:
        run.page.click("#btn-send")
    d = dl.value
    path = os.path.join(folder, d.suggested_filename)
    d.save_as(path)
    run.page.wait_for_selector("#sent:not([hidden])")
    return d.suggested_filename, path


def verify_pdf(run, path, name, label, lossy=()):
    """Everything about one saved PDF that does not depend on the answers' content.
    `lossy` lists question codes whose answers contain characters no font has (checked separately)."""
    data = open(path, "rb").read()
    check(data.startswith(b"%PDF-1.7") and data.rstrip().endswith(b"%%EOF"), f"{label}: file starts with %PDF and ends with %%EOF")
    check(len(data) < 700_000, f"{label}: size is reasonable ({len(data) // 1024} KB)")
    rep = run.report()
    check(("PDF copy: " + name) in rep.split("\n")[:8], f"{label}: the email header names the attached file ({name})")
    if tool("qpdf"):
        res = subprocess.run(["qpdf", "--check", path], capture_output=True, text=True)
        check(res.returncode == 0 and "No syntax or stream encoding errors" in res.stdout, f"{label}: qpdf finds no errors: {res.stdout[-200:]} {res.stderr[-200:]}")
        pages = int(subprocess.run(["qpdf", "--show-npages", path], capture_output=True, text=True).stdout.strip() or 0)
    else:
        SKIPPED.append(f"{label}: qpdf")
        pages = 0
    if tool("pdffonts"):
        rows = subprocess.run(["pdffonts", path], capture_output=True, text=True).stdout.strip().split("\n")[2:]
        check(len(rows) >= 2 and all(re.search(r"\byes\s+yes\s+yes\b", r) for r in rows), f"{label}: every font is embedded, subset and has a text map: {rows}")
    else:
        SKIPPED.append(f"{label}: pdffonts")
    if not tool("pdftotext"):
        SKIPPED.append(f"{label}: pdftotext")
        return None
    text = subprocess.run(["pdftotext", "-enc", "UTF-8", path, "-"], capture_output=True, text=True).stdout
    flat = squash(text)

    # every question the respondent saw is in the PDF, with its hint, and every answer is next to it
    qs = survey_questions(run)
    blocks = report_blocks(rep)
    missing = []
    for code, lines in blocks:
        q = qs[code]
        for needle in (q["text"], q.get("hint", "")):
            if needle and squash(needle) not in flat:
                missing.append((code, "question text", needle[:40]))
        if not re.search(r"(?m)^\s*" + re.escape(code) + r"\s*$", text):
            missing.append((code, "code", ""))
        for line in ([] if code in lossy else lines):
            item = line[2:] if line.startswith("- ") else line
            m = re.match(r"^(.*): (\d) of 5$", item)
            wanted = [m.group(1), m.group(2) + "of5"] if (m and q["type"] == "grid") else [item]
            for w in wanted:
                if squash(w) not in flat:
                    missing.append((code, "answer", w[:50]))
    check(not missing, f"{label}: all {len(blocks)} answered questions are in the PDF with their wording: {missing[:5]}")

    m = re.search(r"Questions answered: (\d+) of (\d+) shown", rep)
    answered, shown = int(m.group(1)), int(m.group(2))
    check(squash(f"{answered} of {shown} questions") in flat, f"{label}: the summary says {answered} of {shown} questions")
    check(text.count("(not answered)") == shown - answered, f"{label}: unanswered visible questions are listed as such ({text.count('(not answered)')} = {shown} - {answered})")
    check(squash("Shaping Dhar survey") in flat and squash("Survey version") in flat, f"{label}: title and details are present")
    if pages:
        check(squash(f"Page {pages} of {pages}") in flat and squash(f"Page 1 of {pages}") in flat, f"{label}: page numbers run 1 to {pages}")

    # nothing may leave the margins
    bbox = subprocess.run(["pdftotext", "-bbox", path, "-"], capture_output=True, text=True).stdout
    words = [(float(a), float(b), float(c), float(d)) for a, b, c, d in re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)"', bbox)]
    off = [w for w in words if w[0] < MARGIN_X - 1 or w[2] > PAGE_W - MARGIN_X + 1 or w[1] < 20 or w[3] > PAGE_H - 20]
    check(words and not off, f"{label}: all {len(words)} words are inside the margins (outside: {off[:3]})")
    return text


def prepare_pdf_run(run, nigerian=True):
    """Walks to the review step typing text with Nigerian-language letters into two open questions."""
    typed = {}

    def on_step(t):
        if t == "Your view of Dhar":
            typed["X7"] = "Ẹ kú àárọ̀. Ṣé ọmọ rẹ wà? Ɓoyayye, ɗaya, ƙarami. Igbo: ị ụ ọ ṅ. Price ₦5,000 → ≥ 2 ✓"
            typed["X6"] = "Emoji and Japanese cannot be drawn in the PDF: 😀 日本語"
            run.page.fill("#in-X7", typed["X7"])
            run.page.fill("#in-X6", typed["X6"])
    run.walk(on_step=on_step if nigerian else None, overrides={"about": about_step(areas=["software"])})
    return typed


@test
def t_pdf_flow(env):
    r = Run(env.browser, env.base).open()
    check(r.page.evaluate("typeof window.DharPdf") == "undefined", "the PDF code is not loaded on the first screen")
    r.pick_roles(["student", "dev"])
    r.next()
    try:
        r.page.wait_for_function("typeof window.DharPdf === 'object'", timeout=8000)
        loaded = True
    except Exception:
        loaded = False
    check(loaded, "the PDF code is fetched quietly once the respondent has started")
    typed = prepare_pdf_run(r)
    t0 = time.time()
    r.page.wait_for_function("document.getElementById('btn-send').textContent.indexOf('Download PDF') === 0", timeout=30000)
    ready_after = time.time() - t0
    check(ready_after < 3.0, f"the PDF is ready within 3 s of reaching the review step ({ready_after:.2f} s)")
    check("PDF ready: shaping-dhar-response-" in r.page.inner_text("#pdf-note"), "the review step says the PDF is ready")
    check("PDF copy: shaping-dhar-response-" in r.report(), "the preview of the email names the PDF copy")
    downloads = []
    r.page.on("download", lambda d: downloads.append(d.suggested_filename))
    with tempfile.TemporaryDirectory() as folder:
        name, path = press_send_and_save_pdf(r, folder)
        check(re.match(r"^shaping-dhar-response-\d{8}-\d{4}\.pdf$", name) is not None, f"file name: {name}")
        mt = r.mailto()
        check(mt is not None and mt.startswith("mailto:garbaabdullahi344@gmail.com?subject="), "the email draft still opens, addressed to the owner")
        body = urllib.parse.parse_qs(urllib.parse.urlparse(mt).query)["body"][0].replace("\r\n", "\n")
        check(("PDF copy: " + name) in body, "the email body names the same PDF file")
        sent = r.page.inner_text("#sent")
        check(name in sent and "attach" in sent.lower(), "the confirmation names the file and says to attach it")
        check(r.page.locator("#sent button:has-text('Download the PDF')").count() == 1, "the panel offers the PDF again")
        check(r.page.locator("#sent button:has-text('Share the PDF')").count() == 0, "no share button where the browser cannot share files")
        text = verify_pdf(r, path, name, "student+dev", lossy=("X6",))
        if text is not None:
            check(squash(typed["X7"]) in squash(text), f"Yoruba, Igbo and Hausa letters, the naira sign, an arrow and a tick survive in the PDF text: {typed['X7']!r}")
            check("could not be shown in this PDF" in text, "the PDF says when some characters could not be drawn")
            check("😀" not in text and "日本語" not in text, "undrawable characters are replaced, not garbled")
        check("😀" in r.report() and "日本語" in r.report(), "the emailed text keeps those characters exactly")
        if ARGS.shots and tool("pdftoppm"):
            os.makedirs(ARGS.shots, exist_ok=True)
            subprocess.run(["pdftoppm", "-r", "70", "-f", "1", "-l", "3", "-png", path, os.path.join(ARGS.shots, "pdf-student-dev")], capture_output=True)
    check(len(downloads) == 1, f"exactly one file is downloaded when Send is pressed ({downloads})")
    check(r.errors == [] and r.external == [], f"no errors and no requests to other sites: {r.errors} {r.external}")
    r.close()


@test
def t_pdf_big_response(env):
    r = Run(env.browser, env.base).open()
    r.pick_roles(ALL_ROLES)
    r.walk(overrides={"about": about_step(areas=["software", "web", "ai", "security"])}, long_text=380, only_required=False)
    t0 = time.time()
    with tempfile.TemporaryDirectory() as folder:
        name, path = press_send_and_save_pdf(r, folder)
        check(time.time() - t0 < 6.0, f"a four-role response with long answers is ready and saved in under 6 s ({time.time() - t0:.1f} s)")
        text = verify_pdf(r, path, name, "all roles")
        if tool("qpdf"):
            pages = int(subprocess.run(["qpdf", "--show-npages", path], capture_output=True, text=True).stdout.strip())
            check(pages >= 8, f"a large response runs to several pages ({pages})")
        if ARGS.shots and tool("pdftoppm"):
            subprocess.run(["pdftoppm", "-r", "70", "-f", "1", "-l", "4", "-png", path, os.path.join(ARGS.shots, "pdf-all-roles")], capture_output=True)
        if text is not None:
            check(text.count("Page ") >= 8, "every page carries its number")
    check(r.errors == [], f"no errors: {r.errors}")
    r.close()


@test
def t_pdf_share_button(env):
    r = Run(env.browser, env.base)
    r.page.add_init_script("""
      navigator.canShare = function (d) { return !!(d && d.files && d.files.length); };
      navigator.share = function (d) {
        window.__shared = { name: d.files[0].name, type: d.files[0].type, size: d.files[0].size, title: d.title, text: d.text };
        return d.files[0].slice(0, 5).text().then(function (t) { window.__shared.head = t; });
      };
    """)
    r.open()
    r.pick_roles(["student"])
    r.walk(overrides={"about": about_step()})
    with tempfile.TemporaryDirectory() as folder:
        name, path = press_send_and_save_pdf(r, folder)
    check(r.page.locator("#sent button:has-text('Share the PDF')").count() == 1, "the panel offers 'Share the PDF' when the browser can share files")
    check("paste" in r.page.inner_text("#sent").lower(), "the panel explains that the address is copied for pasting into the To box")
    r.page.click("#sent button:has-text('Share the PDF')")
    r.page.wait_for_function("window.__shared && window.__shared.head")
    sh = r.page.evaluate("window.__shared")
    check(sh["name"] == name and sh["type"] == "application/pdf" and sh["head"] == "%PDF-" and sh["size"] > 20000, f"the shared file is the PDF: {sh['name']} {sh['type']} {sh['size']} bytes")
    check(sh["title"] == "Shaping Dhar survey response: Student", f"share title is the email subject: {sh['title']!r}")
    check(sh["text"].startswith("To: garbaabdullahi344@gmail.com\nSubject: Shaping Dhar survey response: Student\n\nSHAPING DHAR SURVEY RESPONSE"), "share text starts with the address, the subject and the response")
    check(sh["text"].rstrip().endswith("== END OF RESPONSE =="), "share text carries the whole response")
    check(r.page.evaluate("navigator.clipboard.readText()") == "garbaabdullahi344@gmail.com", "the address was copied for pasting")
    r.close()


@test
def t_pdf_failure_falls_back_to_text(env):
    r = Run(env.browser, env.base)
    r.page.route("**/assets/pdf-fonts.js", lambda route: route.abort())
    downloads = []
    r.page.on("download", lambda d: downloads.append(d))
    r.open()
    r.pick_roles(["student"])
    r.walk(overrides={"about": about_step()})
    r.page.wait_for_function("document.getElementById('pdf-note').textContent.indexOf('could not be made') !== -1", timeout=30000)
    check(r.page.inner_text("#btn-send") == "Send by email" and r.page.is_enabled("#btn-send"), "the button goes back to a plain 'Send by email', enabled")
    check("PDF copy:" not in r.report(), "the email text does not mention a PDF that does not exist")
    r.page.click("#btn-send")
    r.page.wait_for_selector("#sent:not([hidden])")
    mt = r.mailto()
    body = urllib.parse.parse_qs(urllib.parse.urlparse(mt).query)["body"][0].replace("\r\n", "\n")
    check(mt.startswith("mailto:garbaabdullahi344@gmail.com") and body.rstrip().endswith("== END OF RESPONSE =="), "the text email is complete and addressed to the owner")
    check("PDF" not in r.page.inner_text("#sent"), "the confirmation does not talk about a PDF")
    r.page.wait_for_timeout(400)
    check(downloads == [], "nothing is downloaded")
    r.close()


@test
def t_pdf_can_be_switched_off(env):
    r = Run(env.browser, env.base)

    def patch(route):
        resp = route.fetch()
        route.fulfill(response=resp, body=resp.text().replace("pdfEnabled: true", "pdfEnabled: false"))
    r.page.route("**/assets/config.js", patch)
    requests, downloads = [], []
    r.page.on("request", lambda q: requests.append(q.url))
    r.page.on("download", lambda d: downloads.append(d))
    r.open()
    check(r.page.evaluate("window.DHAR_CONFIG.pdfEnabled") is False, "the flag is off")
    r.pick_roles(["student"])
    r.walk(overrides={"about": about_step()})
    check(r.page.inner_text("#btn-send") == "Send by email" and r.page.is_enabled("#btn-send"), "button reads 'Send by email'")
    check("PDF" not in r.page.inner_text("#step-review"), "the review step does not mention a PDF")
    check("PDF copy:" not in r.report(), "no PDF line in the email text")
    r.page.click("#btn-send"); r.page.wait_for_selector("#sent:not([hidden])")
    check(r.mailto() is not None and "PDF" not in r.page.inner_text("#sent"), "the email opens and the panel is the text-only one")
    check(not [u for u in requests if "pdf" in u.lower()], f"the PDF code is never requested: {[u for u in requests if 'pdf' in u.lower()]}")
    check(downloads == [], "nothing is downloaded")
    r.close()


@test
def t_pdf_from_disk(env):
    r = Run(env.browser, env.base, permissions=False)
    r.page.goto("file://" + os.path.join(os.path.abspath(ARGS.site), "index.html"))
    r.page.wait_for_selector("html[data-ready=true]")
    r.pick_roles(["student"])
    r.walk(overrides={"about": about_step()})
    try:
        r.page.wait_for_function("document.getElementById('btn-send').textContent.indexOf('Download PDF') === 0", timeout=30000)
        ok = True
    except Exception:
        ok = False
    check(ok, "the PDF is made when the page is opened straight from disk (file://)")
    r.close()



class Env:
    pass


def main():
    server = start_server()
    env = Env()
    env.base = f"http://127.0.0.1:{server.server_address[1]}"
    with sync_playwright() as p:
        kwargs = {}
        if ARGS.chromium:
            kwargs["executable_path"] = ARGS.chromium
        env.browser = p.chromium.launch(**kwargs)
        for fn in TESTS:
            CURRENT["name"] = fn.__name__
            print(f"- {fn.__name__}")
            try:
                fn(env)
            except Exception as exc:                      # a crash is a failure, with its traceback
                RESULTS.append((fn.__name__, False, "exception: " + repr(exc)))
                print("    EXCEPTION:", repr(exc))
                traceback.print_exc()
        env.browser.close()
    server.shutdown()

    failed = [r for r in RESULTS if not r[1]]
    if SKIPPED:
        print("\nSKIPPED (tool not installed): " + ", ".join(sorted(set(SKIPPED))))
    print(f"\n{len(RESULTS) - len(failed)} of {len(RESULTS)} checks passed in {len(TESTS)} tests")
    for name, ok, msg in failed:
        print(f"  FAILED [{name}] {msg}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
