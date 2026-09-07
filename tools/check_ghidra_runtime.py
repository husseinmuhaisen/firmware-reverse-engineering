#!/usr/bin/env python3
"""Exercise bundled scripts in a real Ghidra Jython runtime on a benign fixture."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ghidra-home', type=Path, default=os.environ.get('GHIDRA_INSTALL_DIR'))
    args = parser.parse_args()
    if not args.ghidra_home:
        parser.error('set GHIDRA_INSTALL_DIR or pass --ghidra-home')
    launcher = args.ghidra_home.resolve() / 'support/analyzeHeadless'
    with tempfile.TemporaryDirectory(prefix='firmware-ghidra-') as directory:
        temp = Path(directory)
        binary = temp / 'analysis_fixture'
        subprocess.run(['gcc', '-O0', '-fno-builtin', '-fno-pie', '-no-pie',
                        str(ROOT / 'tests/fixtures/analysis_fixture.c'), '-o', str(binary)], check=True)
        scripts = ';'.join(str(ROOT / path) for path in [
            'plugins/firmware-reverse-engineering/skills/ghidra-re/scripts', 'tests/ghidra'])
        result = subprocess.run([str(launcher), str(temp), 'Fixture', '-import', str(binary),
                                 '-scriptPath', scripts, '-postScript', 'check_scripts.py', '-deleteProject'],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
        # Ghidra may exit 0 even when a script raises. Require the final assertion marker.
        if result.returncode or 'GHIDRA_REGRESSION_OK:' not in result.stdout or 'Traceback' in result.stdout:
            print(result.stdout)
            raise SystemExit('Ghidra runtime regression failed')
        print(next(line for line in result.stdout.splitlines() if 'GHIDRA_REGRESSION_OK:' in line))

if __name__ == '__main__':
    main()
