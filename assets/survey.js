/*
 * survey.js: the engine behind the "Shaping Dhar" survey page.
 *
 * It reads the question bank (questions.js) and the settings (config.js) and does
 * five jobs:
 *
 *   1. RENDER      builds every step of the survey as accessible HTML.
 *   2. BRANCH      shows only the steps and questions that apply to the roles
 *                  and answers the respondent has given (live, as they type).
 *   3. VALIDATE    checks required questions before moving on.
 *   4. REPORT      turns the visible, answered questions into a plain-text email.
 *   5. HAND OFF    opens the respondent's own email app, addressed to the project,
 *                  with fallbacks for long messages (see config.js).
 *
 * There is no server. Nothing is transmitted by this page itself: the only way an
 * answer leaves the device is the email the respondent presses Send on. Unfinished
 * answers are kept in the browser's localStorage on this device only.
 *
 * Plain script (no modules, no build step, no dependencies) so it also works when
 * index.html is opened straight from disk.
 */
(function () {
  'use strict';

  var SURVEY = window.DHAR_SURVEY;
  var CONFIG = window.DHAR_CONFIG;
  var mount = document.getElementById('survey');
  if (!SURVEY || !CONFIG || !mount) { return; }

  /* ======================================================================= *
   * 1. State
   * ======================================================================= */

  /* answers: { CODE: value, 'CODE#other': text }.
     value is a string (text, radio), an array of option ids (checkbox), a number
     (likert, scale) or { rowIndex: number } (grid). */
  var state = { answers: {}, stepId: 'start' };

  /* dom.q[code] = { el, num, err, inputs... }; dom.step[id] = <section> */
  var dom = { q: {}, step: {}, deep: {} };

  /* The last step is built by this file, not by the question bank. */
  var REVIEW = { id: 'review', title: 'Review and send', reportTitle: 'REVIEW', questions: [] };

  var STORAGE_KEY = CONFIG.storagePrefix + ':' + SURVEY.version;

  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ======================================================================= *
   * 2. Small helpers
   * ======================================================================= */

  /* h('div', {class: 'x', onclick: fn}, child, [children], 'text') */
  function h(tag, attrs) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        var v = attrs[k];
        if (v === null || v === undefined || v === false) { return; }
        if (k === 'class') { node.className = v; }
        else if (k === 'text') { node.textContent = v; }
        else if (k.slice(0, 2) === 'on') { node.addEventListener(k.slice(2), v); }
        else { node.setAttribute(k, v === true ? '' : v); }
      });
    }
    for (var i = 2; i < arguments.length; i++) { add(node, arguments[i]); }
    return node;
  }

  function add(node, kid) {
    if (kid === null || kid === undefined || kid === false) { return; }
    if (Array.isArray(kid)) { kid.forEach(function (k) { add(node, k); }); return; }
    node.appendChild(typeof kid === 'string' ? document.createTextNode(kid) : kid);
  }

  function enc(s) { return encodeURIComponent(s); }

  function pad2(n) { return (n < 10 ? '0' : '') + n; }

  /* "2026-10-17 16:34 (UTC+01:00)" in the respondent's own time zone. */
  function stamp(d) {
    var off = -d.getTimezoneOffset();
    var sign = off >= 0 ? '+' : '-';
    off = Math.abs(off);
    return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()) + ' ' +
      pad2(d.getHours()) + ':' + pad2(d.getMinutes()) +
      ' (UTC' + sign + pad2(Math.floor(off / 60)) + ':' + pad2(off % 60) + ')';
  }

  function fileStamp(d) {
    return d.getFullYear() + pad2(d.getMonth() + 1) + pad2(d.getDate()) + '-' + pad2(d.getHours()) + pad2(d.getMinutes());
  }

  function recipient() { return CONFIG.recipientUser + '@' + CONFIG.recipientDomain; }

  /* Storage can be missing or throw (private windows, blocked site data). Never rely on it. */
  function storageGet() {
    try { return window.localStorage.getItem(STORAGE_KEY); } catch (e) { return null; }
  }
  function storageSet(value) {
    try { window.localStorage.setItem(STORAGE_KEY, value); return true; } catch (e) { return false; }
  }
  function storageClear() {
    try { window.localStorage.removeItem(STORAGE_KEY); } catch (e) { /* nothing to do */ }
  }

  /* ======================================================================= *
   * 3. Question bank access, options and branching
   * ======================================================================= */

  function allQuestions() {
    var out = [];
    SURVEY.sections.forEach(function (s) { s.questions.forEach(function (q) { out.push(q); }); });
    return out;
  }

  /* String options get positional ids ("o1", "o2", ...); objects keep their own. */
  function optionsOf(q) {
    if (!q._opts) {
      q._opts = (q.options || []).map(function (o, i) {
        return typeof o === 'string' ? { id: 'o' + (i + 1), label: o } : o;
      });
    }
    return q._opts;
  }

  function optionById(q, id) {
    var list = optionsOf(q);
    for (var i = 0; i < list.length; i++) { if (list[i].id === id) { return list[i]; } }
    return null;
  }

  function rolesPicked() { return state.answers.ROLE || []; }

  /* Evaluates a showIf condition against the current answers (see questions.js). */
  function test(c) {
    if (!c) { return true; }
    if (c.all) { return c.all.every(test); }
    if (c.any) { return c.any.some(test); }
    if (c.role) { return rolesPicked().indexOf(c.role) !== -1; }
    if (c.roleAny) { return c.roleAny.some(function (r) { return rolesPicked().indexOf(r) !== -1; }); }
    if (c.q) {
      var v = state.answers[c.q];
      if (Object.prototype.hasOwnProperty.call(c, 'is')) { return v === c.is; }
      if (Object.prototype.hasOwnProperty.call(c, 'has')) { return Array.isArray(v) && v.indexOf(c.has) !== -1; }
      if (c.hasAny) { return Array.isArray(v) && c.hasAny.some(function (id) { return v.indexOf(id) !== -1; }); }
    }
    return true;
  }

  function sectionVisible(sec) { return test(sec.showIf); }

  function visibleQuestions(sec) {
    return sec.questions.filter(function (q) { return test(q.showIf); });
  }

  /* The steps the respondent will walk through right now, review step last. */
  function steps() {
    return SURVEY.sections.filter(sectionVisible).concat([REVIEW]);
  }

  function stepIndex(list, id) {
    for (var i = 0; i < list.length; i++) { if (list[i].id === id) { return i; } }
    return -1;
  }

  /* ======================================================================= *
   * 4. Answers: reading, "is it answered?", validation
   * ======================================================================= */

  function otherText(q) { return (state.answers[q.code + '#other'] || '').trim(); }

  function chosenOther(q) {
    var v = state.answers[q.code];
    if (q.type === 'radio') { var o = optionById(q, v); return !!(o && o.other); }
    if (q.type === 'checkbox' && Array.isArray(v)) {
      return v.some(function (id) { var o = optionById(q, id); return !!(o && o.other); });
    }
    return false;
  }

  function isAnswered(q) {
    var v = state.answers[q.code];
    switch (q.type) {
      case 'text': case 'textarea': case 'email': return typeof v === 'string' && v.trim() !== '';
      case 'radio': return typeof v === 'string' && v !== '';
      case 'checkbox': return Array.isArray(v) && v.length > 0;
      case 'likert': case 'scale': return typeof v === 'number';
      case 'grid': return !!v && q.rows.every(function (_, i) { return typeof v[i] === 'number'; });
      default: return false;
    }
  }

  function gridMissing(q) {
    var v = state.answers[q.code] || {};
    return q.rows.filter(function (_, i) { return typeof v[i] !== 'number'; }).length;
  }

  /* Returns '' when the question is fine, otherwise a plain instruction. */
  function problemWith(q) {
    if (!q.required) { return ''; }
    if (!isAnswered(q)) {
      switch (q.type) {
        case 'radio': return 'Choose one option.';
        case 'checkbox': return 'Choose at least one option.';
        case 'likert': return 'Pick a number from 1 to 5.';
        case 'scale': return 'Pick a number from ' + q.from + ' to ' + q.to + '.';
        case 'grid':
          var n = gridMissing(q);
          return 'Rate every line. ' + n + (n === 1 ? ' line is' : ' lines are') + ' still unrated.';
        default: return 'Add an answer.';
      }
    }
    if (chosenOther(q) && otherText(q) === '') { return 'Say what "Other" is, or untick it.'; }
    return '';
  }

  /* ======================================================================= *
   * 5. Rendering
   * ======================================================================= */

  function qid(q, suffix) { return suffix + '-' + q.code; }

  function questionShell(q, isGroup) {
    var legendId = qid(q, 'lg');
    var textNode = h('span', { class: 'q-text-body' }, q.text);
    var optional = q.required ? null : h('span', { class: 'q-opt', text: ' Optional' });
    var num = h('span', { class: 'q-num', 'aria-hidden': 'true' });
    var title = isGroup ?
      h('p', { class: 'q-text', id: legendId }, num, h('span', null, textNode, optional)) :
      h('label', { class: 'q-text', id: legendId, 'for': qid(q, 'in') }, num, h('span', null, textNode, optional));
    var hint = q.hint ? h('p', { class: 'q-hint', id: qid(q, 'hint'), text: q.hint }) : null;
    var err = h('p', { class: 'q-err', id: qid(q, 'err'), hidden: true });
    var describedBy = (q.hint ? qid(q, 'hint') + ' ' : '') + qid(q, 'err');
    var el = h('div', { class: 'q', id: qid(q, 'q'), 'data-code': q.code }, title, hint);
    /* Checkbox lists and grids need an outer group. Radio, likert and scale rows
       carry their own radiogroup role, so they do not get a second one. */
    if (q.type === 'checkbox' || q.type === 'grid') {
      el.setAttribute('role', 'group');
      el.setAttribute('aria-labelledby', legendId);
      el.setAttribute('aria-describedby', describedBy);
    }
    return { el: el, num: num, err: err, describedBy: describedBy, body: null };
  }

  function renderQuestion(q) {
    var grouped = ['radio', 'checkbox', 'likert', 'scale', 'grid'].indexOf(q.type) !== -1;
    var shell = questionShell(q, grouped);
    var rec = { el: shell.el, num: shell.num, err: shell.err, inputs: [], others: {}, count: null, q: q, describedBy: shell.describedBy };
    var body;
    switch (q.type) {
      case 'radio': body = renderChoice(q, rec, 'radio'); break;
      case 'checkbox': body = renderChoice(q, rec, 'checkbox'); break;
      case 'likert': body = renderSegment(q, rec, 1, 5, q.labels || {}, 'likert'); break;
      case 'scale': body = renderSegment(q, rec, q.from, q.to, { 1: (q.labels || {}).from, 5: (q.labels || {}).to }, 'scale'); break;
      case 'grid': body = renderGrid(q, rec); break;
      default: body = renderText(q, rec, shell.describedBy); break;
    }
    shell.el.appendChild(body);
    shell.el.appendChild(shell.err);
    dom.q[q.code] = rec;
    return shell.el;
  }

  /* radio and checkbox lists, with optional "Other" text box and "None" exclusivity */
  function renderChoice(q, rec, kind) {
    var list = h('div', { class: 'opts' + (q.layout === 'chips' ? ' chips' : '') });
    if (kind === 'radio') {
      list.setAttribute('role', 'radiogroup');
      list.setAttribute('aria-labelledby', qid(q, 'lg'));
      list.setAttribute('aria-describedby', rec.describedBy);
    }

    var lastGroup = null;
    optionsOf(q).forEach(function (o) {
      if (o.group && o.group !== lastGroup) {
        list.appendChild(h('p', { class: 'opt-group', text: o.group }));
        lastGroup = o.group;
      }
      var inputId = 'in-' + q.code + '-' + o.id;
      var input = h('input', { type: kind, name: q.code, id: inputId, value: o.id });
      input.addEventListener('change', function () { onChoice(q, o, input); });
      rec.inputs.push(input);

      var body = h('span', { class: 'opt-body' }, h('span', { class: 'opt-label', text: o.label }),
        o.hint ? h('span', { class: 'opt-hint', text: o.hint }) : null);
      var wrap = h('div', { class: 'opt-wrap' }, h('label', { class: 'opt', 'for': inputId }, input, body));

      if (o.other) {
        var other = h('input', {
          type: 'text', class: 'field other', id: 'in-' + q.code + '-other-text', maxlength: '200',
          placeholder: 'Please say what', 'aria-label': 'Other: please say what', hidden: true
        });
        other.addEventListener('input', function () {
          state.answers[q.code + '#other'] = other.value;
          clearError(q); save();
        });
        rec.others[o.id] = other;
        wrap.appendChild(other);
      }
      list.appendChild(wrap);
    });

    var out = h('div', { class: 'q-body' }, list);
    if (q.max) {
      rec.count = h('p', { class: 'q-count', 'aria-live': 'polite' });
      out.appendChild(rec.count);
    }
    return out;
  }

  function onChoice(q, option, input) {
    if (q.type === 'radio') {
      state.answers[q.code] = option.id;
    } else {
      var cur = (state.answers[q.code] || []).slice();
      var at = cur.indexOf(option.id);
      if (input.checked) {
        if (option.exclusive) { cur = []; }
        else { cur = cur.filter(function (id) { var o = optionById(q, id); return !(o && o.exclusive); }); }
        if (at === -1) { cur.push(option.id); }
      } else if (at !== -1) {
        cur.splice(at, 1);
      }
      state.answers[q.code] = cur;
    }
    clearError(q);
    syncQuestion(q);
    refresh();
    save();
  }

  /* 1-5 / 0-10 button rows. `ends` carries the labels at the low and high end. */
  function segmentRow(q, rec, name, from, to, ends, chips, onPick, labelledBy) {
    var row = h('div', { class: 'seg' + (chips ? ' seg-chips' : ''), role: 'radiogroup', 'aria-labelledby': labelledBy });
    for (var n = from; n <= to; n++) {
      (function (value) {
        var id = 'in-' + name.replace(/[^A-Za-z0-9]/g, '-') + '-' + value;
        var input = h('input', { type: 'radio', name: name, id: id, value: String(value) });
        input.addEventListener('change', function () { onPick(value); });
        rec.inputs.push(input);
        var spoken = value + ' of ' + to + (value === from && ends.low ? ', ' + ends.low : '') +
          (value === to && ends.high ? ', ' + ends.high : '') +
          (ends.mid && value === ends.midValue ? ', ' + ends.mid : '');
        row.appendChild(h('label', { class: 'seg-item', 'for': id }, input,
          h('span', { class: 'seg-n', 'aria-hidden': 'true', text: String(value) }),
          h('span', { class: 'sr', text: spoken })));
      })(n);
    }
    return row;
  }

  function endsFrom(labels, from, to) {
    var mid = labels[3] && from === 1 && to === 5 ? labels[3] : '';
    return { low: labels[1] || '', high: labels[5] || '', mid: mid, midValue: 3 };
  }

  function renderSegment(q, rec, from, to, labels, kind) {
    var ends = endsFrom(labels, from, to);
    var row = segmentRow(q, rec, q.code, from, to, ends, kind === 'scale', function (value) {
      state.answers[q.code] = value;
      clearError(q); syncQuestion(q); refresh(); save();
    }, qid(q, 'lg'));
    row.setAttribute('aria-describedby', rec.describedBy);
    var legend = h('div', { class: 'seg-ends', 'aria-hidden': 'true' },
      h('span', { text: ends.low }), ends.mid ? h('span', { class: 'mid', text: ends.mid }) : null, h('span', { text: ends.high }));
    return h('div', { class: 'q-body' }, row, legend);
  }

  function renderGrid(q, rec) {
    var labels = q.labels || {};
    var ends = endsFrom(labels, 1, 5);
    var body = h('div', { class: 'q-body grid' },
      h('p', { class: 'grid-key', text: '1 means ' + ends.low.toLowerCase() + '. 5 means ' + ends.high.toLowerCase() + '.' }));
    q.rows.forEach(function (rowText, i) {
      var labelId = 'gr-' + q.code + '-' + i;
      var row = segmentRow(q, rec, q.code + '.' + i, 1, 5, ends, false, function (value) {
        var cur = state.answers[q.code] || {};
        cur[i] = value;
        state.answers[q.code] = cur;
        clearError(q); syncQuestion(q); refresh(); save();
      }, labelId);
      body.appendChild(h('div', { class: 'grid-row' }, h('p', { class: 'grid-label', id: labelId, text: rowText }), row));
    });
    return body;
  }

  function renderText(q, rec, describedBy) {
    var common = {
      id: qid(q, 'in'), name: q.code, 'aria-describedby': describedBy,
      placeholder: q.placeholder || '', autocomplete: q.autocomplete || 'off'
    };
    var input;
    if (q.type === 'textarea') {
      input = h('textarea', Object.assign({ class: 'field', rows: '4', maxlength: '4000' }, common));
    } else {
      input = h('input', Object.assign({ class: 'field', type: q.type === 'email' ? 'email' : 'text', maxlength: '300' }, common));
    }
    input.addEventListener('input', function () {
      state.answers[q.code] = input.value;
      clearError(q); refresh(); save();
    });
    rec.inputs.push(input);
    return h('div', { class: 'q-body' }, input);
  }

  function renderSection(sec) {
    var headingId = 'h-' + sec.id;
    var el = h('section', { class: 'step', id: 'step-' + sec.id, hidden: true, 'aria-labelledby': headingId, 'data-step': sec.id });
    var count = h('p', { class: 'step-count' });
    var heading = h('h2', { class: 'step-title' + (sec.hideHeading ? ' sr' : ''), id: headingId, tabindex: '-1', text: sec.title });
    el.appendChild(h('header', { class: 'step-head' }, count, heading, sec.intro ? h('p', { class: 'step-intro', text: sec.intro }) : null));

    var body = h('div', { class: 'questions' });
    sec.questions.forEach(function (q) {
      var qEl = renderQuestion(q);
      if (q.group) {
        var d = dom.deep[q.group.id];
        if (!d) {
          var meta = h('span', { class: 'deep-meta' });
          var details = h('details', { class: 'deep', 'data-group': q.group.id },
            h('summary', null, h('span', { class: 'deep-title', text: q.group.title }), meta),
            h('div', { class: 'deep-body' }));
          d = dom.deep[q.group.id] = { el: details, meta: meta, body: details.lastChild, codes: [] };
          body.appendChild(details);
        }
        d.body.appendChild(qEl);
        d.codes.push(q.code);
      } else {
        body.appendChild(qEl);
      }
    });
    el.appendChild(body);
    dom.step[sec.id] = { el: el, count: count, heading: heading, sec: sec };
    return el;
  }

  /* ======================================================================= *
   * 6. Syncing the page with the answers
   * ======================================================================= */

  /* Pushes the stored answer for one question into its inputs (used after every
     change, and once after a saved draft is restored). */
  function syncQuestion(q) {
    var rec = dom.q[q.code];
    if (!rec) { return; }
    var v = state.answers[q.code];
    var i;
    if (q.type === 'radio' || q.type === 'checkbox') {
      var picked = q.type === 'radio' ? (v ? [v] : []) : (Array.isArray(v) ? v : []);
      var full = !!q.max && picked.length >= q.max;
      rec.inputs.forEach(function (input) {
        var id = input.value;
        var o = optionById(q, id);
        var on = picked.indexOf(id) !== -1;
        input.checked = on;
        input.disabled = full && !on && !(o && o.exclusive);
        if (rec.others[id]) {
          rec.others[id].hidden = !on;
          if (rec.others[id].value !== (state.answers[q.code + '#other'] || '')) {
            rec.others[id].value = state.answers[q.code + '#other'] || '';
          }
        }
      });
      if (rec.count) {
        rec.count.textContent = picked.length + ' of ' + q.max + ' chosen';
      }
    } else if (q.type === 'likert' || q.type === 'scale') {
      rec.inputs.forEach(function (input) { input.checked = (typeof v === 'number' && String(v) === input.value); });
    } else if (q.type === 'grid') {
      for (i = 0; i < rec.inputs.length; i++) {
        var input = rec.inputs[i];
        var row = parseInt(input.name.split('.')[1], 10);
        input.checked = !!v && typeof v[row] === 'number' && String(v[row]) === input.value;
      }
    } else if (rec.inputs[0] && rec.inputs[0].value !== (typeof v === 'string' ? v : '')) {
      rec.inputs[0].value = typeof v === 'string' ? v : '';
    }
  }

  function syncAll() { allQuestions().forEach(syncQuestion); }

  function showError(q, message) {
    var rec = dom.q[q.code];
    rec.err.textContent = message;
    rec.err.hidden = false;
    rec.el.classList.add('has-error');
    if (isTextLike(q)) { rec.inputs.forEach(function (input) { input.setAttribute('aria-invalid', 'true'); }); }
  }

  function clearError(q) {
    var rec = dom.q[q.code];
    if (!rec || rec.err.hidden) { return; }
    rec.err.hidden = true;
    rec.err.textContent = '';
    rec.el.classList.remove('has-error');
    rec.inputs.forEach(function (input) { input.removeAttribute('aria-invalid'); });
  }

  function isTextLike(q) { return q.type === 'text' || q.type === 'textarea' || q.type === 'email'; }

  /* Re-evaluates branching and updates everything that depends on it. */
  function refresh() {
    var list = steps();
    if (stepIndex(list, state.stepId) === -1) { state.stepId = list[0].id; }
    var index = stepIndex(list, state.stepId);
    var current = list[index];

    SURVEY.sections.forEach(function (sec) {
      var s = dom.step[sec.id];
      s.el.hidden = (sec.id !== state.stepId);
      if (sec.id === state.stepId) {
        var visible = visibleQuestions(sec);
        var n = 0;
        sec.questions.forEach(function (q) {
          var shown = visible.indexOf(q) !== -1;
          dom.q[q.code].el.hidden = !shown;
          if (shown && !q.group) { n += 1; dom.q[q.code].num.textContent = String(n); }
        });
      }
    });
    dom.step.review.el.hidden = (state.stepId !== 'review');

    /* Folded blocks: show a block only when one of its questions applies. */
    Object.keys(dom.deep).forEach(function (id) {
      var d = dom.deep[id];
      var qs = d.codes.map(function (code) { return dom.q[code].q; });
      var applicable = qs.filter(function (q) { return test(q.showIf); });
      var answered = applicable.filter(isAnswered).length;
      d.el.hidden = applicable.length === 0;
      d.meta.textContent = answered + ' of ' + applicable.length + ' answered';
    });
    var applicableBlocks = Object.keys(dom.deep).filter(function (id) { return !dom.deep[id].el.hidden; });
    if (state.stepId === 'areas' && applicableBlocks.length === 1 && !dom.deep[applicableBlocks[0]].opened) {
      dom.deep[applicableBlocks[0]].el.open = true;   /* a lone block is opened once, for the respondent's convenience */
      dom.deep[applicableBlocks[0]].opened = true;
    }

    /* Part counter, progress band, page mode, buttons. */
    var total = list.length;
    Object.keys(dom.step).forEach(function (id) {
      if (dom.step[id].count) {
        var at = stepIndex(list, id);
        dom.step[id].count.textContent = at === -1 || at === 0 ? '' : 'Part ' + (at + 1) + ' of ' + total;
      }
    });
    var progress = (index + 1) / total;
    document.documentElement.style.setProperty('--p', progress.toFixed(3));
    dom.bar.setAttribute('aria-valuemax', String(total));
    dom.bar.setAttribute('aria-valuenow', String(index + 1));
    dom.bar.setAttribute('aria-valuetext', 'Part ' + (index + 1) + ' of ' + total + ': ' + current.title);
    document.body.setAttribute('data-step', state.stepId);

    var last = index === total - 1;
    dom.back.hidden = index === 0;
    dom.next.hidden = last;
    dom.next.textContent = index === total - 2 ? 'Review answers' : 'Next';
  }

  /* ======================================================================= *
   * 7. Navigation and validation
   * ======================================================================= */

  function scrollToEl(el) {
    try { el.scrollIntoView({ block: 'start', behavior: reduceMotion ? 'auto' : 'smooth' }); } catch (e) { el.scrollIntoView(); }
  }

  /* Validates the visible required questions of a step. Returns the failing questions. */
  function validateStep(sec) {
    var bad = [];
    visibleQuestions(sec).forEach(function (q) {
      var message = problemWith(q);
      if (message) { showError(q, message); bad.push(q); } else { clearError(q); }
    });
    return bad;
  }

  function focusQuestion(q) {
    var rec = dom.q[q.code];
    var target = rec.inputs.filter(function (i) { return !i.disabled; })[0] || rec.inputs[0];
    if (target) { target.focus({ preventScroll: true }); }
    try { rec.el.scrollIntoView({ block: 'center', behavior: reduceMotion ? 'auto' : 'smooth' }); } catch (e) { rec.el.scrollIntoView(); }
  }

  function setNavError(count) {
    if (!count) { dom.navErr.hidden = true; dom.navErr.textContent = ''; return; }
    dom.navErr.textContent = count === 1 ?
      'One question still needs an answer. It is marked above.' :
      count + ' questions still need an answer. The first one is marked above.';
    dom.navErr.hidden = false;
  }

  function go(stepId, options) {
    state.stepId = stepId;
    setNavError(0);
    if (stepId === 'review') { buildReview(); }
    refresh();
    save();
    var s = dom.step[stepId];
    if (!options || !options.quiet) {
      s.heading.focus({ preventScroll: true });
      scrollToEl(dom.stage);
    }
  }

  function onNext() {
    var list = steps();
    var index = stepIndex(list, state.stepId);
    var sec = list[index];
    if (sec.id !== 'review') {
      var bad = validateStep(sec);
      if (bad.length) { setNavError(bad.length); focusQuestion(bad[0]); return; }
    }
    if (index < list.length - 1) { go(list[index + 1].id); }
  }

  function onBack() {
    var list = steps();
    var index = stepIndex(list, state.stepId);
    if (index > 0) { go(list[index - 1].id); }
  }

  /* ======================================================================= *
   * 8. The report (what lands in the inbox)
   * ======================================================================= */

  function roleShortNames() {
    var picked = rolesPicked();
    return SURVEY.roleQuestion.options.filter(function (o) { return picked.indexOf(o.id) !== -1; })
      .map(function (o) { return o.short || o.label; });
  }

  /* Shortens text for the compact report: cut at a word, end with "..." */
  function clip(text, n) {
    var t = String(text).replace(/\s+/g, ' ').trim();
    if (t.length <= n) { return t; }
    var cut = t.slice(0, n);
    var space = cut.lastIndexOf(' ');
    if (space > n * 0.6) { cut = cut.slice(0, space); }
    return cut.replace(/[ ,;:.]+$/, '') + '...';
  }

  var COMPACT_QUESTION_CHARS = 60;
  var COMPACT_ROW_CHARS = 40;

  function withHint(q) { return q.text + (q.hint ? ' (' + q.hint + ')' : ''); }

  function indentLines(text) {
    return String(text).replace(/\r\n?/g, '\n').trim().split('\n').map(function (l) { return '  ' + l; });
  }

  function labelFor(q, id) {
    var o = optionById(q, id);
    if (!o) { return id; }
    if (o.other) { var t = otherText(q); return 'Other: ' + (t || '(not specified)'); }
    return o.label;
  }

  /* One answered question as report lines. `compact` shortens the question wording
     (and drops the scale anchors) but never touches the answer itself. */
  function formatQuestion(q, compact) {
    var v = state.answers[q.code];
    var lines = ['[' + q.code + '] ' + (compact ? clip(q.text, COMPACT_QUESTION_CHARS) : withHint(q))];
    var labels = q.labels || {};
    switch (q.type) {
      case 'radio': lines.push('  ' + labelFor(q, v)); break;
      case 'checkbox': v.forEach(function (id) { lines.push('  - ' + labelFor(q, id)); }); break;
      case 'likert':
        lines.push('  ' + v + ' of 5' + (compact ? '' : ' (1 = ' + labels[1] + ', 5 = ' + labels[5] + ')')); break;
      case 'scale':
        lines.push('  ' + v + ' of ' + q.to + (compact ? '' : ' (' + q.from + ' = ' + labels.from + ', ' + q.to + ' = ' + labels.to + ')')); break;
      case 'grid':
        if (!compact) { lines.push('  (1 = ' + labels[1] + ', 5 = ' + labels[5] + ')'); }
        q.rows.forEach(function (row, i) {
          if (v && typeof v[i] === 'number') { lines.push('  - ' + (compact ? clip(row, COMPACT_ROW_CHARS) : row) + ': ' + v[i] + ' of 5'); }
        });
        break;
      default: lines = lines.concat(indentLines(v));
    }
    return lines;
  }

  /* The report lists the essentials first (contact, basics, overall view), then the role
     sections, then the optional area detail. If an email app ever cuts a long message,
     the part it loses is the least important one. The roles are in the header. */
  var REPORT_FIRST = ['closing', 'about', 'shared'];

  function reportSections() {
    var list = steps().filter(function (s) { return s.id !== 'review' && s.id !== 'start'; });
    var first = [];
    REPORT_FIRST.forEach(function (id) {
      list.forEach(function (s) { if (s.id === id) { first.push(s); } });
    });
    return first.concat(list.filter(function (s) { return REPORT_FIRST.indexOf(s.id) === -1; }));
  }

  /* Builds the plain-text response from the questions that are currently visible and answered.
     Answers to questions that branching has hidden are kept in storage but never reported.
     compact=true gives the same answers with shortened question wording (see buildMailto). */
  function buildReport(compact) {
    var now = new Date();
    var shown = 0, answered = 0, body = [];
    reportSections().forEach(function (sec) {
      var chunk = [];
      visibleQuestions(sec).forEach(function (q) {
        shown += 1;
        if (isAnswered(q)) { answered += 1; chunk = chunk.concat(formatQuestion(q, compact), ['']); }
      });
      if (chunk.length) { body = body.concat(['== ' + sec.reportTitle + ' ==', ''], chunk); }
    });

    var tz = '';
    try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) { /* optional */ }
    var head = [
      'SHAPING DHAR SURVEY RESPONSE',
      'Survey version: ' + SURVEY.version,
      'Submitted: ' + stamp(now) + (tz ? ' ' + tz : ''),
      'Roles: ' + roleShortNames().join('; '),
      'Questions answered: ' + answered + ' of ' + shown + ' shown',
      'Question wording: ' + (compact ? 'shortened' : 'full'),
      ''
    ];
    var text = head.concat(body, ['== END OF RESPONSE ==']).join('\n');
    return { text: text, answered: answered, shown: shown, date: now };
  }

  function subjectLine() {
    var s = CONFIG.subjectPrefix + ': ' + roleShortNames().join(', ');
    return s.length > 110 ? s.slice(0, 107) + '...' : s;
  }

  /* ======================================================================= *
   * 9. Email hand-off
   * ======================================================================= */

  var TRUNCATION_NOTE = '[Shortened by the survey page. Your full answers were copied: select all of this message, paste, and send.]';

  /* Fits `text` into a link of at most `limit` encoded characters. `base` is the
     length of everything in the link that is not the body. Cuts at a line break and
     appends TRUNCATION_NOTE when it has to cut. */
  function fitBody(text, base, limit, newline) {
    function size(s) { return enc(s.split('\n').join(newline)).length; }
    if (base + size(text) <= limit) { return { body: text, truncated: false }; }
    var budget = limit - base - size('\n' + TRUNCATION_NOTE);
    var lines = text.split('\n'), kept = [], used = 0;
    for (var i = 0; i < lines.length; i++) {
      var cost = size(lines[i] + '\n');
      if (used + cost > budget) { break; }
      kept.push(lines[i]);
      used += cost;
    }
    return { body: kept.join('\n') + '\n' + TRUNCATION_NOTE, truncated: true };
  }

  function mailtoLimit() {
    var ua = (navigator && navigator.userAgent) || '';
    return /Windows/i.test(ua) ? CONFIG.mailtoLimitWindows : CONFIG.mailtoLimitOther;
  }

  /* Chooses what goes into a link, in three tiers:
       full     the complete report fits                          -> sent as is
       compact  it does not, but every answer fits with shortened  -> nothing is lost
                question wording
       cut      even that is too long                              -> compact report cut at a line
                break (essentials come first) and marked as cut */
  function pickBody(full, compact, baseLength, limit, newline) {
    var a = fitBody(full, baseLength, limit, newline);
    if (!a.truncated) { return { body: a.body, tier: 'full' }; }
    var b = fitBody(compact, baseLength, limit, newline);
    return { body: b.body, tier: b.truncated ? 'cut' : 'compact' };
  }

  function buildMailto(subject, full, compact) {
    var to = recipient();
    var base = 'mailto:' + to + '?subject=' + enc(subject) + '&body=';
    var pick = pickBody(full, compact, base.length, mailtoLimit(), '\r\n');
    return { url: base + enc(pick.body.split('\n').join('\r\n')), tier: pick.tier };
  }

  var PROVIDERS = [
    { id: 'gmail', label: 'Gmail',
      build: function (to, su, body) { return 'https://mail.google.com/mail/?view=cm&fs=1&to=' + enc(to) + '&su=' + enc(su) + '&body=' + enc(body); } },
    { id: 'outlook', label: 'Outlook',
      build: function (to, su, body) { return 'https://outlook.live.com/mail/0/deeplink/compose?to=' + enc(to) + '&subject=' + enc(su) + '&body=' + enc(body); } },
    { id: 'yahoo', label: 'Yahoo Mail',
      build: function (to, su, body) { return 'https://compose.mail.yahoo.com/?to=' + enc(to) + '&subject=' + enc(su) + '&body=' + enc(body); } }
  ];

  function buildWebLinks(subject, full, compact) {
    var to = recipient();
    return PROVIDERS.map(function (p) {
      var base = p.build(to, subject, '');
      var pick = pickBody(full, compact, base.length, CONFIG.webComposeLimit, '\n');
      return { id: p.id, label: p.label, url: p.build(to, subject, pick.body), tier: pick.tier };
    });
  }

  function legacyCopy(text) {
    var ta = h('textarea', { 'aria-hidden': 'true', tabindex: '-1', style: 'position:fixed;top:0;left:0;opacity:0' });
    ta.value = text;
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
  }

  /* Resolves to true when the text reached the clipboard. */
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).then(function () { return true; }, function () { return legacyCopy(text); });
    }
    return Promise.resolve(legacyCopy(text));
  }

  function announce(message) {
    dom.live.textContent = '';
    window.setTimeout(function () { dom.live.textContent = message; }, 30);
  }

  /* ======================================================================= *
   * 10. The review step
   * ======================================================================= */

  function renderReview() {
    var headingId = 'h-review';
    var count = h('p', { class: 'step-count' });
    var heading = h('h2', { class: 'step-title', id: headingId, tabindex: '-1', text: REVIEW.title });
    dom.summary = h('p', { class: 'review-summary' });
    dom.reportBox = h('textarea', {
      class: 'field report', readonly: true, rows: '14', id: 'report-text', spellcheck: 'false',
      'aria-label': 'Your answers, exactly as they will be emailed'
    });
    dom.sendBtn = h('button', { type: 'button', class: 'btn primary big', id: 'btn-send', text: 'Send by email', onclick: onSend });
    dom.sent = h('div', { class: 'sent', id: 'sent', hidden: true, tabindex: '-1', role: 'region', 'aria-labelledby': 'sent-title' });

    var el = h('section', { class: 'step', id: 'step-review', hidden: true, 'aria-labelledby': headingId, 'data-step': 'review' },
      h('header', { class: 'step-head' }, count, heading,
        h('p', { class: 'step-intro', text: 'Sending opens your email app with your answers already written and addressed to the Dhar project. Nothing is sent until you press Send there.' })),
      dom.summary,
      h('details', { class: 'preview' }, h('summary', { text: 'Read exactly what will be emailed' }), dom.reportBox),
      h('div', { class: 'send-row' }, dom.sendBtn,
        h('p', { class: 'send-note', text: 'Your email app opens with the message ready. If it does not, the options appear below.' })),
      dom.sent);
    dom.step.review = { el: el, count: count, heading: heading, sec: REVIEW };
    return el;
  }

  function buildReview() {
    var report = buildReport(false);
    dom.summary.textContent = 'You answered ' + report.answered + ' questions. Roles: ' + (roleShortNames().join(', ') || 'none') + '.';
    dom.reportBox.value = report.text;
    dom.sent.hidden = true;
  }

  /* Re-checks every visible required question. Used as a safety net before sending:
     returns the first step that still has a problem, or null. */
  function firstInvalidStep() {
    var list = steps();
    for (var i = 0; i < list.length - 1; i++) {
      var bad = visibleQuestions(list[i]).filter(function (q) { return problemWith(q) !== ''; });
      if (bad.length) { return { step: list[i], questions: bad }; }
    }
    return null;
  }

  function openMailto(url) {
    var a = h('a', { href: url, hidden: true });
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  function onSend() {
    var invalid = firstInvalidStep();
    if (invalid) {
      go(invalid.step.id, { quiet: true });
      validateStep(invalid.step);
      setNavError(invalid.questions.length);
      focusQuestion(invalid.questions[0]);
      return;
    }
    var report = buildReport(false);              /* complete wording: clipboard, download, preview */
    var compact = buildReport(true);              /* same answers, shorter question wording */
    var subject = subjectLine();
    var mail = buildMailto(subject, report.text, compact.text);
    var links = buildWebLinks(subject, report.text, compact.text);

    /* Start the copy first (it needs the click's permission), then open the email app. */
    var copied = copyText(report.text);
    openMailto(mail.url);
    copied.then(function (ok) { showSent(report, subject, mail, links, ok); });
  }

  function downloadReport(report) {
    var blob = new Blob([report.text.replace(/\n/g, '\r\n')], { type: 'text/plain;charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var a = h('a', { href: url, download: 'dhar-survey-response-' + fileStamp(report.date) + '.txt', hidden: true });
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
  }

  function showSent(report, subject, mail, links, copiedOk) {
    var box = dom.sent;
    box.textContent = '';
    box.appendChild(h('h3', { class: 'sent-title', id: 'sent-title', text: 'Your email is ready' }));
    box.appendChild(h('ol', { class: 'sent-steps' },
      h('li', { text: 'Check the message in your email app. It should list your answers and end with "END OF RESPONSE".' }),
      h('li', { text: 'Press Send in your email app. Until you do, nothing has been sent.' })));

    if (mail.tier === 'compact') {
      box.appendChild(h('p', { class: 'note', text: 'The message is long, so your email app received your answers with the long question wording shortened. Every answer is included.' }));
    } else if (mail.tier === 'cut') {
      var roomy = links.filter(function (l) { return l.tier !== 'cut'; })[0];
      box.appendChild(h('p', { class: 'warn' }, h('strong', { text: 'Your email may be cut short. ' }),
        'Your email app can only take part of a long message, so it opened with the first part of your answers (contact details and basics come first). ' +
        (roomy ? 'The "Open ' + roomy.label + '" button below carries all your answers without any pasting. Otherwise ' : 'To send everything, ') +
        (copiedOk ?
          'the full set is on your clipboard: select everything in the message, paste, then send.' :
          'press "Copy answers" below, then select everything in the message, paste, and send.')));
    }

    var actions = h('div', { class: 'actions' });
    actions.appendChild(h('button', {
      type: 'button', class: 'btn ghost', text: 'Copy answers',
      onclick: function () { copyText(report.text).then(function (ok) { announce(ok ? 'Answers copied.' : 'Copy failed. Select the text in the box above and copy it.'); }); }
    }));
    actions.appendChild(h('button', { type: 'button', class: 'btn ghost', text: 'Download as a text file', onclick: function () { downloadReport(report); } }));
    links.forEach(function (l) {
      actions.appendChild(h('a', { class: 'btn ghost', href: l.url, target: '_blank', rel: 'noopener', text: 'Open ' + l.label }));
    });
    box.appendChild(h('p', { class: 'sent-lead', text: 'Nothing opened, or you use webmail? Pick another way:' }));
    box.appendChild(actions);
    box.appendChild(h('p', { class: 'sent-manual' }, 'Writing it yourself: to ', h('strong', { text: recipient() }),
      ', subject "' + subject + '", and paste your answers in the body.'));

    box.appendChild(h('div', { class: 'sent-done' },
      h('p', { text: 'Thank you. Your answers help decide what gets built and how it is taught.' }),
      h('button', {
        type: 'button', class: 'btn ghost', text: 'I have sent it. Clear my answers from this device',
        onclick: discard
      })));

    box.hidden = false;
    box.focus({ preventScroll: true });
    scrollToEl(box);
    announce(copiedOk ? 'Your email is ready. Your answers are also copied.' : 'Your email is ready.');
  }

  /* ======================================================================= *
   * 11. Saving and restoring (this device only)
   * ======================================================================= */

  var saveTimer = null;
  var discarded = false;   /* set while the draft is being thrown away, so unloading the page cannot save it again */

  function save() {
    window.clearTimeout(saveTimer);
    saveTimer = window.setTimeout(saveNow, 250);
  }

  /* "Start over" and "I have sent it": forget the draft and reload a blank survey. */
  function discard() {
    discarded = true;
    window.clearTimeout(saveTimer);
    storageClear();
    window.location.reload();
  }

  function saveNow() {
    window.clearTimeout(saveTimer);
    if (discarded) { return; }
    storageSet(JSON.stringify({ v: SURVEY.version, answers: state.answers, stepId: state.stepId, at: Date.now() }));
  }

  /* Returns true when a saved draft with at least one answer was restored. */
  function restore() {
    var raw = storageGet();
    if (!raw) { return false; }
    var data;
    try { data = JSON.parse(raw); } catch (e) { return false; }
    if (!data || data.v !== SURVEY.version || !data.answers || typeof data.answers !== 'object') { return false; }
    var known = {};
    allQuestions().forEach(function (q) { known[q.code] = true; known[q.code + '#other'] = true; });
    var kept = 0;
    Object.keys(data.answers).forEach(function (k) {
      if (known[k]) { state.answers[k] = data.answers[k]; kept += 1; }
    });
    if (typeof data.stepId === 'string') { state.stepId = data.stepId; }
    return kept > 0;
  }

  /* ======================================================================= *
   * 12. Start-up
   * ======================================================================= */

  function init() {
    mount.textContent = '';

    dom.bar = document.getElementById('temper');
    dom.live = document.getElementById('live');
    dom.stage = document.getElementById('stage') || mount;

    var form = h('form', { class: 'survey-form', novalidate: true, autocomplete: 'on' });
    SURVEY.sections.forEach(function (sec) { form.appendChild(renderSection(sec)); });
    form.appendChild(renderReview());

    dom.navErr = h('p', { class: 'nav-err', role: 'alert', hidden: true });
    dom.back = h('button', { type: 'button', class: 'btn ghost', text: 'Back', onclick: onBack });
    dom.next = h('button', { type: 'submit', class: 'btn primary', text: 'Next' });
    form.appendChild(dom.navErr);
    form.appendChild(h('div', { class: 'nav' }, dom.back, dom.next));
    form.addEventListener('submit', function (e) { e.preventDefault(); onNext(); });
    mount.appendChild(form);

    var restored = restore();
    syncAll();
    if (restored) {
      var note = document.getElementById('restored');
      if (note) {
        note.hidden = false;
        var restart = document.getElementById('restart');
        if (restart) { restart.addEventListener('click', discard); }
      }
    }
    if (state.stepId === 'review') { buildReview(); }
    refresh();

    window.addEventListener('pagehide', saveNow);
    document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'hidden') { saveNow(); } });
    document.documentElement.setAttribute('data-ready', 'true');
  }

  init();
})();
