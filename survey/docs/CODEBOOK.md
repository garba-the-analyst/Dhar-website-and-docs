# Shaping Dhar survey: codebook

Generated from `questions.js` by `tools/export_codebook.js`. Do not edit by hand; edit the questions and run the script again.

- Survey version: **1.0**
- Questions in the bank: **80** (not counting the role question)
- Each question code is a column in the CSV made by `tools/parse_responses.py`.
- A code never changes meaning. If wording or option order changes, the survey version is raised.

## How long it is for each kind of respondent

| Role picked on its own | Questions without any optional area blocks | With every area ticked |
| --- | ---: | ---: |
| Academic (professor or lecturer) | 25 | 49 |
| Technical researcher | 23 | 47 |
| Student | 23 | 47 |
| Developer or engineer | 23 | 47 |

Picking several roles adds the questions of each. Questions in the optional area blocks can be skipped.

## How answers are written in the CSV

| Question type | Cell value |
| --- | --- |
| one choice | the option text |
| several choices | option texts joined with ` \| ` |
| 1 to 5, number scale | the number |
| grid | `statement: number` pairs joined with ` \| ` |
| text | the text as typed |

An "Other" option appears as `Other: what they typed`. An unanswered question is an empty cell.

## Start

Report heading: `== ROLES ==`. Shown to: everyone.

### ROLE (required)

Which of these describe you?

_Pick every one that fits. You will only see the questions for the roles you pick._

Type: several choices · Shown to: everyone

| Id | Option |
| --- | --- |
| `prof` | I teach at a university, polytechnic or similar institution |
| `researcher` | I do technical or academic research |
| `student` | I am a student or independent learner |
| `dev` | I work as a developer or engineer |

## About you

_A few basics, so your answers can be read in context._

Report heading: `== ABOUT YOU ==`. Shown to: everyone.

### A1 (required)

Which country or region are you currently based in?

Type: short text · Shown to: everyone

### A2 (required)

How many years of experience do you have with programming or software-related work?

Type: one choice · Shown to: everyone

| Id | Option |
| --- | --- |
| `o1` | Less than 1 year |
| `o2` | 1 to 3 years |
| `o3` | 3 to 5 years |
| `o4` | 5 to 10 years |
| `o5` | 10+ years |

### A3 (required)

Which of the following are you currently involved in, in any capacity?

_Select all that apply. The areas you pick decide which optional detail questions you see later._

Type: several choices · Shown to: everyone

| Id | Option |
| --- | --- |
| `software` | Software and application development (backend, tools, enterprise) |
| `web` | Web development |
| `mobile` | Mobile development |
| `data` | Data analysis and data science |
| `ai` | Artificial intelligence (LLMs, agents, vision, speech) |
| `ml` | Machine learning (training, models, MLOps) |
| `systems` | Systems and embedded programming |
| `security` | Cybersecurity |
| `blockchain` | Blockchain and Web3 |
| `cloud` | Cloud and DevOps infrastructure |
| `games` | Game development |
| `other` | Other (with a text box) |
| `none` | None of these yet (clears the other choices) |

### A4 (required)

Which programming languages do you currently use regularly?

_Select all that apply._

Type: several choices · Shown to: everyone

| Id | Option |
| --- | --- |
| `o1` | C |
| `o2` | C++ |
| `o3` | Rust |
| `o4` | Java |
| `o5` | Python |
| `o6` | JavaScript or TypeScript |
| `o7` | Go |
| `o8` | C# |
| `o9` | Swift |
| `o10` | Kotlin |
| `o11` | PHP |
| `o12` | Ruby |
| `o13` | SQL |
| `other` | Other (with a text box) |
| `none` | None yet (clears the other choices) |

### A5 (required)

Before today, had you heard of Dhar?

Type: one choice · Shown to: everyone

| Id | Option |
| --- | --- |
| `o1` | No, this is the first time I am hearing of it |
| `o2` | I had heard the name but knew nothing about it |
| `o3` | I knew a little about it |
| `o4` | I am already familiar with it |

