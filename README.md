# Firmware Reverse Engineering Skills

Five agent skills from [OrbitCurve](https://github.com/OrbitCurve) for firmware extraction, static analysis, Ghidra reverse engineering, emulation, and security reporting, by [Hussein Muhaisen](https://github.com/husseinmuhaisen).

The collection packages the existing workflows, references, templates, and Ghidra scripts for Claude Code and Codex. Installing it makes the instructions available to your agent; install the analysis tools separately.

**Validation:** Claude Code and Codex packaging/discovery checks, Ghidra script regressions, and selected extraction/reporting checks are included. See [tested versions and limitations](docs/release-readiness.md). Firmware emulation remains target-specific.

## Skills

| Skill | Purpose |
| --- | --- |
| [firmware-extraction](plugins/firmware-reverse-engineering/skills/firmware-extraction/SKILL.md) | Extract with unblob, summarize its JSON report, and investigate unresolved regions. |
| [firmware-static-analysis](plugins/firmware-reverse-engineering/skills/firmware-static-analysis/SKILL.md) | Inspect ELF architecture, metadata, strings, symbols, and binary structure. |
| [ghidra-re](plugins/firmware-reverse-engineering/skills/ghidra-re/SKILL.md) | Analyze firmware binaries with Ghidra and bundled analysis scripts. |
| [firmware-emulation](plugins/firmware-reverse-engineering/skills/firmware-emulation/SKILL.md) | Work with QEMU, GDB, network analysis, Firmadyne, and FirmAE. |
| [firmware-security-reports](plugins/firmware-reverse-engineering/skills/firmware-security-reports/SKILL.md) | Turn assessment evidence into findings, working notes, and reports. |

## Install

To test a local checkout, see [local testing](docs/compatibility.md#local-testing).

### Claude Code

In Claude Code:

```text
/plugin marketplace add OrbitCurve/firmware-reverse-engineering
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
codex plugin marketplace add OrbitCurve/firmware-reverse-engineering
codex plugin add firmware-reverse-engineering@firmware-reverse-engineering
```

Use `/skills` in Codex to find the installed skills, or mention one in a prompt:

```text
$firmware-reverse-engineering:firmware-static-analysis Inspect ./samples/busybox and report its architecture, imports, and protections.
```

### Other agents and standalone installation

For agents supported by the [skills CLI](https://github.com/vercel-labs/skills), list the available skills, then select your agent interactively:

```sh
npx skills add OrbitCurve/firmware-reverse-engineering --list
npx skills add OrbitCurve/firmware-reverse-engineering
```

This installs skill directories rather than a full plugin. Keep each directory's `references/`, `assets/`, and `scripts/` beside its `SKILL.md`. Avoid installing the same collection through both routes in the same agent.

For manual installation paths, updates, removal, and tool requirements, see [docs/compatibility.md](docs/compatibility.md).

## Repository layout

| Path | Contents |
| --- | --- |
| `.claude-plugin/marketplace.json` | Claude Code marketplace catalog. |
| `.agents/plugins/marketplace.json` | Codex marketplace catalog. |
| `plugins/firmware-reverse-engineering/` | One self-contained plugin with manifests for both hosts. |
| `plugins/firmware-reverse-engineering/skills/` | Five skills with references, templates and four Ghidra scripts. |
| `tools/` and `tests/` | Packaging/runtime checks and an approved content baseline. |
| `docs/` | Compatibility instructions and release findings. |

The old top-level skill directories have moved under the plugin. Update any local symlinks or installation paths that pointed at the old layout.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Changes to skill instructions, reference material, templates, and analysis scripts require explicit maintainer approval.

## License

Licensed under the [Apache License 2.0](LICENSE). See [NOTICE](NOTICE) for attribution.
