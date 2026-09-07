# Release readiness review

Review date: September 7, 2026. Original repository commit: `e47b88bc96f2e269f71acfc702c0699f6593581b` (January 17, 2026).

## Scope and preservation

This change prepares repository structure, agent packaging, installation documentation, and validation. The five original skills and all 25 files inside them were moved without byte changes. That includes frontmatter, instructions, references, templates, and all three Ghidra scripts.

The repository was already public at review time. No visibility change, default-branch merge, release tag, or license selection is part of this packaging change.

## Technical changes awaiting maintainer approval

These are findings, not replacement instructions. No proposed fix below has been applied to the skills.

| Finding | Evidence | Proposed work requiring approval |
| --- | --- | --- |
| Missing Ghidra script | `ghidra-re/SKILL.md` directs the agent to run `scripts/auto_rename.py`, but that file is absent from the original repository. | Decide whether to supply the intended implementation or remove/correct the reference. |
| Undefined Ghidra script state | `find_auth_functions.py` and `find_buffer_overflows.py` use `listing` without initialization. Minimal probes of their helper functions reproduce `NameError: name 'listing' is not defined`. Ghidra's documented script state supplies `currentProgram`; it does not supply a `listing` field. | Initialize the listing through the program API and test the scripts on a small fixture in the selected Ghidra runtime. |
| Missing symbol import | `find_auth_functions.py` and `find_crypto.py` use `SourceType.ANALYSIS` without importing `ghidra.program.model.symbol.SourceType`. The data-package wildcard import in `find_crypto.py` does not import the symbol package. | Add the required import and exercise the rename paths in Ghidra. |
| Crypto scan termination and runtime assumptions | `find_crypto.py` advances addresses with `addr.add(4)` under `while addr`, catches memory-read errors, and has no explicit end-address bound. Its byte search passes a Python string to a Java byte-array API. These paths were reviewed, not run in Ghidra. | Bound scanning to initialized memory blocks, check cancellation, and verify byte conversion in the intended scripting runtime. |
| Binwalk CLI drift | Extraction instructions use `-C`, `--dd`, `-J`, and other legacy options. The current upstream Rust CLI parser instead defines options such as `--directory` and `--png`; it does not define those legacy flags. Some recipes also need a correctness review beyond a simple version substitution. | Choose supported Binwalk versions and validate command examples against a known firmware fixture before revising them. |
| External report capability | The reporting skill refers to a separate `pdf` skill, which this repository does not include. It also describes a Pandoc route. | Decide whether to make the dependency explicit in the skill and document a tested conversion route. |

Paths in this table are relative to `plugins/firmware-reverse-engineering/skills/` where appropriate.

The helper probes establish a missing-name problem only. They are not Ghidra integration tests. QEMU, Firmadyne, FirmAE, extraction tools, and PDF rendering have not been exercised against firmware in this packaging review. Do not claim all technical recipes are current or fully working until their runtime checks are complete.

## License decision

The original repository contains no license file. No license was added or inferred. The maintainer must select a license and confirm any needed attribution before an open-source release. Plugin manifests intentionally omit the license field until then.

## Verification

- SHA-256 baseline covers all 25 original skill files, including all three scripts.
- Plugin and marketplace metadata are validated separately from technical behavior.
- Repository checks surface the missing `auto_rename.py` and license as release blockers.
- Regression tests deliberately change a skill, delete a reference, add an unapproved script, break a catalog path, and drift a plugin version to ensure those failures are detected.
- Claude Code `2.1.263` strict manifest validation and the Codex plugin schema validator accept the package.
- Codex CLI `0.153.4` app-server `plugin/read` loaded the local marketplace and discovered all five namespaced skills. This was a read-only discovery check, not an installed model session.
- The `skills` CLI `1.5.24` found all five skills with `skills add . --list`; it did not install them.
- Claude Code marketplace installation and broader skill validation could not complete in the review environment: execution reported that network approval was cancelled. No Claude model session or firmware analysis run is claimed.

`python3 tools/validate_repo.py` checks packaging and prints detected release blockers. `python3 tools/validate_repo.py --release` exits unsuccessfully while a required local resource or license is missing. Neither command substitutes for the runtime work in the table above.

## Upstream evidence

- [Binwalk CLI parser](https://github.com/ReFirmLabs/binwalk/blob/master/src/cliparser.rs), reviewed September 7, 2026.
- [GhidraScript API source](https://github.com/NationalSecurityAgency/ghidra/blob/master/Ghidra/Features/Base/src/main/java/ghidra/app/script/GhidraScript.java).
- [Ghidra FlatProgramAPI source](https://github.com/NationalSecurityAgency/ghidra/blob/master/Ghidra/Features/Base/src/main/java/ghidra/program/flatapi/FlatProgramAPI.java).
- [Ghidra SourceType API](https://ghidra.re/ghidra_docs/api/ghidra/program/model/symbol/SourceType.html).

See [compatibility.md](compatibility.md) for agent documentation and reproducible host checks.
