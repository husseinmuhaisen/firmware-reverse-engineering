# Agent compatibility

## Supported installation paths

| Host | Packaging | Invocation |
| --- | --- | --- |
| Claude Code | `.claude-plugin` catalog and plugin manifest | `/firmware-reverse-engineering:<skill-name>` |
| Codex | `.agents/plugins` catalog and `.codex-plugin` manifest | Select in `/skills` or mention `$firmware-reverse-engineering:<skill-name>`. |
| Other Agent Skills hosts | Complete skill directories, including their resources | Depends on the host. |

All routes use the same five skills. Plugin skills have the `firmware-reverse-engineering:` prefix in both hosts. Standalone skill copies use their original names. The original frontmatter mentions Claude, but it contains the standard `name` and `description` fields and no host-specific tool restrictions. The wording has been preserved.

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
| Extraction | Binwalk and the filesystem utilities used by the selected recipe. Binwalk version differences are an open release issue. |
| Static analysis | `file`, `strings`, `readelf`, `objdump`, `xxd`, and relevant architecture toolchains. |
| Ghidra | Ghidra with its scripting runtime. The bundled scripts are Ghidra scripts, not ordinary standalone Python programs. Known script issues remain open. |
| Emulation | Linux with the relevant QEMU targets, GDB, and networking tools. Firmadyne/FirmAE are separate installations. |
| Reports | Markdown output works with the supplied templates. PDF conversion needs an external PDF skill or the Pandoc/LaTeX route already described by the reporting skill. |

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

Then perform a real static-analysis task against a small binary you own and check the output against `file` and `readelf`. Ghidra and emulation require their own runtime tests after the technical issues are resolved. Do not infer their correctness from manifest validation.

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
- [SpecterOps skills](https://github.com/SpecterOps/skills)
- [Vercel skills CLI](https://github.com/vercel-labs/skills)
