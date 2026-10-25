/*
 * dhar-db.js: the website's way of saving things in its database (Supabase, a hosted PostgreSQL).
 *
 * WHAT IT IS
 *   A very small client, with no library and no build step. It knows one operation, `insert`, and
 *   only for the tables listed in TABLES below. Today that is one table, survey_responses. A table
 *   for a future need is added in two places: a migration in supabase/migrations/ (which creates the
 *   table and its security rules) and one line in TABLES here.
 *
 * WHAT IS PUBLIC AND WHAT IS NOT
 *   The address and the "publishable" key below are meant to be public: every visitor's browser
 *   needs them, and Supabase designs them that way. They are not a password. What protects the data
 *   is the database itself, through row-level security (see supabase/migrations/): the public key can
 *   ADD a response and can do nothing else. It cannot read, change or delete anything. Only the
 *   project owner, signed in to Supabase, can read the responses.
 *   NEVER put the database password, or a "secret" / "service_role" key, in this file or anywhere
 *   else in this repository.
 *
 * HOW A PAGE USES IT
 *   <script src="../assets/dhar-db.js"></script>
 *   DharDB.ready()                    true when an address and key are set and this browser can send
 *   DharDB.insert('survey_responses', { client_id: ..., answers: {...}, ... })
 *       -> Promise that always resolves (never rejects) to
 *          { kind: 'ok' }                                  stored; or { kind: 'ok', duplicate: true } when
 *                                                          that client_id was already stored (see below)
 *          { kind: 'rejected', status, code, message }     the database said no (bad shape, too many)
 *          { kind: 'unreachable', why }                    offline, blocked or timed out; the row may
 *                                                          or may not have arrived, so retrying is safe
 *   Retrying is safe because the row carries a client_id that is unique in the table: the database
 *   refuses a second copy (PostgreSQL error 23505, which PostgREST answers with HTTP 409), and this
 *   client reports that as "ok, duplicate" because the response is stored. (A plain insert is used,
 *   not "ON CONFLICT", because that form needs permission to READ the column and the public key
 *   deliberately has none. supabase/tests/verify_migrations.mjs proves this against PostgreSQL.)
 *
 * TESTS AND OTHER HOSTS
 *   A page (or a test) can set window.DHAR_DB_CONFIG = { url: '...', key: '...' } before this script
 *   runs, or { url: '', key: '' } to switch the database off. Nothing else here needs changing.
 */
(function () {
  'use strict';

  /* ---- settings ------------------------------------------------------------------------- */
  var DEFAULTS = {
    url: 'https://ctpjbmolgvkagdbafsvh.supabase.co',
    key: 'sb_publishable_3SubF-oSyq6QDrrONNqdcg_fnxO-nE0'
  };

  /* Tables this client may write to. `unique` is the column the database keeps unique, so that a
     repeated send of the same row (a retry) is recognised: a repeat comes back as 409 / 23505. */
  var TABLES = {
    survey_responses: { unique: 'client_id' }
  };

  var TIMEOUT_MS = 20000;

  var CFG = window.DHAR_DB_CONFIG || DEFAULTS;
  /* https only, except a web server on this computer (used by the tests). */
  var URL_OK = /^(https:\/\/[a-z0-9.-]+|http:\/\/(localhost|127\.0\.0\.1)(:\d+)?)$/i;
  var BASE = typeof CFG.url === 'string' ? CFG.url.trim().replace(/\/+$/, '') : '';
  var KEY = typeof CFG.key === 'string' ? CFG.key.trim() : '';

  function ready() {
    return URL_OK.test(BASE) && KEY !== '' && typeof window.fetch === 'function' && typeof Promise !== 'undefined';
  }

  /* ---- insert --------------------------------------------------------------------------- */
  function insert(table, row) {
    if (!ready()) { return Promise.resolve({ kind: 'unreachable', why: 'not-configured' }); }
    if (!Object.prototype.hasOwnProperty.call(TABLES, table)) {
      return Promise.resolve({ kind: 'rejected', status: 0, code: 'unknown-table', message: 'This page may not write to ' + table + '.' });
    }
    var body;
    try { body = JSON.stringify(row); } catch (e) {
      return Promise.resolve({ kind: 'rejected', status: 0, code: 'client', message: 'The data could not be prepared.' });
    }

    var controller = typeof window.AbortController === 'function' ? new window.AbortController() : null;
    var timer = null;
    var timeout = new Promise(function (resolve) {
      timer = window.setTimeout(function () {
        if (controller) { controller.abort(); }
        resolve({ kind: 'unreachable', why: 'timeout' });
      }, TIMEOUT_MS);
    });

    var url = BASE + '/rest/v1/' + encodeURIComponent(table);
    var attempt = window.fetch(url, {
      method: 'POST',
      headers: {
        'apikey': KEY,
        'Content-Type': 'application/json',
        /* return=minimal: the key is not allowed to read rows back, so none is asked for. */
        'Prefer': 'return=minimal'
      },
      body: body,
      credentials: 'omit',
      cache: 'no-store',
      referrerPolicy: 'no-referrer',
      signal: controller ? controller.signal : undefined
    }).then(function (res) {
      if (res.status >= 200 && res.status < 300) { return { kind: 'ok', status: res.status }; }
      return res.text().then(function (text) {
        var data = null;
        try { data = JSON.parse(text); } catch (e) { data = null; }
        var code = data && data.code ? String(data.code) : 'http-' + res.status;
        /* "This client_id is already stored": a retry of a response that did arrive. Not a failure. */
        if (res.status === 409 && code === '23505') { return { kind: 'ok', status: 409, duplicate: true }; }
        return {
          kind: 'rejected',
          status: res.status,
          code: code,
          message: data && data.message ? String(data.message) : 'The database answered with HTTP ' + res.status + '.'
        };
      }, function () {
        return { kind: 'rejected', status: res.status, code: 'http-' + res.status, message: 'The database answered with HTTP ' + res.status + '.' };
      });
    }, function () {
      return { kind: 'unreachable', why: 'network' };
    });

    return Promise.race([attempt, timeout]).then(function (outcome) {
      window.clearTimeout(timer);
      return outcome;
    });
  }

  window.DharDB = { ready: ready, insert: insert, tables: Object.keys(TABLES) };
})();
