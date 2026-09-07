# Repository maintenance

This repository distributes firmware reverse engineering skills as one Claude Code and Codex plugin.

## Preserve technical content

Do not edit skill instructions, frontmatter, references, templates, or analysis scripts under `plugins/firmware-reverse-engineering/skills/` without explicit approval from Hussein Muhaisen. Moving complete directories without changing their bytes is a packaging change.

Keep packaging work in separate changes from technical revisions. Record discovered technical issues in `docs/release-readiness.md` instead of silently repairing or working around them. Do not add instruction wrappers that alter the protected workflows.

## Packaging

- Keep one copy of each skill and its resources, inside the plugin directory.
- Keep the Claude Code and Codex plugin names, versions, descriptions, and skill roots consistent.
- Marketplace source paths are relative to the repository root.
- Do not add hooks, MCP servers, dependency installers, or automatic tool permissions unless requested.
- Never infer an open-source license or claim an analysis workflow was tested when only packaging was checked.

## Validation

Run `python3 tools/validate_repo.py` and `python3 -m unittest discover -s tests -v`. These check packaging, the approved content baseline, and selected executable examples. `python3 tools/validate_repo.py --release` also treats missing resources and license files as release blockers. Run the Ghidra and Binwalk runtime checks in docs/compatibility.md when changing their scripts or recipes.

The content baseline records approved bytes. Update it only with explicit approval for the corresponding technical changes; do not regenerate it just to make checks pass.
