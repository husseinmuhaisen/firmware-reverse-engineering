# Firmware Reverse Engineering Skills

Five agent skills for firmware extraction, static analysis, Ghidra reverse engineering, emulation, and security reporting, by [Hussein Muhaisen](https://github.com/husseinmuhaisen).

The collection packages the existing workflows, references, templates, and Ghidra scripts for Claude Code and Codex. Installing it makes the instructions available to your agent; install the analysis tools separately.

**Release status:** packaging is prepared for review. Known technical issues and the license decision remain open in [docs/release-readiness.md](docs/release-readiness.md). This is not yet an end-to-end validated firmware analysis environment.

## Skills

| Skill | Purpose |
| --- | --- |
| [firmware-extraction](plugins/firmware-reverse-engineering/skills/firmware-extraction/SKILL.md) | Unpack firmware images and embedded filesystems. |
| [firmware-static-analysis](plugins/firmware-reverse-engineering/skills/firmware-static-analysis/SKILL.md) | Inspect ELF architecture, metadata, strings, symbols, and binary structure. |
| [ghidra-re](plugins/firmware-reverse-engineering/skills/ghidra-re/SKILL.md) | Analyze firmware binaries with Ghidra and bundled analysis scripts. |
| [firmware-emulation](plugins/firmware-reverse-engineering/skills/firmware-emulation/SKILL.md) | Work with QEMU, GDB, network analysis, Firmadyne, and FirmAE. |
| [firmware-security-reports](plugins/firmware-reverse-engineering/skills/firmware-security-reports/SKILL.md) | Turn assessment evidence into findings, working notes, and reports. |

## Install

These commands apply once the packaging changes are merged into the default branch. To test an unmerged checkout, see [local testing](docs/compatibility.md#local-testing).

### Claude Code

In Claude Code:

```text
/plugin marketplace add husseinmuhaisen/firmware-reverse-engineering
/plugin install firmware-reverse-engineering@firmware-reverse-engineering
```

Invoke a skill with its plugin namespace:

```text
/firmware-reverse-engineering:firmware-static-analysis
```

Then provide the binary path and your analysis goal. The agent can also select skills from their descriptions.

### Codex

In your terminal:

```sh
codex plugin marketplace add husseinmuhaisen/firmware-reverse-engineering
codex plugin add firmware-reverse-engineering@firmware-reverse-engineering
```

Use `/skills` in Codex to find the installed skills, or mention one in a prompt:

```text
$firmware-reverse-engineering:firmware-static-analysis Inspect ./samples/busybox and report its architecture, imports, and protections.
```

### Other agents and standalone installation

For agents supported by the [skills CLI](https://github.com/vercel-labs/skills), list the available skills, then select your agent interactively:

```sh
npx skills add husseinmuhaisen/firmware-reverse-engineering --list
npx skills add husseinmuhaisen/firmware-reverse-engineering
```

This installs skill directories rather than a full plugin. Keep each directory's `references/`, `assets/`, and `scripts/` beside its `SKILL.md`. Avoid installing the same collection through both routes in the same agent.

For manual installation paths, updates, removal, and tool requirements, see [docs/compatibility.md](docs/compatibility.md).

## Repository layout

| Path | Contents |
| --- | --- |
| `.claude-plugin/marketplace.json` | Claude Code marketplace catalog. |
| `.agents/plugins/marketplace.json` | Codex marketplace catalog. |
| `plugins/firmware-reverse-engineering/` | One self-contained plugin with manifests for both hosts. |
| `plugins/firmware-reverse-engineering/skills/` | The five original skill directories and all supporting files. |
| `tools/` and `tests/` | Packaging checks and a content preservation baseline. |
| `docs/` | Compatibility instructions and release findings. |

The old top-level skill directories have moved under the plugin. Update any local symlinks or installation paths that pointed at the old layout.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Changes to skill instructions, reference material, templates, and analysis scripts require explicit maintainer approval.

## License

No license has been selected yet. The maintainer must choose the license before this is advertised as an open-source release.
