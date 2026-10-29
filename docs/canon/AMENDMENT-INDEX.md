# Canon amendment index

The Canon's working principle is that a correction goes into every affected document, not only the one where it began.
This index records what each document received from Amendments A-1 (direction) and A-2 (Stage 0 targets), and where. It
lists amendments, not status; status never goes into the Canon (Master Index §2).

**How amendments were issued.** Master Index §10: a ratified document changes only through a new minor or major version
with a one-line reason in its revision log. So each document received a new version, dated 26 October 2026, whose
revision-log line is the right-hand column below, copied word for word (`tests/run_tests.py` checks that the two agree).
§3.4, "one rule, one home", decided where each rule is ratified: a keyword in Spec1, a security guarantee in Tempering
Dhar, a licensing, export or data-protection decision in The Hallmark of Dhar, the list of targets in Amendment A-2 §3.1.
Everywhere else links back instead of restating. The fixed section numbers that the documents cite one another by are in
[AUTHORING.md](AUTHORING.md) §3.

## Amendments that apply to every document

* **X1. Direction paragraph.** Where the document states Dhar's purpose, a short paragraph in its own terms: trustworthy
  computation; cybersecurity, then artificial intelligence, then quantum computing; every other domain kept as modules (P6).
* **X2. Order of domains.** Wherever a document lists domains: cybersecurity, then AI, then quantum, then the rest. Nothing
  is removed.
* **X3. Claims name their gate.** A claim about security, speed or correctness points at the gate that backs it (A-1 §9,
  A-2 §6) or is worded as an aim (Master Index §3.6; Tempering Dhar §11).
* **X4. Revision log.** One line per amendment, naming it.

## What each document received

| Volume | Document | Version | Revision-log line |
| --- | --- | --- | --- |
| Master Index | **Canon of Dhar** | v1.1 | Amendments A-1 (direction) and A-2 (Stage 0 targets) registered; §3.5 to §3.8 added (amendments, claims, presentation, stage names); the direction added to §1; Tooling Dhar entered as written; reading paths and §10 updated. |
| I | **Spec0** | v1.3 | Amendments A-1 and A-2: the direction (§1, §5.1), breadth kept as modules (§5.2), the principles and gates (§5.3), the targets (§4.1), the stage plan (§8) and the reading list (§9); statements about other languages (§2.2, §7), the intermediate representation (§3, §4) and Spec1 references (§6) corrected. |
| I | **Spec1** | v3.2 | Amendments A-1 and A-2: numeric types for models and cryptography (§4.7), secret values (§14.5), arenas (§14.6), bounds checking extended to every slice, tensor and view (§14.4), sys across targets (§20.1), the print function gen (§20.2); four keywords added with provisional spellings (50 reserved words); overflow, division and conversion rules stated for the numeric types. |
| II | **Stage-alpha** | v1.1 | Amendment A-2 (Stage 0 targets): direct emission for every committed target, the neutral operation set and target preludes (§3.1), the system interface and gen on every target (§3.2), the conformance battery and the gates G0 and G1 (§3.3), exit criteria and a frozen hand-off (§4, §5). Amendment A-1: the direction (§1) and the order of the tracks (§5). |
| II | **Stage-beta** | v1.1 | Amendment A-1: design requirements R1 to R5 for the intermediate representation (§3.1) and the build gates S4 (§4.1). Amendment A-2: back ends for every committed target re-implemented on the IR and held to the same battery (§2.1, §4.2); a frozen Stage-alpha (§5). Cross-references to Spec1 corrected to the current section numbers. |
| II | **Stage-gamma** | v1.1 | Amendment A-1: the constant-time-preserving rule as an invariant of every pass, with a test per pass (§3.1); deterministic floating point by default; the performance commitment worded as an aim whose evidence is gate A4 (§1, §4). |
| II | **Stage-delta** | v2.2 | Amendment A-1: the domain modules, in the order of the tracks, each with its gate (§2.1); numerics, tensors and quantum modules; test oracles are never dependencies (§3.8); acceptance criteria for the module gates (§7). Reference to Spec1's collections corrected to §13. |
| II | **Stage-epsilon** | v1.1 | Amendment A-2: cross-compilation for every committed target (§2, §4). Amendment A-1: release gates S4, timing tests, post-quantum migration (§3.2); the hosted compile service of the in-browser playground (§3.1); acceptance criteria (§4). |
| III | **Tooling Dhar** | v1.0 | First edition, written under Amendments A-1 and A-2: diagnostics, the language server, the commands and the documentation generator, and the in-browser playground (§5). Proposed for ratification by the project lead. |
| III | **The Guild of Dhar** | v1.1 | Amendments A-1 and A-2: decision rights over amendments, gates, targets and the rule for claims, with review of security-critical changes and maintainers of the tracks (§2), the scope of the RFC process (§3), contribution rules on test oracles, claims and community data (§4), and the references in §7. |
| III | **Tempering Dhar** | v1.1 | Amendments A-1 and A-2: the rule for claims made a section of its own (§11), the threat model widened (§2, §3.2, §3.3), the two-compiler check specified as gate S4 (§5.3, §5.4), constant time, clearing and post-quantum cryptography specified (§6), acceptance criteria extended (§9), and Spec1 cross-references corrected. |
| III | **Casting Dhar** | v1.1 | Amendments A-1 and A-2: curricula in the order of the tracks (§2.4), the in-browser playground for learners (§2.5), hardware reach through the targets and small-model inference (§3.2), community data and the mailing list (§5), metrics per track (§6), and corrected references (§2.2, §2.3, §7). |
| III | **Fueling Dhar** | v1.1 | Amendments A-1 and A-2: funding lines by deliverable and gate, including the independent audit of std.crypto, the device lab for gate G1 and the hosted playground (§3.4), the modules as the broad base of sustainability (§4), and corrected references (§2, §5). |
| III | **The Hallmark of Dhar** | v1.1 | Amendments A-1 and A-2: materials outside Dhar's own code, with oracles, model weights and system libraries (§2.1); export review extended to the post-quantum algorithms and the hosted service (§5); new §7, Personal Data and Data Protection, and new §8, Terms of the Hosted Services. |
| IV | **The Pact of Developing Dhar** | v1.1 | Amendments A-1 and A-2: the roadmap restated with every committed target at gate G1 (§2), the order of the targets (§2.1), the gates as milestones in the order of the tracks (§2.2), risks added or restated (§3), and metrics counted by gate (§4). |
| Amendments | **Amendment A-1** | v1.0 | Ratified on the author's instruction of October 25, 2026 to apply every amendment to every Canon document. Principle P6 added (breadth is kept, as modules); §1, §2, §7, §8 and §10 aligned with Amendment A-2 and with P6; ratification block completed. |
| Amendments | **Amendment A-2** | v1.0 | First edition. Records the author's decision of October 23, 2026 (the ARM64, RISC-V and WebAssembly back ends are built in Stage 0, not postponed to Stage 1) and its extension of October 25, 2026 (every processor and operating system the Canon names, with the print function gen, in Stage 0 before Stage-beta begins). Ratified on the author's instruction of October 25, 2026. |

