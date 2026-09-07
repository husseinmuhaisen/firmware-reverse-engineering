# Binwalk Reference

Command reference for **Binwalk 3.1.0**. Check `binwalk --version` and
`binwalk --help`: development-branch and legacy 2.x options differ.
See the [tagged installation guide](https://github.com/ReFirmLabs/binwalk/blob/v3.1.0/README.md)
for build and external extractor dependencies. The Rust CLI does not provide the
legacy Python `binwalk` module required by some Firmadyne-based extractors.

## Basic Usage

### Signature Scanning

```bash
# Basic scan
binwalk firmware.bin

# Display all recursive extraction results (primarily useful with -M)
binwalk -v firmware.bin

# Show only specific signatures
binwalk firmware.bin --include squashfs,jffs2,ubi,cramfs,ext
binwalk firmware.bin --include tarball,zip
binwalk firmware.bin --include gzip,xz,lzma

# Exclude certain signatures
binwalk firmware.bin --exclude jpeg  # Exclude JPEG
```

### Extraction

```bash
# Extract all found filesystems/archives
binwalk -e firmware.bin

# Extract to specific directory
binwalk -e firmware.bin -C /path/to/output

# Carve a verified component without executing an extractor
dd if=firmware.bin of=component.bin bs=1 skip=OFFSET count=LENGTH
```

### Advanced Scanning

```bash
# Search supported signatures at all offsets
binwalk -a firmware.bin

# List exact supported signature names and extractor commands
binwalk -L

# Machine-readable log
binwalk firmware.bin --log scan.json
```

Binwalk 3.1.0 has no legacy opcode scan, raw-pattern, custom-magic-file or
`--dd` rule interface. Use architecture-appropriate `objdump` for disassembly,
a byte-search script for raw patterns, and `dd` for explicit carving. Custom
signature development requires the Rust signature API.

## Entropy Analysis

```bash
# Basic entropy analysis
binwalk -E firmware.bin

# Save entropy plot as PNG
binwalk -E firmware.bin

# Also write per-block entropy values to JSON (block size is selected internally)
binwalk -E firmware.bin --log entropy.json

# Combine signature scan with entropy
binwalk -E firmware.bin && binwalk firmware.bin
```

**Interpreting entropy:** Values range from 0 to 8 bits per byte. Near-uniform
compressed data and encrypted data can both approach 8; colors and thresholds
do not identify a format. Corroborate changes with signatures, headers and
successful parsing. `-E` writes `firmware.bin.png` in the current directory;
choose a clean output directory for repeated plots.

## Extraction Strategies

### Automatic Extraction

Binwalk's automatic extraction uses magic signatures and known file formats.

```bash
binwalk -e firmware.bin
```

Output goes under `extractions/` by default, or the path supplied to `-C`.
Inspect the report and resulting directories; paths depend on signature offset
and extractor. Binwalk 2's `_firmware.bin.extracted` layout is not portable.

### Selecting Component Types

```bash
# Filename precedes the variable-length --include list
binwalk -e firmware.bin --include squashfs
binwalk -e firmware.bin --include jffs2
binwalk -e firmware.bin --include gzip
```

Use `binwalk -L` to check exact names. Header sizes and decompressor results are
better evidence of component length than the next signature offset.

### Carving Specific Regions

```bash
# Carve by offset (found from binwalk scan)
dd if=firmware.bin of=extracted.bin bs=1 skip=OFFSET

# Carve with specific length
dd if=firmware.bin of=extracted.bin bs=1 skip=OFFSET count=LENGTH

# Example: Extract SquashFS at offset 0x10000
dd if=firmware.bin of=squashfs.bin bs=1 skip=65536
```

## Best Practices

1. **Always scan before extracting**
```bash
binwalk firmware.bin > scan_results.txt
binwalk -E firmware.bin  # Check entropy
# Review results, then extract
```

2. **Preserve original firmware**
```bash
cp firmware.bin firmware_backup.bin
# Work on copy
binwalk -e firmware_backup.bin
```

3. **Document offsets and findings**
```bash
binwalk firmware.bin | tee binwalk_scan.txt
# Keep scan results for reference
```

4. **Verify extracted filesystems**
```bash
# After extraction
file extracted_files/*
ls -lh extracted_files/
# Ensure filesystems are valid
```

5. **Use appropriate tools for each filesystem**
```bash
# Don't rely solely on binwalk extraction
# Use filesystem-specific tools:
# - unsquashfs/sasquatch for SquashFS
# - jefferson for JFFS2
# - ubi_reader for UBIFS
```

## Useful Binwalk Options Reference

| Option | Description |
|--------|-------------|
| `-e` | Extract recognized file types using installed extractors |
| `-E` | Calculate entropy and write a PNG (separate from `-e`) |
| `-a` | Search all signatures at all offsets |
| `-L` | List signatures and extractors |
| `-v` | Display all results during recursive extraction |
| `-q` | Suppress stdout |
| `-M` | Recursively scan extracted files |
| `-C <dir>` | Extraction output directory |
| `-l <file>` | Write JSON log |
| `-t <count>` | Number of threads |
| `--include <names>` | Comma-separated signature names; put filename first |
| `--exclude <names>` | Exclude signature names; put filename first |
