# Shaping Dhar: the survey page

A role-branching survey for **lecturers, researchers, students and developers**, about Dhar, the systems language and toolchain built independently in Nigeria. It asks how people feel about a new Nigerian / African language and which features they want across software, web, mobile, data, AI, machine learning, systems, cybersecurity and blockchain.

It is **a page of the Dhar website**: the files are in `public/survey/` of this repository, and it is served from the same address as the site, at `/survey/` (https://dhar.onrender.com/survey/). There is no separate host and no separate branch. It is plain HTML, CSS and JavaScript, uses the website's own stylesheet, header, footer and six brand colours, and has nothing to build or install.

It has three ways of delivering a finished response (`assets/config.js` and `../assets/dhar-db.js`). The page uses the first one that is switched on:

- **Database (shipped).** The respondent presses **Send my answers**. The page saves the answers in the website's own **Supabase database** (table `survey_responses`, defined in `supabase/`), over an encrypted connection, and makes a **PDF copy of the questions and answers** on the respondent's device for them to keep. Nothing else is needed: no mail setup, no Google account.
- **Relay (optional, off).** Posts the answers and the PDF to a small **Google Apps Script that you run on your own Google account** (`relay/Code.gs`, set up with `relay/SETUP.md`), which emails you the response with the PDF attached and saves a row in a Google Sheet. It is used only if the database is switched off and `relayUrl` is set.
- **Email draft (always available, and the fallback).** The page saves the PDF on the respondent's device and opens their own email app with a message already addressed to the project lead and containing the answers as text. They attach the PDF and press Send there. The other two modes offer this as a button for people who prefer it, and automatically if delivery fails or cannot be confirmed.

- Page: `public/survey/index.html`, with `public/survey/assets/` (questions, script, styles, PDF code) and the shared `public/assets/dhar-db.js` (the database client).
- Dependencies: none. The page loads nothing from other sites. Its fonts are the website's own (Saira, JetBrains Mono); the PDF carries an embedded Archivo and a DejaVu Sans subset, so it needs nothing installed to read.
- Works when `index.html` is opened straight from disk, except that sending to the database or the relay needs the published address.

Where things are:

| Path | What |
| --- | --- |
| `public/survey/` | the page, as deployed |
| `public/assets/dhar-db.js` | the database client shared by the whole site |
| `supabase/` | the database definition and its checks (see `supabase/README.md`) |
| `survey/README.md`, `survey/docs/` | this file and the codebook |
| `survey/tools/` | the response parser, the codebook export, the PDF-font builder |
| `survey/relay/` | the optional Google Apps Script relay and its tests |
| `survey/tests/run_tests.py` | the survey's tests |

---

## 1. What the respondent sees

1. **Start**: tick the roles that fit (more than one is allowed).
2. **About you**: country, experience, current areas of work, languages used, whether they had heard of Dhar.
3. **One step per role ticked**: Teaching, Research, Learning, Building. Only the questions for the ticked roles appear.
4. **Your areas in detail**: optional blocks, one for each area ticked on the About step (backend and software, web and mobile, data, AI, machine learning, systems, cybersecurity, blockchain). Each asks what Dhar would need to offer, which tools it must work with, and the biggest problem a new language could fix. These can be skipped.
5. **Your view of Dhar**: sentiment, priorities, what would make them try it, what put them off new languages before.
6. **Stay in touch**: optional contact details.
7. **Review and send**: the page builds the PDF copy. **Send my answers** saves everything in the database and shows a reference number; **Send it from my own email app instead** opens the email draft. If the database is switched off (and the relay too), one button saves the PDF and opens the email draft. If sending fails, the panel says so, keeps the answers on the page, and offers the email route and, when a retry makes sense, a retry.

The survey has 80 questions plus the role question. A person with one role and no optional blocks answers about 23 to 25 questions (8 to 12 minutes). `docs/CODEBOOK.md` lists every question, its answer options and who sees it.

---

## 2. Put it online

Nothing separate. The survey is part of the website, so the website's hosting is the survey's hosting: the Render static site `dhar` publishes `public/`, and `public/survey/index.html` is therefore served at `/survey/`. The site's links to it are relative (`survey/`). Push to `main` and Render redeploys both together. See the repository's README.

The **database** is the one thing that is not in the deploy: it lives at Supabase and must have its table created once, from `supabase/migrations/` (the steps are in `supabase/README.md`). Until that is done, the page still loads, and pressing Send tells the respondent that it could not store the answers and offers the email route. Nothing is lost.

---

## 3. Change things

| To change | Edit | Then |
| --- | --- | --- |
| Questions, options, branching | `public/survey/assets/questions.js` (the header of that file explains every field) | raise `version`, add a migration if a limit in the table changes, run the tests, run `node survey/tools/export_codebook.js` |
| Who receives email-draft answers | `recipientUser` and `recipientDomain` in `public/survey/assets/config.js` (change both halves) | reload |
| Email subject, size limits, repository link, the PDF on or off | `public/survey/assets/config.js` | reload |
| Which database (or none) | `DEFAULTS` in `public/assets/dhar-db.js` (an empty `url` switches the database off) | reload |
| The relay on or off | `relayUrl` in `public/survey/assets/config.js` (empty = off), after setting up `survey/relay/Code.gs`; only used when the database is off | reload; check with `survey/relay-check.html` |
| Spacing and layout of the survey | `public/survey/assets/survey.css`. Colours and fonts come from the website's tokens in `public/assets/site.css`; do not add colours here (the six brand colours are fixed) | reload |
| Page text (title, intro) | `public/survey/index.html`; the privacy note and the sending wording are in `survey.js` (`applyDeliveryText`) | reload |

Rules for the question bank:

- A question **code** (`A3`, `D5`, `SW1`) never changes meaning. If you reword a question substantially or change the order of options, **raise `version`**. The version is printed in every response and names the browser-storage slot, so old drafts never mix with new questions.
- Options written as plain strings get positional ids (`o1`, `o2`, ...), so their order matters. Options written as objects have stable ids you choose.
- The `ROLE` option ids (`prof`, `researcher`, `student`, `dev`) must match the `role` conditions in `showIf` rules.

---

## 4. How answers reach you

### Direct delivery to the database (shipped)

Pressing **Send my answers** makes one request from the respondent's browser to the website's Supabase project (`public/assets/dhar-db.js`): a plain insert of one row into `survey_responses`:

| Column | What it holds |
| --- | --- |
| `client_id` | the reference number the respondent sees (`dhar-20261024-153012-k3x9aq`). Unique in the table. |
| `survey_version` | the question-set version answered (`questions.js` `version`) |
| `roles` | the roles ticked (at most four) |
| `answers` | every answer that was shown and answered, as JSON keyed by question code. Answers to questions hidden by a later change of mind are **not** sent. |
| `report_text` | exactly the readable text the respondent was shown under "Read exactly what will be sent" |
| `received_at` | set by the database |

What the page does with each outcome (all tested in `t_db_*` against an imitation of the database's web interface):

- **Stored.** It says so, shows the reference, clears the saved draft from the device, and offers the respondent their PDF.
- **Already stored** (the database answers "duplicate"). That happens when an earlier attempt reached the database but its answer was lost. It is treated as success, and the panel notes that the response had already arrived. **A response is never stored twice**, because the table keeps `client_id` unique; the page retries once after a network failure on that basis.
- **Refused** (a limit or a shape rule, a wrong key): it says "not sent yet", keeps the answers, and offers the email route. No retry button, because the same answer would be refused again.
- **Busy or down** (rate limit, server error): the same, with a retry button.
- **No connection, or no answer in 20 seconds**: it says it could not confirm that the answers arrived, because they may have; it offers the email route and a retry, and keeps the draft. If both arrive, the duplicate is recognised by the reference.

The database accepts **inserts only** from the public key: a visitor cannot read, change or delete anything, including their own response. That is enforced inside the database (`supabase/migrations/`) and checked on a real PostgreSQL by `supabase/tests/verify_migrations.mjs`. **What has not been verified from here:** the live Supabase project (the sandbox this was built in cannot reach it), so that the migration has been applied, and that a real request from a real browser is accepted. The first real response, and a look at the table, is the check. See `supabase/README.md`.

### Email text

The email (email-draft mode, relay mode, and the `report_text` column) is written in plain text and always starts with `SHAPING DHAR SURVEY RESPONSE` and ends with `== END OF RESPONSE ==`:

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

### Optional: direct delivery through the relay

The relay is off in the shipped site. With the database switched off and `relayUrl` set in `public/survey/assets/config.js`, **Send my answers** posts the response to your Google Apps Script web app instead. Setup, step by step, is in **`relay/SETUP.md`**; in short: paste `relay/Code.gs` into a new script at script.google.com, run `selfTest`, deploy it as a web app ("Execute as: Me", "Who has access: Anyone"), and put the web app URL in `relayUrl`. Then open `/survey/relay-check.html` on the published site and press its two buttons.

What it does with each response:

- **Emails it to you**, from your own Gmail account (display name "Shaping Dhar survey"), with the PDF attached, the full answers as text, and the respondent's address as **Reply-To** if the contact answer contains one. **No website can send mail "from" the respondent**; Reply-To is the honest equivalent.
- **Saves it in the Google Sheet "Shaping Dhar responses"**: a `Responses` sheet with one row per response and one column per question code (single answers as text, multiple choices joined with ` | `, scales as numbers, grids as `statement: number` pairs, the whole response in `response_text`), and a `Questions` sheet with the code, survey version and wording of every question. This is the record to analyse and the safety net.
- **Never loses a response to one failure.** If the email cannot be sent (for example Google's daily mail limit of about 100 for a free Gmail account), the response is still saved and the respondent still sees "sent". If the sheet cannot be written, the email still goes. Only if both fail does the page say so and offer the email-draft route.
- **Never records a response twice.** Every response carries a reference (`dhar-20261019-154500-k3x9ab`). The page retries once after a network failure, the relay ignores a repeated reference, and the parser keeps one row if the same response arrives both ways.
- **Is honest about what it cannot confirm.** If the page cannot read the relay's answer (offline, timed out, or a deployment that blocks it), it says it could not confirm delivery, keeps the respondent's answers, and offers a ready-addressed email and a retry. It does not clear the saved draft until delivery is confirmed.
- **Protects itself.** A shared token (visible in the page source, so only a speed bump), strict validation (JSON shape, response ID, survey-shaped text, size limits, a real PDF or none, a real email address or none, no line breaks in headers), an hourly limit, a check of the daily mail quota, plain-text mail only, and spreadsheet formulas in answers neutralised (a leading apostrophe).

Privacy changes with this mode, and the start page says so plainly: answers pass over an encrypted connection to a Google Apps Script that you own, which saves them in your Sheet and mails them to you. Respondents are anonymous unless they give a contact address.

**What has not been verified:** the relay is tested against an imitation of Google's services and of an Apps Script web app (`relay/test/`), not against real Google servers from here. `relay-check.html` and the first real response are the verification: that a page on the site's address may read the relay's answer, that attachments and Reply-To arrive as documented, and that Sheets keeps the apostrophe text marker. If the browser cannot read the answer, the survey falls back as described above rather than failing silently.

### Size limits (read this)

A `mailto:` link carries the whole message inside the web address, and email apps differ in how much they accept. The page tries three forms and uses the first that fits:

1. **full**: every question's full wording and the answer
2. **compact**: the same answers with long question wording shortened (`Question wording: shortened` appears in the header)
3. **cut**: the compact text cut at a line break and clearly marked as cut

Whatever is sent, the **complete** answers are also copied to the respondent's clipboard, and the confirmation panel offers **Copy answers**, **Download .txt**, and links that open Gmail, Outlook and Yahoo Mail in the browser with the message prefilled.

The limits are set in `public/survey/assets/config.js` (`mailtoLimitWindows` 1900, `mailtoLimitOther` 7500, `webComposeLimit` 7000). **These are cautious estimates, not measured values.** No authoritative published limits were found, and they differ by mail app and version. The Outlook and Yahoo compose-link formats were also not checked against a live account. Treat the first few real submissions from Windows, Android and iPhone as the test, and adjust the numbers if people are being cut when they need not be.

### The PDF copy (and what a web page cannot do)

Pressing the main button on the review step does three things at once: copies the full text to the clipboard, **saves a PDF of every question the respondent saw together with their answers**, and opens the email draft. The PDF is made in the browser; nothing is uploaded.

What a static web page **cannot** do, and what this page therefore does not claim:

- **It cannot attach the PDF to the email.** The `mailto:` format has no attachment field, and webmail compose links cannot take a file. The respondent attaches the saved PDF (paperclip) themselves. The draft says so and names the file.
- **It cannot send mail as the respondent.** Only their own email app or provider can. The relay (above) removes the attaching step by sending from your own Gmail account instead, with the respondent's address as Reply-To.
- **On phones, there is a shortcut.** Where the browser supports sharing files, the panel shows **Share the PDF**. The phone's share menu attaches the file to a new email for you, but it cannot fill in the To box, so the page copies your address for the respondent to paste. This was tested with a simulated share menu, **not on real phones**; it depends on the browser and the mail app.

Because attaching is manual, **the email body always carries the answers as text too** (see above), and the header line `PDF copy: <file name>` lets you match an attachment to its message. If a respondent skips the attachment you lose nothing.

What is in the PDF: A4 pages with the title, survey version, time, roles and file name; then the same sections as the email, in the same order (contact first). Every question the respondent saw is listed with its hint; unanswered ones are marked `(not answered)`. The text is real text (selectable, searchable). It is written by `assets/pdf.js` with no libraries, and its fonts come from `assets/pdf-fonts.js`, both loaded only after the respondent starts the survey.

Characters: the fonts cover the letters used for Yoruba, Igbo and Hausa (for example e and o with a dot below, hooked b, d and k), tone marks, the naira sign, Greek and common symbols. A character in no font (emoji, Chinese, Arabic script) is drawn as `?` in the PDF, and the PDF says so on its last page. The emailed text keeps every character exactly as typed. Tone marks that are not available as single letters are placed by the font's own mark glyphs without full text shaping, so a few stacked-mark combinations may sit slightly off.

If the PDF cannot be made (an old browser, a blocked script, a very slow connection), the button becomes a plain **Send by email** and the email goes as text only. Set `pdfEnabled: false` in `public/survey/assets/config.js` to remove the PDF step completely, or `pdfAutoDownload: false` to make the PDF a button on the confirmation panel instead of saving it at once.

Rebuild the fonts file after changing fonts or the character ranges: `python3 -I survey/tools/make_pdf_fonts.py --archivo <archivo-latin-wdth-normal.woff2> --dejavu <DejaVuSans.ttf> --out public/survey/assets/pdf-fonts.js` (the header of that script lists the inputs).

### Reading the responses

From the database: in the Supabase dashboard, open the table `survey_responses` (Table Editor). `report_text` is the readable response and `answers` is the same data as JSON keyed by question code. Export the table as CSV and turn it into one row per response and one column per question:

```
python3 survey/tools/parse_responses.py survey_responses.csv -o responses.csv
```

From email (email-draft or relay mode): save the response emails (or export a mailbox) and run:

```
python3 survey/tools/parse_responses.py responses.mbox -o responses.csv
python3 survey/tools/parse_responses.py mail/*.txt mail/*.eml -o responses.csv
```

It needs only Python 3 and accepts `.txt`, `.eml`, `.mbox`, a `.csv` or `.json` export of the database table, several responses per file, and quoted replies; the sources can be mixed in one run. The CSV has one row per response, the columns `source`, `response`, `response_id`, `survey_version`, `submitted`, `roles`, `answered`, `wording`, `pdf_copy`, `complete`, then one column per question code. With the relay on, the Google Sheet already holds the same data (the tests check that the sheet and this parser agree). `pdf_copy` is the file name of the PDF, so you can pair it with the PDF in your mailbox (empty when no PDF was made). `response_id` is the reference printed in every response: a response that arrives twice (database and email, relay and email, or a retry) is merged into one row, keeping the complete copy; responses without an ID are never merged. `complete` is `no` for an email that was cut short; its first part is still read. `docs/CODEBOOK.md` explains each column.

---

## 5. Privacy, stated plainly

- The page itself collects nothing. There are no analytics and no cookies, and no requests to other sites except, only when the respondent presses Send, one request to the website's database (or, in relay mode, to your Apps Script web app). The test suite checks that. The PDF is made on the respondent's device; in database mode it never leaves it unless they share it themselves.
- Unfinished answers are saved in the browser's local storage on that device so a refresh does not lose them. They are cleared by **Start over**, after a confirmed send, and after **I have sent it**.
- **Database mode (shipped):** you see only what the respondent typed, and an email address only if they put one in the contact question. The responses sit in a private table that the public cannot read; only you can, signed in to Supabase. Supabase, as the host, stores the data and keeps ordinary technical records of requests (time, network address); the start page says so. A contact detail given in answers is personal data: do not share an export widely, and do not publish responses with names.
- **Email-draft mode:** an email sent from the respondent's own app **shows you their email address**, even if they leave the contact question blank. The page says so in its introduction. Do not describe that mode as anonymous.
- **Relay mode:** as database mode, except that Google runs the script and holds the sheet and the mailbox on your account.
- The recipient address for email-draft mode is joined from two halves at run time, which only deters simple scrapers. It is visible to anyone who reads the page's JavaScript and in every email. The repository and the page are public.
- Email-draft mode: each respondent must press Send in their own email app. If they close it, nothing arrives. The database mode removes that step.

---

## 6. Tests

`survey/tests/run_tests.py` drives the survey page (as served by the site, `/survey/`) in headless Chromium the way a respondent would and checks, among other things: all 15 combinations of roles show the right steps; validation, "up to N" limits, "Other" boxes and the exclusive "None"; hidden answers stay out of the report; the report text, the `mailto:` link, the webmail links, download and clipboard; the full, compact and cut email forms on Windows and other systems; drafts saving and clearing; no requests to other sites and no JavaScript errors; no sideways scrolling at phone, tablet and desktop widths; accessibility with axe-core (the site is dark only, so one theme); and that `survey/tools/parse_responses.py` reads what the page produces, including a CSV or JSON export of the database table. The PDF checks save the real file the page makes and test it with qpdf and poppler (`pdftotext`, `pdffonts`): the file is valid, every font is embedded, every question and answer is in it, Yoruba, Igbo and Hausa letters survive, no word leaves the margins, page numbers are right, and the page falls back cleanly to a text-only email when the PDF cannot be made or is switched off. Those file checks need qpdf and poppler installed (`apt install qpdf poppler-utils`); without them the suite says which checks it skipped.

Every test runs with the database switched off unless it asks for it, so the email and relay routes are tested on their own and nothing can reach the real database.

The database tests (names starting `t_db_`) point the page at a local imitation of the part of Supabase's web interface that the page uses: `POST /rest/v1/survey_responses` with an `apikey` header, 201 when stored, 409 with code `23505` when the reference was stored before, JSON errors otherwise, CORS headers and a pre-flight answer. They check that exactly one row with exactly the table's writable columns is stored, equal to what the review step showed; that the public key is the only credential, with no cookies or referrer; that nothing else leaves the page; that answers to questions hidden by a role change are not sent; that a connection dropped after the row was stored is retried and ends as one row; that a refusal, a rate limit, a server error, a wrong key and no connection each lead to the right panel (email offered, retry only when it can help, draft kept); that an unsafe database address (not https) is refused and only `survey_responses` can be written; that the shipped configuration really points at the project's Supabase address with a publishable key (the request is intercepted before it leaves the machine); and the wording. They were checked by breaking the code two ways (treating "already stored" as a failure, sending hidden answers) and confirming they fail. What the **real** database accepts is checked separately, on PostgreSQL itself, by `supabase/tests/verify_migrations.mjs`.

The relay tests (names starting `t_relay_`) run the **real `survey/relay/Code.gs`** behind `survey/relay/test/mock_apps_script.js`, a local server that behaves like an Apps Script web app: the POST is answered with a redirect to a second address, both carry the CORS header, and a CORS pre-flight gets no answer. They check delivery with the PDF attached and byte-identical to the respondent's own copy; Reply-To taken from the contact answer (and not from a phone number); an anonymous response; a dropped connection retried without a double email; a reply the page cannot read (no email twice, the draft kept, the email route offered); an unreachable server; a timeout; relay errors, an exhausted mail quota and a refused token; a reply that is not JSON; a response with no PDF; the email route chosen by the respondent; the start page's wording; layout and accessibility of the new panels; `relay-check.html`; and that the Google Sheet the relay writes agrees, answer by answer, with what `parse_responses.py` reads from the emails (including a hostile contact answer that must not become a formula). `node survey/relay/test/relay_test.js` tests `Code.gs` on its own against an imitation of the Google services (mail, cache, lock, properties, spreadsheets with a sheet's 26-column start and its refusal of out-of-range writes): validation, header injection, size limits, quota and hourly limits, retries, every combination of email and log succeeding or failing, formula neutralisation, long cells, and parity with the Python parser. They need Node; without it the suite skips them and says so.

The site's own tests (`tests/run_tests.py` in the repository root) also open `/survey/` at phone, tablet and desktop widths and check that it has the website's background, header and footer, no console errors, no sideways scroll, and requests nothing from other sites; that its stylesheet holds only palette tokens and no rounded corners; that the site's survey button opens it; and that no secret key or database password is anywhere in the repository.

```
pip install playwright --break-system-packages    # plus a Chromium for it
npm pack axe-core && tar -xzf axe-core-*.tgz      # gives package/axe.min.js (optional)
CHROMIUM=/path/to/chromium AXE_JS=package/axe.min.js python3 survey/tests/run_tests.py --shots shots
node survey/relay/test/relay_test.js
npm install @electric-sql/pglite && PGLITE=. node supabase/tests/verify_migrations.mjs
```

Add `--only t_db_` (or any text) to run just the tests whose names contain it, or `--shard N/M` to run every M-th test so the suite can be split over M processes (the whole suite takes several minutes in one). The exit status is 0 only if every check passed. The last run (25 October 2026, four shards): the survey suite, 61 tests and 451 checks, all passed; `relay_test.js`, 39 tests and 309 checks, all passed; `supabase/tests/verify_migrations.mjs`, 36 checks, all passed. These ran against imitations of Supabase's web interface and of Google's services, and against PostgreSQL in memory, not against the live services.

---

## 7. Notes

- **Opening `index.html` from disk** works for reading and answering, but browsers refuse to load font files from a `file://` address, so the page falls back to the system font and the console shows a font error, and sending needs the published address. From the site, the fonts load normally.
- **No JavaScript** shows a message asking the visitor to turn it on.
- **PDF fonts are only fetched after the respondent starts.** About 290 KB of script, once, then cached. Opening the page and leaving costs nothing extra.
- **Spec1 code sample** in the page header shows syntax as Spec1 defines it today. Update `index.html` if the specification changes.

### Where this differs from the original blueprint

The survey follows the original blueprint's questions and intent. These things changed, and why:

| Blueprint | This page | Why |
| --- | --- | --- |
| Four yes/no gate questions, one per role | One "tick every role that fits" question | The gates existed only because Google Forms cannot branch from a checkbox. Here branching is in code. |
| Hosted in a form builder, "anonymous unless contact left" | Static page. Direct delivery goes to an Apps Script you run (emails you the PDF, saves a row in your Sheet); the email-draft route is the fallback | You asked for a GitHub page that emails the answers, then for the PDF to be sent for you. A form builder and a connector were ruled out. In email-draft mode the sender's address is visible, so that mode cannot be called anonymous; in relay mode the respondent is anonymous unless they leave a contact. |
| AI/ML as one option in "what are you involved in" | AI and machine learning are separate options, and "None of these yet" was added. Languages list also gets "None yet". | Lets each area drive its own detail block, and lets beginners answer honestly. |
| One shared list of areas | The About step's area question drives optional detail blocks (backend, web and mobile, data, AI, ML, systems, security, blockchain) | To capture wanted features per area without making everyone answer everything. |
| Contact last | Contact is written first in the email | If an email is cut short, the contact details survive. |
| Responses arrive as form entries | Responses arrive as an email with the answers as text and the PDF attached, and as a row in a Google Sheet (relay mode); or as an email with the answers as text, plus a PDF copy the respondent attaches (email-draft mode) | A form builder was ruled out. The Sheet gives the form-style table; the text is what the parser reads; the PDF is the readable record. |

---

## 8. Layout

Under `public/survey/` (deployed at `/survey/`):

```
index.html              the page, in the website's template (shared stylesheet, header and footer)
relay-check.html        for you: tests the route from the published site to the relay (not linked from the survey)
assets/config.js        recipient, subject, limits, repository link, relay address
assets/questions.js     the question bank (data only)
assets/survey.js        the engine: steps, branching, validation, report, PDF, delivery and email hand-off
assets/survey.css       the survey's layout, using only the website's colour and type tokens
assets/pdf.js           writes the PDF copy (no libraries), loaded after the respondent starts
assets/pdf-fonts.js     fonts and glyph widths for the PDF (generated, about 290 KB)
assets/fonts/           licence texts for the fonts embedded in the PDF (Archivo: SIL OFL; DejaVu)
```

Elsewhere in the repository:

```
public/assets/dhar-db.js         the database client (address, publishable key, the tables the site may write to)
supabase/                        migrations, config and the migration checks (see supabase/README.md)
survey/docs/CODEBOOK.md          every question code, wording, options and audience (generated)
survey/docs/codebook.json        the same, as data
survey/tools/parse_responses.py  responses (email, mailbox, database export) to CSV
survey/tools/export_codebook.js  regenerates the codebook
survey/tools/make_pdf_fonts.py   rebuilds assets/pdf-fonts.js
survey/relay/                    the optional Google Apps Script relay: Code.gs, appsscript.json, SETUP.md, test/
survey/tests/run_tests.py        end-to-end tests of the survey page
```

## Licence

MIT, copyright 2026 Abdullahi Baba Garba. The Archivo font subset embedded in the PDF is under the SIL Open Font License 1.1 and the DejaVu Sans subset under the Bitstream Vera licence with public-domain additions (`public/survey/assets/fonts/`). The page's own fonts (Saira, JetBrains Mono, Noto Naskh Arabic) are under the SIL Open Font License.
