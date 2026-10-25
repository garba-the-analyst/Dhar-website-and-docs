/*
 * verify_migrations.mjs: runs every file in supabase/migrations/ against a real PostgreSQL engine
 * (PGlite, PostgreSQL compiled to WebAssembly, in memory) and then tries to misuse the result AS A
 * VISITOR, the way a stranger with the public key could.
 *
 *   npm install @electric-sql/pglite      (once, anywhere; or set PGLITE to its folder)
 *   node supabase/tests/verify_migrations.mjs
 *
 * What it does NOT prove: that PostgREST, the Supabase service that turns web requests into SQL, behaves
 * as assumed (it cannot be run here), or that the live database has had the migration applied. The
 * statements below are the ones PostgREST issues for the request dhar-db.js sends. Exit code 0 only if
 * every check passes.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const migrations = process.env.MIGRATIONS || path.join(here, '..', 'migrations');
const require = createRequire(process.env.PGLITE ? path.join(process.env.PGLITE, 'x.js') : import.meta.url);
const { PGlite } = require('@electric-sql/pglite');

let passed = 0, failed = 0;
function check(ok, message) { if (ok) { passed++; } else { failed++; console.log('  FAIL: ' + message); } }

const db = new PGlite();

// What a Supabase project has before any migration of ours: the three API roles, and default
// privileges that hand every new table in "public" to all of them.
await db.exec(`
  create role anon nologin noinherit;
  create role authenticated nologin noinherit;
  create role service_role nologin noinherit bypassrls;
  grant usage on schema public to anon, authenticated, service_role;
  alter default privileges in schema public grant all on tables to anon, authenticated, service_role;
  alter default privileges in schema public grant all on sequences to anon, authenticated, service_role;
`);

for (const f of readdirSync(migrations).filter(n => n.endsWith('.sql')).sort()) {
  await db.exec(readFileSync(path.join(migrations, f), 'utf8'));
  console.log('applied ' + f);
}

async function asRole(role, sql, params) {
  await db.exec('set role ' + role);
  try { return { ok: true, res: await db.query(sql, params) }; }
  catch (e) { return { ok: false, code: e.code, message: e.message }; }
  finally { await db.exec('reset role'); }
}

const good = () => ['dhar-20261024-153012-k3x9aq', '1.0', ['student', 'dev'], { ROLE: ['student'], B1: 'x' }, 'Dhar survey response\nROLE: student'];
// The statement PostgREST runs for the request dhar-db.js sends: POST /rest/v1/survey_responses, Prefer: return=minimal.
// (No ON CONFLICT: see the note in dhar-db.js, and the check below that proves why.)
const INSERT = `insert into public.survey_responses (client_id, survey_version, roles, answers, report_text)
                values ($1, $2, $3, $4::jsonb, $5)`;
// Every malformed case gets its own fresh reference, so it can only be refused for its own defect and
// never because the reference was already used.
let fresh = 0;
const withVals = (...pairs) => { const v = good(); v[0] = 'dhar-20261024-160000-' + String(++fresh).padStart(6, '0'); for (const [i, x] of pairs) v[i] = x; return v; };
const ins = (v) => asRole('anon', INSERT, [v[0], v[1], v[2], JSON.stringify(v[3]), v[4]]);

console.log('as a visitor (role anon), the happy path');
let r = await ins(good());
check(r.ok, 'a well-formed response can be inserted: ' + (r.message || ''));
r = await ins(good());
check(!r.ok && r.code === '23505', 'sending the same reference again is refused as a duplicate (23505, which PostgREST answers with HTTP 409; dhar-db.js reports it as already stored): ' + (r.code || 'it was accepted'));
r = await asRole('anon', INSERT + ' on conflict (client_id) do nothing', good().map((v, i) => i === 3 ? JSON.stringify(v) : v));
check(!r.ok && r.code === '42501', 'the ON CONFLICT (client_id) form is NOT usable by a visitor (it needs read permission), which is why the client does not use it: ' + (r.code || 'it was accepted'));
r = await db.query('select count(*)::int as n from public.survey_responses');
check(r.rows[0].n === 1, 'the retry did not store a second copy (rows: ' + r.rows[0].n + ')');
r = await db.query('select received_at is not null as t, id from public.survey_responses');
check(r.rows[0].t && r.rows[0].id === 1, 'the database filled in id and received_at');

console.log('as a visitor, everything else is refused');
for (const [what, sql] of [
  ['read all rows', 'select * from public.survey_responses'],
  ['read one column', 'select client_id from public.survey_responses'],
  ['count rows', 'select count(*) from public.survey_responses'],
  ['update a row', "update public.survey_responses set report_text = 'x'"],
  ['delete a row', 'delete from public.survey_responses'],
  ['truncate the table', 'truncate public.survey_responses'],
  ['drop the table', 'drop table public.survey_responses'],
  ['insert with a chosen id', "insert into public.survey_responses (id, client_id, survey_version, answers, report_text) values (99, 'dhar-20261024-153012-zzzzzz', '1.0', '{}', 'x')"],
  ['insert with a chosen received_at', "insert into public.survey_responses (received_at, client_id, survey_version, answers, report_text) values ('2000-01-01', 'dhar-20261024-153012-yyyyyy', '1.0', '{}', 'x')"],
  ['read back what it inserted (RETURNING)', "insert into public.survey_responses (client_id, survey_version, answers, report_text) values ('dhar-20261024-153012-xxxxxx', '1.0', '{}', 'x') returning *"],
]) {
  const x = await asRole('anon', sql);
  const refused = !x.ok || (x.res && x.res.rows && x.res.rows.length === 0 && /^select/i.test(sql));
  check(refused, 'a visitor cannot ' + what + (x.ok ? ' (it was allowed, rows: ' + JSON.stringify(x.res.rows) + ')' : ''));
}
r = await db.query('select count(*)::int as n from public.survey_responses');
check(r.rows[0].n === 1, 'after all those attempts the table still holds exactly the one good row (rows: ' + r.rows[0].n + ')');

console.log('as a signed-in visitor (role authenticated), same story');
for (const [what, sql] of [
  ['read', 'select * from public.survey_responses'],
  ['insert', "insert into public.survey_responses (client_id, survey_version, answers, report_text) values ('dhar-20261024-153012-wwwwww', '1.0', '{}', 'x')"],
  ['update', "update public.survey_responses set report_text = 'x'"],
  ['delete', 'delete from public.survey_responses'],
]) {
  const x = await asRole('authenticated', sql);
  check(!x.ok, 'role authenticated cannot ' + what);
}

console.log('the shape of a row is enforced by the database, not trusted from the browser');
const shapes = [
  ['a reference that is not in the dhar-... form', withVals([0, 'anything-at-all'])],
  ['a reference that is already stored', withVals([0, 'dhar-20261024-153012-k3x9aq'])],
  ['an empty version', withVals([1, ''])],
  ['a version longer than 20 characters', withVals([1, 'v'.repeat(21)])],
  ['five roles', withVals([2, ['a', 'b', 'c', 'd', 'e']])],
  ['roles longer than 83 characters in total', withVals([2, ['r'.repeat(90)]])],
  ['answers that are an array, not an object', withVals([3, ['x']])],
  ['answers larger than 200,000 characters', withVals([3, { big: 'x'.repeat(200001) }])],
  ['an empty report', withVals([4, ''])],
  ['a report larger than 200,000 characters', withVals([4, 'x'.repeat(200001)])],
];
for (const [what, v] of shapes) {
  const x = await ins(v);
  const expected = what === 'a reference that is already stored' ? '23505' : '23514';
  check(!x.ok && x.code === expected, 'rejects ' + what + ' with ' + expected + (x.ok ? ' (it was stored)' : ' [got ' + x.code + ']'));
}
let x = await ins(withVals([0, 'dhar-20261024-153013-aaaaaa'], [2, []], [3, {}]));
check(x.ok, 'accepts no roles and no answers (a respondent may skip everything optional): ' + (x.message || ''));
x = await ins(withVals([0, 'dhar-20261024-153014-bbbbbb'], [2, ['prof', 'researcher', 'student', 'dev']]));
check(x.ok, 'accepts all four roles: ' + (x.message || ''));
x = await ins(withVals([0, 'dhar-20261024-153015-cccccc'], [3, { T: 'x'.repeat(150000) }], [4, 'y'.repeat(150000)]));
check(x.ok, 'accepts a large but allowed response (150,000 characters of answers and of text): ' + (x.message || ''));

console.log('the project owner can read');
r = await asRole('service_role', 'select count(*)::int as n from public.survey_responses');
check(r.ok && r.res.rows[0].n === 4, 'service_role (the owner path) reads every row (rows: ' + (r.ok ? r.res.rows[0].n : r.message) + ')');

console.log('the table is as documented');
r = await db.query("select relrowsecurity from pg_class where oid = 'public.survey_responses'::regclass");
check(r.rows[0].relrowsecurity === true, 'row-level security is on');
r = await db.query("select policyname, cmd, roles::text from pg_policies where tablename = 'survey_responses'");
check(r.rows.length === 1 && r.rows[0].cmd === 'INSERT' && /anon/.test(r.rows[0].roles), 'exactly one policy exists, for INSERT, for anon: ' + JSON.stringify(r.rows));

console.log(`\n${passed} of ${passed + failed} checks passed`);
process.exit(failed ? 1 : 0);
