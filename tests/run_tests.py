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
  - the relay (direct delivery): the REAL relay/Code.gs runs behind relay/test/mock_apps_script.js, a local
    server that behaves like an Apps Script web app (redirect to a second origin, CORS on the answer, no
    pre-flight). Covers delivery with the PDF attached, Reply-To, retries, unconfirmed delivery, timeouts,
    errors and quota, the email fallback, and that nothing is ever sent twice (needs node; skipped without it)
  - the PDF copy: valid file, every question and answer in it, text selectable, Nigerian-language
    letters intact, nothing outside the margins, share-sheet button, and a clean fall-back to a
    text-only email when the PDF cannot be made or is switched off (needs qpdf and poppler's
    pdftotext/pdffonts for the file checks; without them those checks are reported as skipped)

Usage
  pip install playwright            # and a Chromium for it (see README)
  python3 tests/run_tests.py [--site DIR] [--shots DIR] [--chromium PATH] [--axe PATH] [--only TEXT]

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
import urllib.request

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

ap = argparse.ArgumentParser()
ap.add_argument("--site", default=ROOT, help="folder that contains index.html")
ap.add_argument("--shots", default=None, help="folder for screenshots (optional)")
ap.add_argument("--chromium", default=os.environ.get("CHROMIUM"), help="path to a Chromium/Chrome binary")
ap.add_argument("--axe", default=os.environ.get("AXE_JS"), help="path to axe.min.js")
ap.add_argument("--only", default=None, help="run only the tests whose name contains this text (for example: relay)")
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
        import csv
        # the same response twice (one copy quoted the way a reply or forward would quote it) is ONE response
        open(src, "w", encoding="utf-8").write("From: someone\nSubject: x\n\n" + rep + "\n\n> " + rep.replace("\n", "\n> ") + "\n")
        out = os.path.join(d, "out.csv")
        res = subprocess.run([sys.executable, "-I", parser, src, "-o", out], capture_output=True, text=True)
        check(res.returncode == 0, f"parser exits cleanly: {res.stderr[-300:]}")
        check("1 duplicate merged" in res.stderr, f"the parser reports the merged duplicate: {res.stderr.strip()!r}")
        rows = list(csv.DictReader(open(out, encoding="utf-8")))
        check(len(rows) == 1, f"two copies with the same response ID give one row ({len(rows)})")
        # two different responses (a different ID in the second copy) stay two rows
        rid = re.search(r"Response ID: (\S+)", rep).group(1)
        other = rep.replace(rid, rid[:-6] + "zzzzzz")
        open(src, "w", encoding="utf-8").write("From: someone\nSubject: x\n\n" + rep + "\n\n> " + other.replace("\n", "\n> ") + "\n")
        res = subprocess.run([sys.executable, "-I", parser, src, "-o", out], capture_output=True, text=True)
        rows = list(csv.DictReader(open(out, encoding="utf-8")))
        check(len(rows) == 2 and "duplicate" not in res.stderr, f"different response IDs stay separate rows ({len(rows)})")
        # a cut-short copy is replaced by the complete one, whichever comes first
        cut = rep.split("== PERSONA")[0] if "== PERSONA" in rep else "\n".join(rep.split("\n")[:20])
        open(src, "w", encoding="utf-8").write(cut + "\n\n" + rep + "\n")
        res = subprocess.run([sys.executable, "-I", parser, src, "-o", out], capture_output=True, text=True)
        rows = list(csv.DictReader(open(out, encoding="utf-8")))
        check(len(rows) == 1 and rows[0]["complete"] == "yes" and rows[0]["A1"] == "Nigeria", f"a cut-short copy is replaced by the complete one: {len(rows)} row(s), complete={rows[0]['complete'] if rows else None}")
        # a response without an ID is never merged with another
        legacy = re.sub(r"(?m)^Response ID: .*\n", "", rep)
        open(src, "w", encoding="utf-8").write(legacy + "\n\n" + legacy + "\n")
        res = subprocess.run([sys.executable, "-I", parser, src, "-o", out], capture_output=True, text=True)
        rows = list(csv.DictReader(open(out, encoding="utf-8")))
        check(len(rows) == 2, f"responses without an ID are never merged ({len(rows)})")
        # the main file, for the field checks
        open(src, "w", encoding="utf-8").write("From: someone\nSubject: x\n\n" + rep + "\n")
        subprocess.run([sys.executable, "-I", parser, src, "-o", out], capture_output=True, text=True)
        rows = list(csv.DictReader(open(out, encoding="utf-8")))
        if rows:
            row = rows[0]
            check(row.get("response_id") == rid, f"response_id column holds the reference: {row.get('response_id')!r}")
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



