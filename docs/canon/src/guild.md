---
key: guild
file: 11_GuildOfDhar_Governance.pdf
kind: canon
volume: "Volume III — Ecosystem, Trust & Adoption"
short: "The Guild of Dhar"
title: "The Guild of Dhar — Governance & Community"
quote: "A guild trains the next smith. It doesn't gatekeep the forge."
version: "1.1"
date: "October 26, 2026"
status: "Ratified"
running: "DHAR — THE GUILD OF DHAR · Governance & Community"
part_label: "THE CANON OF DHAR · VOLUME III"
cover:
  - "Part of": "The Canon of Dhar, Volume III"
  - "Depends on": "Master Index §3.2 (status), §10 (amendment); Amendments A-1 and A-2"
  - "Audience": "Contributors, community leads"
revisions:
  - v: "v1.0"
    date: "September 9, 2026"
    text: "first ratified edition."
  - v: "v1.1"
    date: "October 26, 2026"
    text: "Amendments A-1 and A-2: decision rights over amendments, gates, targets and the rule for claims, with review of security-critical changes and maintainers of the tracks (§2), the scope of the RFC process (§3), contribution rules on test oracles, claims and community data (§4), and the references in §7."
---

# 1. Mandate

Give Dhar a governance model that matches where the project actually is, not where it wishes to be: a founder-led effort that decides in the open, with a stated, credible path to broader stewardship as contributors arrive. This document does not invent a new amendment process for the Canon — the Master Index §10 already defines Draft → Proposed → Ratified. The Guild specifies who gets to move a document through those states, and how a contributor becomes one of the people who can.

Dhar is a language for trustworthy computation: it goes first to cybersecurity, then to artificial intelligence, then to quantum computing, with every other domain kept as modules (Spec0 §5.1, §5.2; Amendment A-1). The Guild's part is to make sure the people who decide about that direction, and about the code that carries it, can be named, and that a contributor in any domain has a way in.

# 2. Decision Rights

Every document in this Canon reaches Ratified status by the project lead's acceptance (Master Index §10). That is stated plainly rather than dressed up as something more distributed than it is: a governance document that pretends a one-person project already has a steering committee would be exactly the kind of overclaiming Tempering Dhar §1 and Casting Dhar §1 both explicitly rule out elsewhere in this Canon. The obligation this places on the project lead is to use §3's RFC process for any change a contributor proposes, rather than deciding informally outside a record anyone else can review.

## 2.1 Who decides what

| Decision | Decided by | Home of the rule |
| --- | --- | --- |
| Ratifying an amendment, or a new version of a document | The project lead, after the RFC process of §3 where a design decision is in it | Master Index §10 |
| Adding, changing or withdrawing a gate | The project lead, by an amendment, after an RFC | Amendment A-1 §9; Amendment A-2 §6 |
| Promoting a candidate target to the committed list, or moving one back | The project lead, by revising Amendment A-2 §3, after an RFC | Amendment A-2 §3 |
| The order in which the targets are built | The project lead, by revising The Pact §2.1 | The Pact of Developing Dhar §2.1 |
| The spelling of a new keyword | The project lead, after an RFC | Spec1 |
| A rule about secret values, or the rule for claims | The project lead, after an RFC that the maintainer of the security track has reviewed, where there is one | Spec1 §14.5; Tempering Dhar §11 |

## 2.2 Review of security-critical changes

A change to `std.crypto`, to the rules for secret values (Spec1 §14.5) or to the clearing of secrets is reviewed by at least two people other than its author before it is merged. Where fewer than two reviewers exist, the change is not released until an outside reviewer has been found, and the gap is recorded with the change. A security-critical change that fails a gate (Amendment A-1 §9) is not merged, whoever reviewed it.

## 2.3 Maintainers of the tracks

When Stage-beta compiles itself and the work of the three tracks begins (Amendment A-1 §7), each track — cybersecurity, artificial intelligence, quantum computing — has a named maintainer, who reviews changes to that track's code and brings its RFCs. The project lead names the first maintainers; later ones are admitted by the path of §4. A track with no maintainer is the project lead's. Modules outside the three tracks have maintainers by the same path, and carry no lesser standing (Amendment A-1, P6).

# 3. The RFC Process