## Decisions taken while applying the amendments

These were not settled by A-1 or A-2 and are recorded so the author can overrule them. Each is a one-line change in the
document named.

* **Tooling Dhar is Proposed**, not Ratified: it had no text before. Ratifying it is the author's act (Master Index §3.2).
* **Plain integer overflow must fail safely** (Spec1 §4.7): the default arithmetic does not wrap silently; wrapping,
  saturating and checked forms are separate, named operations.
* **Spellings of new keywords are provisional** (Spec1 §4.7, §14.5, §14.6, §20.1): the secret qualifier `veil` and its
  explicit reveal `unveil`, the constant-time select `blend`, the region allocator `arena`, the wide and vector types.
* **The order of the targets** is The Pact §2.1, a roadmap matter the author may change: Linux ARM64, Linux RISC-V 64,
  WebAssembly (WASI), Windows x64, then macOS x86-64 and ARM64 last. macOS is in the committed list and iOS is not
  targeted (A-2 §3.1, §3.3); both are proposals the author may revise by revising A-2.
* **Open: a defect found in the frozen Stage-alpha.** A-2 §2 freezes Stage-alpha at hand-off and says nothing about a
  defect found afterwards. The working assumption is a new archived version with its hash recorded, never an edit of the
  frozen one. The Canon does not say so yet; the author decides, and A-2 or Stage-alpha §5 is revised.
* **The Guild** (two-reviewer rule for security-critical code, maintainers of each track, The Guild of Dhar §2) and
  **The Hallmark §7** (personal data under the Nigeria Data Protection Act 2023) are proposals for the author and for
  counsel qualified in Nigerian law; Hallmark §7 must be reviewed by counsel before any data is collected.
* **Spec0 §3, pillar 1** says the parser is not written in assembly. Stage-alpha's parser is. The sentence was left as the
  author wrote it; the conflict is the author's to resolve.