## Teaching

_For lecturers, professors and instructors._

Report heading: `== ACADEMIC: PROFESSOR OR LECTURER ==`. Shown to: role is Academic (professor or lecturer).

### P1 (required)

What level(s) do you currently teach?

_Select all that apply._

Type: several choices · Shown to: role is Academic (professor or lecturer)

| Id | Option |
| --- | --- |
| `o1` | Undergraduate: introductory and foundational |
| `o2` | Undergraduate: advanced |
| `o3` | Postgraduate (Masters) |
| `o4` | PhD supervision |
| `other` | Other (with a text box) |

### P2

Which courses do you teach (or have taught) that a new language could realistically fit into?

_Select all that apply._

Type: several choices · Shown to: role is Academic (professor or lecturer)

| Id | Option |
| --- | --- |
| `o1` | Introduction to Programming |
| `o2` | Data Structures and Algorithms |
| `o3` | Compilers or Programming Language Theory |
| `o4` | Operating Systems |
| `o5` | Computer Architecture or Systems Programming |
| `o6` | Computer Security |
| `o7` | Software Engineering |
| `o8` | Database Systems |
| `o9` | AI and Machine Learning |
| `other` | Other (with a text box) |

### P3 (required)

How open would you be to introducing a new, independently built programming language into your teaching?

Type: 1 to 5 · Shown to: role is Academic (professor or lecturer)

Scale: 1 = Not open at all, 5 = Very open

### P4 (required)

What would most influence that decision?

_Pick your top 3._

Type: several choices · Shown to: role is Academic (professor or lecturer) · Up to 3 choices

| Id | Option |
| --- | --- |
| `o1` | Quality and completeness of documentation |
| `o2` | A textbook or structured course material |
| `o3` | An existing job market for the language |
| `o4` | Institutional or departmental approval processes |
| `o5` | Peer or colleague adoption elsewhere |
| `o6` | Student interest and demand |
| `o7` | Tooling and IDE support |
| `o8` | Being open source and freely usable |
| `o9` | Alignment with accreditation or curriculum standards |
| `other` | Other (with a text box) |

### P5 (required)

Dhar’s own bootstrap compiler is being built in public, stage by stage: lexer, parser, type checker, code generator, self-hosting. How useful would that documented process be as course material for a compilers or programming-languages course?

Type: 1 to 5 · Shown to: role is Academic (professor or lecturer)

Scale: 1 = Not useful, 5 = Very useful

### P6 (required)

Would you be interested in co-developing or piloting a course module using Dhar?

Type: one choice · Shown to: role is Academic (professor or lecturer)

| Id | Option |
| --- | --- |
| `o1` | Yes, definitely |
| `o2` | Possibly, send me more information |
| `o3` | Unlikely |
| `o4` | No |

### P7 (required)

Would you be willing to supervise a student thesis, dissertation or capstone project that extends Dhar?

_For example a standard-library module, a new hardware backend, or formally verifying part of its type system._

Type: one choice · Shown to: role is Academic (professor or lecturer)

| Id | Option |
| --- | --- |
| `o1` | Yes |
| `o2` | Possibly |
| `o3` | No |

### P8

What institutional or administrative barriers do you anticipate to adopting a new teaching language?

Type: long text · Shown to: role is Academic (professor or lecturer)

### P9

Which existing language(s) do you currently find hardest to teach effectively, and why?

Type: long text · Shown to: role is Academic (professor or lecturer)

### P10

Is there a specific gap in how programming or computer science is taught in your context that a language built for both teaching and real-world capability could help address?

Type: long text · Shown to: role is Academic (professor or lecturer)

### P11 (required)

Would free teaching materials, sample syllabi and instructor support increase your interest?

Type: one choice · Shown to: role is Academic (professor or lecturer)

