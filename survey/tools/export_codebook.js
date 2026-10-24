#!/usr/bin/env node
/*
 * export_codebook.js: writes the codebook of the survey, straight from questions.js.
 *
 * The codebook lists every question code, its exact wording, its answer options (with
 * their ids), who sees it and why. It is what you read next to the CSV made by
 * parse_responses.py. Generating it from questions.js means it can never drift out of
 * date: run this again after every edit of the questions.
 *
 * USAGE (Node 14 or newer, no installs)
 *   node tools/export_codebook.js                 writes docs/CODEBOOK.md and docs/codebook.json
 *   node tools/export_codebook.js path/to/questions.js out-dir
 *
 * The questions file is looked for at src/assets/questions.js (the development layout)
 * and at assets/questions.js (the published layout) unless you give a path.
 */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');

var root = path.resolve(__dirname, '..');
var candidates = [
  process.argv[2],
  path.join(root, 'src', 'assets', 'questions.js'),
  path.join(root, 'assets', 'questions.js')
].filter(Boolean);
var questionsFile = candidates.filter(function (f) { return fs.existsSync(f); })[0];
if (!questionsFile) {
  console.error('Could not find questions.js. Tried:\n  ' + candidates.join('\n  '));
  process.exit(1);
}
var outDir = path.resolve(process.argv[3] || path.join(root, 'docs'));

/* questions.js is a browser script that fills window.DHAR_SURVEY. Run it in a sandbox. */
var sandbox = { window: {} };
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(questionsFile, 'utf8'), sandbox, { filename: questionsFile });
var SURVEY = sandbox.window.DHAR_SURVEY;
if (!SURVEY || !SURVEY.sections) {
  console.error('questions.js did not define window.DHAR_SURVEY.');
  process.exit(1);
}

/* ---- helpers -------------------------------------------------------------- */

var roleName = {};
SURVEY.roleQuestion.options.forEach(function (o) { roleName[o.id] = o.short || o.label; });

var optionLabel = {}; /* code -> id -> label */
function allQuestions() {
  var out = [];
  SURVEY.sections.forEach(function (sec) {
    sec.questions.forEach(function (q) { out.push({ section: sec, question: q }); });
  });
  return out;
}
allQuestions().forEach(function (e) {
  var q = e.question;
  optionLabel[q.code] = {};
  (q.options || []).forEach(function (o, i) {
    var obj = typeof o === 'string' ? { id: 'o' + (i + 1), label: o } : o;
    optionLabel[q.code][obj.id] = obj.label;
  });
});

function describe(cond) {
  if (!cond) { return ''; }
  if (cond.role) { return 'role is ' + roleName[cond.role]; }
  if (cond.roleAny) { return 'role is ' + cond.roleAny.map(function (r) { return roleName[r]; }).join(' or '); }
  if (cond.q) {
    var lab = function (id) { return '"' + ((optionLabel[cond.q] || {})[id] || id) + '"'; };
    if (cond.is !== undefined) { return cond.q + ' is ' + lab(cond.is); }
    if (cond.has !== undefined) { return cond.q + ' includes ' + lab(cond.has); }
    if (cond.hasAny) { return cond.q + ' includes ' + cond.hasAny.map(lab).join(' or '); }
  }
  if (cond.all) { return cond.all.map(describe).join(' and '); }
  if (cond.any) { return '(' + cond.any.map(describe).join(' or ') + ')'; }
  return JSON.stringify(cond);
}

/* Evaluates a condition for a hypothetical respondent: roles = ids, picks = {code: [ids]} */
function holds(cond, roles, picks) {
  if (!cond) { return true; }
  if (cond.role) { return roles.indexOf(cond.role) >= 0; }
  if (cond.roleAny) { return cond.roleAny.some(function (r) { return roles.indexOf(r) >= 0; }); }
  if (cond.q) {
    var have = picks[cond.q] || [];
    if (cond.is !== undefined) { return have.indexOf(cond.is) >= 0; }
    if (cond.has !== undefined) { return have.indexOf(cond.has) >= 0; }
    if (cond.hasAny) { return cond.hasAny.some(function (id) { return have.indexOf(id) >= 0; }); }
  }
  if (cond.all) { return cond.all.every(function (c) { return holds(c, roles, picks); }); }
  if (cond.any) { return cond.any.some(function (c) { return holds(c, roles, picks); }); }
  return false;
}