# --------------------------------------------------------------------------- the relay (direct delivery)
#
# These tests run the REAL relay/Code.gs behind relay/test/mock_apps_script.js (a local web server that
# behaves like an Apps Script web app: POST, a redirect to a second origin, CORS headers on the answer,
# no answer to a pre-flight). The "emails" it sends are read back from /__outbox.

RELAY = {}


def start_relay():
    node = shutil.which("node")
    script = os.path.join(ROOT, "relay", "test", "mock_apps_script.js")
    if not node or not os.path.exists(script):
        return None
    proc = subprocess.Popen([node, script], stdout=subprocess.PIPE, text=True)
    info = json.loads(proc.stdout.readline())
    RELAY.update(proc=proc, origin=f"http://127.0.0.1:{info['port']}", echo=f"http://127.0.0.1:{info['echoPort']}")
    RELAY["url"] = RELAY["origin"] + "/macros/s/MOCK/exec"
    return proc


def relay_call(path, data=None):
    req = urllib.request.Request(RELAY["origin"] + path, data=None if data is None else json.dumps(data).encode(),
                                 method="GET" if data is None else "POST")
    with urllib.request.urlopen(req, timeout=10) as res:
        return json.loads(res.read().decode())


def relay_reset():
    relay_call("/__reset", {})


def relay_mode(**mode):
    relay_call("/__mode", mode)


def relay_run(env, token=None, timeout_ms=None, url=None, **run_kwargs):
    """A Run whose config.js points at the mock relay (and optionally has another token or timeout)."""
    r = Run(env.browser, env.base, **run_kwargs)
    target = url or RELAY["url"]

    def patch(route):
        resp = route.fetch()
        body = resp.text().replace("relayUrl: ''", f"relayUrl: '{target}'")
        if token is not None:
            body = re.sub(r"relayToken: '[^']*'", f"relayToken: '{token}'", body)
        if timeout_ms is not None:
            body = re.sub(r"relayTimeoutMs: \d+", f"relayTimeoutMs: {timeout_ms}", body)
        route.fulfill(response=resp, body=body)
    r.page.route("**/assets/config.js", patch)
    return r


CONTACT = "ada.obi@example.com or WhatsApp +234 801 234 5678"


def relay_walk(r, contact=CONTACT, roles=("student", "dev")):
    """Opens the page, picks roles, answers the required questions, and lands on the review step.
    contact=None answers 'Not right now' to the contact question (an anonymous response)."""
    r.open()
    r.pick_roles(list(roles))

    def on_step(t):
        if t == "Stay in touch":
            if contact is None:
                r.page.check("#in-C1-no")
            else:
                r.page.check("#in-C1-yes")
                r.page.fill("#in-C2", contact)
    r.walk(on_step=on_step, overrides={"about": about_step(areas=["software"])})


def wait_relay_ready(r, label="Send my answers"):
    r.page.wait_for_function("label => { const b = document.getElementById('btn-send'); return !!b && !b.disabled && b.textContent === label; }",
                             arg=label, timeout=30000)


def panel_title(r):
    r.page.wait_for_selector("#sent:not([hidden])", timeout=20000)
    return r.page.inner_text("#sent-title")


def only_relay_traffic(r):
    return [u for u in r.external if not (u.startswith(RELAY["origin"]) or u.startswith(RELAY["echo"]))]


def attachment_to_file(mail, folder):
    att = mail["attachments"][0]
    path = os.path.join(folder, att["name"])
    import base64
    open(path, "wb").write(base64.b64decode(att["base64"]))
    return att["name"], path