A Request for Comments is how a change to a Ratified document moves back to Proposed. It exists specifically for changes with a design decision in them — a new keyword, a changed default, a new Stage-delta module, a rule about secret values, the rule for claims, a gate, or a change to the list of targets — not for typo fixes or clarifications, which may be corrected directly with a note in the affected document's own revision log.

1. Written proposal: what changes, in which document(s), and why — including what alternative was considered and rejected, following the same discipline Spec1's specification defaults already model.
2. Open comment period on the proposal, minimum two weeks, extended once if active discussion is ongoing when it would otherwise close.
3. Disposition: accepted, rejected, or returned for revision, with the reasoning recorded — a rejected RFC is kept, not deleted, so the same proposal isn't re-litigated from zero a year later.
4. An accepted RFC is implemented as a version bump to the affected document(s), with the RFC referenced by number in that document's revision log entry.

This is deliberately close to the process Rust and Python both use for language-level changes (Rust's RFC repository; Python's PEP process) — not copied for its own sake, but because both have run this exact process at scale for over a decade and the failure modes it avoids are well understood.

# 4. Contribution Guidelines
- Every commit carries a Developer Certificate of Origin sign-off (the same lightweight mechanism the Linux kernel uses) — a one-line attestation that the contributor has the right to submit the code under Dhar's license. For a project naming defence and critical-infrastructure adopters among its intended users (Spec0 §5.2), being able to show exactly who contributed what, and that they were entitled to, is not paperwork for its own sake.
- Code contributions to any Volume II stage follow that stage's own required architecture (one-definition-per-file, per Stage-alpha §3 and Stage-beta §3) — the Guild does not introduce a separate contribution standard when the engineering documents already ratified one.
- A change to a back end passes the conformance battery on the target it changes (Stage-alpha §3.3), and a change that touches the code of a secret-handling routine is reviewed under §2.2.
- Outside implementations (OpenSSL, libsodium, NumPy, Qiskit and the like) are used only as test oracles. A contribution never links, copies or distributes one with Dhar, and one that puts an oracle dependency into a build of the core is refused (Amendment A-1, P1; Stage-delta §3.8).
- A contribution that adds a statement about security, speed or correctness, or about a target, names its gate or words the statement as an aim (Tempering Dhar §11).
- A first-time contributor's path in: a labeled backlog of scoped, real gaps (Casting Dhar §5 already commits to this), a review within a stated window, and a named point of contact — not a pull request into silence. The path is open in every domain of Spec0 §5.2.
- Names, email addresses and optional phone numbers that people give the project, for the mailing list or a survey, are governed by The Hallmark of Dhar §7 and not by this document.

# 5. Code of Conduct

Participation is open regardless of nationality, background, or company affiliation, and is expected to stay technical: disagreement is with a proposal, not a person. Reports of conduct that falls short go to a named contact outside the immediate dispute, with a stated response window. This section stays short deliberately — a code of conduct that takes longer to read than the contribution guide gets read less, not more.

# 6. Toward a Foundation

A single-maintainer project is a real bus-factor risk (formalized in The Pact of Developing Dhar's risk register, Volume IV) that this document does not pretend otherwise. The realistic path, once Dhar has paid contributors, corporate users, or grant funding (Fueling Dhar) to steward: a small foundation modeled on the already-proven examples — the Rust Foundation (corporate-membership funded, formed 2021) or the Python Software Foundation (grants, sponsorship, and conference revenue) — rather than a bespoke structure invented from nothing. This Canon does not found that organization prematurely; it records the trigger condition (sustained outside funding or a multi-employer contributor base) so the transition is a planned decision, not a scramble.

# 7. Relationship to Other Volumes

| This document assumes | Ratified in |
| --- | --- |
| The amendment process it wires the RFC into | Master Index §3.2, §10 |
| The engineering standards contributions must follow | Stage-alpha §3, Stage-beta §3 |
| The contributor pipeline referenced in §4 | Casting Dhar §5 |
| The bus-factor risk formalized in §6 | The Pact of Developing Dhar §3 |
| The gates and the targets whose changes §2.1 governs | Amendment A-1 §9; Amendment A-2 §3, §6; The Pact §2.1 |
| The rule for claims that contributions follow | Tempering Dhar §11 |
| The handling of community members' personal data | The Hallmark of Dhar §7 |