| Id | Option |
| --- | --- |
| `o1` | Yes |
| `o2` | No |
| `o3` | I already have enough information to decide |

### P12

Any other thoughts, from a teaching perspective?

Type: long text · Shown to: role is Academic (professor or lecturer)

## Research

_For people who do technical or academic research._

Report heading: `== TECHNICAL RESEARCHER ==`. Shown to: role is Technical researcher.

### R1 (required)

Which areas does your research touch on?

_Select all that apply._

Type: several choices · Shown to: role is Technical researcher

| Id | Option |
| --- | --- |
| `o1` | Programming language design and theory |
| `o2` | Compilers and code generation |
| `o3` | Formal verification and methods |
| `o4` | Operating systems |
| `o5` | Computer and network security |
| `o6` | Cryptography |
| `o7` | Distributed systems |
| `o8` | AI and ML systems |
| `o9` | Human-computer interaction |
| `o10` | Software engineering |
| `o11` | Data science and analytics |
| `o12` | Blockchain and distributed ledgers |
| `other` | Other (with a text box) |

### R2 (required)

How interested would you be in using Dhar as a research vehicle, for example to study multi-paradigm language design, memory-safety models without a garbage collector, or compiler bootstrapping?

Type: 1 to 5 · Shown to: role is Technical researcher

Scale: 1 = Not interested, 5 = Very interested

### R3 (required)

Dhar’s memory model combines compile-time ownership tracking with arena allocation, deliberately without Rust-style explicit lifetimes. How interesting is that specific trade-off as a research question?

Type: 1 to 5 · Shown to: role is Technical researcher

Scale: 1 = Not interesting, 5 = Very interesting

### R3b

What would you want to test about it?

Type: long text · Shown to: role is Technical researcher

### R4 (required)

Would you be interested in independently verifying or benchmarking Dhar’s safety or performance claims once a working compiler exists?

Type: one choice · Shown to: role is Technical researcher

| Id | Option |
| --- | --- |
| `o1` | Yes |
| `o2` | Possibly |
| `o3` | No |

### R5 (required)

The project has already identified one open problem. Proving the bootstrap compiler is free of a "Trusting Trust"-style backdoor requires an independently built second compiler for comparison (Diverse Double-Compiling). Are you interested in that as a research collaboration?

Type: one choice · Shown to: role is Technical researcher

| Id | Option |
| --- | --- |
| `o1` | Yes, very interested |
| `o2` | Interested, I want more detail |
| `o3` | Not my area |
| `o4` | No |

### R6

Would you consider publishing or citing work related to Dhar’s design once there is a stable specification and working implementation? What would make it citation-worthy?

Type: long text · Shown to: role is Technical researcher

### R7

What would you want to see benchmarked, formally proven or independently audited first?

Type: long text · Shown to: role is Technical researcher

### R8 (required)

Would open access to Dhar’s full specification and design-decision history, including rejected alternatives, be useful to your research process?

Type: one choice · Shown to: role is Technical researcher

| Id | Option |
| --- | --- |
| `o1` | Yes |
| `o2` | Somewhat |
| `o3` | No |

### R9

Any other thoughts, from a research perspective?

Type: long text · Shown to: role is Technical researcher

## Learning

_For students and independent learners._

Report heading: `== STUDENT ==`. Shown to: role is Student.

### S1 (required)

What best describes your current stage?

Type: one choice · Shown to: role is Student

| Id | Option |
| --- | --- |
| `o1` | Undergraduate (early years) |
| `o2` | Undergraduate (final years) |
| `o3` | Postgraduate: Masters |
| `o4` | Postgraduate: PhD |
| `o5` | Coding bootcamp |
| `o6` | Self-taught, independent learner |

### S2

What was, or is, the first programming language you learned?

Type: short text · Shown to: role is Student

### S3 (required)

What makes a programming language easy or hard for you to learn?

_Pick your top 3 concerns._

Type: several choices · Shown to: role is Student · Up to 3 choices