@test
def t_relay_happy_path(env):
    relay_reset()
    r = relay_run(env)
    downloads = []
    r.page.on("download", lambda d: downloads.append(d.suggested_filename))
    relay_walk(r)
    check(r.page.inner_text("#btn-send") in ("Preparing your PDF...", "Send my answers"), "the main button is 'Send my answers'")
    check(r.page.locator("#btn-email").count() == 1, "the email route is still offered next to it")
    check("Google" in r.page.inner_text("#step-review") and "encrypted" in r.page.inner_text("#step-review"), "the review step says where the answers go")
    wait_relay_ready(r)
    rep = r.report()
    check("Response ID: dhar-" in rep, "the report carries a response ID")
    r.page.click("#btn-send")
    check(panel_title(r) == "Your answers were sent", "the confirmation says the answers were sent")
    check(r.page.inner_text("#btn-send") == "Sent" and r.page.is_disabled("#btn-send") and r.page.is_disabled("#btn-email"), "both send buttons are disabled afterwards")

    outbox = relay_call("/__outbox")
    check(len(outbox) == 1, f"exactly one email was produced ({len(outbox)})")
    m = outbox[0]
    rid = re.search(r"Response ID: (dhar-[0-9]{8}-[0-9]{6}-[a-z0-9]{6})", rep).group(1)
    check(m["to"] == "owner@example.com" and m["name"] == "Shaping Dhar survey", "sent to the script owner under the survey's name")
    check(m.get("replyTo") == "ada.obi@example.com", f"Reply-To is the respondent's address, taken from the contact answer: {m.get('replyTo')!r}")
    check(m["subject"] == "Shaping Dhar survey response: Student, Developer or engineer [" + rid + "]", f"subject: {m['subject']!r}")
    check(m["body"].startswith(rep + "\n") and "Response ID: " + rid in m["body"].split("== END OF RESPONSE ==")[1], "the body is exactly the report shown on the review step, plus the relay's trailer")
    check("PDF attached: yes" in m["body"] and "Reply-To: ada.obi@example.com" in m["body"], "the trailer says the PDF is attached and who the Reply-To is")
    check(len(m["attachments"]) == 1 and m["attachments"][0]["type"] == "application/pdf", "one PDF is attached")
    with tempfile.TemporaryDirectory() as folder:
        name, path = attachment_to_file(m, folder)
        verify_pdf(r, path, name, "PDF attached to the relayed email")
        with r.page.expect_download() as dl:
            r.page.click("#sent button:has-text('Download my copy (PDF)')")
        mine = os.path.join(folder, "mine.pdf")
        dl.value.save_as(mine)
        check(open(mine, "rb").read() == open(path, "rb").read(), "the respondent's own copy is byte-for-byte the PDF that was emailed")
    sheets = relay_call("/__sheets")
    head, rows = sheets["Responses"][0], sheets["Responses"][1:]
    check(len(rows) == 1, f"the response is also in the log sheet ({len(rows)} row)")
    row = dict(zip(head, rows[0]))
    check(row["response_id"] == rid and row["status"] == "emailed" and row["reply_to"] == "ada.obi@example.com", f"the log row has the same reference, status and reply-to: {row['response_id']} {row['status']} {row['reply_to']}")
    check(row["response_text"] == rep, "the log row holds the whole response text, the same as the email")
    qs = survey_questions(r)
    logged_q = {c: t for c, _v, t in sheets["Questions"][1:]}
    codes = [c for c, _ in report_blocks(rep)]
    check(set(codes) <= set(logged_q) and all(logged_q[c].startswith(qs[c]["text"]) for c in codes), "the Questions sheet holds the full wording of every question that was answered (the line may carry the hint after it)")
    check(r.mailto() is None, "no email app was opened")
    check(len(downloads) == 1, f"nothing was downloaded until the respondent asked for their copy ({downloads})")
    check(rid in r.page.inner_text("#sent"), "the confirmation shows the reference number")
    check("removed from this device" in r.page.inner_text("#sent"), "the confirmation says the draft was removed")
    check(r.page.evaluate("Object.keys(localStorage).filter(k => k.indexOf('dhar-survey') === 0)") == [], "the saved draft is gone from this device")

    traffic = [l for l in relay_call("/__log")]
    posts = [l for l in traffic if l["method"] == "POST"]
    check(len(posts) == 1 and posts[0]["type"].lower().startswith("text/plain"), f"one POST, as text/plain: {posts}")
    check([l for l in traffic if l["method"] == "OPTIONS"] == [], "no CORS pre-flight was needed")
    check(not any(l["cookie"] for l in traffic), "no cookies were sent to the relay")
    check(only_relay_traffic(r) == [], f"the page talked to nobody but the relay: {only_relay_traffic(r)}")
    check(r.errors == [], f"no console errors: {r.errors}")
    r.close()


