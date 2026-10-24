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
 *          { kind: 'ok' }                                  stored (or already stored: see below)
 *          { kind: 'rejected', status, code, message }     the database said no (bad shape, too many)
 *          { kind: 'unreachable', why }                    offline, blocked or timed out; the row may
 *                                                          or may not have arrived, so retrying is safe
 *   Retrying is safe because the row carries a client_id that is unique in the table: a second copy
 *   is ignored by the database instead of being stored twice.
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

  /* Tables this client may write to. `conflict` is the column whose repeat is ignored. */
  var TABLES = {
    survey_responses: { conflict: 'client_id' }
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

    var url = BASE + '/rest/v1/' + encodeURIComponent(table) + '?on_conflict=' + encodeURIComponent(TABLES[table].conflict);
    var attempt = window.fetch(url, {
      method: 'POST',
      headers: {
        'apikey': KEY,
        'Content-Type': 'application/json',
        /* return=minimal: the key is not allowed to read rows back. ignore-duplicates: a repeat of the
           same client_id is not an error, it is simply not stored twice. */
        'Prefer': 'return=minimal,resolution=ignore-duplicates'
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
        return {
          kind: 'rejected',
          status: res.status,
          code: data && data.code ? String(data.code) : 'http-' + res.status,
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
