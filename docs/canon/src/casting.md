---
key: casting
file: 13_CastingDhar_Adoption_Education.pdf
kind: canon
volume: "Volume III — Ecosystem, Trust & Adoption"
short: "Casting Dhar"
title: "Casting Dhar — Adoption, Education & Pan-African Strategy"
quote: "Cast far enough, and it reaches people who were never going to come looking for it."
version: "1.1"
date: "October 26, 2026"
status: "Ratified"
running: "DHAR — CASTING DHAR · Adoption & Pan-African Strategy"
part_label: "THE CANON OF DHAR · VOLUME III"
contents: true
cover:
  - "Part of": "The Canon of Dhar, Volume III"
  - "Depends on": "Spec0 §2.1, Stage-delta §3 (Kun), Amendments A-1 and A-2"
  - "Audience": "Education partners, policymakers, developer relations"
colophon: "Grounded in Nigeria's 3MTT programme (Federal Ministry of Communications, Innovation & Digital Economy / NITDA, launched 2023) and the Smart Africa Alliance (founded 2013, AU-endorsed 2014)."
revisions:
  - v: "v1.0"
    date: "September 9, 2026"
    text: "first ratified edition."
  - v: "v1.1"
    date: "October 26, 2026"
    text: "Amendments A-1 and A-2: curricula in the order of the tracks (§2.4), the in-browser playground for learners (§2.5), hardware reach through the targets and small-model inference (§3.2), community data and the mailing list (§5), metrics per track (§6), and corrected references (§2.2, §2.3, §7)."
---

# 1. Mandate

Make Dhar something Nigerian and African developers actually encounter, learn, and choose — not a language that exists only inside this Canon. Spec0 §2.1 states the motivation; this document turns it into a plan evaluated against institutions and programs that already exist, not invented from nothing. Every claim below is checked against a real, currently operating initiative; where this Canon could not verify a specific fact, it says so rather than filling the gap with something that sounds right.

Dhar is a language for trustworthy computation: it goes first to cybersecurity, then to artificial intelligence, then to quantum computing, with every other domain kept as modules (Spec0 §5.1, §5.2; Amendment A-1). For learning that means the first unit a learner meets is about writing code that survives hostile input, the next about running a small model on modest hardware, the next about cryptography for the quantum era, and the rest of the language is taught as modules beside them (§2.4).

# 2. Education & Curriculum Integration

## 2.1 A module inside 3MTT, not a program competing with it

Nigeria's 3 Million Technical Talent programme (3MTT), launched by the Federal Ministry of Communications, Innovation & Digital Economy with NITDA in late 2023, is already the largest structure of its kind in the country: Phase 1 trained 31,270 fellows across all 36 states and the FCT against a 30,000 target, Phase 2 is running 300,000 fellows through three cohorts, and the programme reports over 135,000 people trained directly with more than 300,000 additional learners reached through community platforms. It already runs a Software Development track and a Cybersecurity track, and it already solves the distribution problem — reach, government backing, a talent registry connecting graduates to jobs — that a new program would otherwise have to build from zero.

The realistic strategy is therefore not a competing “Dhar Academy,” but a Dhar module contributed into 3MTT's existing Software Development and Cybersecurity tracks: a short, self-contained unit built around the same bootstrap story this Canon itself tells — lexer, parser, type checker, code generator, self-hosting — which is a real compilers curriculum, not a marketing exercise, and doubles as a demonstration of the memory-safety guarantees Tempering Dhar specifies. It goes first into the Cybersecurity track, because cybersecurity is where Dhar goes first (Spec0 §5.1).

## 2.2 University & polytechnic partnerships