@test
def t_relay_anonymous_has_no_reply_to(env):
    relay_reset()
    r = relay_run(env)
    relay_walk(r, contact=None)
    wait_relay_ready(r)
    r.page.click("#btn-send")
    check(panel_title(r) == "Your answers were sent", "an anonymous response is sent too")
    m = relay_call("/__outbox")[0]
    check("replyTo" not in m, f"no Reply-To when the respondent gave no address: {m.get('replyTo')!r}")
    check("Reply-To: none given" in m["body"], "the trailer says so")
    check("ada.obi" not in json.dumps(m), "no address appears anywhere in the email")
    r.close()


@test
def t_relay_a_phone_number_is_not_a_reply_to(env):
    relay_reset()
    r = relay_run(env)
    relay_walk(r, contact="WhatsApp +234 801 234 5678")
    wait_relay_ready(r)
    r.page.click("#btn-send")
    panel_title(r)
    m = relay_call("/__outbox")[0]
    check("replyTo" not in m and "+234 801 234 5678" in m["body"], "a WhatsApp number is reported in the text but is not used as a Reply-To")
    r.close()


@test
def t_relay_retries_after_a_dropped_connection(env):
    relay_reset()
    relay_mode(dropFirst=True)
    r = relay_run(env)
    relay_walk(r)
    wait_relay_ready(r)
    r.page.click("#btn-send")
    check(panel_title(r) == "Your answers were sent", "the page retried and the response arrived")
    posts = [l for l in relay_call("/__log") if l["method"] == "POST"]
    check(len(posts) == 2, f"two attempts were made ({len(posts)})")
    check(len(relay_call("/__outbox")) == 1, "one email only")
    check(len(relay_call("/__sheets")["Responses"]) == 2, "one row in the log")
    r.close()


@test
def t_relay_unconfirmed_delivery_offers_email_without_double_sending(env):
    """The relay processes the response but the page may not read the answer (here: no CORS header on it).
    The page cannot know, so it must say so, offer the email route, and never mail the response twice."""
    relay_reset()
    relay_mode(noCors=True)
    r = relay_run(env)
    relay_walk(r)
    wait_relay_ready(r)
    r.page.click("#btn-send")
    check(panel_title(r) == "We could not confirm that your answers arrived", "the page says it could not confirm delivery")
    check(len(relay_call("/__outbox")) == 1, "the retry did not produce a second email (the relay ignored the repeated ID)")
    check(len(relay_call("/__sheets")["Responses"]) == 2, "nor a second row in the log")
    rid = re.search(r"Response ID: (dhar-\S+)", r.report()).group(1)
    check(rid in r.page.inner_text("#sent"), "the panel quotes the reference number")
    link = r.page.locator("#sent a:has-text('Open my email app')")
    check(link.count() == 1 and link.get_attribute("href").startswith("mailto:garbaabdullahi344@gmail.com?subject="), "the panel offers a ready-addressed email")
    body = urllib.parse.parse_qs(urllib.parse.urlparse(link.get_attribute("href")).query)["body"][0].replace("\r\n", "\n")
    check("Response ID: " + rid in body and body.rstrip().endswith("== END OF RESPONSE =="), "that email carries the same reference and the full response")
    check(r.page.locator("#sent button:has-text('Try sending again')").count() == 1, "a retry button is offered")
    check(r.page.locator("#sent a[target=_blank]").count() == 3, "the three webmail links are offered")
    check(r.page.inner_text("#btn-send") == "Send my answers" and r.page.is_enabled("#btn-send"), "the main button is usable again")
    downloads = []
    r.page.on("download", lambda d: downloads.append(d.suggested_filename))
    link.click()
    r.page.wait_for_timeout(600)
    check(r.mailto() is not None and len(downloads) == 1, "pressing it opens the email app and saves the PDF copy")
    check(r.page.evaluate("Object.keys(localStorage).filter(k => k.indexOf('dhar-survey') === 0)") != [], "the draft was NOT cleared, because delivery was not confirmed")
    r.close()


