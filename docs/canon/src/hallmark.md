---
key: hallmark
file: 15_HallmarkOfDhar_Legal.pdf
kind: canon
volume: "Volume III — Ecosystem, Trust & Adoption"
short: "The Hallmark of Dhar"
title: "The Hallmark of Dhar — Legal, Licensing, IP & Export Posture"
quote: "A hallmark certifies the metal, not the sentiment behind it."
version: "1.1"
date: "October 26, 2026"
status: "Ratified"
running: "DHAR — THE HALLMARK OF DHAR · Legal & IP Posture"
part_label: "THE CANON OF DHAR · VOLUME III"
cover:
  - "Part of": "The Canon of Dhar, Volume III"
  - "Depends on": "Spec1 §18 (foreign), Spec0 §5.2 (defence use case), Tempering Dhar §6.3, Amendments A-1 and A-2"
  - "Audience": "Legal counsel, leadership"
colophon: "General information, not legal advice; consult qualified counsel before relying on any statement in §5, §7 or §8."
revisions:
  - v: "v1.0"
    date: "September 9, 2026"
    text: "first ratified edition."
  - v: "v1.1"
    date: "October 26, 2026"
    text: "Amendments A-1 and A-2: materials outside Dhar's own code, with oracles, model weights and system libraries (§2.1); export review extended to the post-quantum algorithms and the hosted service (§5); new §7, Personal Data and Data Protection, and new §8, Terms of the Hosted Services."
---

# 1. Mandate

Record Dhar's legal posture accurately, at the level this Canon can responsibly state it: general, factual, and explicit about where a real lawyer is required rather than a document. Nothing here is legal advice; it is the map a lawyer would need to be handed before giving any.

Dhar is a language for trustworthy computation: it goes first to cybersecurity, then to artificial intelligence, then to quantum computing, with every other domain kept as modules (Spec0 §5.1, §5.2; Amendment A-1). For the legal posture that has two consequences. The export and dual-use review (§5) falls first on the cryptography that the first and third tracks produce. And a project that asks people for their data, or runs a service for strangers, has to be trustworthy with both in the way it asks the world to trust its compiler (§7, §8).

# 2. License Choice: Why MIT

Dhar's repositories are licensed under MIT, copyright Abdullahi Baba Garba. This Canon ratifies that choice rather than revisiting it, for reasons distinct from Fueling Dhar's business framing: MIT is short, widely understood without specialist interpretation, compatible with nearly every other license an adopter might need to combine Dhar with, and imposes no reciprocal obligation on downstream users — the same property that makes it business-friendly (Fueling Dhar §2) also makes it legally simple to clear through an institutional legal review, which for a government or defence adopter (Spec0 §5.2) is frequently the actual bottleneck, not the license's substance.

## 2.1 Material that is not Dhar's own code

The MIT license covers Dhar's own code. Three kinds of material have terms of their own, and none of them is relicensed by this Canon:

1. **Test oracles.** Outside implementations such as OpenSSL, libsodium, NumPy and Qiskit are used only to check Dhar's answers. They are never linked into, copied into or distributed with a release (Amendment A-1, P1; Stage-delta §3.8), which is meant to keep their licenses from attaching to Dhar's releases. Counsel is asked to confirm that this holds for the way tests are run and published.
2. **Model weights and datasets.** A model or a dataset that an example of the artificial-intelligence track uses carries the license its owner gave it, stated beside the file. Dhar publishes no weights or data it has no right to publish.
3. **The operating system's own library.** On Windows and macOS a program calls the system's interface library (Amendment A-2 §3.1); it does not contain it. Counsel is asked what, if anything, the terms of those systems require of a program that calls them.

# 3. Trademark

“Dhar” and “Kun” function as source identifiers for a specific toolchain and package manager, distinct from the open license covering their code — the same separation Rust (the language, unregistered common-law mark for years before formal registration) and Python (a registered PSF trademark, licensed for community use under a written policy) both maintain. Registering both names in at least the jurisdictions of primary use, with a short, public trademark policy stating that the license to the code and the license to use the names are not the same grant, is recorded here as a required future action, not yet completed by this Canon itself.

# 4. Patent Posture

