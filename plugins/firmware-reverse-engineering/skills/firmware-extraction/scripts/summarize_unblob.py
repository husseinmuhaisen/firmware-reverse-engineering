#!/usr/bin/env python3
"""Summarize unblob task reports without executing tools or reading extracted files."""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys


def clipped(value):
    """Bound free-form metadata; the original report remains the source of truth."""
    if isinstance(value, str):
        return value if len(value) <= 256 else value[:256] + " [truncated; see report]"
    if isinstance(value, list):
        result = [clipped(item) for item in value[:6]]
        if len(value) > 6:
            result.append({"omitted_items": len(value) - 6})
        return result
    if isinstance(value, dict):
        result = {clipped(k): clipped(v) for k, v in list(value.items())[:12]}
        if len(value) > 12:
            result["omitted_fields"] = len(value) - 12
        return result
    return value


def objects(value, where):
    if not isinstance(value, list) or any(not isinstance(x, dict) for x in value):
        raise ValueError(f"{where}: expected a list of objects")
    return value


def task_fields(task):
    if not isinstance(task, dict) or not isinstance(task.get("path"), str):
        raise ValueError("Task must contain a path string")
    if type(task.get("depth")) is not int or task["depth"] < 0:
        raise ValueError("Task must contain a nonnegative depth")
    return {"source": task["path"], "depth": task["depth"]}


def reports_at(reports, pointer):
    for index, report in enumerate(objects(reports, pointer)):
        location = f"{pointer}/{index}"
        if not isinstance(report.get("__typename__"), str):
            raise ValueError(f"{location}: report has no __typename__")
        yield report, location
        if "extraction_reports" in report:
            yield from reports_at(report["extraction_reports"], location + "/extraction_reports")


def randomness(report):
    if report is None:
        return None
    result = {}
    for name in ("shannon", "chi_square"):
        measurement = report[name]
        samples = measurement["percentages"]
        if not isinstance(samples, list) or not samples:
            raise ValueError("Randomness samples must be a nonempty list")
        values = [measurement["mean"], *samples]
        if any(type(n) not in (int, float) or not math.isfinite(n) for n in values):
            raise ValueError("Randomness measurements must be finite numbers")
        result[name + "_percent"] = {
            "mean": round(measurement["mean"], 3),
            "min": round(min(samples), 3), "max": round(max(samples), 3),
            "block_size": measurement["block_size"], "samples": len(samples),
        }
    return result


def bounds(report):
    start, end, size = (report[k] for k in ("start_offset", "end_offset", "size"))
    if any(type(n) is not int for n in (start, end, size)) or not 0 <= start < end or size != end - start:
        raise ValueError("Invalid chunk bounds or size")
    return {"start": start, "end_exclusive": end, "size": size}