@test
def t_relay_unreachable_server(env):
    relay_reset()
    r = relay_run(env, url="http://127.0.0.1:9/macros/s/NOBODY/exec")     # nothing listens on port 9
    relay_walk(r)
    wait_relay_ready(r)
    t0 = time.time()
    r.page.click("#btn-send")
    check(panel_title(r) == "We could not confirm that your answers arrived", "no connection at all leads to the email route")
    check(time.time() - t0 < 12, f"it gives up quickly ({time.time() - t0:.1f} s)")
    check(r.page.locator("#sent a:has-text('Open my email app')").count() == 1, "the email route is offered")
    r.close()


@test
def t_relay_timeout(env):
    relay_reset()
    relay_mode(delayMs=1500)
    r = relay_run(env, timeout_ms=300)
    relay_walk(r)
    wait_relay_ready(r)
    t0 = time.time()
    r.page.click("#btn-send")
    check(panel_title(r) == "We could not confirm that your answers arrived", "a relay that answers too slowly leads to the email route")
    check(time.time() - t0 < 8, f"after about two short attempts ({time.time() - t0:.1f} s)")
    r.page.wait_for_timeout(4500)       # let the slow server finish
    check(len(relay_call("/__outbox")) == 1, "the slow response was emailed once, not twice")
    check(len(relay_call("/__sheets")["Responses"]) == 2, "and logged once")
    r.close()


@test
def t_relay_server_errors_can_be_retried(env):
    relay_reset()
    relay_mode(sendThrows=True, logToSheet=False)      # with the log on, a mail failure is absorbed (next test)
    r = relay_run(env)
    relay_walk(r)
    wait_relay_ready(r)
    r.page.click("#btn-send")
    check(panel_title(r) == "Your answers have not been sent yet", "a relay error is reported")
    check("busy or at its limit" in r.page.inner_text("#sent"), "in plain words")
    check(relay_call("/__outbox") == [], "nothing was sent")
    check(r.page.locator("#sent a:has-text('Open my email app')").count() == 1, "the email route is offered")
    relay_mode(sendThrows=False)
    r.page.click("#sent button:has-text('Try sending again')")
    r.page.wait_for_function("document.getElementById('sent-title') && document.getElementById('sent-title').textContent === 'Your answers were sent'", timeout=20000)
    check(len(relay_call("/__outbox")) == 1, "trying again worked, and sent exactly one email")
    r.close()


@test
def t_relay_daily_quota_still_saves_the_response(env):
    relay_reset()
    relay_mode(quota=2)
    r = relay_run(env)
    relay_walk(r)
    wait_relay_ready(r)
    r.page.click("#btn-send")
    check(panel_title(r) == "Your answers were sent", "an exhausted daily mail quota does not stop the respondent")
    check("received and saved" in r.page.inner_text("#sent"), "the panel says the answers were saved (not emailed): " + r.page.inner_text("#sent")[:160])
    check(relay_call("/__outbox") == [], "no email was attempted")
    rows = relay_call("/__sheets")["Responses"]
    check(len(rows) == 2 and rows[1][rows[0].index("status")] == "stored", "the response is in the log, marked stored")
    r.close()


@test
def t_relay_quota_with_the_log_off_leads_to_email(env):
    relay_reset()
    relay_mode(quota=2, logToSheet=False)
    r = relay_run(env)
    relay_walk(r)
    wait_relay_ready(r)
    r.page.click("#btn-send")
    check(panel_title(r) == "Your answers have not been sent yet" and "busy or at its limit" in r.page.inner_text("#sent"), "with no log to fall back on, an exhausted quota is reported as busy")
    check(relay_call("/__outbox") == [] and r.page.locator("#sent a:has-text('Open my email app')").count() == 1, "nothing was sent and the email route is there")
    r.close()


@test
def t_relay_email_failure_is_absorbed_by_the_log(env):
    relay_reset()
    relay_mode(sendThrows=True)
    r = relay_run(env)
    relay_walk(r)
    wait_relay_ready(r)
    r.page.click("#btn-send")
    check(panel_title(r) == "Your answers were sent" and "received and saved" in r.page.inner_text("#sent"), "a failing email is not the respondent's problem when the log has the response")
    rows = relay_call("/__sheets")["Responses"]
    check(len(rows) == 2 and rows[1][rows[0].index("status")] == "stored", "the log has it, marked stored")
    check(relay_call("/__outbox") == [], "no email went")
    r.close()