| Id | Option |
| --- | --- |
| `o1` | Clarity of error messages |
| `o2` | Quality and quantity of documentation |
| `o3` | Availability of tutorials and courses |
| `o4` | Simplicity of syntax |
| `o5` | Community support (forums, Discord, Stack Overflow) |
| `o6` | Job-market demand |
| `o7` | IDE and editor support |
| `o8` | Number of existing libraries |
| `other` | Other (with a text box) |

### S4 (required)

How important is it to you that a language you invest time learning has strong job-market demand?

Type: 1 to 5 · Shown to: role is Student

Scale: 1 = Not important, 5 = Essential

### S5 (required)

Would learning a systems-level language (closer to C or Rust) that also reads simply (closer to Python) make you more interested in exploring lower-level programming, compilers or systems engineering?

Type: one choice · Shown to: role is Student

| Id | Option |
| --- | --- |
| `o1` | Yes |
| `o2` | Maybe |
| `o3` | No |
| `o4` | I am already interested regardless |

### S6 (required)

Would you be interested in contributing to Dhar’s open-source development as a way to build real experience, for example through a guided "good first issue" path?

Type: one choice · Shown to: role is Student

| Id | Option |
| --- | --- |
| `o1` | Yes, very interested |
| `o2` | Interested if guided |
| `o3` | Not right now |
| `o4` | No |

### S7 (required)

Would a free elective module, hackathon or recognized certificate around Dhar make it more appealing to learn?

Type: one choice · Shown to: role is Student

| Id | Option |
| --- | --- |
| `o1` | Yes |
| `o2` | No |
| `o3` | It depends on whether my institution recognizes it |

### S8

What worries you, if anything, about investing time in a brand-new language rather than an established one?

Type: long text · Shown to: role is Student

### S9

What would most excite you about a Nigerian or African-built programming language specifically?

Type: long text · Shown to: role is Student

### S10

Any other thoughts, from a student’s perspective?

Type: long text · Shown to: role is Student

## Building

_For developers and engineers._

Report heading: `== DEVELOPER OR ENGINEER ==`. Shown to: role is Developer or engineer.

### D1 (required)

What is your primary domain of work?

_Select all that apply._

Type: several choices · Shown to: role is Developer or engineer

| Id | Option |
| --- | --- |
| `o1` | Backend and server software |
| `o2` | Web development |
| `o3` | Mobile development |
| `o4` | Data analysis and data science |
| `o5` | Artificial intelligence (LLMs, agents, vision, speech) |
| `o6` | Machine learning (training, models, MLOps) |
| `o7` | Systems, embedded and OS-level programming |
| `o8` | Cybersecurity |
| `o9` | Blockchain and Web3 |
| `other` | Other (with a text box) |

### D2 (required)

How many years of professional experience do you have?

Type: one choice · Shown to: role is Developer or engineer

| Id | Option |
| --- | --- |
| `o1` | Less than 1 |
| `o2` | 1 to 3 |
| `o3` | 3 to 5 |
| `o4` | 5 to 10 |
| `o5` | 10+ |

### D3 (required)

What would make you personally consider using a new systems language for a real project, even a small or internal one?

_Choose up to 4._

Type: several choices · Shown to: role is Developer or engineer · Up to 4 choices

| Id | Option |
| --- | --- |
| `o1` | Proven, benchmarked performance |
| `o2` | Strong memory-safety guarantees |
| `o3` | Good IDE, editor and debugging support |
| `o4` | A mature package ecosystem |
| `o5` | Ability to call existing C, Rust, Python and Java libraries |
| `o6` | An active community and support |
| `o7` | Clear, stable documentation |
| `o8` | Backing from a credible organization |
| `o9` | Employer or team buy-in |
| `other` | Other (with a text box) |

### D4

What are your biggest deal-breakers, the things that would stop you adopting a new language regardless of its technical merits?

Type: long text · Shown to: role is Developer or engineer

