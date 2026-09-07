# Agent compatibility

## Supported installation paths

| Host | Packaging | Invocation |
| --- | --- | --- |
| Claude Code | `.claude-plugin` catalog and plugin manifest | `/firmware-reverse-engineering:<skill-name>` |
| Codex | `.agents/plugins` catalog and `.codex-plugin` manifest | Select in `/skills` or mention `$firmware-reverse-engineering:<skill-name>`. |
| Other Agent Skills hosts | Complete skill directories, including their resources | Depends on the host. |

All routes use the same five skills. Plugin skills have the `firmware-reverse-engineering:` prefix in both hosts. Standalone skill copies use their original names. Frontmatter uses standard `name` and `description` fields, host-neutral wording and no host-specific tool restrictions.

If you prefer manual installation, copy the desired complete skill directories from `plugins/firmware-reverse-engineering/skills/` into one of these locations:

| Host | Per-project location | Per-user location |
| --- | --- | --- |
| Claude Code | `.claude/skills/<skill-name>/` | `~/.claude/skills/<skill-name>/` |
| Codex | `.agents/skills/<skill-name>/` | `~/.agents/skills/<skill-name>/` |

For example, copy `firmware-static-analysis/`, including `references/`, as a directory named `firmware-static-analysis` under the chosen location. Do not copy only `SKILL.md`. Back up an existing installation before replacing it. On Windows, `~` refers to your user profile.

## Tool requirements

The plugin contains instructions and analysis resources. It does not install external software or configure MCP servers.

| Workflow | External environment needed |
| --- | --- |
| Extraction | Binwalk 3.1.0 plus selected external extractors. Development-branch and 2.x flags differ. |
| Static analysis | `file`, `strings`, `readelf`, `objdump`, `xxd`, and relevant architecture toolchains. |
| Ghidra | Ghidra 12.1.3, JDK 21 and the bundled Jython extension. Scripts explicitly select Jython, not the default PyGhidra runtime. |
| Emulation | Linux with the relevant QEMU targets, GDB, and networking tools. Firmadyne/FirmAE are separate installations. |
| Reports | Markdown output works with the supplied templates. PDF conversion needs Pandoc/XeLaTeX or a separately installed PDF skill. |

Most recipes assume Linux and use Debian/Ubuntu package names. Native Windows and macOS firmware execution have not been validated; use a suitable Linux environment for those recipes. Agent installation compatibility does not establish compatibility of every firmware target or tool version.

## Local testing

From a checkout, validate both manifests and the catalog:

```sh
python3 tools/validate_repo.py
python3 -m unittest discover -s tests -v
claude plugin validate . --strict
claude plugin validate ./plugins/firmware-reverse-engineering --strict
python3 tools/check_codex_discovery.py
```

The Codex discovery probe uses the local app-server API to read the catalog and enumerate its five skills. It does not install the plugin or call a model. Pass `--cli /path/to/codex` if the CLI is not on your PATH.

Load the plugin in Claude Code for a session:

```sh
claude --plugin-dir ./plugins/firmware-reverse-engineering
```

Verify that all five names appear, invoke `/firmware-reverse-engineering:firmware-static-analysis`, and ask it to locate its bundled architecture reference. For Codex, register the local checkout and install the plugin:

```sh
codex plugin marketplace add /absolute/path/to/firmware-reverse-engineering
codex plugin add firmware-reverse-engineering@firmware-reverse-engineering
codex plugin list --marketplace firmware-reverse-engineering
```

In Codex, verify the five skills in `/skills`, select `firmware-static-analysis`, and ask it to locate `references/architectures.md`. Local and remote copies use the same marketplace name, so remove the local test registration before switching to the hosted repository.

Test standalone discovery without installing anything:

```sh
npx skills add . --list
```

Then perform a real static-analysis task against a small binary you own and check the output against `file` and `readelf`. Run the separate runtime checks below. Do not infer firmware behavior from manifest validation.

## Runtime checks

Install `requirements-dev.txt` before the unit tests. The Ghidra test needs GCC,
Ghidra 12.1.3 and JDK 21. Install its bundled Jython extension through File →
Install Extensions, or unpack the release's `Extensions/Ghidra/*_Jython.zip`
into `Ghidra/Extensions/` in an isolated test installation.

```sh
python3 tools/validate_repo.py --release
python3 -m unittest discover -s tests -v
python3 tools/check_ghidra_runtime.py --ghidra-home /absolute/path/to/ghidra_12.1.3_PUBLIC
python3 tools/check_binwalk_runtime.py --binwalk /absolute/path/to/binwalk
```

The Ghidra test compiles a benign x86-64 ELF, runs all four scripts twice and
checks naming, annotations, direct call sites, both table byte orders and
bounded scanning across sparse memory. It requires an explicit success marker
because headless Ghidra can exit zero after a script exception. The Binwalk test
checks extraction against exact gzip plaintext, CLI filters, JSON and entropy
output. Neither test boots vendor firmware or demonstrates exploitability.

## Updates and removal

In Claude Code:

```text
/plugin marketplace update firmware-reverse-engineering
/plugin update firmware-reverse-engineering@firmware-reverse-engineering
```

To remove it:

```text
/plugin uninstall firmware-reverse-engineering@firmware-reverse-engineering
/plugin marketplace remove firmware-reverse-engineering
```

For Codex, refresh the catalog and reinstall the updated plugin:

```sh
codex plugin marketplace upgrade firmware-reverse-engineering
codex plugin add firmware-reverse-engineering@firmware-reverse-engineering
```

To remove it:

```sh
codex plugin remove firmware-reverse-engineering@firmware-reverse-engineering
codex plugin marketplace remove firmware-reverse-engineering
```

For manual copies, update or remove only the five skill directories you installed. Do not remove the host's whole skills directory.

## Sources

Packaging was checked against these sources on September 7, 2026:

- [Claude Code plugin reference](https://code.claude.com/docs/en/plugins-reference)
- [Claude Code marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [OpenAI skills documentation](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI plugins documentation](https://learn.chatgpt.com/docs/plugins)
- [Trail of Bits skills](https://github.com/trailofbits/skills)
- [Vercel skills CLI](https://github.com/vercel-labs/skills)