@test
def t_relay_log_failure_is_absorbed_by_the_email(env):
    relay_reset()
    relay_mode(sheetThrows=True)
    r = relay_run(env)
    relay_walk(r)
    wait_relay_ready(r)
    r.page.click("#btn-send")
    check(panel_title(r) == "Your answers were sent" and "PDF copy were sent" in r.page.inner_text("#sent"), "a failing log is not the respondent's problem when the email went")
    check(len(relay_call("/__outbox")) == 1 and relay_call("/__sheets") == {}, "the email went; nothing in the log")
    r.close()


@test
def t_relay_log_agrees_with_the_parser(env):
    """The sheet the relay writes and the CSV the parser makes from the emails must say the same."""
    relay_reset()
    for n, (roles, kwargs) in enumerate([(("student", "dev"), {}), (tuple(ALL_ROLES), {"long_text": 380, "only_required": False})]):
        r = relay_run(env)
        r.open()
        r.pick_roles(list(roles))
        areas = ["software", "web", "ai", "security"] if n else ["software"]

        def on_step(t, r=r):
            if t == "Stay in touch":
                r.page.check("#in-C1-yes")
                r.page.fill("#in-C2", "=cmd|' /C calc'!A0 ada@example.com")     # a hostile contact answer
        r.walk(on_step=on_step, overrides={"about": about_step(areas=areas)}, **kwargs)
        wait_relay_ready(r)
        r.page.click("#btn-send")
        panel_title(r)
        r.close()
    out = relay_call("/__outbox")
    check(len(out) == 2, f"two responses arrived ({len(out)})")
    sheets = relay_call("/__sheets")["Responses"]
    head, rows = sheets[0], sheets[1:]
    check(len(rows) == 2, f"two rows in the log ({len(rows)})")
    parser = os.path.join(ROOT, "tools", "parse_responses.py")
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "mail.txt")
        open(src, "w", encoding="utf-8").write("\n\n".join(m["body"] for m in out))
        csv_path = os.path.join(d, "out.csv")
        res = subprocess.run([sys.executable, "-I", parser, src, "-o", csv_path], capture_output=True, text=True)
        check(res.returncode == 0, f"the parser reads the relayed emails: {res.stderr[-200:]}")
        import csv
        parsed = {rw["response_id"]: rw for rw in csv.DictReader(open(csv_path, encoding="utf-8"))}
    check(len(parsed) == 2, "the parser finds both responses")
    compared = mismatched = 0
    for raw in rows:
        row = dict(zip(head, raw))
        want = parsed[row["response_id"]]
        for code in head[10:]:
            if want.get(code, "") == "" and raw[head.index(code)] == "":
                continue
            got = str(raw[head.index(code)])
            if got.startswith("'") and not want.get(code, "").startswith("'"):
                got = got[1:]
            compared += 1
            if got != want.get(code, ""):
                mismatched += 1
                print(f"    {code}: log={got[:60]!r} parser={want.get(code, '')[:60]!r}")
        check(row["survey_version"] == want["survey_version"] and row["roles"] == want["roles"] and row["pdf_copy"] == want["pdf_copy"], "header fields agree")
    check(compared > 60 and mismatched == 0, f"{compared} answers compared, {mismatched} differ")
    hostile = [dict(zip(head, rw))["C2"] for rw in rows]
    check(all(h.startswith("'=cmd") for h in hostile), f"the hostile contact answer is stored as text, not as a formula: {hostile}")
    check(all(dict(zip(head, rw))["reply_to"] == "ada@example.com" for rw in rows), "the Reply-To is the address found inside the contact answer")


@test
def t_relay_refusal_goes_to_email_without_retry(env):
    relay_reset()
    r = relay_run(env, token="not-the-token")
    relay_walk(r)
    wait_relay_ready(r)
    r.page.click("#btn-send")
    check(panel_title(r) == "Your answers have not been sent yet" and "(forbidden)" in r.page.inner_text("#sent"), "a refused token is reported with its code")
    check(r.page.locator("#sent button:has-text('Try sending again')").count() == 0, "no pointless retry button")
    check(r.page.locator("#sent a:has-text('Open my email app')").count() == 1, "the email route is offered")
    check(relay_call("/__outbox") == [], "nothing was sent")
    r.close()


