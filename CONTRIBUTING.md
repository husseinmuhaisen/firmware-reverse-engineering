# Contributing

Keep changes focused on either packaging or technical content. Technical changes to a skill, reference, template, or Ghidra script need explicit approval from Hussein Muhaisen before implementation.

## Validate a checkout

Python 3.10 or later is required for the repository checks. Use a virtual environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python tools/validate_repo.py
.venv/bin/python -m unittest discover -s tests -v
```

On Windows, use `.venv\Scripts\python.exe` in place of `.venv/bin/python`.

The checks validate catalogs, plugin manifests, skill discovery metadata, local references, Python syntax, and the original content hashes. They do not execute firmware or prove the correctness of Ghidra scripts. See [compatibility testing](docs/compatibility.md#local-testing) for the host CLI checks.

## Content baseline

`tests/skill-content-baseline.json` records the SHA-256 digest of every original skill file from commit `e47b88bc96f2e269f71acfc702c0699f6593581b`, with a destination prefix for the new layout. This makes byte-preserving moves verifiable without depending on Git rename heuristics.

If a technical change is approved, include that approval in the pull request and update only its affected baseline entries. The baseline is a regression check, not a replacement for human review. CODEOWNERS records the maintainer; required code-owner review must be enabled separately in GitHub settings if desired.

## Pull requests

Explain the problem, the resulting behavior, what was tested, and any remaining limitations. Do not describe a parser check as an end-to-end skill evaluation. For technical fixes, include a meaningful reproducer and verification in the relevant tool runtime.

For releases, keep both plugin manifest versions aligned. After approval, bump them together and refresh the marketplace before checking the new installation. Run `python3 tools/validate_repo.py --release` before creating a release. Select and add the license, resolve the documented blockers, and complete the runtime checks first.