### D5 (required)

How important is each of the following to you?

_Rate every line from 1 to 5._

Type: grid of 1 to 5 ratings · Shown to: role is Developer or engineer

Scale: 1 = Not important, 5 = Essential

Rows:
1. Performance at or above C’s level, with no garbage collector
2. Memory safety guaranteed by the compiler (bounds checking, no use-after-free)
3. Explicit typing for systems work, with inference for everyday code
4. A dynamic-typing option for scripting-style flexibility
5. Multi-paradigm support (procedural, object-oriented, functional, logical and symbolic in one language)
6. Built-in async and concurrency support
7. Generics and traits or interfaces for reusable code
8. A package manager with real dependency resolution and lockfiles
9. Direct interoperability with existing C, C++, Rust, Java and Python code
10. Cross-platform support (x86-64, ARM64, RISC-V, WASI, Windows)
11. Formal security assurance and audit-readiness for critical systems

### D6

Which existing library or framework gap, if filled in Dhar, would most motivate you to actually use it?

Type: long text · Shown to: role is Developer or engineer

### D7 (required)

Would you contribute a package to Dhar’s package registry (Kun) if the core tooling were solid?

Type: one choice · Shown to: role is Developer or engineer

| Id | Option |
| --- | --- |
| `o1` | Yes |
| `o2` | Possibly |
| `o3` | No |

### D8 (required)

Which of these target domains are you personally most interested in using Dhar for?

_Pick one._

Type: one choice · Shown to: role is Developer or engineer

| Id | Option |
| --- | --- |
| `o1` | Backend and server |
| `o2` | Web |
| `o3` | Mobile |
| `o4` | Data analysis and data science |
| `o5` | Artificial intelligence |
| `o6` | Machine learning |
| `o7` | Systems and embedded |
| `o8` | Cybersecurity |
| `o9` | Blockchain and Web3 |
| `other` | Other (with a text box) |

### D9

What would convince your employer or team to seriously evaluate Dhar for a real project?

Type: long text · Shown to: role is Developer or engineer

### D10

Any other thoughts, from a developer or engineering perspective?

Type: long text · Shown to: role is Developer or engineer

## Your areas in detail

_You said you work in these areas. Open any you would like to say more about. Everything on this page is optional._

Report heading: `== AREAS IN DETAIL ==`. Shown to: A3 includes "Software and application development (backend, tools, enterprise)" or "Web development" or "Mobile development" or "Data analysis and data science" or "Artificial intelligence (LLMs, agents, vision, speech)" or "Machine learning (training, models, MLOps)" or "Systems and embedded programming" or "Cybersecurity" or "Blockchain and Web3".

### SW1

What would Dhar need to offer in backend and software development before you would use it for real work?

_Choose up to 5._

Type: several choices · Shown to: A3 includes "Software and application development (backend, tools, enterprise)" · Optional block: Backend and software development · Up to 5 choices

| Id | Option |
| --- | --- |
| `o1` | Web server, HTTP, REST and gRPC libraries |
| `o2` | Database drivers (PostgreSQL, MySQL, SQLite, MongoDB, Redis) |
| `o3` | An ORM or query builder |
| `o4` | Logging, tracing and metrics |
| `o5` | Built-in testing, benchmarking and mocking |
| `o6` | JSON, TOML and YAML parsing and configuration |
| `o7` | Container and CI/CD support |
| `o8` | Calling existing Java, C# or Python services and libraries |
| `o9` | Fast compile times and hot reload |
| `o10` | Long-term backward compatibility |
| `other` | Other (with a text box) |

### SW2

Which libraries, frameworks or tools do you rely on in backend and software development today that Dhar would need to work with or replace?

Type: long text · Shown to: A3 includes "Software and application development (backend, tools, enterprise)" · Optional block: Backend and software development

### SW3

What is the biggest problem in backend and software development that a new language could realistically help fix?

