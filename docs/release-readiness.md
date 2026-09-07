# Release readiness review

Reviewed September 7, 2026. Original commit: `e47b88bc96f2e269f71acfc702c0699f6593581b`.

## Authorized scope

The initial packaging commit moved all 25 original skill files without byte
changes. Hussein subsequently explicitly authorized the technical fixes and
Apache-2.0 licensing. The technical revision fixes concrete errors while
retaining the five skills and their workflows. It adds Apache-2.0 with matching
plugin metadata and NOTICE files.
The content baseline now records the approved revised files and missing script.
The packaging and technical fixes were merged in [PR #1](https://github.com/OrbitCurve/firmware-reverse-engineering/pull/1) before the repository was transferred to OrbitCurve.

## Technical fixes

| Area | Corrections |
| --- | --- |
| Ghidra scripts | Explicit Jython runtime for 12.1.3; initialized state/imports; proper Java byte arrays; bounded initialized-block scans; both crypto-table byte orders; cancellation checks; repeated call sites; preserved analyst names/comments; idempotent annotations. Supplied the documented auto-rename implementation. |
| Ghidra examples | Correct signature API use, loader entry points, A32 prologue byte order, previous-instruction traversal, analyzer API and headless script paths. Marked incomplete inference sketches and optional export scripts accurately. |
| Analysis evidence | Source/sink co-occurrence is not taint analysis; crypto prefixes and string/API matches are candidates. PIE is separate from runtime ASLR; RELRO, canary and Fortify conclusions require appropriate evidence. |
| Extraction | Pinned examples to tagged Binwalk 3.1.0; corrected filters, entropy and output assumptions; removed nonexistent options. Corrected JFFS2/UBI mounting assumptions, RomFS extraction, filesystem tool syntax, byte order, XOR/header checks and AES probe validation. |
| Emulation/debugging | Corrected FirmAE modes and Firmadyne flags, AFL++ invocation, QEMU paths and machine prerequisites, GDB userspace attach/core/Thumb/format-argument examples, and snapshot limitations. Removed invented performance/success guarantees. |
| Network examples | Distinguished QEMU user networking from system NAT and GDB traffic; corrected certificate decoding/trust setup, TCP stream assumptions, packet modification, TCP fuzz connections and Lua PDU bounds/reassembly. |
| Reporting | Corrected CVSS definitions and scenario assumptions, separated examples from evidence, fixed privilege dropping before exec, made PDF dependencies explicit and repaired nested Markdown fences/status glyphs. |

## Verification and limits

| Check | Evidence / boundary |
| --- | --- |
| Repository checks | Five skills, matching manifests/catalogs/licenses, complete resources and approved SHA-256 baseline. Mutation tests exercise dropped files, changed content, bad paths and metadata drift. |
| Claude Code | 2.1.263 strict marketplace/plugin validation. No authenticated model session or complete firmware task is claimed. |
| Codex | 0.153.4 app-server `plugin/read` discovers all five namespaced skills from the local marketplace, without model calls. |
| Standalone discovery | `skills` 1.5.24 lists all five skills. This does not prove each supported host's runtime behavior. |
| Ghidra | 12.1.3 with Jython and JDK 21: compiled x86-64 fixture, four scripts twice, exact call-site and annotation assertions, LE/BE constants and a large uninitialized memory block. Not an ARM/MIPS accuracy benchmark or a PyGhidra support claim. |
| Binwalk | Tagged 3.1.0: known gzip data recovered byte-for-byte, signature filters/all-offset scanning, JSON output and entropy PNG. Jefferson 0.4.7 and ubi-reader 0.8.16 CLI options checked; not every filesystem variant extracted. |
| Static skill forward test | An independent agent used the revised skill on the compiled fixture: verified the guarded copies, distinguished literal comparison from an authentication boundary, and left runtime ASLR unclaimed. |
| Executable examples | Python syntax; documented CVSS vectors recomputed using `cvss` 3.6; AES-ECB/CBC and header-offset regressions using PyCryptodome 3.23.0. |
| PDF | Supplied report template converted with Pandoc/XeLaTeX. Final client reports still need evidence and page-layout review. |
| Device-specific workflows | QEMU full-system boot, FirmAE/Firmadyne installation, live network interception, arbitrary firmware and exploitability were not end-to-end tested. Recipes state their required environment and target assumptions. |

The earlier marketplace-install attempt could not finish in this environment
because execution reported cancelled network approval. Loader/manifest tests
are reported separately from installed agent sessions. Nothing here guarantees
that every vendor kernel, filesystem variant or analyzer hypothesis will work.

## Reproduction and upstream evidence

See [compatibility.md](compatibility.md#runtime-checks) for commands. CI runs the
lightweight regressions and a checksum-pinned Ghidra integration test. Binwalk's
runtime test is separately runnable with 3.1.0 installed.

- [Binwalk 3.1.0 CLI](https://github.com/ReFirmLabs/binwalk/blob/v3.1.0/src/cliparser.rs) and [entropy implementation](https://github.com/ReFirmLabs/binwalk/blob/v3.1.0/src/entropy.rs). The development branch has different flags; `-C` is valid in 3.1.0.
- [Ghidra 12.1.3 release](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.3_build); bundled API documentation and Jython extension examples were used for runtime corrections.
- [FirmAE mode parser](https://github.com/pr0v3rbs/FirmAE/blob/master/run.sh) and [Firmadyne workflow](https://github.com/firmadyne/firmadyne#usage)
- [AFL++ QEMU mode](https://github.com/AFLplusplus/AFLplusplus/blob/stable/qemu_mode/README.md)
- [QEMU ARM board requirements](https://www.qemu.org/docs/master/system/target-arm.html) and [GDB support](https://www.qemu.org/docs/master/system/gdb.html)
- [GDB breakpoint command lists](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Break-Commands.html)
- [Wireshark TLS guidance](https://wiki.wireshark.org/TLS)
- [FIRST CVSS 3.1 specification](https://www.first.org/cvss/v3.1/specification-document) and [user guide](https://www.first.org/cvss/v3.1/user-guide)