function whoSees(sec, q) {
  var parts = [];
  /* A question that narrows the same answer the section already tests (the area blocks
     narrow "A3 includes any area" to one area) is described by the narrower rule alone. */
  var narrower = sec.showIf && q.showIf && sec.showIf.q && q.showIf.q === sec.showIf.q;
  if (sec.showIf && !narrower) { parts.push(describe(sec.showIf)); }
  if (q.showIf) { parts.push(describe(q.showIf)); }
  return parts.length ? parts.join('; and ') : 'everyone';
}

var TYPE_NAME = {
  text: 'short text', textarea: 'long text', email: 'email', radio: 'one choice',
  checkbox: 'several choices', likert: '1 to 5', scale: 'number scale', grid: 'grid of 1 to 5 ratings'
};

function oneLine(s) { return String(s || '').replace(/\s+/g, ' ').trim(); }
function cell(s) { return oneLine(s).replace(/\|/g, '\\|'); }

/* ---- data (codebook.json) -------------------------------------------------- */

var questions = [];
allQuestions().forEach(function (e) {
  var sec = e.section, q = e.question;
  var rec = {
    code: q.code,
    section: sec.title,
    type: q.type,
    required: !!q.required,
    text: q.text,
    hint: q.hint || '',
    shownTo: whoSees(sec, q)
  };
  if (q.group) { rec.optionalBlock = q.group.title; }
  if (q.options) {
    rec.options = q.options.map(function (o, i) {
      var obj = typeof o === 'string' ? { id: 'o' + (i + 1), label: o } : o;
      var item = { id: obj.id, label: obj.label };
      if (obj.other) { item.otherText = true; }
      if (obj.exclusive) { item.exclusive = true; }
      return item;
    });
  }
  if (q.max) { rec.maxChoices = q.max; }
  if (q.type === 'likert') { rec.scale = { from: 1, to: 5, labels: q.labels || {} }; }
  if (q.type === 'scale') { rec.scale = { from: q.from, to: q.to, labels: q.labels || {} }; }
  if (q.type === 'grid') { rec.rows = q.rows.slice(); rec.scale = { from: 1, to: 5, labels: q.labels || {} }; }
  questions.push(rec);
});

/* ---- how many questions each kind of respondent sees ----------------------- */

var AREA_IDS = ['software', 'web', 'mobile', 'data', 'ai', 'ml', 'systems', 'security', 'blockchain'];
function countFor(roles, areas) {
  var picks = { A3: areas };
  var n = 0, areaQs = 0;
  allQuestions().forEach(function (e) {
    if (e.question.code === 'ROLE') { return; }
    if (holds(e.section.showIf, roles, picks) && holds(e.question.showIf, roles, picks)) {
      n++;
      if (e.question.group) { areaQs++; }
    }
  });
  return { all: n, optional: areaQs };
}
var counts = Object.keys(roleName).map(function (r) {
  var none = countFor([r], []), most = countFor([r], AREA_IDS);
  return { role: roleName[r], withoutAreas: none.all, withAllAreas: most.all };
});

/* ---- Markdown -------------------------------------------------------------- */