Type: long text · Shown to: A3 includes "Software and application development (backend, tools, enterprise)" · Optional block: Backend and software development

### WM1

What would Dhar need to offer in web and mobile before you would use it for real work?

_Choose up to 5._

Type: several choices · Shown to: A3 includes "Web development" or "Mobile development" · Optional block: Web and mobile · Up to 5 choices

| Id | Option |
| --- | --- |
| `o1` | A WebAssembly target for the browser |
| `o2` | A web framework (routing, templating, sessions) |
| `o3` | Frontend, DOM bindings or a UI toolkit |
| `o4` | Android and iOS support |
| `o5` | HTTP client and WebSocket support |
| `o6` | Authentication libraries (OAuth, JWT) |
| `o7` | SDKs for African payments, mobile money, USSD and SMS |
| `o8` | Small binaries and low memory use for low-end phones |
| `o9` | Offline-first apps and data sync |
| `o10` | Easy deployment (a single static binary or serverless) |
| `other` | Other (with a text box) |

### WM2

Which libraries, frameworks or tools do you rely on in web and mobile today that Dhar would need to work with or replace?

Type: long text · Shown to: A3 includes "Web development" or "Mobile development" · Optional block: Web and mobile

### WM3

What is the biggest problem in web and mobile that a new language could realistically help fix?

Type: long text · Shown to: A3 includes "Web development" or "Mobile development" · Optional block: Web and mobile

### DA1

What would Dhar need to offer in data analysis and data science before you would use it for real work?

_Choose up to 5._

Type: several choices · Shown to: A3 includes "Data analysis and data science" · Optional block: Data analysis and data science · Up to 5 choices

| Id | Option |
| --- | --- |
| `o1` | A DataFrame library (like pandas or Polars) |
| `o2` | Readers for CSV, Excel, Parquet, JSON and SQL |
| `o3` | Plotting and visualization |
| `o4` | Numerical arrays and statistics (like NumPy and SciPy) |
| `o5` | A notebook or REPL experience |
| `o6` | SQL integration or a query engine |
| `o7` | Calling existing Python data libraries |
| `o8` | Handling large datasets in limited memory |
| `o9` | Geospatial and time-series support |
| `other` | Other (with a text box) |

### DA2

Which libraries, frameworks or tools do you rely on in data analysis and data science today that Dhar would need to work with or replace?

Type: long text · Shown to: A3 includes "Data analysis and data science" · Optional block: Data analysis and data science

### DA3

What is the biggest problem in data analysis and data science that a new language could realistically help fix?

Type: long text · Shown to: A3 includes "Data analysis and data science" · Optional block: Data analysis and data science

### AI1

What would Dhar need to offer in artificial intelligence before you would use it for real work?

_Choose up to 5._

Type: several choices · Shown to: A3 includes "Artificial intelligence (LLMs, agents, vision, speech)" · Optional block: Artificial intelligence · Up to 5 choices

| Id | Option |
| --- | --- |
| `o1` | Calling hosted LLM and inference APIs |
| `o2` | Running local models (GGUF, ONNX) through bindings |
| `o3` | Embeddings, vector search and RAG tooling |
| `o4` | Agent and tool-calling frameworks |
| `o5` | Speech, vision and NLP tooling, including African-language models |
| `o6` | GPU and accelerator access (CUDA, ROCm, Vulkan, Metal) |
| `o7` | Tokenizer and prompt tooling |
| `o8` | Python interop for existing AI libraries |
| `o9` | Efficient on-device and edge inference |
| `other` | Other (with a text box) |

### AI2

Which libraries, frameworks or tools do you rely on in artificial intelligence today that Dhar would need to work with or replace?

Type: long text · Shown to: A3 includes "Artificial intelligence (LLMs, agents, vision, speech)" · Optional block: Artificial intelligence

### AI3

What is the biggest problem in artificial intelligence that a new language could realistically help fix?

