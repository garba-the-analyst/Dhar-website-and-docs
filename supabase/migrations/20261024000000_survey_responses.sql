-- survey_responses: where the survey page (public/survey/) saves a finished response.
--
-- THE SECURITY MODEL, IN ONE PARAGRAPH
--   The website's browser code carries a public "publishable" key (it has to; every visitor's browser
--   needs it). So the database, not the key, decides what a visitor may do. Here a visitor may ADD one
--   row to this table, and nothing else: not read any row (including their own), not change one, not
--   delete one. Row-level security is on, the only policy is "insert", and the privileges below are
--   narrowed to the same thing. Only the project owner, signed in to Supabase (or using the
--   service_role key, which is never put in this repository), can read the responses.
--
-- WHAT A ROW HOLDS
--   client_id      the reference number the respondent sees ("dhar-20261024-153012-k3x9aq"). Unique, so
--                  a retried send is refused as a duplicate (error 23505) and stored once, not twice.
--   survey_version the version of the question set that was answered (questions.js "version").
--   roles          the roles the respondent chose (at most four, at most 83 characters in all).
--   answers        every answer that was shown and answered, as JSON, keyed by question code
--                  (see survey/docs/CODEBOOK.md). Answers to questions hidden by an earlier choice are not sent.
--   report_text    the same answers as the readable text the respondent was shown before sending.
--   received_at    set by the database.
--
-- A respondent who chooses to leave contact details (question C2) has them inside answers/report_text.
-- That is personal data: keep access to this table to the project owner.

create table public.survey_responses (
  id             bigint generated always as identity primary key,
  client_id      text        not null unique,
  survey_version text        not null,
  roles          text[]      not null default '{}',
  answers        jsonb       not null,
  report_text    text        not null,
  received_at    timestamptz not null default now(),

  constraint survey_responses_client_id_shape   check (client_id ~ '^dhar-[0-9]{8}-[0-9]{6}-[a-z0-9]{6}$'),
  constraint survey_responses_version_length    check (char_length(survey_version) between 1 and 20),
  constraint survey_responses_roles_count       check (cardinality(roles) <= 4),
  constraint survey_responses_roles_length      check (char_length(array_to_string(roles, ',')) <= 83),   -- 4 roles of up to 20 characters, and 3 commas
  constraint survey_responses_answers_object    check (jsonb_typeof(answers) = 'object'),
  constraint survey_responses_answers_size      check (octet_length(answers::text) <= 200000),
  constraint survey_responses_report_text_size  check (char_length(report_text) between 1 and 200000)
);

comment on table public.survey_responses is
  'Finished responses to the Dhar survey. Visitors may insert; only the project owner may read.';

alter table public.survey_responses enable row level security;

-- Start from nothing, then give back exactly one thing. (Supabase grants new tables to anon and
-- authenticated by default; this removes that.)
revoke all on table public.survey_responses from public, anon, authenticated;

-- A visitor (role "anon") may insert these columns and no others: id and received_at are the database's.
grant insert (client_id, survey_version, roles, answers, report_text) on public.survey_responses to anon;

create policy survey_responses_visitors_may_add
  on public.survey_responses
  for insert
  to anon
  with check (true);
-- There is deliberately no select, update or delete policy for anon or authenticated.
