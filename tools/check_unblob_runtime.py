#!/usr/bin/env python3
"""Exercise the unblob CLI and bundled report reducer on deterministic archives."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import random
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SUMMARIZER = ROOT / "plugins/firmware-reverse-engineering/skills/firmware-extraction/scripts/summarize_unblob.py"


def archive(files):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size, info.mtime, info.mode = len(data), 0, 0o644
            tar.addfile(info, io.BytesIO(data))
    return output.getvalue()


def check(cli, directory):
    temp = Path(directory)
    payload = b"OrbitCurve extraction fixture\n"
    inner = archive({"etc/release": payload})
    outer = archive({"nested.tar": inner, "README.txt": b"Benign regression data\n"})
    firmware = temp / "firmware.bin"
    firmware.write_bytes(b"\xff" * 4096 + outer + random.Random(41).randbytes(8192))
    unknown = temp / "unknown.bin"
    unknown.write_bytes(random.Random(54).randbytes(8192))
    whole = temp / "whole.tar"
    whole.write_bytes(inner)
    original_hash = hashlib.sha256(firmware.read_bytes()).hexdigest()

    def run(name, source=firmware, depth=10, entropy_depth=1, output=None):
        report = temp / f"{name}.json"
        destination = output or temp / f"{name}-output"
        command = [cli, "-p", "1", "-d", str(depth), "-n", str(entropy_depth),
                   "-e", str(destination), "--report", str(report),
                   "--log", str(temp / f"{name}.log"), str(source)]
        result = subprocess.run(command, cwd=temp, text=True, capture_output=True, timeout=60)
        if not report.exists():
            raise AssertionError(f"Missing report: {result.returncode}\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}")
        reduced = subprocess.run([sys.executable, str(SUMMARIZER), str(report), "--extract-depth", str(depth)],
                                 check=True, text=True, capture_output=True, timeout=30)
        return json.loads(reduced.stdout), destination

    result, output = run("full")
    assert result["formats"] == {"padding": 1, "tar": 2}, result["formats"]
    assert result["sections"]["issues"]["total"] == 0, result["sections"]["issues"]
    assert result["sections"]["inputs"]["items"][0]["sha256"] == original_hash
    region = result["sections"]["unknown_regions"]["items"][0]
    assert (region["start"], region["end_exclusive"]) == (4096 + len(outer), firmware.stat().st_size)
    assert region["randomness"]["shannon_percent"]["mean"] > 90
    assert any(p.read_bytes() == payload for p in output.rglob("release")), "Nested file bytes differ"
    nested = next(x for x in result["sections"]["chunks"]["items"] if x["source"].endswith("nested.tar"))
    assert nested["start"] == 0 and nested["end_exclusive"] == len(inner)
    assert nested["output_count"] == 1 and Path(nested["output_paths"][0]).is_dir()

    shallow, output = run("shallow", depth=1, entropy_depth=0)
    assert shallow["sections"]["depth_limit_tasks"]["total"] > 0
    assert shallow["sections"]["unknown_regions"]["items"][0]["randomness"] is None
    assert not list(output.rglob("release")), "Depth limit was not respected"

    whole_unknown, _ = run("unknown", source=unknown)
    assert whole_unknown["sections"]["unknown_regions"]["total"] == 0
    assert whole_unknown["sections"]["unclassified_files"]["items"][0]["randomness"] is not None

    successful, output = run("whole-first", source=whole)
    assert successful["sections"]["issues"]["total"] == 0
    collision, _ = run("whole-collision", source=whole, output=output)
    errors = collision["sections"]["issues"]["items"]
    assert any(e["type"] == "OutputDirectoryExistsReport" and "/extraction_reports/" in e["pointer"] for e in errors), errors
    assert hashlib.sha256(firmware.read_bytes()).hexdigest() == original_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unblob", default="unblob")
    args = parser.parse_args()
    version = subprocess.check_output([args.unblob, "--version"], text=True).strip()
    if version != "26.6.4":
        raise SystemExit(f"This check targets unblob 26.6.4, got {version!r}")
    with tempfile.TemporaryDirectory(prefix="firmware-unblob-") as directory:
        check(args.unblob, directory)
    print("UNBLOB_REGRESSION_OK: nested bytes, padding, source offsets, unknown data, entropy depth, depth limits and nested errors")


if __name__ == "__main__":
    main()
