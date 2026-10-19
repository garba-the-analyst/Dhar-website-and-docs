# Shaping Dhar: the survey page

A role-branching survey for **lecturers, researchers, students and developers**, about Dhar, the systems language and toolchain built independently in Nigeria. It asks how people feel about a new Nigerian / African language and which features they want across software, web, mobile, data, AI, machine learning, systems, cybersecurity and blockchain.

It is a static page. There is no server, no database and no form service. When a respondent presses **Send**, the page makes a **PDF copy of the questions and their answers**, saves it on their device, and opens their own email app with a message addressed to the project lead and already containing the answers as text. They attach the PDF and press Send there.

- Page: `index.html` (plain HTML, CSS and JavaScript, nothing to build or install)
- Dependencies: none. The page loads nothing from other sites. It ships self-hosted fonts (Archivo, SIL OFL, for the page and the PDF; a DejaVu Sans subset, for the PDF only).
- Works from GitHub Pages, from any web host, and when `index.html` is opened straight from disk.

---

## 1. What the respondent sees

1. **Start**: tick the roles that fit (more than one is allowed).
2. **About you**: country, experience, current areas of work, languages used, whether they had heard of Dhar.
3. **One step per role ticked**: Teaching, Research, Learning, Building. Only the questions for the ticked roles appear.
4. **Your areas in detail**: optional blocks, one for each area ticked on the About step (backend and software, web and mobile, data, AI, machine learning, systems, cybersecurity, blockchain). Each asks what Dhar would need to offer, which tools it must work with, and the biggest problem a new language could fix. These can be skipped.
5. **Your view of Dhar**: sentiment, priorities, what would make them try it, what put them off new languages before.
6. **Stay in touch**: optional contact details.
7. **Review and send**: the page builds the PDF copy and the email. One button saves the PDF and opens the email draft; the panel afterwards gives fallbacks.

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
| Email subject, size limits, repository link, the PDF on or off | `assets/config.js` | reload |
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

### The PDF copy (and what a web page cannot do)

Pressing the main button on the review step does three things at once: copies the full text to the clipboard, **saves a PDF of every question the respondent saw together with their answers**, and opens the email draft. The PDF is made in the browser; nothing is uploaded.

What a static web page **cannot** do, and what this page therefore does not claim:

- **It cannot attach the PDF to the email.** The `mailto:` format has no attachment field, and webmail compose links cannot take a file. The respondent attaches the saved PDF (paperclip) themselves. The draft says so and names the file.
- **It cannot send mail as the respondent.** Only their own email app or provider can. A server could send the PDF with no attaching step, but it would send it from the server's address, and the answers and your address would pass through that service. That is not built into this page.
- **On phones, there is a shortcut.** Where the browser supports sharing files, the panel shows **Share the PDF**. The phone's share menu attaches the file to a new email for you, but it cannot fill in the To box, so the page copies your address for the respondent to paste. This was tested with a simulated share menu, **not on real phones**; it depends on the browser and the mail app.

Because attaching is manual, **the email body always carries the answers as text too** (see above), and the header line `PDF copy: <file name>` lets you match an attachment to its message. If a respondent skips the attachment you lose nothing.

What is in the PDF: A4 pages with the title, survey version, time, roles and file name; then the same sections as the email, in the same order (contact first). Every question the respondent saw is listed with its hint; unanswered ones are marked `(not answered)`. The text is real text (selectable, searchable). It is written by `assets/pdf.js` with no libraries, and its fonts come from `assets/pdf-fonts.js`, both loaded only after the respondent starts the survey.

Characters: the fonts cover the letters used for Yoruba, Igbo and Hausa (for example e and o with a dot below, hooked b, d and k), tone marks, the naira sign, Greek and common symbols. A character in no font (emoji, Chinese, Arabic script) is drawn as `?` in the PDF, and the PDF says so on its last page. The emailed text keeps every character exactly as typed. Tone marks that are not available as single letters are placed by the font's own mark glyphs without full text shaping, so a few stacked-mark combinations may sit slightly off.

If the PDF cannot be made (an old browser, a blocked script, a very slow connection), the button becomes a plain **Send by email** and the email goes as text only. Set `pdfEnabled: false` in `assets/config.js` to remove the PDF step completely, or `pdfAutoDownload: false` to make the PDF a button on the confirmation panel instead of saving it at once.

Rebuild the fonts file after changing fonts or the character ranges: `python3 -I tools/make_pdf_fonts.py --archivo <archivo-latin-wdth-normal.woff2> --dejavu <DejaVuSans.ttf> --out assets/pdf-fonts.js` (the header of that script lists the inputs).

### Reading the responses

Save the response emails (or export a mailbox) and run:

```
python3 tools/parse_responses.py responses.mbox -o responses.csv
python3 tools/parse_responses.py mail/*.txt mail/*.eml -o responses.csv
```

