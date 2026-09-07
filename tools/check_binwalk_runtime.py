#!/usr/bin/env python3
"""Check the documented Binwalk 3.1.0 CLI with a deterministic gzip fixture."""
import argparse
import gzip
import json
from pathlib import Path
import random
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binwalk', default='binwalk')
    args = parser.parse_args()
    cli = args.binwalk
    version = subprocess.check_output([cli, '--version'], text=True).strip()
    if version != 'binwalk 3.1.0':
        raise SystemExit('This regression targets binwalk 3.1.0; got ' + version)
    signatures = subprocess.check_output([cli, '-L'], text=True)
    for name in ['squashfs', 'jffs2', 'ubi', 'cramfs', 'ext', 'gzip', 'xz', 'lzma', 'tarball', 'zip']:
        assert name in signatures, name
    payload = random.Random(42).randbytes(8192)
    with tempfile.TemporaryDirectory(prefix='firmware-binwalk-') as directory:
        temp = Path(directory)
        firmware = temp / 'fixture.bin'
        firmware.write_bytes(b'\0' * 4096 + gzip.compress(payload, mtime=0))
        def run(*flags):
            return subprocess.run([cli, *flags], cwd=temp, check=True, text=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        run(str(firmware), '-e', '-C', 'out', '--log', 'scan.json', '--include', 'gzip')
        files = [p for p in (temp / 'out').rglob('*') if p.is_file()]
        assert any(p.read_bytes() == payload for p in files), 'Extracted gzip content differs'
        assert 'gzip' in (temp / 'scan.json').read_text(), 'Missing signature log'
        json.loads((temp / 'scan.json').read_text())
        run('-a', str(firmware))
        run(str(firmware), '--exclude', 'jpeg')
        run('-E', str(firmware), '--log', 'entropy.json')
        assert (temp / 'fixture.bin.png').is_file(), 'Entropy PNG missing'
    print('BINWALK_REGRESSION_OK: 3.1.0 flags, signature filters, gzip bytes, JSON and entropy PNG')

if __name__ == '__main__':
    main()
