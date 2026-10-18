# Shaping Dhar: the survey page

A role-branching survey for **lecturers, researchers, students and developers**, about Dhar, the systems language and toolchain built independently in Nigeria. It asks how people feel about a new Nigerian / African language and which features they want across software, web, mobile, data, AI, machine learning, systems, cybersecurity and blockchain.

It is a static page. There is no server, no database and no form service. When a respondent presses **Send**, the page opens their own email app with the questions and their answers already written into a message addressed to the project lead. They press Send there.

- Page: `index.html` (plain HTML, CSS and JavaScript, nothing to build or install)
- Dependencies: none. The page loads nothing from other sites. It ships one self-hosted font (Archivo, SIL OFL).
- Works from GitHub Pages, from any web host, and when `index.html` is opened straight from disk.

---

## 1. What the respondent sees

1. **Start**: tick the roles that fit (more than one is allowed).
2. **About you**: country, experience, current areas of work, languages used, whether they had heard of Dhar.
3. **One step per role ticked**: Teaching, Research, Learning, Building. Only the questions for the ticked roles appear.
4. **Your areas in detail**: optional blocks, one for each area ticked on the About step (backend and software, web and mobile, data, AI, machine learning, systems, cybersecurity, blockchain). Each asks what Dhar would need to offer, which tools it must work with, and the biggest problem a new language could fix. These can be skipped.
5. **Your view of Dhar**: sentiment, priorities, what would make them try it, what put them off new languages before.
6. **Stay in touch**: optional contact details.
7. **Review and send**: the page builds the email. It shows where it is going and gives fallbacks.

The survey has 80 questions plus the role question. A person with one role and no optional blocks answers about 23 to 25 questions (8 to 12 minutes). `docs/CODEBOOK.md` lists every question, its answer options and who sees it.

---

## 2. Put it online (GitHub Pages)

The site is the content of the repository's root folder (`index.html`, `assets/`, `LICENSE`, `.nojekyll`).

1. Put these files on a branch of your repository. The scripted publish uses a branch named `gh-pages`.
2. On GitHub open **Settings → Pages**.
3. Under **Build and deployment**, choose **Deploy from a branch**, pick `gh-pages` and the folder `/ (root)`, and save.
4. After a minute the page is at `https://<user>.github.io/<repository>/`.

Pushing the branch may not switch Pages on by itself. If the page does not appear, step 3 is the missing piece.

To use another host (Netlify, Cloudflare Pages, your own server), upload the same files. No settings are needed.

---

## 3. Change things

| To change | Edit | Then |
| --- | --- | --- |
| Questions, options, branching | `assets/questions.js` (the header of that file explains every field) | raise `version`, run the tests, run `node tools/export_codebook.js` |
| Who receives the answers | `recipientUser` and `recipientDomain` in `assets/config.js` (change both halves) | reload |
| Email subject, size limits, repository link | `assets/config.js` | reload |
| Colours, spacing, fonts | `assets/survey.css` (tokens are at the top) | reload |
| Page text (title, intro, privacy note) | `index.html` | reload |

Rules for the question bank:

- A question **code** (`A3`, `D5`, `SW1`) never changes meaning. If you reword a question substantially or change the order of options, **raise `version`**. The version is printed in every response and names the browser-storage slot, so old drafts never mix with new questions.
- Options written as plain strings get positional ids (`o1`, `o2`, ...), so their order matters. Options written as objects have stable ids you choose.
- The `ROLE` option ids (`prof`, `researcher`, `student`, `dev`) must match the `role` conditions in `showIf` rules.

---

## 4. How answers reach you

The email is written in plain text and always starts with `SHAPING DHAR SURVEY RESPONSE` and ends with `== END OF RESPONSE ==`:

```
SHAPING DHAR SURVEY RESPONSE
Survey version: 1.0
Submitted: 2026-10-18 21:40 (UTC+01:00) Africa/Lagos
Roles: Student; Developer or engineer
Questions answered: 41 of 52 shown
Question wording: full

== CONTACT ==

[C1] Would you like to stay informed ...
  Yes, here is how to reach me
[C2] What email address or other contact should we use?
  ada@example.edu

== ABOUT YOU ==
...
```

The order is contact, about you, sentiment and priorities, then the role sections, then the optional area blocks. If an email is ever cut short, the least important part is lost.

### Size limits (read this)

A `mailto:` link carries the whole message inside the web address, and email apps differ in how much they accept. The page tries three forms and uses the first that fits:

1. **full**: every question's full wording and the answer
2. **compact**: the same answers with long question wording shortened (`Question wording: shortened` appears in the header)
3. **cut**: the compact text cut at a line break and clearly marked as cut

Whatever is sent, the **complete** answers are also copied to the respondent's clipboard, and the confirmation panel offers **Copy answers**, **Download .txt**, and links that open Gmail, Outlook and Yahoo Mail in the browser with the message prefilled.