var md = [];
md.push('# Shaping Dhar survey: codebook');
md.push('');
md.push('Generated from `questions.js` by `tools/export_codebook.js`. Do not edit by hand; edit the questions and run the script again.');
md.push('');
md.push('- Survey version: **' + SURVEY.version + '**');
md.push('- Questions in the bank: **' + (questions.length - 1) + '** (not counting the role question)');
md.push('- Each question code is a column in the CSV made by `tools/parse_responses.py`.');
md.push('- A code never changes meaning. If wording or option order changes, the survey version is raised.');
md.push('');
md.push('## How long it is for each kind of respondent');
md.push('');
md.push('| Role picked on its own | Questions without any optional area blocks | With every area ticked |');
md.push('| --- | ---: | ---: |');
counts.forEach(function (c) { md.push('| ' + c.role + ' | ' + c.withoutAreas + ' | ' + c.withAllAreas + ' |'); });
md.push('');
md.push('Picking several roles adds the questions of each. Questions in the optional area blocks can be skipped.');
md.push('');
md.push('## How answers are written in the CSV');
md.push('');
md.push('| Question type | Cell value |');
md.push('| --- | --- |');
md.push('| one choice | the option text |');
md.push('| several choices | option texts joined with ` \\| ` |');
md.push('| 1 to 5, number scale | the number |');
md.push('| grid | `statement: number` pairs joined with ` \\| ` |');
md.push('| text | the text as typed |');
md.push('');
md.push('An "Other" option appears as `Other: what they typed`. An unanswered question is an empty cell.');

var currentSection = null;
allQuestions().forEach(function (e) {
  var sec = e.section, q = e.question;
  if (sec !== currentSection) {
    currentSection = sec;
    md.push('');
    md.push('## ' + sec.title);
    md.push('');
    if (sec.intro) { md.push('_' + oneLine(sec.intro) + '_'); md.push(''); }
    md.push('Report heading: `== ' + sec.reportTitle + ' ==`. Shown to: ' + (sec.showIf ? describe(sec.showIf) : 'everyone') + '.');
  }
  md.push('');
  md.push('### ' + q.code + (q.required ? ' (required)' : ''));
  md.push('');
  md.push(oneLine(q.text));
  if (q.hint) { md.push(''); md.push('_' + oneLine(q.hint) + '_'); }
  md.push('');
  var facts = ['Type: ' + TYPE_NAME[q.type], 'Shown to: ' + whoSees(sec, q)];
  if (q.group) { facts.push('Optional block: ' + q.group.title); }
  if (q.max) { facts.push('Up to ' + q.max + ' choices'); }
  md.push(facts.join(' · '));
  if (q.options) {
    md.push('');
    md.push('| Id | Option |');
    md.push('| --- | --- |');
    q.options.forEach(function (o, i) {
      var obj = typeof o === 'string' ? { id: 'o' + (i + 1), label: o } : o;
      var label = cell(obj.label) + (obj.other ? ' (with a text box)' : '') + (obj.exclusive ? ' (clears the other choices)' : '');
      md.push('| `' + obj.id + '` | ' + label + ' |');
    });
  }
  if (q.type === 'likert' || q.type === 'grid') {
    var L = q.labels || {};
    md.push('');
    md.push('Scale: 1 = ' + (L[1] || '') + ', 5 = ' + (L[5] || '') + (L[3] ? ', 3 = ' + L[3] : ''));
  }
  if (q.type === 'scale') {
    var S = q.labels || {};
    md.push('');
    md.push('Scale: ' + q.from + ' = ' + (S.from || '') + ', ' + q.to + ' = ' + (S.to || ''));
  }
  if (q.type === 'grid') {
    md.push('');
    md.push('Rows:');
    q.rows.forEach(function (r, i) { md.push((i + 1) + '. ' + oneLine(r)); });
  }
});
md.push('');

/* ---- write ----------------------------------------------------------------- */

fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(path.join(outDir, 'CODEBOOK.md'), md.join('\n'), 'utf8');
fs.writeFileSync(path.join(outDir, 'codebook.json'),
  JSON.stringify({ version: SURVEY.version, title: SURVEY.title, counts: counts, questions: questions }, null, 2) + '\n', 'utf8');
console.log('Wrote ' + path.join(outDir, 'CODEBOOK.md') + ' and codebook.json (' + (questions.length - 1) + ' questions, version ' + SURVEY.version + ').');
