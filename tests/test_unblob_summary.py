"""Check that report reduction preserves evidence and does not manufacture success."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "plugins/firmware-reverse-engineering/skills/firmware-extraction/scripts/summarize_unblob.py"
spec = importlib.util.spec_from_file_location("unblob_summary", SCRIPT)
summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary)


def task(path, depth=0, reports=None, subtasks=None, size=4096, directory=False):
    return {"task": {"path": path, "depth": depth, "blob_id": ""},
            "reports": [{"__typename__": "StatReport", "path": path, "size": size,
                         "is_file": not directory, "is_dir": directory}, *(reports or [])],
            "subtasks": subtasks or []}


def chunk(**fields):
    return {"__typename__": "ChunkReport", "id": "chunk-1", "handler_name": "tar",
            "start_offset": 512, "end_offset": 1536, "size": 1024,
            "is_encrypted": False, "extraction_reports": [], **fields}


def entropy():
    return {"__typename__": "RandomnessReport",
            "shannon": {"percentages": [0.0, 75.0, 100.0], "mean": 62.5, "block_size": 1024},
            "chi_square": {"percentages": [5.0, 20.0, 40.0], "mean": 20.0, "block_size": 1024}}


class UnblobSummaryTests(unittest.TestCase):
    def test_out_of_order_results_keep_sources_offsets_and_output_links(self):
        data = [task("/output/nested.tar", 1, [chunk(id="nested", start_offset=0, end_offset=1024)]),
                task("/firmware.bin", reports=[chunk()], subtasks=[
                    {"path": "/output", "depth": 1, "blob_id": "chunk-1"}])]
        result = summary.summarize(data)
        self.assertEqual(result["sections"]["inputs"]["items"][0]["source"], "/firmware.bin")
        rows = result["sections"]["chunks"]["items"]
        self.assertEqual([(r["source"], r["start"], r["end_exclusive"]) for r in rows],
                         [("/firmware.bin", 512, 1536), ("/output/nested.tar", 0, 1024)])
        self.assertEqual(rows[0]["output_paths"], ["/output"])
        self.assertEqual(rows[0]["pointer"], "/1/reports/1")
        data[1]["subtasks"][0]["chunk_id"] = data[1]["subtasks"][0].pop("blob_id")
        self.assertEqual(summary.summarize(data)["sections"]["chunks"]["items"][0]["output_paths"], ["/output"])

    def test_large_inventory_does_not_displace_nested_failures_or_custom_reports(self):
        data = [task(f"/output/file-{i:04d}", 1, [entropy()]) for i in range(1000)]
        data.append(task("/firmware.bin", reports=[chunk(extraction_reports=[
            {"__typename__": "ExtractorDependencyNotFoundReport", "severity": "ERROR", "dependencies": ["7z"]},
            {"__typename__": "ExtractCommandFailedReport", "severity": "WARNING", "exit_code": 2,
             "command": "7z x image", "stdout": "A" * 10000, "stderr": "B" * 10000},
        ]), {"__typename__": "VendorSpecificReport", "message": "x" * 10000}]))
        result = summary.summarize(data, limit=2)
        self.assertEqual(result["sections"]["unclassified_files"]["total"], 1000)
        self.assertEqual(result["sections"]["unclassified_files"]["omitted"], 998)
        self.assertEqual(result["sections"]["issues"]["total"], 3)
        issues = result["sections"]["issues"]["items"]
        self.assertEqual(issues[0]["detail"]["dependencies"], ["7z"])
        self.assertIn("extraction_reports", issues[0]["pointer"])
        self.assertEqual(result["counts"]["errors"], 1)
        self.assertEqual(result["counts"]["warnings"], 1)
        last = summary.summarize(data, limit=2, offset=2)["sections"]["issues"]["items"][0]
        self.assertEqual(last["type"], "VendorSpecificReport")
        self.assertIn("truncated", last["detail"]["message"])
        self.assertLess(len(json.dumps(result)), len(json.dumps(data)) // 20)
        self.assertNotIn('"success"', json.dumps(result))

    def test_unknown_regions_whole_files_and_absent_randomness_are_distinct(self):
        unknown = {"__typename__": "UnknownChunkReport", "id": "unknown", "start_offset": 0,
                   "end_offset": 4096, "size": 4096, "randomness": entropy()}
        data = [task("/whole-unknown.bin", reports=[entropy()]),
                task("/mixed.bin", reports=[unknown]), task("/ordinary.txt", depth=1)]
        result = summary.summarize(data)
        region = result["sections"]["unknown_regions"]["items"][0]
        self.assertEqual(region["randomness"]["shannon_percent"]["mean"], 62.5)
        self.assertEqual(region["randomness"]["shannon_percent"]["min"], 0.0)
        whole = next(r for r in result["sections"]["unclassified_files"]["items"] if r["source"] == "/whole-unknown.bin")
        self.assertIsNotNone(whole["randomness"])
        unknown["randomness"] = None
        self.assertIsNone(summary.summarize(data)["sections"]["unknown_regions"]["items"][0]["randomness"])
        self.assertNotIn("percentages", json.dumps(result))

    def test_depth_limit_and_source_filter_preserve_counts(self):
        data = [task("/output", depth=2, directory=True), task("/normal.txt", depth=1)]
        result = summary.summarize(data, extract_depth=2, path_filter="/output")
        self.assertEqual(result["counts"]["tasks"], 2)
        self.assertEqual(result["sections"]["depth_limit_tasks"]["total"], 1)
        self.assertEqual(result["sections"]["unclassified_files"]["total"], 1)
        self.assertEqual(result["sections"]["unclassified_files"]["matched"], 0)
        self.assertEqual(summary.summarize(data)["sections"]["depth_limit_tasks"]["total"], 0)

    def test_multifile_warnings_and_padding_keep_their_semantics(self):
        report = {"__typename__": "MultiFileReport", "id": "group", "handler_name": "multi-gzip",
                  "paths": ["/archive.gz.1", "/archive.gz.2"], "name": "archive",
                  "extraction_reports": [{"__typename__": "PathTraversalProblem", "path": "../x",
                                          "problem": "unsafe path", "resolution": "removed"}]}
        data = [task("/", directory=True, reports=[report, chunk(handler_name="padding")],
                     subtasks=[{"path": "/out", "depth": 1, "blob_id": "group"}])]
        result = summary.summarize(data)
        self.assertEqual(result["formats"]["padding"], 1)
        group = next(r for r in result["sections"]["chunks"]["items"] if r["format"] == "multi-gzip")
        self.assertNotIn("start", group)
        self.assertEqual(group["output_paths"], ["/out"])
        self.assertEqual(result["sections"]["issues"]["items"][0]["type"], "PathTraversalProblem")

    def test_invalid_or_empty_reports_fail_visibly_in_cli(self):
        cases = [[], {}, [task("/x", reports=[chunk(size=1)])],
                 [{"task": {"path": "/x", "depth": 0}, "reports": [42], "subtasks": []}]]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            for data in cases:
                path.write_text(json.dumps(data))
                result = subprocess.run([sys.executable, str(SCRIPT), str(path)], text=True, capture_output=True)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertIn("Cannot summarize", result.stderr)
            path.write_text("{truncated")
            result = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True)
            self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