@test
def t_relay_reply_that_is_not_json(env):
    relay_reset()
    relay_mode(html=True)
    r = relay_run(env)
    relay_walk(r)
    wait_relay_ready(r)
    r.page.click("#btn-send")
    check(panel_title(r) == "Your answers have not been sent yet" and "(bad-response)" in r.page.inner_text("#sent"), "a sign-in page instead of JSON is reported, not mistaken for success")
    r.close()


@test
def t_relay_without_a_pdf_still_sends(env):
    relay_reset()
    r = relay_run(env)
    r.page.route("**/assets/pdf-fonts.js", lambda route: route.abort())
    relay_walk(r)
    r.page.wait_for_function("document.getElementById('pdf-note').textContent.indexOf('could not be made') !== -1", timeout=30000)
    check(r.page.inner_text("#btn-send") == "Send my answers" and r.page.is_enabled("#btn-send"), "the send button is usable without a PDF")
    check("without it" in r.page.inner_text("#pdf-note"), "the note says the answers go without a PDF")
    r.page.click("#btn-send")
    check(panel_title(r) == "Your answers were sent", "sent")
    m = relay_call("/__outbox")[0]
    check("attachments" not in m or m["attachments"] == [], "no attachment")
    check("PDF" not in r.page.inner_text("#sent").replace("PDF copy", ""), "the confirmation does not claim a PDF")
    check("PDF copy:" not in m["body"], "the text does not mention a PDF copy")
    r.close()


@test
def t_relay_email_route_by_choice(env):
    relay_reset()
    r = relay_run(env)
    downloads = []
    r.page.on("download", lambda d: downloads.append(d.suggested_filename))
    relay_walk(r)
    wait_relay_ready(r)
    r.page.click("#btn-email")
    r.page.wait_for_selector("#sent:not([hidden])")
    check(r.page.inner_text("#sent-title") == "Your email is ready" and r.mailto() is not None, "choosing the email button opens the email draft")
    check(len(downloads) == 1, "the PDF copy is saved for attaching")
    check([l for l in relay_call("/__log") if l["method"] == "POST"] == [] and relay_call("/__outbox") == [], "the relay was never contacted")
    r.close()


@test
def t_relay_off_by_default(env):
    r = Run(env.browser, env.base).open()
    check("emailed to Abdullahi" in r.page.inner_text("#privacy") or "emailed to Abdullahi" in r.page.inner_text(".privacy"), "without a relay the start page keeps its email-route wording")
    r.pick_roles(["student"])
    r.walk(overrides={"about": about_step()})
    check(r.page.locator("#btn-email").count() == 0, "no second 'email instead' button")
    check(r.page.evaluate("window.DHAR_CONFIG.relayUrl") == "", "relayUrl is empty in the shipped config until the relay is set up")
    r.close()


@test
def t_relay_wording_and_layout(env):
    relay_reset()
    r = relay_run(env, permissions=False)
    r.open()
    privacy = r.page.inner_text(".privacy")
    check("Google" in privacy and "encrypted" in privacy and "Send" in privacy, "the start page says plainly that answers pass through a service on Google's servers")
    check("emailed to Abdullahi" not in privacy and "sent from your own email app" not in privacy, "and no longer claims they only leave through the respondent's email app")
    check("Answers are sent only when you press Send" in r.page.inner_text(".foot"), "the footer matches")
    r.close()
    axe_src = open(ARGS.axe, encoding="utf-8").read() if ARGS.axe and os.path.exists(ARGS.axe) else None
    for w, h, scheme in [(375, 780, "light"), (1280, 900, "light"), (375, 780, "dark")]:
        relay_reset()
        r = relay_run(env, viewport={"width": w, "height": h}, scheme=scheme, permissions=False)
        relay_walk(r)
        wait_relay_ready(r)
        over = []
        if r.page.evaluate("document.documentElement.scrollWidth") > w:
            over.append("review")
        if axe_src and scheme == "dark":
            r.page.add_script_tag(content=axe_src)
        r.shot(f"relay-{w}-{scheme}-review")
        r.page.click("#btn-send")
        panel_title(r)
        if r.page.evaluate("document.documentElement.scrollWidth") > w:
            over.append("sent")
        r.shot(f"relay-{w}-{scheme}-sent")
        check(not over, f"{w}px {scheme}: no sideways scrolling ({over})")
        if axe_src and scheme == "dark":
            res = r.page.evaluate("""async () => (await axe.run(document, {resultTypes: ['violations']})).violations.map(v => v.id + ': ' + v.nodes.slice(0, 2).map(n => n.target.join(' ')).join(' | '))""")
            check(res == [], f"axe (dark) on the relay confirmation: {res}")
        r.close()
    # the fallback panel too
    relay_reset()
    relay_mode(noCors=True)
    r = relay_run(env, viewport={"width": 375, "height": 780}, permissions=False)
    relay_walk(r)
    wait_relay_ready(r)
    r.page.click("#btn-send")
    panel_title(r)
    r.shot("relay-375-fallback")
    check(r.page.evaluate("document.documentElement.scrollWidth") <= 375, "375px: the fallback panel does not scroll sideways")
    if axe_src:
        r.page.add_script_tag(content=axe_src)
        res = r.page.evaluate("""async () => (await axe.run(document, {resultTypes: ['violations']})).violations.map(v => v.id + ': ' + v.nodes.slice(0, 2).map(n => n.target.join(' ')).join(' | '))""")
        check(res == [], f"axe on the fallback panel: {res}")
    r.close()


