#!/usr/bin/env python3
"""Check packaging and the approved content baseline without executing analysis workflows."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

PLUGIN = "firmware-reverse-engineering"
SKILLS = {
    "firmware-emulation", "firmware-extraction", "firmware-security-reports",
    "firmware-static-analysis", "ghidra-re",
}
RESOURCE = re.compile(r"`((?:references|scripts|assets)/[^`\s]+)`")
LINK = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)\)")


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name}: expected an object")
    return value


def validate(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    blockers: list[str] = []
    plugin = root / "plugins" / PLUGIN
    skills_root = plugin / "skills"
    try:
        claude = read_json(plugin / ".claude-plugin/plugin.json")
        codex = read_json(plugin / ".codex-plugin/plugin.json")
        for field in ("name", "version", "description", "author", "repository", "skills", "license"):
            if not claude.get(field) or claude.get(field) != codex.get(field):
                errors.append(f"Plugin manifests must agree on {field}")
        if claude.get("license") != "Apache-2.0":
            errors.append("Plugin license must be Apache-2.0")
        if claude.get("name") != PLUGIN:
            errors.append("Plugin name does not match its directory")
        if not re.fullmatch(r"\d+\.\d+\.\d+", str(claude.get("version", ""))):
            errors.append("Plugin version must be major.minor.patch")
        if claude.get("skills") != "./skills/":
            errors.append("Plugin must discover ./skills/")
        for host, manifest in (("Claude", claude), ("Codex", codex)):
            if any(k in manifest for k in ("hooks", "mcpServers", "apps", "commands", "agents")):
                errors.append(f"{host}: unexpected executable or additional components")
        interface = codex.get("interface", {})
        for field in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
            if not isinstance(interface.get(field), str) or not interface[field].strip():
                errors.append(f"Codex interface missing {field}")

        for path, native in ((".claude-plugin/marketplace.json", False), (".agents/plugins/marketplace.json", True)):
            catalog = read_json(root / path)
            entries = catalog.get("plugins", [])
            if catalog.get("name") != PLUGIN or len(entries) != 1:
                errors.append(f"{path}: expected one plugin in the {PLUGIN} marketplace")
                continue
            entry = entries[0]
            source = entry.get("source")
            expected = {"source": "local", "path": f"./plugins/{PLUGIN}"} if native else f"./plugins/{PLUGIN}"
            if source != expected or entry.get("name") != PLUGIN:
                errors.append(f"{path}: plugin name or source does not resolve to the packaged plugin")
            if "version" in entry and entry["version"] != claude.get("version"):
                errors.append(f"{path}: stale marketplace version")
            if native:
                if entry.get("policy") != {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}:
                    errors.append(f"{path}: unexpected installation policy")
                if entry.get("category") != "Security":
                    errors.append(f"{path}: expected Security category")

        baseline = read_json(root / "tests/skill-content-baseline.json")
        expected_prefix = f"plugins/{PLUGIN}/skills/"
        if baseline.get("destination_prefix") != expected_prefix:
            errors.append("Content baseline has an unexpected destination prefix")
        expected_files = baseline["files"]
        actual_files = {
            str(p.relative_to(skills_root)).replace("\\", "/"): p
            for p in skills_root.rglob("*") if p.is_file()
            and "__pycache__" not in p.parts and p.suffix != ".pyc"
        }
        for path in sorted(set(expected_files) - set(actual_files)):
            errors.append(f"Approved skill file missing: {path}")
        for path in sorted(set(actual_files) - set(expected_files)):
            errors.append(f"Skill file added without a baseline entry: {path}")
        for path in sorted(set(actual_files) & set(expected_files)):
            if hashlib.sha256(actual_files[path].read_bytes()).hexdigest() != expected_files[path]:
                errors.append(f"Protected skill content changed: {path}")

        discovered = {p.parent.name for p in skills_root.glob("*/SKILL.md")}
        if discovered != SKILLS:
            errors.append(f"Expected five skills, found: {sorted(discovered)}")
        for skill_file in sorted(skills_root.glob("*/SKILL.md")):
            data = skill_file.read_text(encoding="utf-8")
            match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", data, re.S)
            if not match:
                errors.append(f"{skill_file.parent.name}: missing YAML frontmatter")
                continue
            meta = yaml.safe_load(match.group(1))
            if not isinstance(meta, dict):
                errors.append(f"{skill_file.parent.name}: invalid frontmatter mapping")
                continue
            name, description = meta.get("name"), meta.get("description")
            if name != skill_file.parent.name or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(name)):
                errors.append(f"{skill_file.parent.name}: invalid skill name")
            if not isinstance(description, str) or not 1 <= len(description) <= 1024:
                errors.append(f"{skill_file.parent.name}: description must have 1-1024 characters")
            for resource in sorted(set(RESOURCE.findall(data))):
                if not (skill_file.parent / resource).is_file():
                    blockers.append(f"{skill_file.relative_to(root)} references missing {resource}")

        for path in skills_root.rglob("*.py"):
            ast.parse(path.read_bytes(), filename=str(path))
        for path in plugin.rglob("*"):
            if path.is_symlink():
                errors.append(f"Plugin must be self-contained without symlinks: {path.relative_to(root)}")

        docs = [root / "README.md", root / "CONTRIBUTING.md", *sorted((root / "docs").glob("*.md"))]
        for path in docs:
            for target in LINK.findall(path.read_text(encoding="utf-8")):
                url = urlsplit(target)
                if url.scheme or url.netloc or not url.path:
                    continue
                if not (path.parent / unquote(url.path)).exists():
                    errors.append(f"Broken documentation link in {path.relative_to(root)}: {target}")

        for name in ("LICENSE", "NOTICE"):
            if not (root / name).is_file() or not (plugin / name).is_file():
                blockers.append(f"Missing {name}: ship it in both repository and plugin")
            elif (root / name).read_bytes() != (plugin / name).read_bytes():
                errors.append(f"Repository and plugin {name} must match")
    except (OSError, ValueError, TypeError, KeyError, AttributeError, SyntaxError, yaml.YAMLError) as exc:
        errors.append(f"Validation could not complete: {exc}")
    return errors, blockers


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--release", action="store_true", help="Fail on missing resources or a missing license as well")
    args = parser.parse_args()
    errors, blockers = validate(args.root.resolve())
    for item in errors:
        print(f"ERROR: {item}")
    for item in blockers:
        print(f"RELEASE BLOCKER: {item}")
    if errors or (args.release and blockers):
        return 1
    print("Packaging passed: five skills; manifests, catalogs, links, syntax, and content baseline checked.")
    print("This does not validate firmware analysis behavior. See docs/release-readiness.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
