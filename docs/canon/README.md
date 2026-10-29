# The Canon of Dhar

The Canon is the forward-looking specification: what Dhar is to become, and the tests that say when it has. It contains no
status; what exists today is on the website and in [../reports/PROGRESS.md](../reports/PROGRESS.md).

The documents are written in Markdown in [src/](src/) and built into the PDFs in [pdf/](pdf/) with one tool, so that every
document has the same look (the website's colours and type) and a source anyone can read and review. **Edit the source,
never the PDF.** The working manual for authors is [AUTHORING.md](AUTHORING.md).

## The documents

Seventeen documents: the Master Index, the fourteen documents of Volumes I to IV, and Amendments A-1 and A-2. All are
dated 26 October 2026; each document's own revision log gives its earlier editions.

| Volume | Document | Version | Standing | PDF |
| --- | --- | --- | --- | --- |
| | **Master Index** | 1.1 | Ratified | [Canon_of_Dhar_Master_Index.pdf](pdf/Canon_of_Dhar_Master_Index.pdf) |
| I: Vision and Specification | Spec0: Overview and Vision | 1.3 | Ratified | [Spec0_Overview_and_Vision.pdf](pdf/Spec0_Overview_and_Vision.pdf) |
| | Spec1: Language Specification | 3.2 | Ratified | [Spec1_Language_Specification.pdf](pdf/Spec1_Language_Specification.pdf) |
| II: Engineering Roadmap | Stage-alpha: Forge of Dhar | 1.1 | Ratified | [StageAlpha_Forge_of_Dhar.pdf](pdf/StageAlpha_Forge_of_Dhar.pdf) |
| | Stage-beta: Honing Dhar | 1.1 | Ratified | [6_StageBeta_Honing_Dhar.pdf](pdf/6_StageBeta_Honing_Dhar.pdf) |
| | Stage-gamma: Optimizing Dhar | 1.1 | Ratified | [7_StageGamma_Optimizing_Dhar.pdf](pdf/7_StageGamma_Optimizing_Dhar.pdf) |
| | Stage-delta: Gearing Dhar | 2.2 | Ratified | [8_StageDelta_Gearing_Dhar.pdf](pdf/8_StageDelta_Gearing_Dhar.pdf) |
| | Stage-epsilon: Deploying Dhar | 1.1 | Ratified | [9_StageEpsilon_Deploying_Dhar.pdf](pdf/9_StageEpsilon_Deploying_Dhar.pdf) |
| III: Ecosystem, Trust and Adoption | Tooling Dhar: Developer Tools, Diagnostics and the Playground | 1.0 | **Proposed** | [10_ToolingDhar_Developer_Experience.pdf](pdf/10_ToolingDhar_Developer_Experience.pdf) |
| | The Guild of Dhar: Governance | 1.1 | Ratified | [11_GuildOfDhar_Governance.pdf](pdf/11_GuildOfDhar_Governance.pdf) |
| | Tempering Dhar: Security and Assurance | 1.1 | Ratified | [12_TemperingDhar_Security_Assurance.pdf](pdf/12_TemperingDhar_Security_Assurance.pdf) |
| | Casting Dhar: Adoption and Education | 1.1 | Ratified | [13_CastingDhar_Adoption_Education.pdf](pdf/13_CastingDhar_Adoption_Education.pdf) |
| | Fueling Dhar: Business and Funding | 1.1 | Ratified | [14_FuelingDhar_Business_Funding.pdf](pdf/14_FuelingDhar_Business_Funding.pdf) |
| | The Hallmark of Dhar: Legal | 1.1 | Ratified | [15_HallmarkOfDhar_Legal.pdf](pdf/15_HallmarkOfDhar_Legal.pdf) |
| IV: Program Management | The Pact of Developing Dhar | 1.1 | Ratified | [ThePact_Program_Management.pdf](pdf/ThePact_Program_Management.pdf) |
| Amendments | A-1: Direction | 1.0 | Ratified | [Amendment_A1_Direction.pdf](pdf/Amendment_A1_Direction.pdf) |
| | A-2: Stage 0 Targets | 1.0 | Ratified | [Amendment_A2_Stage0_Targets.pdf](pdf/Amendment_A2_Stage0_Targets.pdf) |

**Tooling Dhar is Proposed, not Ratified.** It was reserved in the Master Index and had no text; it was written under the
two amendments and is awaiting the author's ratification (Master Index §3.2: Draft, Proposed, Ratified). Amendments A-1 and
A-2 are Ratified on the author's instruction of 25 October 2026 to apply them to every document.

The numbers in the table are checked against the sources by `tests/run_tests.py`.

## What the amendments decided

* **A-1, Direction.** Dhar is a language for trustworthy computation. It goes first to cybersecurity, then to artificial
  intelligence, then to quantum computing. Every other domain (systems and hardware, web and backend, data, blockchain and
  Web3, and the rest) stays, as modules on the same core (principle P6). Principles P1 to P6, design requirements R1 to R5
  for the self-hosting compiler, and acceptance gates S1 to S4, A1 to A4 and Q1 to Q4.
* **A-2, Stage 0 targets.** The first compiler produces programs for every processor and operating system the Canon names
  (one list, A-2 §3.1), with the print function `gen`, and passes the gates G0 (emulator) and G1 (real system) on each
  before the self-hosting compiler begins. An unsupported target is a fatal error.

## How the Canon changes

Master Index §10: a ratified document changes only through a new minor or major version, with a one-line reason in its
revision log. "One rule, one home" (§3.4) decides where each rule goes: keyword semantics in Spec1, a security guarantee in
Tempering Dhar, a licensing, export or data-protection decision in The Hallmark of Dhar, the list of targets in A-2, and
everywhere else links back. [AMENDMENT-INDEX.md](AMENDMENT-INDEX.md) lists what each document received and where.

The September 2026 editions the author supplied are in this repository's git history (the commits before the Canon was
rebuilt from sources). Every new version keeps the revision log of the one before it.

## Build and check

```
python3 tools/build_canon.py --list                 # every source, its version, its PDF
python3 tools/build_canon.py KEY                    # build one document
python3 tools/build_canon.py                        # build all
python3 tools/build_canon.py --verify               # is every PDF built from the present sources?
python3 tools/canon_fidelity.py ORIGINAL.pdf NEW.pdf   # what changed in the words between two PDFs
python3 tests/run_tests.py                          # includes the Canon checks
```

`pdf/MANIFEST.json` records, for each PDF, the hash of its source and of the builder, so `--verify` fails if a source or
the look changed and the PDFs were not rebuilt.