@test
def t_relay_check_page(env):
    relay_reset()
    r = relay_run(env, permissions=False)
    r.page.goto(env.base + "/relay-check.html")
    r.page.wait_for_selector("#btn-ping")
    check(RELAY["url"] in r.page.inner_text("#config-status"), "the check page shows the configured relay address")
    r.page.click("#btn-ping")
    r.page.wait_for_function("document.getElementById('ping-verdict').classList.contains('good') || document.getElementById('ping-verdict').classList.contains('bad')", timeout=15000)
    check("relay is alive" in r.page.inner_text("#ping-verdict"), f"ping succeeds: {r.page.inner_text('#ping-verdict')!r}")
    r.page.click("#btn-test")
    r.page.wait_for_function("document.getElementById('test-verdict').classList.contains('good') || document.getElementById('test-verdict').classList.contains('bad')", timeout=15000)
    check(r.page.inner_text("#test-verdict").startswith("Accepted in"), f"the test response is accepted: {r.page.inner_text('#test-verdict')!r}")
    out = relay_call("/__outbox")
    check(len(out) == 1 and out[0]["subject"].startswith("[TEST] Shaping Dhar survey response") and len(out[0]["attachments"]) == 1, "a [TEST] email with a PDF reached the outbox")
    # a relay the browser cannot read
    relay_mode(noCors=True)
    r.page.click("#btn-ping")
    r.page.wait_for_function("document.getElementById('ping-verdict').textContent.indexOf('could not read') !== -1", timeout=15000)
    check("Who has access" in r.page.inner_text("#ping-verdict") or "Anyone" in r.page.inner_text("#ping-verdict"), "an unreadable relay is explained, with the likely causes")
    r.close()
    r = Run(env.browser, env.base, permissions=False)
    r.page.goto(env.base + "/relay-check.html")
    r.page.click("#btn-test")
    check("relayUrl is empty" in r.page.inner_text("#test-verdict"), "with no relayUrl the page says what to do")
    r.close()


class Env:
    pass


def main():
    server = start_server()
    env = Env()
    env.base = f"http://127.0.0.1:{server.server_address[1]}"
    relay_proc = start_relay()
    if relay_proc is None:
        SKIPPED.append("node (the relay tests)")
    with sync_playwright() as p:
        kwargs = {}
        if ARGS.chromium:
            kwargs["executable_path"] = ARGS.chromium
        env.browser = p.chromium.launch(**kwargs)
        for fn in TESTS:
            if relay_proc is None and fn.__name__.startswith("t_relay_"):
                continue
            if ARGS.only and ARGS.only not in fn.__name__:
                continue
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
    if relay_proc is not None:
        relay_proc.terminate()

    failed = [r for r in RESULTS if not r[1]]
    if SKIPPED:
        print("\nSKIPPED (tool not installed): " + ", ".join(sorted(set(SKIPPED))))
    print(f"\n{len(RESULTS) - len(failed)} of {len(RESULTS)} checks passed in {len(TESTS)} tests")
    for name, ok, msg in failed:
        print(f"  FAILED [{name}] {msg}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