Type: long text · Shown to: A3 includes "Artificial intelligence (LLMs, agents, vision, speech)" · Optional block: Artificial intelligence

### ML1

What would Dhar need to offer in machine learning before you would use it for real work?

_Choose up to 5._

Type: several choices · Shown to: A3 includes "Machine learning (training, models, MLOps)" · Optional block: Machine learning · Up to 5 choices

| Id | Option |
| --- | --- |
| `o1` | A tensor library with automatic differentiation |
| `o2` | Training loops, optimizers and common layers |
| `o3` | Interop with PyTorch, TensorFlow and JAX models (ONNX) |
| `o4` | GPU and accelerator compute kernels |
| `o5` | Data loading, augmentation and batching pipelines |
| `o6` | Experiment tracking, model packaging and serving (MLOps) |
| `o7` | Classical ML (like scikit-learn) |
| `o8` | Reproducible, deterministic numerics |
| `o9` | Quantization and edge or embedded deployment |
| `other` | Other (with a text box) |

### ML2

Which libraries, frameworks or tools do you rely on in machine learning today that Dhar would need to work with or replace?

Type: long text · Shown to: A3 includes "Machine learning (training, models, MLOps)" · Optional block: Machine learning

### ML3

What is the biggest problem in machine learning that a new language could realistically help fix?

Type: long text · Shown to: A3 includes "Machine learning (training, models, MLOps)" · Optional block: Machine learning

### SY1

What would Dhar need to offer in systems and embedded programming before you would use it for real work?

_Choose up to 5._

Type: several choices · Shown to: A3 includes "Systems and embedded programming" · Optional block: Systems and embedded programming · Up to 5 choices

| Id | Option |
| --- | --- |
| `o1` | Direct hardware access (registers, volatile memory, inline assembly) |
| `o2` | A freestanding, no-runtime mode for kernels and bare metal |
| `o3` | Deterministic memory with no garbage-collection pauses |
| `o4` | Targets such as ARM Cortex-M, RISC-V and x86-64 |
| `o5` | Linker-script and memory-layout control |
| `o6` | Debugger support (GDB, LLDB, DWARF) |
| `o7` | Calling C libraries through the C ABI |
| `o8` | Interrupt, DMA and async embedded support |
| `o9` | Static analysis and worst-case stack bounds |
| `o10` | Safety-certification evidence (MISRA-style rules, DO-178C or ISO 26262 qualification) |
| `other` | Other (with a text box) |

### SY2

Which libraries, frameworks or tools do you rely on in systems and embedded programming today that Dhar would need to work with or replace?

Type: long text · Shown to: A3 includes "Systems and embedded programming" · Optional block: Systems and embedded programming

### SY3

What is the biggest problem in systems and embedded programming that a new language could realistically help fix?

Type: long text · Shown to: A3 includes "Systems and embedded programming" · Optional block: Systems and embedded programming

### SE1

What would Dhar need to offer in cybersecurity before you would use it for real work?

_Choose up to 5._

Type: several choices · Shown to: A3 includes "Cybersecurity" · Optional block: Cybersecurity · Up to 5 choices

| Id | Option |
| --- | --- |
| `o1` | A vetted, constant-time cryptography library |
| `o2` | Sockets, packet capture and raw network access |
| `o3` | Binary parsing, disassembly and reverse-engineering helpers |
| `o4` | Coverage-guided fuzzing support and sanitizers |
| `o5` | Memory-safety guarantees that remove whole bug classes |
| `o6` | A secure-by-default standard library |
| `o7` | Reproducible builds, SBOMs and signing |
| `o8` | Sandboxing and capability-style permissions |
| `o9` | Tooling for authorized penetration testing and exploit research |
| `o10` | Formal verification or audit-friendly semantics |
| `other` | Other (with a text box) |

### SE2

Which libraries, frameworks or tools do you rely on in cybersecurity today that Dhar would need to work with or replace?

Type: long text · Shown to: A3 includes "Cybersecurity" · Optional block: Cybersecurity

