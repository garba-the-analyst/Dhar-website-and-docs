---
key: fueling
file: 14_FuelingDhar_Business_Funding.pdf
kind: canon
volume: "Volume III — Ecosystem, Trust & Adoption"
short: "Fueling Dhar"
title: "Fueling Dhar — Business Model, Sustainability & Funding"
quote: "A forge that runs on donated coal for too long eventually goes cold."
version: "1.1"
date: "October 26, 2026"
status: "Ratified"
running: "DHAR — FUELING DHAR · Business Model & Funding"
part_label: "THE CANON OF DHAR · VOLUME III"
cover:
  - "Part of": "The Canon of Dhar, Volume III"
  - "Depends on": "The Hallmark of Dhar (licensing), Casting Dhar (government contacts), Amendments A-1 and A-2"
  - "Audience": "Funders, co-founders, leadership"
colophon: "Grounded in Germany's Sovereign Tech Fund (€23M+ invested, 2022–2024, global applications accepted) and the Rust Foundation's corporate-membership model (founded 2021)."
revisions:
  - v: "v1.0"
    date: "September 9, 2026"
    text: "first ratified edition."
  - v: "v1.1"
    date: "October 26, 2026"
    text: "Amendments A-1 and A-2: funding lines by deliverable and gate, including the independent audit of std.crypto, the device lab for gate G1 and the hosted playground (§3.4), the modules as the broad base of sustainability (§4), and corrected references (§2, §5)."
---

# 1. Mandate

State plainly how the work in this Canon actually gets paid for, rather than leaving sustainability as an implied assumption. A single unfunded maintainer building a compiler, a package manager, and a standard library is not a funding gap this Canon can wish away with an MIT license and good intentions — it is the single most common reason ambitious open-source infrastructure projects stall after their first burst of momentum, and this document names real, existing funding mechanisms rather than generic ones.

Dhar is a language for trustworthy computation: it goes first to cybersecurity, then to artificial intelligence, then to quantum computing, with every other domain kept as modules (Spec0 §5.1, §5.2; Amendment A-1). For funding that gives the case a lead and a shape: it leads with security, where an independent audit and a public gate are things a funder can check, and it is made in deliverables that each carry the gate that says when they are done (§3.4).

# 2. Licensing as a Business Decision, Not Only a Legal One

Dhar's code is released under the MIT license. The Hallmark of Dhar owns the legal reasoning; the business reasoning is simpler: a permissive license is the lowest-friction choice for the adopters Spec0 §5.2 names. Government and defence procurement in particular routinely screens out copyleft licenses (GPL-family) by policy, since they can impose obligations on adjacent, separately developed code that a procuring institution cannot always accept. MIT removes that objection before it's raised, at the direct cost of not requiring downstream contributions back — a trade this Canon makes deliberately, and revisits in §3 rather than pretending it has no cost.

# 3. Funding Pathways

## 3.1 Sovereign Tech Fund (and its emerging peers)

Germany's Sovereign Tech Fund, run by the Sovereign Tech Agency and financed by the Federal Ministry for Economic Affairs and Climate Action, has invested over €23 million in roughly 60 open-source infrastructure projects in its first two years, explicitly to address projects “maintained by small teams or even single individuals” that underpin digital infrastructure well beyond Germany's own borders — it accepts applications globally, not only from German or EU projects, and has funded foundational technologies like curl and GNOME on exactly that basis. A proposal-stage European Union Sovereign Tech Fund would extend the same model continentally. This is, almost implausibly precisely, the funding model Dhar's own framing already matches: a small team building foundational, sovereignty-framed digital infrastructure that the wider ecosystem depends on but does not yet fund. A funding application naming a specific, scoped deliverable (a Stage-delta module, a backend, an audit) rather than general support money is how the fund's own stated model works.

## 3.2 Nigerian and Pan-African public funding

Casting Dhar §4 already names NITDA as the natural first point of institutional contact through the 3MTT relationship. This Canon does not invent specific Nigerian grant program names here without a confirmed one to cite — the same discipline Casting Dhar §2.2 applies to universities applies to funding bodies. The realistic path is the same door: a 3MTT curriculum relationship (Casting Dhar §2.1) is also the natural entry point for a conversation about institutional or grant support, since it is evidence of adoption a funding body can point to, rather than a cold pitch.

## 3.3 Corporate sponsorship, once there is something to sponsor

The Rust Foundation's funding model — dues-paying corporate members (its founding members included AWS, Google, Huawei, Microsoft, and Mozilla) who benefit directly from the language's stability — is the template for Dhar once real production usage exists to justify it. This is explicitly a later-stage mechanism: soliciting corporate membership before Stage-epsilon exists asks companies to fund a promise rather than a dependency, which is a much harder sell and not one this Canon recommends attempting early.

## 3.4 Funding lines by deliverable

A funder is asked for a scoped deliverable, never for general support (§3.1), and each deliverable below carries the gate that says when it is done, so that a funder can check the result without taking the project's word for it (Tempering Dhar §11).

| Deliverable | What the money pays for | The gate that says it is done |
| --- | --- | --- |
| An independent audit of `std.crypto` and of the secret-value rules | An outside security review of the cryptographic library, the post-quantum algorithms and the compiler's checks on secret values; the report is published | S2, S3 and Q1 pass first (Amendment A-1 §9) |
| A device lab | Real machines for every committed target (ARM64 and RISC-V 64 Linux boards, Windows and Apple computers) on which the conformance battery is run | G1 for each target (Amendment A-2 §6) |
| A back end in the first compiler for every target | The cost of one generator per committed target in Stage-alpha, accepted knowingly (Amendment A-2 §1.2) | G0 and G1 for each target |
| Hosting the playground's compile service | Servers, bandwidth and the handling of abuse for the in-browser playground (Stage-epsilon §3.1; The Hallmark of Dhar §8) | The tests of Stage-epsilon §4, criterion 8 |
| Curriculum units for the three tracks | Writing and teaching the units of Casting Dhar §2.4 | The gate of the track the unit teaches |

# 4. Sustainability Over Time

The single-maintainer bus-factor risk this document exists to address is not solved by funding alone — money without a second and third contributor able to make Ratified decisions (The Guild of Dhar §6) just delays the same risk. Fueling Dhar's criterion for “funded enough” is therefore not a dollar figure; it is whether funding has been used to grow the number of people who can review, ratify, and maintain the Canon, per The Guild of Dhar's foundation-transition trigger.

The three tracks lead the case for funding, but they are not the whole market. The modules on the same core (Spec0 §5.2; Amendment A-1, P6) — web and backend, data, blockchain and Web3, systems and hardware — are what make Dhar useful to the widest range of adopters, and so they are the base on which sponsorship and membership (§3.3) can stand. A funder of one track and a corporate member of the project are not asked to pay for different languages.

# 5. Relationship to Other Volumes

| This document assumes | Ratified in |
| --- | --- |
| The license whose trade-offs §2 states | The Hallmark of Dhar |
| The institutional relationship §3.2 relies on | Casting Dhar §4 |
| The foundation-transition trigger §4 defers to | The Guild of Dhar §6 |
| Funding-dependency risk | The Pact of Developing Dhar §3 |
| The deliverables of §3.4 and the gates behind them | Amendment A-1 §9; Amendment A-2 §6 |
| What the hosted playground holds, and its terms | The Hallmark of Dhar §7, §8 |