The limits are set in `assets/config.js` (`mailtoLimitWindows` 1900, `mailtoLimitOther` 7500, `webComposeLimit` 7000). **These are cautious estimates, not measured values.** No authoritative published limits were found, and they differ by mail app and version. The Outlook and Yahoo compose-link formats were also not checked against a live account. Treat the first few real submissions from Windows, Android and iPhone as the test, and adjust the numbers if people are being cut when they need not be.

### Reading the responses

Save the response emails (or export a mailbox) and run:

```
python3 tools/parse_responses.py responses.mbox -o responses.csv
python3 tools/parse_responses.py mail/*.txt mail/*.eml -o responses.csv
```

It needs only Python 3 and accepts `.txt`, `.eml` and `.mbox`, several responses per file, and quoted replies. The CSV has one row per response, the columns `source`, `response`, `survey_version`, `submitted`, `roles`, `answered`, `wording`, `complete`, then one column per question code. `complete` is `no` for an email that was cut short; its first part is still read. `docs/CODEBOOK.md` explains each column.

---

## 5. Privacy, stated plainly

- The page itself collects nothing and sends nothing. There are no analytics, no cookies and no requests to other sites (the test suite checks this).
- Unfinished answers are saved in the browser's local storage on that device so a refresh does not lose them. They are cleared by **Start over** and after **I have sent it**.
- An email sent from the respondent's own app **shows you their email address**, even if they leave the contact question blank. The page says so in its introduction. Do not describe the survey as anonymous.
- The recipient address is joined from two halves at run time, which only deters simple scrapers. It is visible to anyone who reads the page's JavaScript and in every email. The repository and the page are public.
- Each respondent must press Send in their own email app. If they close it, nothing arrives.

---

## 6. Tests

`tests/run_tests.py` drives the page in headless Chromium the way a respondent would and checks, among other things: all 15 combinations of roles show the right steps; validation, "up to N" limits, "Other" boxes and the exclusive "None"; hidden answers stay out of the report; the report text, the `mailto:` link, the webmail links, download and clipboard; the full, compact and cut email forms on Windows and other systems; drafts saving and clearing; no requests to other sites and no JavaScript errors; no sideways scrolling at phone, tablet and desktop widths; accessibility with axe-core in light and dark; and that `tools/parse_responses.py` reads what the page produces.

```
pip install playwright --break-system-packages    # plus a Chromium for it
npm pack axe-core && tar -xzf axe-core-*.tgz      # gives package/axe.min.js (optional)
CHROMIUM=/path/to/chromium AXE_JS=package/axe.min.js python3 tests/run_tests.py --shots shots
```

Add `--site src` if you keep the site in a `src/` folder. The exit status is 0 only if every check passed. The last run: 20 tests, 185 checks, all passed.

---

## 7. Notes

- **Opening `index.html` from disk** works, but browsers refuse to load the font file from a `file://` address, so the page falls back to the system font and the console shows a font error. On GitHub Pages or any web server the font loads normally.
- **No JavaScript** shows a message asking the visitor to turn it on.
- **Spec1 code sample** in the page header shows syntax as Spec1 defines it today. Update `index.html` if the specification changes.

### Where this differs from the original blueprint

The survey follows the original blueprint's questions and intent. These things changed, and why:

| Blueprint | This page | Why |
| --- | --- | --- |
| Four yes/no gate questions, one per role | One "tick every role that fits" question | The gates existed only because Google Forms cannot branch from a checkbox. Here branching is in code. |
| Hosted in a form builder, "anonymous unless contact left" | Static page that hands off to the respondent's email app | You asked for a GitHub page that emails the answers. The sender's address is visible, so the page no longer says "anonymous". |
| AI/ML as one option in "what are you involved in" | AI and machine learning are separate options, and "None of these yet" was added. Languages list also gets "None yet". | Lets each area drive its own detail block, and lets beginners answer honestly. |
| One shared list of areas | The About step's area question drives optional detail blocks (backend, web and mobile, data, AI, ML, systems, security, blockchain) | To capture wanted features per area without making everyone answer everything. |
| Contact last | Contact is written first in the email | If an email is cut short, the contact details survive. |

---

## 8. Layout

```
index.html              the page
assets/config.js        recipient, subject, limits, repository link
assets/questions.js     the question bank (data only)
assets/survey.js        the engine: steps, branching, validation, report, email hand-off
assets/survey.css       styles, light and dark
assets/fonts/           Archivo subset (SIL OFL)
docs/CODEBOOK.md        every question code, wording, options and audience (generated)
docs/codebook.json      the same, as data
tools/parse_responses.py   emailed responses to CSV
tools/export_codebook.js   regenerates docs/CODEBOOK.md and docs/codebook.json
tools/make_font.py         rebuilds the font subset
tests/run_tests.py      end-to-end tests
LICENSE                 MIT (the font is OFL, see assets/fonts/OFL.txt)
```

## Licence

MIT, copyright 2026 Abdullahi Baba Garba. The Archivo font subset is under the SIL Open Font License 1.1.