### SE3

What is the biggest problem in cybersecurity that a new language could realistically help fix?

Type: long text · Shown to: A3 includes "Cybersecurity" · Optional block: Cybersecurity

### BC1

What would Dhar need to offer in blockchain and web3 before you would use it for real work?

_Choose up to 5._

Type: several choices · Shown to: A3 includes "Blockchain and Web3" · Optional block: Blockchain and Web3 · Up to 5 choices

| Id | Option |
| --- | --- |
| `o1` | Smart-contract targets (Solana, WebAssembly contracts, EVM interop) |
| `o2` | Wallet, signing and key-management libraries (ed25519, secp256k1) |
| `o3` | Client SDKs for chains (RPC and transactions) |
| `o4` | Fully deterministic execution with no undefined behaviour |
| `o5` | Hashing, Merkle trees and zero-knowledge proof libraries |
| `o6` | Validator-grade performance and peer-to-peer networking |
| `o7` | Formal verification of contracts |
| `o8` | A local test validator, deployment and testing tooling |
| `o9` | Binary serialization (Borsh, protobuf, ABI encoding) |
| `o10` | Cross-chain and bridge interoperability |
| `other` | Other (with a text box) |

### BC2

Which libraries, frameworks or tools do you rely on in blockchain and web3 today that Dhar would need to work with or replace?

Type: long text · Shown to: A3 includes "Blockchain and Web3" · Optional block: Blockchain and Web3

### BC3

What is the biggest problem in blockchain and web3 that a new language could realistically help fix?

Type: long text · Shown to: A3 includes "Blockchain and Web3" · Optional block: Blockchain and Web3

## Your view of Dhar

_For everyone._

Report heading: `== SENTIMENT AND PRIORITIES ==`. Shown to: everyone.

### X1 (required)

Overall, how do you feel about a new systems programming language being built independently out of Nigeria and Africa?

Type: 1 to 5 · Shown to: everyone

Scale: 1 = Very negative, 5 = Very positive, 3 = Neutral

### X2 (required)

How important do you think it is for Africa to have its own independently built systems-level language and toolchain, rather than relying entirely on foreign-built ones?

Type: 1 to 5 · Shown to: everyone

Scale: 1 = Not important, 5 = Very important

### X3 (required)

On a scale of 0 to 10, how likely are you to try Dhar once a working, installable compiler is available?

Type: number scale · Shown to: everyone

Scale: 0 = Not at all likely, 10 = Extremely likely

### X4

What would most increase that likelihood?

Type: long text · Shown to: everyone

### X5 (required)

Of the areas Dhar aims to serve, which two or three matter most to you personally?

_Choose up to 3._

Type: several choices · Shown to: everyone · Up to 3 choices

| Id | Option |
| --- | --- |
| `software` | Backend and software development |
| `web` | Web |
| `mobile` | Mobile |
| `data` | Data analysis and data science |
| `ai` | Artificial intelligence (LLMs, agents, vision, speech) |
| `ml` | Machine learning (training, models, MLOps) |
| `systems` | Systems and embedded programming |
| `security` | Cybersecurity |
| `blockchain` | Blockchain and Web3 |

### X6

What has caused you to abandon or avoid adopting a new programming language in the past, even one you were initially curious about?

Type: long text · Shown to: everyone

### X7

Is there a feature, capability or design idea, not covered anywhere above, that you think Dhar should have?

Type: long text · Shown to: everyone

## Stay in touch

Report heading: `== CONTACT ==`. Shown to: everyone.

### C1 (required)

Would you like to stay informed as Dhar develops: early access, updates and ways to contribute?

Type: one choice · Shown to: everyone

| Id | Option |
| --- | --- |
| `yes` | Yes, here is how to reach me |
| `no` | Not right now |

### C2 (required)

What email address or other contact should we use?

Type: short text · Shown to: C1 is "Yes, here is how to reach me"
