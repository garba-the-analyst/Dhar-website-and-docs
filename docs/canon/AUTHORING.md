# Authoring the Canon of Dhar

How a Canon document is written, built, checked and amended. The rules of the Canon itself are in the Master Index
(`src/master_index.md`); this file is the working manual for whoever edits a source. It is a repository document, not
part of the Canon, and it contains no status.

## 1. What you are writing

A Canon document is a **target specification**: it states what Dhar is to be and what must be true for a stage, a
guarantee or a policy to count as done. It never says what exists today (Master Index §2). Status lives in the Progress
Reports (`docs/reports/`) and on the website, both generated from one status file.

* Write `must`, `should`, `may` as the Master Index §3.1 defines them.
* Plain, precise, short sentences. No hype, no marketing, no adjectives that cannot be tested.
* Never write what exists or how well it works: "implemented", "a stub", "N tests pass", "N/N", dates of work done.
  Say what must hold, not what holds. (A reserved document that has not been written is "Reserved", not "missing".)
  `tests/run_tests.py` scans every Canon source for the phrases listed below.
* Keep the spelling the document already uses (British in the amendments and in most of the Volume III text,
  American in proper names such as "Optimizing Dhar"). Keep the document's em-dash style.
* **A claim names its gate** (Master Index §3.6): a statement about security, speed or correctness is allowed only if
  it names the acceptance gate that backs it (A-1 §9, A-2 §6) or is worded as an aim ("Dhar aims to…", "the design
  requires…"). "Secure", "safe", "fast" are never used alone. The allowed form is "passes gate S3 on these vectors as
  of this commit", and that sentence belongs in a Progress Report, not in the Canon; in the Canon you write what the
  gate requires.

Status phrases the test rejects in Canon sources (case-insensitive, whole words): `currently implemented`,
`already implemented`, `not yet implemented`, `has been implemented`, `is a stub`, `are stubs`, `TODO`, `FIXME`, `as of
today`, `at the time of writing`, `tests pass`, `all tests`, `45/45`, `108`, `64 of 64`. The Master Index's own statement
of the rule (§2, "not a status report") is the one line exempt. A phrase such as "the system-interface stub" of a target
is a design term, not a status, and is not rejected; "is implemented as a version bump" (the RFC process) is not rejected.

## 2. Source format and commands

A source is `docs/canon/src/<key>.md`: YAML front matter, then Markdown. The builder is `tools/build_canon.py`; the
look is `tools/canon/canon.css` and `tools/canon/template.html` (the website's palette, Saira and JetBrains Mono,
chamfered shapes, dark pages). **Never edit the builder, the stylesheet or the template**; if something cannot be
expressed, report it.

Front matter fields: `key`, `file` (the PDF name, unchanged from the original), `kind: canon`, `volume`, `short`,
`title`, `quote`, `version`, `date`, `status`, `running`, `part_label`, optional `contents: true`, optional `cover`
(ordered extra rows: `Part of`, `Depends on`, `Precedes`, `Audience`, …), optional `colophon` (one sentence in the
closing line), and `revisions` (list of `v`, `date`, `text`).

Body: `#` is a section, `##` a subsection, `###` below that. The document title is on the cover, so the body has no
level-one title of its own. Tables, fenced code, `<div class="note" markdown="1">` (also `decision`, `warn`) and
`<div class="compact" markdown="1">` around a wide table are available.

    python3 tools/build_canon.py KEY                 build one document (PDF in docs/canon/pdf/)
    python3 tools/build_canon.py KEY --html DIR      also keep the HTML
    python3 tools/build_canon.py --list              all sources, versions, output files
    python3 tools/build_canon.py --verify            is every PDF built from the present sources?
    python3 tools/canon_fidelity.py ORIGINAL.pdf NEW.pdf          what changed in the words (see §6)
    python3 tools/canon_extract.py ORIGINAL.pdf --scaffold        a first source from an old PDF

The originals of September 2026 are in `/home/claude/canon_originals/` and are never edited.

Several documents may be built at the same time by different people: the manifest is locked, and a malformed source
that is not yours is skipped. Build only your own keys. Never run the builder without keys while others are working.

## 3. One rule, one home, and what may be cited

* **Do not renumber.** Other documents cite sections (`Spec1 §14.3`). A new section goes at the end of its parent
  (the next free number) or at the end of the document. If a section has no subsections yet, its existing text stays
  as its opening and the new text becomes `§N.1`, `§N.2`.
* **The numbers below are fixed**, because several documents cite them. Create exactly these:

| Cited as | Contains | Written in |
| --- | --- | --- |
| Spec0 §4.1 | Targets: a back end per target and the one list in Amendment A-2 §3.1 (link, never restate) | Spec0 |
| Spec0 §5.1, §5.2, §5.3 | The direction (security, AI, quantum); breadth kept as modules (P6); the principles P1 to P6 and the gates, summarised with a link to A-1 | Spec0 |
| Spec1 §4.7 | Numeric types for models and cryptography (wide integers, `f16`, `bf16`, fixed-point and 8-bit arithmetic with wrapping, saturating and checked variants, fixed-width vector types, the complex pair) | Spec1 |
| Spec1 §14.5 | Secret values: the S2 rules, explicit reveal, constant-time select, clearing on scope exit | Spec1 |
| Spec1 §14.6 | Arenas (regions) and checked views over fixed-shape arrays (A2) | Spec1 |
| Spec1 §20.1 | `sys` across targets: numbers are the Linux x86-64 numbers, named forms such as `sys.write`, what a target without a call does (A-2 §5.1) | Spec1 |
| Spec1 §20.2 | The print function `gen` (A-2 §5.2): the exact rule | Spec1 |
| Stage-alpha §3.1, §3.2, §3.3 | The neutral operation set and target preludes (A-2 §4); the system interface and `gen` on every target (A-2 §5); the conformance battery and the gate (A-2 §6) | Stage-alpha |
| Stage-delta §2.1 | Domain modules: security, numerics and tensors, quantum, web, backend, blockchain and Web3, data, systems and hardware, each with the gate that applies (A-1 P6) | Stage-delta |
| Stage-epsilon §3.1 | Hosted services: the in-browser playground's service (sandbox, limits, no persistence) | Stage-epsilon |
| Tooling Dhar §5 | The in-browser playground | Tooling Dhar |
| Tempering §11 | Claims and gates: the rule of Master Index §3.6, what may be said, the allowed form | Tempering |
| Hallmark §7, §8 | Personal data and data protection (the mailing list, the survey, the playground); terms of the hosted services | Hallmark |
| Pact §2.1, §2.2 | The order in which the targets are built (A-2 §7); the gates as milestones in track order | The Pact |

* **New keyword spellings live only in Spec1.** Every other document refers to a new feature by its role ("the secret
  qualifier", "arenas", "the wide numeric types") and links to the Spec1 section. `gen`, `sys` and `sysret` are already
  ratified keywords and may be named anywhere.
* **The one list of targets is Amendment A-2 §3.1.** Other documents link to it; they never copy it. A document may
  name one target when its own rule is about that target ("the WebAssembly target").
* **Stage names.** Canon documents use Stage-alpha to Stage-epsilon. "Stage 0", "Stage 1" and "Stage 2" are the same
  stages (Master Index §3.8); they appear in Amendments A-1 and A-2 and in quotations, and are not used in new
  Canon text.
* **A keyword's meaning is ratified in Spec1 only**, a guarantee in Tempering Dhar, a licence, export or data-protection
  decision in The Hallmark of Dhar, the list of targets in A-2.

## 4. What every document receives (X1 to X4)

* **X1. Direction.** Where the document states Dhar's purpose, a short paragraph in the document's own terms (not a
  copy of A-1 §2): Dhar is a language for trustworthy computation; it goes first to cybersecurity, then to artificial
  intelligence, then to quantum computing; every other domain is kept as modules (P6). At most about 100 words, with a
  link to A-1.
* **X2. Order of domains.** Wherever the document lists domains, the order is cybersecurity, artificial intelligence,
  quantum computing, then the rest (systems and hardware, web and backend, data, blockchain and Web3, and so on), and
  **nothing is removed**.
* **X3. Claims name their gate.** See §1.
* **X4. Revision log.** The version moves up one minor step (Spec0 1.2 → 1.3, Spec1 3.1 → 3.2, Stage-delta 2.1 →
  2.2, every other document 1.0 → 1.1). The date is October 26, 2026. `revisions` gets one new entry whose text is one
  sentence naming the amendment and what it did ("Amendments A-1 and A-2: …"). Keep the older entries exactly. Add the
  amendments to the `cover` row `Depends on` where the document depends on them. The status stays `Ratified`.

What each document received is in `AMENDMENT-INDEX.md`, and the decisions below.

## 5. Decisions already taken (do not reopen)

1. **Order, and breadth kept.** Cybersecurity, then AI, then quantum; all other use cases stay, as modules on the
   same core (A-1 P6). A module outside the three tracks has no gate yet; it is never held back for that reason.
2. **Stage 0 is complete first.** Stage-alpha emits directly (no IR) for every committed target and must pass gate
   G1 on each before Stage-beta begins. No work on tracks S, A or Q begins before Stage-beta compiles itself (A-1 §7;
   A-2 §2, §7). Stage-alpha is frozen and archived at hand-off.
3. **An unsupported target is a fatal error**, never a fallback (A-2 §2).
4. **`gen` is part of Stage-alpha** and behaves identically on every target (A-2 §5.2; Spec1 §20.2).
5. **macOS and Windows use the operating system's own library as the system interface** (A-2 §3.1). Principle P1 is
   about the language, the compiler and the standard library; it is met.
6. **The in-browser playground.** Anyone can try Dhar in a web page with nothing to install. The first version
   compiles on a sandboxed, stateless service to a WebAssembly (WASI) module that runs inside the visitor's browser
   sandbox with a small JavaScript WASI shim; the service keeps no code and no account. The later version runs the
   compiler itself in the browser once Stage-beta targets WebAssembly. It requires the WebAssembly target at G1 (A-2
   §7). Home: Tooling Dhar §5; the service: Stage-epsilon §3.1; legal terms: Hallmark §8.
7. **Community data.** An opt-in mailing list (name and email; phone optional), shown a consent notice, with a copy of
   a survey response sent to the respondent, and the rights to withdraw, access and erasure. Nigeria Data Protection Act
   2023 governs. Home: Hallmark §7; other documents link. The text of the Hallmark must say that it is a statement of
   intent that counsel qualified in Nigerian law must review before any collection begins.
8. **Progress is separate.** The Progress Report series (PR-001, PR-002, …) and the website's status board report
   what exists; they are generated from one status file and are outside the Canon.
9. **Spellings of new keywords are provisional** until the author fixes them (A-1, Ratification notes). Spec1 marks
   each as *provisional*. Proposed spellings: the secret qualifier `veil` and its explicit reveal `unveil`, the
   constant-time select `blend`; the region allocator `arena`; the types `i128`, `u128`, `f16`, `bf16`, `c128`,
   `vec[T; N]`; arithmetic variants as methods `wrap_add`, `sat_add`, `chk_add` (checked returns an `option`).
10. **Targets are built in this order** (The Pact §2.1, a roadmap matter the author may change): the neutral operation
    set and the Linux ARM64 prelude first; then Linux RISC-V 64; then WebAssembly (WASI); then Windows x64; then macOS
    x86-64 and ARM64 last, because gate G1 needs Apple hardware. Linux x86-64 is the host and exists first.

## 6. Checking your work

1. **Build** your key and read the build output for warnings (a heading without a page number means a defect).
2. **Fidelity.** `python3 tools/canon_fidelity.py /home/claude/canon_originals/<original>.pdf docs/canon/pdf/<new>.pdf`.
   Every `REMOVED` run must be deliberate: a sentence you rewrote, a cell you changed, the cover and the revision
   log (those always show up: the cover words, "Revision log"). Anything else is a defect to fix. Report each
   deliberate removal in one line.
3. **Look.** Render with `pdftoppm -r 70 -png FILE.pdf OUT` and look at every page that has a table or a code block.
   Tables are where conversion fails silently: columns shifted, a cell merged into its neighbour.
4. **Read the whole result once**, as the reader: is it still one voice, are the new parts consistent with A-1, A-2,
   Master Index and the other documents' fixed section numbers (§3 above), does any sentence say what *exists*?
5. **Cross-references.** Every `§` you cite exists in the document it names (use the fixed numbers above for sections
   other authors are writing at the same time).

## 7. What an author reports when done

* the files changed, the new version and date;
* each new section with its number;
* the fidelity summary line and every deliberate removal;
* decisions you had to make that the list above did not settle (the author may overrule them);
* anything in another document that contradicts what you wrote.