A defensive, not offensive, posture: Dhar does not initiate patent claims against implementations or users of the language, and should adopt a written non-aggression commitment once an entity exists to hold one — the same shape as the patent grants built into the Apache 2.0 license and the separate non-aggression pledges some foundations layer on top of an MIT-licensed codebase specifically because MIT itself contains no patent grant language. This is identified here as a gap MIT's brevity leaves open, worth closing with a short, separate written pledge rather than by switching licenses.

# 5. Export Control Awareness

This section states what regimes exist and why they are relevant to check against, not a conclusion about whether they apply — that determination requires counsel reviewing the actual, finished software, not a language specification.

- The US Export Administration Regulations (EAR, administered by the Department of Commerce's Bureau of Industry and Security) have historically applied specific treatment to encryption software — std.crypto (Stage-delta §2) is the module this Canon flags as needing that review first, once it exists. Publicly available open-source encryption source code has generally received favorable treatment under EAR (historically via License Exception TSU and a notification requirement), a legacy of the 1990s policy debates over exporting cryptography — relevant background, not a determination that it automatically applies to Dhar's eventual std.crypto.
- The International Traffic in Arms Regulations (ITAR, administered by the Department of State) cover defense articles and services specifically; a general-purpose compiler and standard library are not defense articles by nature, but a specific deployment or customization for a named defence end use, per Spec0 §5.2, is exactly the kind of context where this needs a real legal read rather than an assumption in either direction.
- Dual-use awareness is a standing posture, not a one-time check: it should be revisited whenever std.crypto or a defence-specific integration (Tempering Dhar) reaches a releasable state, not decided once here and forgotten.
- The review covers all of std.crypto, the post-quantum algorithms of Tempering Dhar §6.3 included. This Canon states no conclusion about how any regulation treats them.
- The in-browser playground and its compile service (Stage-epsilon §3.1) make Dhar reachable from any country. Counsel is asked whether that changes the analysis for what is distributed, or for what is hosted.
- A statement that Dhar is “exempt”, “permitted” or “cleared” is made only on counsel's written advice, and the advice is kept with the record of the release it concerns (Tempering Dhar §11).

# 6. Relationship to Other Volumes

| This document assumes | Ratified in |
| --- | --- |
| The license whose business rationale it complements | Fueling Dhar §2 |
| The defence use case that motivates §5 | Spec0 §5.2, Tempering Dhar |
| The crypto module §5 flags for review | Stage-delta §2 |
| Oracle dependencies, which §2.1 keeps out of releases | Stage-delta §3.8 |
| The services whose terms §8 states, and the rule that they keep no source | Stage-epsilon §3.1; Tooling Dhar §5 |
| The lists and surveys that §7 covers | Casting Dhar §5; The Guild of Dhar §4 |

# 7. Personal Data and Data Protection

The project asks people for a small amount of personal data, which they may choose to give: a name, an email address, optionally a phone number, and the answers to a survey. This section states what the project may do with it. It is a statement of intent and a map for counsel. It is not legal advice, and it is not a determination that any law applies or is met.

**Counsel qualified in Nigerian law must review this section, the notice of §7.3 and the processes behind them before any collection begins.** Collection **must not** begin earlier.

## 7.1 The law the Canon treats as relevant

The Canon treats the Nigeria Data Protection Act 2023 (the NDPA), regulated by the Nigeria Data Protection Commission, together with the directives the Commission issues under it, including the General Application and Implementation Directive of 2025, as the law that governs. The points below are the general obligations the Canon has taken from the Act and from published guidance, for counsel to check and to state in detail. None of them is a conclusion that the project complies.

- **Principles.** Processing is lawful, fair and transparent; limited to its stated purpose; minimal; accurate; kept no longer than needed; secure; and the controller can show that it meets these.
- **Consent.** The controller carries the burden of showing that consent was given. Silence or inactivity is not consent. Consent may be withdrawn at any time, and withdrawal does not make earlier processing unlawful.
- **The person's rights.** To confirmation and access, to rectification and erasure, to object, to a copy of their data in electronic form, and to complain to the Commission.
- **Breach.** Where a breach is likely to put people's rights at risk, the controller notifies the Commission within seventy-two hours of becoming aware of it, on the conditions the Act sets. Records of every breach are kept.
- **Transfer abroad.** Personal data leaves Nigeria only on a basis the Act allows, such as adequate protection in the receiving country or contractual safeguards. Where the project's database is hosted is part of this question.
- **Registration.** Controllers and processors of major importance register with the Commission. Whether the project is one depends on a threshold the Commission sets. Counsel confirms it.

## 7.2 What is collected, and why

| Item | Purpose | Choice |
| --- | --- | --- |
| A survey response | To learn how people who might use Dhar work and what they need | Anyone may answer without giving any contact detail |
| Name and email address | To send the person a copy of their survey response, if they ask for one | A separate choice, never pre-ticked |
| Name and email address, for the mailing list | To send news of the project's releases and gates | Opt-in, a separate choice, with the notice of §7.3 |
| Phone number | To reach the person for a follow-up conversation, only if they say so | Optional, and always a separate choice |

A person can answer the survey and decline every contact choice. Data given for one purpose is never used for another, never sold or rented, and never given to a third party for that party's own purposes.

## 7.3 The notice and the record of consent

Before a person gives any contact detail, the notice tells them in plain words: who is responsible and how to reach them; what is collected and why; where it is kept and for how long; who can see it; their rights and how to use them, including withdrawal; and that giving it is optional and that declining costs them nothing. The project keeps a record of each consent: the person's email address, the version of the notice's wording, each choice made, the date and time, and, later, the date of any withdrawal.

## 7.4 Rights in practice

- **Withdrawal.** Every message sent from the mailing list carries a way to withdraw, and withdrawal is confirmed to the person.
- **Access and rectification.** A person can ask what is held about them and receive it, and can have it corrected.
- **Erasure.** A person can ask for their data to be erased. It is removed from the database and from the mailing list, and from backups within a stated period.
- **Copy of a response.** A person who asks for it is sent a copy of their survey response at the email address they gave.
- A named contact answers a request within a stated period. Counsel sets the period.

## 7.5 Safeguards

The database that holds the data **must** allow the public to add a response and **must not** allow the public to read, change or delete any entry; only named administrators, who are the project lead and anyone the project lead names in writing, can read it, and their access is logged. Data is encrypted in transit. A key that gives administrative access to the database is never placed in a repository, a document or a message, and a test that scans the repository **must** enforce this. A breach is handled under Tempering Dhar §8 and the duties of §7.1.

## 7.6 Children

The mailing list and the contact fields are for people aged eighteen or over. The project does not knowingly collect contact details from a child. The Act requires consent from a parent or guardian for a child, and counsel is asked to state the age and the verification that the project must apply.

## 7.7 The playground

The in-browser playground collects no personal data beyond what a request unavoidably carries. It keeps no source code and no identity (Stage-epsilon §3.1). A limit on requests per client is kept only for the length of its window and is not linked to a person.

# 8. Terms of the Hosted Services

The hosted services are the compile service behind the in-browser playground (Stage-epsilon §3.1; Tooling Dhar §5) and any later service of the same kind. The terms below are the ones they operate under. Counsel reviews their wording before the first service opens to the public, as §7 requires of the notice.

1. **Purpose.** The service lets people try Dhar. It is not a place to store code or to run production work.
2. **Acceptable use.** A person does not attack the service or other people through it, does not try to leave its sandbox, does not send unlawful material and does not put it under excessive load. The service can refuse or rate-limit a client (Stage-epsilon §3.1).
3. **Your code.** The code a person submits remains theirs. Submitting it gives the service the right to compile it for that request and no more. The service does not keep it.
4. **What comes back.** The compiled module is the person's. It runs in their own browser, and the service never runs it; the project is not responsible for what a program does when its author runs it.
5. **No warranty.** The service is offered as it is, without promise of availability, and its limits can change. Counsel states how far liability can be limited under Nigerian law.
6. **Security reports.** A weakness found in the service is reported through the channel of Tempering Dhar §8.
7. **Changes and withdrawal.** The terms can change, with the new terms shown on the page, and the service can be withdrawn. Because it holds nothing of a person's, there is nothing to return.
8. **Who answers.** The terms name the person responsible and a contact address, and the law that governs them, as counsel advises.