It needs only Python 3 and accepts `.txt`, `.eml` and `.mbox`, several responses per file, and quoted replies. The CSV has one row per response, the columns `source`, `response`, `survey_version`, `submitted`, `roles`, `answered`, `wording`, `pdf_copy`, `complete`, then one column per question code. `pdf_copy` is the file name the respondent was told to attach, so you can pair it with the PDF in your mailbox (empty when no PDF was made). `complete` is `no` for an email that was cut short; its first part is still read. `docs/CODEBOOK.md` explains each column.

---

## 5. Privacy, stated plainly

- The page itself collects nothing and sends nothing. There are no analytics, no cookies and no requests to other sites (the test suite checks this). The PDF is made on the respondent's device and stays there unless they attach it to their email.
- Unfinished answers are saved in the browser's local storage on that device so a refresh does not lose them. They are cleared by **Start over** and after **I have sent it**.
- An email sent from the respondent's own app **shows you their email address**, even if they leave the contact question blank. The page says so in its introduction. Do not describe the survey as anonymous.
- The recipient address is joined from two halves at run time, which only deters simple scrapers. It is visible to anyone who reads the page's JavaScript and in every email. The repository and the page are public.
- Each respondent must press Send in their own email app. If they close it, nothing arrives.

---

## 6. Tests

`tests/run_tests.py` drives the page in headless Chromium the way a respondent would and checks, among other things: all 15 combinations of roles show the right steps; validation, "up to N" limits, "Other" boxes and the exclusive "None"; hidden answers stay out of the report; the report text, the `mailto:` link, the webmail links, download and clipboard; the full, compact and cut email forms on Windows and other systems; drafts saving and clearing; no requests to other sites and no JavaScript errors; no sideways scrolling at phone, tablet and desktop widths; accessibility with axe-core in light and dark; and that `tools/parse_responses.py` reads what the page produces. The PDF checks save the real file the page makes and test it with qpdf and poppler (`pdftotext`, `pdffonts`): the file is valid, every font is embedded, every question and answer is in it, Yoruba, Igbo and Hausa letters survive, no word leaves the margins, page numbers are right, and the page falls back cleanly to a text-only email when the PDF cannot be made or is switched off. Those file checks need qpdf and poppler installed (`apt install qpdf poppler-utils`); without them the suite says which checks it skipped.

```
pip install playwright --break-system-packages    # plus a Chromium for it
npm pack axe-core && tar -xzf axe-core-*.tgz      # gives package/axe.min.js (optional)
CHROMIUM=/path/to/chromium AXE_JS=package/axe.min.js python3 tests/run_tests.py --shots shots
```

Add `--site src` if you keep the site in a `src/` folder. The exit status is 0 only if every check passed. The last run: 26 tests, 249 checks, all passed.

---

## 7. Notes

- **Opening `index.html` from disk** works, but browsers refuse to load the font file from a `file://` address, so the page falls back to the system font and the console shows a font error. On GitHub Pages or any web server the font loads normally.
- **No JavaScript** shows a message asking the visitor to turn it on.
- **PDF fonts are only fetched after the respondent starts.** About 290 KB of script, once, then cached. Opening the page and leaving costs nothing extra.
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
| Responses arrive as form entries | Responses arrive as an email with the answers as text, plus a PDF copy the respondent attaches | A form builder was ruled out. Text is what the parser reads; the PDF is the readable record. |

---

## 8. Layout

```
index.html              the page
assets/config.js        recipient, subject, limits, repository link
assets/questions.js     the question bank (data only)
assets/survey.js        the engine: steps, branching, validation, report, PDF and email hand-off
assets/survey.css       styles, light and dark
assets/pdf.js           writes the PDF copy (no libraries), loaded after the respondent starts
assets/pdf-fonts.js     fonts and glyph widths for the PDF (generated, about 290 KB)
assets/fonts/           Archivo subset for the page (SIL OFL), licence texts for Archivo and DejaVu
docs/CODEBOOK.md        every question code, wording, options and audience (generated)
docs/codebook.json      the same, as data
tools/parse_responses.py   emailed responses to CSV
tools/export_codebook.js   regenerates docs/CODEBOOK.md and docs/codebook.json
tools/make_font.py         rebuilds the page's font subset
tools/make_pdf_fonts.py    rebuilds assets/pdf-fonts.js
tests/run_tests.py      end-to-end tests
LICENSE                 MIT (fonts: see assets/fonts/OFL.txt and DEJAVU-LICENSE.txt)
```

## Licence

MIT, copyright 2026 Abdullahi Baba Garba. The Archivo font subset is under the SIL Open Font License 1.1. The DejaVu Sans subset used in the PDF is under the Bitstream Vera licence with public-domain additions (`assets/fonts/DEJAVU-LICENSE.txt`).