This Canon does not name specific institutions here, since doing so without a confirmed partnership would be exactly the kind of unverified claim §1 rules out. The model instead: an elective module or a compilers-course project pack (Stage-alpha's bootstrap pipeline is a ready-made syllabus), offered to computer science and computer engineering departments, with final-year and postgraduate project sponsorship (implementing a Stage-delta standard-library module, or a new backend for a candidate target of Amendment A-2 §3.2, per Spec0 §4.1, are both real, scoped, publishable research problems, not busywork).

## 2.3 Why Dhar fits as a second language, not a first

Spec1's explicit typing and systems-level constructs (§14: view/grab/own, raw memory) assume the learner already has a first language's worth of programming concepts. The concise/explicit split Spec1 §4.3–4.4 specifies (inferred by default, explicit when it matters, wild when genuinely dynamic) is deliberately built so that a learner arriving from Python or JavaScript reads Dhar's concise form immediately, then grows into the explicit, systems-level form as the course does — matching how 3MTT's own tracks are sequenced rather than requiring a learner to restart from zero.

## 2.4 Curricula in the order of the tracks

The units follow the order in which Dhar itself is built (Amendment A-1 §7):

1. **Security first.** Writing code that handles hostile input: checked indexing and ownership (Spec1 §14), secret values that the compiler checks (Spec1 §14.5), what constant time means and how the timing test shows it (Tempering Dhar §6.1). It suits the Cybersecurity track of §2.1.
2. **Artificial intelligence second.** Running a small trained network with memory use known before the run: the numeric types for models, fixed-shape tensors and arenas (Spec1 §4.7, §14.6). It is chosen for learners whose machines are modest (§3.2).
3. **Quantum computing third.** Post-quantum cryptography read against the NIST standards it implements (Tempering Dhar §6.3), and quantum circuits written as ordinary data and checked by a simulator (Amendment A-1, Q2 and Q3).

A unit is offered only when the gate of its track has passed (Amendment A-1 §9), so that what is taught is what has been tested. Web and backend development, data, blockchain and Web3, systems and hardware are taught as modules on the same core and need none of the three units first (Amendment A-1, P6).

## 2.5 Try it with nothing installed

The in-browser playground (Tooling Dhar §5) lets a learner write and run a Dhar program in a web page with nothing to install, which removes the first obstacle in a classroom with shared or older machines. Its first version sends the program to a hosted compile service and so needs a connection each time a program is run; the later version runs the compiler itself in the page, once Stage-beta targets WebAssembly, and aims to need a connection only to load the page (Stage-epsilon §3.1). A learner who has installed the toolchain runs exactly the same program on any committed target (Amendment A-2 §3.1).

# 3. Pan-African Reach

## 3.1 Smart Africa as the distribution structure, not a new one

Smart Africa, founded in 2013 by seven heads of state and endorsed by the African Union in 2014, now spans roughly 40 member states representing over a billion people, with a stated vision of a Single Digital Market in Africa by 2030. The African Union's own Digital Transformation Strategy for Africa 2020–2030, which Smart Africa implements, states as an explicit objective ensuring “Africa's ownership of modern tools of digital management” — language that could be lifted directly from Spec0 §2.1 and was written without any knowledge of this project. The pan-African strategy this Canon commits to is aligning with that existing structure's digital-skills and e-governance workstreams rather than building a country-by-country outreach effort from scratch; a continent-wide alliance already exists and already has the mandate.

## 3.2 Hardware & connectivity reality

A meaningful share of the continent's developers work on older, lower-specification hardware and less consistent power and connectivity than the markets most developer tooling is designed against by default. This Canon records it as a design requirement, not an afterthought: Kun (Stage-delta §3.3) must resolve and reuse a lockfile entirely from local cache with no network round-trip when nothing has changed, and dhar build's resource footprint should be a stated, tracked property of every stage release, not something discovered late. A toolchain that only runs comfortably on well-resourced machines has quietly narrowed “independence” (Spec0 §2.2) to whoever can already afford it. Two further parts of the Canon serve the same requirement. The committed targets include ARM64 and RISC-V 64 Linux systems, the processors of many low-cost devices, and a WebAssembly target for the browser (Amendment A-2 §3.1); and the artificial-intelligence track runs a model with its memory use known before it starts, so a small model can run on modest hardware (Amendment A-1, A2).

# 4. Government & Industry Partnerships

| Body | What it actually is | Where Dhar plugs in |
| --- | --- | --- |
| NITDA (National Information Technology Development Agency, Nigeria) | Nigeria's federal IT policy and standards agency; co-runs 3MTT with the Ministry of Communications, Innovation & Digital Economy. | The natural first point of contact for a 3MTT curriculum module (§2.1) and for any future national digital-sovereignty framing of Spec0's mission. |
| 3MTT | Active national training programme, 12 tracks including Software Development and Cybersecurity; already past its Phase 1 target. | Direct curriculum integration, §2.1. |
| Smart Africa Alliance | ~40-member-state pan-African digital policy alliance, AU-endorsed. | Distribution and policy alignment across borders, §3.1, without a separate country-by-country effort. |

# 5. Developer Relations & Community Growth
- Hackathons scoped around real Stage-delta gaps (a new std.collections method, a Kun registry feature) or a track's open gate, rather than generic build-anything events — a hackathon that produces a merged contribution is worth more than one that produces a demo.
- A public showcase of real Kun packages, updated as they appear, functioning as both social proof and a map of where the ecosystem still has gaps — the same showcase doubles as an honest to-do list.
- “Good first issue” labeling and a mentorship pairing for first-time contributors, owned procedurally by The Guild of Dhar (§4), referenced here rather than duplicated (Master Index §3.6).
- An opt-in mailing list for people who want to follow the project. What it collects, the consent it asks for, the copy of a survey response sent to the person who gave it, and the rights to withdraw and to be erased are in The Hallmark of Dhar §7, and are not repeated here (Master Index §3.6).

# 6. Success Metrics

The Pact of Developing Dhar §4 formalizes this set, which deliberately avoids vanity metrics that measure attention rather than adoption:

- 3MTT fellows completing the Dhar module, and how many go on to publish a Kun package.
- Learners completing a unit of each track's curriculum (§2.4), counted per track, and only for units offered after their gate has passed.
- University courses using the bootstrap pipeline as course material, and student projects that extend a Stage-delta module or backend.
- Published, non-trivial Kun packages (excluding placeholder/example packages) and their download counts over time.
- Countries with an active local user group or meetup, tracked against Smart Africa's own member-state list as the realistic ceiling.
- Government or institutional pilot deployments — the single metric that most directly validates Spec0 §5.2's defence and critical-infrastructure ambition.

# 7. Relationship to Other Volumes

| This document assumes | Ratified in |
| --- | --- |
| The founding motivation this strategy serves | Spec0 §2.1 |
| Kun's offline-friendly resolution requirement (§3.2) | Stage-delta §3.3 |
| Community/contribution mechanics referenced in §5 | The Guild of Dhar §4 |
| Formal adoption metrics (§6) | The Pact of Developing Dhar §4 |
| The playground of §2.5 | Tooling Dhar §5; Stage-epsilon §3.1 |
| The mailing list and survey data of §5 | The Hallmark of Dhar §7 |
| The order of the units in §2.4, and the gate that opens each | Amendment A-1 §7, §9 |