def summarize(data, *, limit=10, offset=0, path_filter="", extract_depth=None):
    if not objects(data, "report"):
        raise ValueError("Empty report: extraction was not established")
    if limit < 1 or offset < 0 or (extract_depth is not None and extract_depth < 1):
        raise ValueError("Use positive limits/depth and a nonnegative offset")
    sections = {name: [] for name in (
        "inputs", "chunks", "unknown_regions", "unclassified_files", "issues",
        "depth_limit_tasks", "output_directories",
    )}
    counts = Counter({"tasks": 0, "files": 0, "directories": 0, "errors": 0, "warnings": 0})
    formats = Counter()
    metadata_types = {"StatReport", "HashReport", "FileMagicReport", "CarveDirectoryReport", "RandomnessReport"}

    for index, result in enumerate(data):
        task = task_fields(result.get("task"))
        reports = objects(result.get("reports"), f"/{index}/reports")
        subtasks = objects(result.get("subtasks"), f"/{index}/subtasks")
        for subtask in subtasks:
            task_fields(subtask)
        flattened = list(reports_at(reports, f"/{index}/reports"))
        top = {r["__typename__"]: r for r in reports}
        stat = top.get("StatReport", {})
        counts["tasks"] += 1
        counts["files"] += stat.get("is_file") is True
        counts["directories"] += stat.get("is_dir") is True
        base = {**task, "pointer": f"/{index}", "size": stat.get("size")}
        if task["depth"] == 0:
            sections["inputs"].append({**base, "sha256": top.get("HashReport", {}).get("sha256")})
        if extract_depth is not None and task["depth"] >= extract_depth:
            sections["depth_limit_tasks"].append(base)
        if stat.get("is_file") and stat.get("size", 0) > 0 and not any(
            r["__typename__"] in ("ChunkReport", "UnknownChunkReport", "MultiFileReport") for r in reports
        ):
            sections["unclassified_files"].append({
                **base, "magic": top.get("FileMagicReport", {}).get("magic"),
                "randomness": randomness(top.get("RandomnessReport")),
            })

        for report, pointer in flattened:
            kind = report["__typename__"]
            entry = {**task, "pointer": pointer}
            if kind in ("ChunkReport", "UnknownChunkReport"):
                entry.update(bounds(report))
                entry["id"] = report["id"]
            if kind in ("ChunkReport", "MultiFileReport"):
                if not isinstance(report.get("id"), str):
                    raise ValueError("Chunk and multi-file IDs must be strings")
                handler = report["handler_name"]
                if not isinstance(handler, str):
                    raise ValueError("handler_name must be a string")
                formats[handler] += 1
                outputs = [s["path"] for s in subtasks if s.get("blob_id", s.get("chunk_id")) == report["id"]]
                entry.update({"format": handler, "output_paths": outputs, "output_count": len(outputs)})
                if kind == "ChunkReport":
                    entry["is_encrypted"] = report.get("is_encrypted")
                else:
                    entry.update({"id": report["id"], "input_paths": report["paths"]})
                sections["chunks"].append(entry)
                for output in outputs:
                    sections["output_directories"].append({**task, "pointer": pointer, "path": output})
            elif kind == "UnknownChunkReport":
                entry["randomness"] = randomness(report.get("randomness"))
                sections["unknown_regions"].append(entry)
            elif kind == "CarveDirectoryReport":
                sections["output_directories"].append({**entry, "path": report["carve_dir"]})

            if "severity" in report or "problem" in report or kind not in metadata_types | {
                "ChunkReport", "UnknownChunkReport", "MultiFileReport"
            }:
                # Preserve unfamiliar reports for review rather than silently dropping them.
                detail = {k: v for k, v in report.items() if k not in (
                    "__typename__", "extraction_reports", "stdout", "stderr"
                )}
                if "stdout" in report or "stderr" in report:
                    detail["command_output"] = "See base64 stdout/stderr at this pointer in the original report"
                sections["issues"].append({**entry, "type": kind, "detail": detail})
                counts["errors"] += report.get("severity") == "ERROR"
                counts["warnings"] += report.get("severity") == "WARNING" or "problem" in report

    def page(items):
        matched = [x for x in items if path_filter in x["source"]]
        matched.sort(key=lambda x: (x["source"], x.get("start", -1), x["pointer"]))
        selected = matched[offset:offset + limit]
        return {"total": len(items), "matched": len(matched), "offset": offset,
                "omitted": len(matched) - len(selected), "items": [clipped(x) for x in selected]}

    return {
        "counts": dict(counts), "formats": clipped(dict(sorted(formats.items()))),
        "extract_depth": extract_depth,
        "sections": {name: page(items) for name, items in sections.items()},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--limit", type=int, default=10, help="Rows per section")
    parser.add_argument("--offset", type=int, default=0, help="Starting row in each filtered section")
    parser.add_argument("--path", default="", help="Filter sections by source path substring")
    parser.add_argument("--extract-depth", type=int, help="The exact -d value used for this extraction")
    args = parser.parse_args()
    def invalid_constant(value):
        raise ValueError(f"Non-finite JSON number: {value}")
    try:
        data = json.loads(args.report.read_text(encoding="utf-8"), parse_constant=invalid_constant)
        result = summarize(data, limit=args.limit, offset=args.offset,
                           path_filter=args.path, extract_depth=args.extract_depth)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, RecursionError) as exc:
        print(f"Cannot summarize unblob report: {clipped(str(exc))}. Inspect the original report and log.", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
