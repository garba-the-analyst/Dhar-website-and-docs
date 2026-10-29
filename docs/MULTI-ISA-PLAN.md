# Plan: every processor and operating system in Stage 0

**Decision (the author):** on 23 October 2026 the ARM64, RISC-V and WebAssembly back ends were to be built **in Stage 0**,
not postponed to Stage 1. On 25 October 2026 that was extended to every processor and operating system the Canon names,
with the print function `gen` on each, **before** the self-hosting compiler begins. It is now in the Canon as
[Amendment A-2](canon/pdf/Amendment_A2_Stage0_Targets.pdf) (source: [canon/src/a2_stage0_targets.md](canon/src/a2_stage0_targets.md)),
and in Stage-alpha v1.1 (§3), Spec1 v3.2 (§20), The Pact v1.1 (§2.1) and the other documents listed in
[canon/AMENDMENT-INDEX.md](canon/AMENDMENT-INDEX.md).

This file is the working plan behind that amendment: how the work is done and how each step is checked. It is not part of
the Canon. Where it and the Canon differ, **the Canon is right** and this file is out of date. What is built, and what is
not, is on the website's status board and in [reports/PROGRESS.md](reports/PROGRESS.md); this file does not repeat it.

## 1. What the Canon fixes

* **One list of targets**, Amendment A-2 §3.1: Linux x86-64, Windows x64, macOS x86-64, macOS ARM64, Linux ARM64,
  Linux RISC-V 64 and WebAssembly with WASI preview 1. Candidates (FreeBSD, Android, 32-bit ARM and x86, bare metal) are in
  §3.2; iOS and iPadOS are not targeted (§3.3). This plan never restates the list; if it ever disagrees, A-2 wins.
* **Direct emission, no intermediate form.** Stage-alpha writes assembly text for each target. Stage-beta's intermediate
  representation and its back ends come after.
* **An unsupported target is a fatal error**: a diagnostic, a non-zero exit status and no output file. `dharc` already
  behaves this way for every target it has not been built for.
* **Two gates** (A-2 §6): **G0**, the whole battery passes in an emulator or runtime that enforces the target's rules,
  after which the compiler accepts the target; and **G1**, it passes on the real system, after which the target counts toward
  Stage-alpha's exit criteria and may be described as supported.
* **Stage-beta begins only when every committed target has passed G1** (A-2 §2, §7). Work on the security, AI and quantum
  tracks begins only when Stage-beta compiles itself (A-1 §7).

## 2. What it costs (recorded so the choice is an informed one)

Stage 0 has no intermediate form. It reads a token and writes assembly text for it. The Windows target needed only a small
header and one runtime stub because Windows x64 is the same instruction set with a different system interface. A different
instruction set is a different generator, and most of it is re-done when Stage-beta writes its own back ends on the
intermediate representation (A-2 §1.2). The author has weighed that and chosen to have the targets first. What keeps the cost
bounded is the design of section 3: one small file per target. What stops the work being thrown away is that the Stage-alpha
back ends become the reference output the Stage-beta back ends are compared against (A-2 §7).

WebAssembly has structured control flow and a stack machine, so text templates that jump to labels do not translate
directly; it needs a dispatcher form.

## 3. Design

**One emitter, a neutral operation set, a prelude per target** (A-2 §4; Stage-alpha §3.1). Stage 0 keeps its token-walking
emitter. For each new target it writes a neutral line-per-operation form (`dh.li`, `dh.ld`, `dh.st`, `dh.add`, `dh.jmp`,
`dh.call` and so on, one line per operation, one operand slot per line like today's templates), and each target supplies a
**prelude** of assembler macros that expand the neutral operations into its own instructions. The emitter stays small, and
each target's knowledge sits in one file that can be read and checked in one place. The names `dh.*` are the working names
of this plan; Stage-alpha §3.1 states the rule, not the spelling.

| Target | Assembler and linker | System interface | Calling convention |
| --- | --- | --- | --- |
| Linux x86-64 | NASM, `ld` | `syscall`, number in `rax` (read 0, write 1, exit 60) | System V |
| Windows x64 | NASM `win64`, `lld-link` | `dhar_rt_syscall` stub mapping 0, 1, 60 to `ReadFile`, `WriteFile`, `ExitProcess` | Windows x64 |
| Linux ARM64 | GNU-syntax `llvm-mc`, `lld` | `svc #0`, number in `x8` (asm-generic: read 63, write 64, openat 56, close 57, exit 93) | AAPCS64: `x0` to `x7`, result `x0`, 16-byte stack alignment |
| Linux RISC-V 64 | `llvm-mc`, `lld` | `ecall`, number in `a7` (same asm-generic table) | LP64: `a0` to `a7`, result `a0`; conditional branches reach ±4 KiB, so each is emitted inverted over an unconditional `j` |
| WebAssembly (WASI preview 1) | text format assembled by a small in-tree tool, or `wasm-ld` | `fd_write`, `fd_read`, `proc_exit` imports; linear memory | one function per task; control flow as a `loop` with a `br_table` over block numbers |
| macOS x86-64 | NASM `macho64`, a Mach-O linker | `libSystem`, the operating system's own interface library | System V AMD64 |
| macOS ARM64 | `llvm-mc`, a Mach-O linker | `libSystem` | AAPCS64, Apple variant |

The tools in the second column are the tools the **plan** uses to assemble and check Stage 0's output. They are test and
build aids, not dependencies of the language: a program Dhar produces does not call them, and Principle P1 (A-1) is about the
language, the compiler and the standard library. Apple silicon needs a code signature on native programs; how Dhar produces
one without an outside tool is an open question recorded in The Pact (§2.1) and is settled before that target is started.

**`sys` by number.** Programs call `sys 1, ...` with Linux x86-64 numbers. A target prelude translates the numbers Stage 0
supports (read, write, exit and the file calls Spec1 lists) to its own, so one source program runs on each target. The named
forms (`sys.write` and so on) are in Spec1 §20.1; their spellings are provisional there.

**`gen`.** One print function with one rule on every target (A-2 §5.2; Spec1 §20.2): exactly the text of the value, with no
added newline and no trailing zero byte. Its tests run on every target.

## 4. How each is verified

The same conformance battery with the same expected results, run per target, as is done for Windows now (A-2 §6).

* ARM64 and RISC-V: assemble and link with `llvm-mc` and `lld`, run in the Unicorn CPU emulator (which supports both), using
  the method in the forge-of-dhar `tools/pe_emulate.py`. That is G0.
* WebAssembly: run under Node's WASI support, and a second runtime if one can be installed. A WASI host is a real runtime
  for this target, so a passing battery there is G1 as well as G0.
* G1 for every other target is a run on the real system: a machine for each of Linux ARM64, Linux RISC-V 64, Windows x64,
  macOS x86-64 and macOS ARM64. Emulator-only stays at G0, and the status board says **Partly**, as it does for Windows.

## 5. Order and exit criteria

The order is The Pact §2.1 (it is a roadmap matter and the author may change it there): the neutral operation set and Linux
ARM64 first; Linux RISC-V 64; WebAssembly (WASI), because it needs the dispatcher form and it unlocks the in-browser
playground; Windows x64 to G1; macOS last, because G1 needs Apple hardware.

A target is switched on (accepted by `--target`) when its whole battery passes in an emulator or runtime (G0), the rejects
still reject, and the status file, README, website and progress log say exactly what was run and where. Until then it stays
refused. It is called supported only after G1.

**The risk that matters most:** G1 needs real hardware for four targets. If one cannot be reached, A-2 §3 is revised to move
it to the candidate list; it is never counted as complete without its run (The Pact §3).
