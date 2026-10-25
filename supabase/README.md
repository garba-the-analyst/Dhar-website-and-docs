# The website's database (Supabase)

The Dhar website keeps a small database on [Supabase](https://supabase.com) (a hosted PostgreSQL). Today it holds one
thing: the finished responses to the survey (`/survey/`). It is also where any later need of the website goes (a
sign-up list, a feedback box, a counter), one table at a time, by the same method.

This folder is the database's definition. The database is not edited by hand in the dashboard; it is changed by adding a
file here, so that what exists in production is always what this repository says.

```
supabase/
  config.toml                                      project settings (no secrets)
  migrations/20261024000000_survey_responses.sql   the survey table and who may do what to it
  tests/verify_migrations.mjs                      runs the migrations on a real PostgreSQL and tries to misuse them
```

## What is public and what is not

| Item | Where it is | Public? |
| --- | --- | --- |
| Project address `https://ctpjbmolgvkagdbafsvh.supabase.co` | `public/assets/dhar-db.js` | Yes. Every visitor's browser needs it. |
| Publishable key `sb_publishable_...` | `public/assets/dhar-db.js` | Yes, by design. It is not a password. |
| Database password | Supabase dashboard only | **No. Never in this repository, never in a chat.** |
| `secret` / `service_role` key | Supabase dashboard only | **No. Never in this repository.** |

What protects the data is the database, not the key. The key lets a visitor **add one row** to `survey_responses` and
nothing else: not read any row (not even their own), not change or delete one. That is enforced by row-level security,
a single `insert` policy for the `anon` role, and a column-level `grant insert` (see the migration, which explains
each line). Only the project owner, signed in to Supabase, can read the responses.

`tests/run_tests.py` fails if a secret-looking key or a database URL with a real password appears anywhere in this
repository.

## Turning it on (once)

The Supabase project already exists. The table does not exist until the migration has run. Either way works:

**A. With the GitHub integration (what the project is set up for).** In the Supabase dashboard, Project settings,
Integrations, GitHub: repository `Dhar-website-and-docs`, working directory `.`, branch `main`, "Deploy to production"
on. Press **Enable integration**. From then on, every commit to `main` that adds a file in `supabase/migrations/` is
applied to the database automatically. The first deploy creates `survey_responses`.

**B. By hand, once.** Supabase dashboard, SQL Editor, New query: paste the contents of
`migrations/20261024000000_survey_responses.sql`, press Run. (If you later enable the integration, it will find the
table already there and the migration will fail on "already exists"; in that case mark it as applied in the
dashboard's migration list rather than running it twice.)

To check it worked: the table `survey_responses` appears in the dashboard's Table Editor with row-level security shown
as enabled, and its list of policies has exactly one, `survey_responses_visitors_may_add`, for `INSERT`. (The dashboard's
menus move between versions; look for "Policies" on the table.)

## Reading the responses

Only you can, in the dashboard:

* **Table Editor, survey_responses**: one row per response. `report_text` is the readable response; `answers` holds the
  same answers as JSON keyed by question code (the codes are in `survey/docs/CODEBOOK.md`).
* **Export**: the Table Editor can export a table as CSV (look for an export option on the table). Turn the file into
  one row per response and one column per question with:

  ```
  python3 survey/tools/parse_responses.py survey_responses.csv -o responses.csv
  ```

  The same reader handles responses that came by email, so the two sources merge: a response that arrived both ways is
  one row (the reference number, `client_id`, is the same).
* A respondent who chose to leave contact details has them in `answers` and `report_text` (question C2). That is personal
  data: do not share an export widely.

## Adding a table for a future need

Two edits, then push:

1. **A migration**: a new file in `migrations/`, named `<YYYYMMDDHHMMSS>_<what>.sql`, with a timestamp later than every
   existing file. Copy the shape of the survey migration: create the table, put **size and shape limits** in `check`
   constraints (the database cannot trust the browser), `enable row level security`, `revoke all ... from public, anon,
   authenticated`, then grant back **only** what the page needs (normally `insert` on named columns) and write the one
   matching policy. Never grant `select` to `anon` for a table that holds people's answers.
2. **One line in `public/assets/dhar-db.js`**, in `TABLES`: `my_table: { unique: 'client_id' }` (the column the database
   keeps unique so a retried send is recognised, or leave it out if the table has no such column). The page then calls
   `DharDB.insert('my_table', { ... })`. A table that is not listed there is refused by the client.

Then extend `tests/verify_migrations.mjs` with the same kind of checks (what a visitor can do, what they cannot, what
shapes are refused), and run it.

## Checking the migration without Supabase

```
npm install @electric-sql/pglite               # once, anywhere
PGLITE=<that folder> node supabase/tests/verify_migrations.mjs
```

It starts PostgreSQL (PGlite, PostgreSQL compiled to WebAssembly) in memory, creates the roles Supabase creates (`anon`,
`authenticated`, `service_role`) with Supabase's default privileges, runs every migration in order, and then acts as a
visitor: it inserts a good row, and tries to read, count, update, delete, truncate, drop, choose its own `id`, read a row
back with `RETURNING`, and insert a dozen kinds of malformed row. It exits non-zero unless every check passes. The test
was itself checked by breaking the migration five ways (no row-level security, a read policy, a wider grant, no
uniqueness, no limits) and confirming each break is caught.

**What this does not prove.** It is PostgreSQL, not Supabase: it cannot show that the live project has had the migration
applied, that PostgREST (Supabase's web interface to the database) answers as its documentation says, or that
Supabase's own dashboard settings (such as an API rate limit) are as wanted. The survey page's behaviour against each
kind of answer (stored, already stored, refused, busy, unreachable) is tested in `survey/tests/run_tests.py` against a
local imitation of PostgREST, `t_db_*`. The first real response, and a look at the table afterwards, is the final check.
Status of this feature on the website's board stays at **Partly** until that has been done.

## Honest limits

* **A determined stranger can add junk rows.** The publishable key is public, so anyone can send rows that pass the
  shape checks. Each row is size-limited (200,000 characters), which bounds the damage, and junk can be deleted in the
  dashboard. If it ever happens, the next step is a small server-side function (a Supabase Edge Function) between the page
  and the table, which can check a CAPTCHA and limit requests per network address; the table would then stop accepting
  inserts from the public key directly. It has not been needed yet and nothing here prevents it.
* **A response can lose the race with a closed tab.** If the respondent closes the page the instant they press Send,
  the request may not finish. The page keeps their answers until delivery is confirmed, and offers email.
* Supabase, as the host, keeps ordinary technical records of requests (time, network address). The survey's privacy
  note says so.
