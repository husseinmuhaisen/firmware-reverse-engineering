"""Exercise the preservation and discovery checks with broken checkout copies."""

import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validate_repo", ROOT / "tools/validate_repo.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__"))
        self.skills = self.root / "plugins/firmware-reverse-engineering/skills"

    def test_preserved_checkout_and_visible_blockers(self):
        errors, blockers = validator.validate(self.root)
        self.assertEqual(errors, [])
        self.assertTrue(any("auto_rename.py" in issue for issue in blockers))
        self.assertTrue(any("LICENSE" in issue for issue in blockers))

    def test_skill_edit_is_rejected(self):
        path = self.skills / "firmware-extraction/SKILL.md"
        path.write_bytes(path.read_bytes() + b"\nChanged instruction.\n")
        errors, _ = validator.validate(self.root)
        self.assertTrue(any("Protected skill content changed" in issue for issue in errors))

    def test_dropped_resource_is_rejected(self):
        (self.skills / "firmware-static-analysis/references/architectures.md").unlink()
        errors, blockers = validator.validate(self.root)
        self.assertTrue(any("Original skill file missing" in issue for issue in errors))
        self.assertTrue(any("architectures.md" in issue for issue in blockers))

    def test_unapproved_new_script_is_rejected(self):
        (self.skills / "ghidra-re/scripts/auto_rename.py").write_text("pass\n")
        errors, _ = validator.validate(self.root)
        self.assertTrue(any("added without a baseline" in issue for issue in errors))

    def test_broken_catalog_source_is_rejected(self):
        path = self.root / ".agents/plugins/marketplace.json"
        data = json.loads(path.read_text())
        data["plugins"][0]["source"]["path"] = "./nonexistent"
        path.write_text(json.dumps(data))
        errors, _ = validator.validate(self.root)
        self.assertTrue(any("does not resolve" in issue for issue in errors))

    def test_manifest_version_drift_is_rejected(self):
        path = self.root / "plugins/firmware-reverse-engineering/.codex-plugin/plugin.json"
        data = json.loads(path.read_text())
        data["version"] = "9.0.0"
        path.write_text(json.dumps(data))
        errors, _ = validator.validate(self.root)
        self.assertIn("Plugin manifests must agree on version", errors)


if __name__ == "__main__":
    unittest.main()
