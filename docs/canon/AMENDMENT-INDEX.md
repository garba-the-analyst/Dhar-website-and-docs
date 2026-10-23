# Canon amendment index

The Canon's working principle is that a correction goes into every affected document, not only the one where it began.
This index is the list of what each document must receive, so none is missed. It lists amendments, not status; status
never goes into the Canon (Master Index §2).

**How amendments are issued.** Master Index §10: a ratified document changes only through a new minor or major version
with a one-line reason in its revision log. So each document below receives a **v1.1** that carries the amendment and a
revision-log line naming it. §3.4, "one rule, one home", decides where a rule is ratified: a keyword in Spec1, a security
guarantee in Tempering Dhar, a licensing or export decision in The Hallmark of Dhar. Everywhere else links back instead of
restating.

**What was available.** The 13 documents supplied as PDFs (see [README.md](README.md)) and the Master Index, which fixes
each document's role. **Tooling Dhar was not supplied** and needs to be written. Where a row says *to confirm*, the
amendment is placed by the Master Index's description of the document, and its exact section is chosen when the document
itself is edited.

## Amendments that apply to every document

* **X1. Direction paragraph.** Where the document states Dhar's purpose, add the direction paragraph of A-1 §2 (by
  reference to Spec0, where it is ratified).
* **X2. Order of domains.** Wherever a document lists the domains Dhar serves, order them: cybersecurity, then AI, then
  quantum, then the rest.
* **X3. Claims name their gate.** A claim about security, speed or correctness points at the A-1 gate that backs it, or
  is worded as an aim.
* **X4. Revision log.** One line per amendment, naming it (for example "v1.1: Amendment A-1, direction").

## Per document

| Volume | Document | Role (Master Index) | Amendment | Source of the rule |
| --- | --- | --- | --- | --- |
| Master Index | Canon of Dhar | Index, conventions | List A-1 and A-2 and the new documents; add "direction" to §1; add the amendment to §10's examples. | A-1, A-2 |
| I | **Spec0** | Problem, thesis, architecture, use cases, positioning | Add principles P1 to P5 (A-1 §3) and the three tracks to the use cases; state that outside implementations are test oracles only (independence); in §4 (architecture) state that a back end exists per target and that Stage-alpha also emits directly for its targets (A-2). | A-1, A-2 |
| I | **Spec1** | Full lexical, syntactic and semantic rules | (a) Numeric types: `f16`, `bf16`, a complex pair, fixed-width vector types, and wrapping, saturating and checked arithmetic. (b) A *secret* qualifier with the S2 rules and an explicit reveal; constant-time select and rotate. (c) Extend the bounds-checking rule from `raw[N]` to every slice, tensor and view. (d) Define `sys` by name (`sys.write`, `sys.exit`) in addition to by number, so one program can target several operating systems (Linux x86-64 write is 1, Linux ARM64 and RISC-V write is 64, WASI uses `fd_write`). (e) `give` takes a value or one operation. Keyword names are provisional until ratified. | A-1 §4 to §6, A-2 |
| II | **Stage-alpha** | Specify the bootstrap compiler | §2.1 and §2.3 say Stage-alpha targets "x86-64 directly and only" and that the IR boundary begins at Stage-beta. Amend to: Stage-alpha emits directly for the architectures and platforms the Canon names (x86-64 on Linux and Windows, ARM64, RISC-V, WebAssembly/WASI), still with no IR; an unsupported target is a fatal error, never a fallback; §4 gains a criterion that the conformance battery passes on every supported target; `give`'s accepted shapes; `gen` emits exactly its text. | A-2 |
| II | **Stage-beta** | Self-hosting compiler | Add R1 to R5 (A-1 §8); the back-end list and the target-description tables; the S4 build gates (fixed point, diverse double-compilation, reproducibility); Stage-alpha archived after hand-off. The back ends re-implemented on the IR must produce programs that pass the same battery Stage-alpha's did. | A-1, A-2 |
| II | **Stage-gamma** | Optimizing back end: SSA, register allocation, passes | Add the constant-time-preserving rule (R2) as an invariant every pass keeps, with a test per pass; deterministic floating point by default; vectorisation as a goal for the A4 kernels. | A-1 |
| II | **Stage-delta** | Standard library and tooling; Kun | Add `std.crypto` (S3, then Q1), `std.num` and `std.tensor` (A1, A2), `std.quantum` (Q2, Q3); the documented weight-file format for A3; conformance vectors as the library's own tests. | A-1 |
| II | **Stage-epsilon** | Production hardening: cross-compilation, fuzzing, reproducible builds, signing | Add reproducible builds, bill of materials and signing (S4) as release gates; constant-time timing tests and fuzzing in continuous integration; a migration path for post-quantum algorithms; cross-compilation matrix for every target. | A-1, A-2 |
| III | **Tooling Dhar** | Editor/LSP, documentation generator, build system, error messages | *Not supplied.* When written: `dhar test --vectors`, `dhar verify-build`, `dhar sbom`, an OpenQASM export tool, and diagnostics that name the secret-flow rule a program breaks. | A-1 |
| III | **The Guild of Dhar** | Governance: RFC process, contribution rules, conduct, decision rights | A two-reviewer rule and a disclosure process for code in `std.crypto`; an RFC required to change the secret rules; maintainer admission at the Stage-beta self-hosting gate (the author's stated plan, to confirm). | A-1 |
| III | **Tempering Dhar** | Security and assurance: threat model, memory-safety guarantees, supply chain, certification | The home of the S1 to S4 guarantees and of the claims rule (A-1 §10): what may be said and which gate backs it. Add constant-time and side-channel limits to the threat model; the diverse double-compilation argument; certification pathways cite passed gates. | A-1 |
| III | **Casting Dhar** | Adoption, education, Pan-African reach, hardware accessibility, partnerships | Security-first curricula (secure coding, cryptography engineering); inference of small models on modest hardware as the hardware-accessibility case for Track A; post-quantum readiness as a teaching and partnership theme. | A-1 |
| III | **Fueling Dhar** | Business model, sustainability, funding, licensing strategy | Funding lines by track (security, AI, post-quantum), with independent audits of `std.crypto` as a named line. | A-1 |
| III | **The Hallmark of Dhar** | Legal, licensing, IP, export posture, dual-use | Cryptography export and dual-use handling for `std.crypto` and security tooling; licensing of model weights and datasets used by Track A; the rule that a public trust claim needs a passed gate. | A-1 |
| IV | **The Pact of Developing Dhar** | Roadmap timeline, risk register, adoption metrics | The honesty clause (four status words, one source of truth, claims need evidence, a correction is a new entry); the A-1 gates as roadmap milestones in track order; new risks (constant-time regressions, back-end divergence across targets, unverified emulator-only targets); metrics that count passed gates. | A-1, A-2 |

## What is done and what is not

* Done: this index, Amendment A-1, the rules in `../HONESTY.md`.
* Next: Amendment A-2 (Stage 0 targets), then the v1.1 documents themselves. They are not edited in these PDFs yet.
* Open for the author: ratify A-1 and A-2 (the Master Index §3.2 process: Draft, Proposed, Ratified); supply or commission
  Tooling Dhar.
