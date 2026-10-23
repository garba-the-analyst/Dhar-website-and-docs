# Plan: ARM64, RISC-V and WebAssembly (WASI) in Stage 0

**Decision (the author, 23 October 2026):** all the other architecture back ends are built **in Stage 0**, not postponed
to Stage 1. This replaces the earlier recommendation, which was to build them on the Stage 1 IR (options A and B of the
first version of this plan; the author chose B, for every target). Nothing in this file is built yet; the board and the
README say **Not yet** for these targets until a run says otherwise.

Because Stage-alpha v1.0 (ratified) says Stage 0 targets "x86-64 directly and only" and puts multiple back ends at
Stage-beta, the decision needs a Canon amendment, **A-2**, and then a v1.1 of Stage-alpha (see
[canon/AMENDMENT-INDEX.md](canon/AMENDMENT-INDEX.md)). Until A-2 is ratified, the code and this plan follow the author's
instruction and the Canon still says otherwise; that gap is recorded here rather than hidden.

## 1. Where things stand

| Target | `dharc` today |
| --- | --- |
| Linux x86-64 | Works. Native, all conformance tests pass. |
| Windows x64 | Partly. All tests pass in an emulator that enforces the Windows calling rules; not yet run on a real Windows machine. |
| ARM64, RISC-V, WASI | Not built. `dharc` refuses them with `Fatal Error: unsupported target`, exit 1, and leaves no `output.asm`. |

Refusing is deliberate. Before 22 October 2026, `--target=wasi` and an unknown target quietly produced Linux x86-64
code, which a user could mistake for the thing they asked for. Each target is switched on only when its battery passes.

## 2. What it costs (recorded so the choice is an informed one)

Stage 0 has no intermediate form. It reads a token and writes assembly text for it. The Windows target needed only a small
header and one runtime stub because Windows x64 is the same instruction set with a different system interface. A different
instruction set is a different generator, and all of it is retired or re-done when Stage 1 gets its own back ends on the
IR. The author has weighed that and chosen to have the targets now. WebAssembly has structured control flow and a stack
machine, so text templates that jump to labels do not translate directly; it needs a dispatcher form (section 3).

## 3. Design

**One emitter, a small virtual instruction set, a per-target prelude.** Stage 0 keeps its token-walking emitter. For the
new targets it writes a neutral line-per-operation form (`dh.li`, `dh.ld`, `dh.st`, `dh.add`, `dh.jmp`, `dh.call` and so
on, one line per operation, one operand slot per line like today's templates), and each target supplies a **prelude** of
assembler macros that expand the neutral operations into its own instructions. The text emitter stays small, and each
target's knowledge sits in one file that can be read and checked in one place.

| Target | Assembler and linker | Entry and system interface | Calling convention |
| --- | --- | --- | --- |
| Linux x86-64 | NASM, `ld` | `syscall`, number in `rax` (read 0, write 1, exit 60) | System V |
| Windows x64 | NASM `win64`, `lld-link` | `dhar_rt_syscall` stub mapping 0, 1, 60 to `ReadFile`, `WriteFile`, `ExitProcess` | Windows x64 |
| Linux ARM64 | GNU-syntax `llvm-mc`, `lld` | `svc #0`, number in `x8` (asm-generic: read 63, write 64, openat 56, close 57, exit 93) | AAPCS64: `x0` to `x7`, result `x0`, 16-byte stack alignment |
| Linux RISC-V 64 | `llvm-mc`, `lld` | `ecall`, number in `a7` (same asm-generic table) | LP64: `a0` to `a7`, result `a0`; conditional branches reach ±4 KiB, so each is emitted inverted over an unconditional `j` |
| WebAssembly (WASI preview 1) | text format assembled by a small in-tree tool, or `wasm-ld` | `fd_write`, `fd_read`, `proc_exit` imports; linear memory | one function per task; control flow as a `loop` with a `br_table` over block numbers |

**`sys` by number.** Programs today call `sys 1, ...` with Linux x86-64 numbers. A target prelude translates the three
numbers Stage 0 supports (read, write, exit) to its own, so one source program runs on each target. Names such as
`sys.write` come later, with the Spec1 amendment in the index.

## 4. How each is verified

The same conformance battery, run per target, as is done for Windows now.

* ARM64 and RISC-V: assemble and link with `clang`/`llvm-mc` and `lld`, run in the Unicorn CPU emulator (which supports
  both), using the method in `tools/pe_emulate.py`.
* WebAssembly: run under Node's WASI support, and a second runtime if one can be installed.
* A target's status can be **Works** only after a run on real hardware or a real runtime. Emulator-only stays
  **Partly**, as Windows does. For WebAssembly, Node's WASI is a real runtime, so a passing battery there is **Works**.

## 5. Order and exit criteria

Order: ARM64, RISC-V, WebAssembly. ARM64 first because it is the most common target outside x86-64; RISC-V second
because it is the smallest to emit; WebAssembly third because it needs the dispatcher form and it unlocks the in-browser
playground.

A target is switched on (accepted by `--target`) when: the whole conformance battery passes on it; rejects still reject;
and the status file, README, website and progress log say exactly what was run and where. Until then it stays refused.
