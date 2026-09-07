# Binwalk Reference

Comprehensive guide to binwalk usage for firmware analysis.

## Basic Usage

### Signature Scanning

```bash
# Basic scan
binwalk firmware.bin

# Verbose output
binwalk -v firmware.bin

# Show only specific signatures
binwalk -y filesystem firmware.bin
binwalk -y archive firmware.bin
binwalk -y compression firmware.bin

# Exclude certain signatures
binwalk -X jpeg firmware.bin  # Exclude JPEG
```

### Extraction

```bash
# Extract all found filesystems/archives
binwalk -e firmware.bin

# Extract to specific directory
binwalk -e firmware.bin -C /path/to/output

# Extract with original offsets preserved
binwalk -e --dd='.*' firmware.bin

# Manual extraction using dd rules
binwalk -e --dd='squashfs:squashfs' firmware.bin
```

### Advanced Scanning

```bash
# Show raw signatures (no filtering)
binwalk -A firmware.bin

# Scan with custom signature file
binwalk -B custom_signatures.txt firmware.bin

# Byte-level scan (slower but more thorough)
binwalk -R firmware.bin

# Disassemble executable code
binwalk -Y firmware.bin
```

## Entropy Analysis

```bash
# Basic entropy analysis
binwalk -E firmware.bin

# Save entropy plot as PNG
binwalk -E -J firmware.bin

# Set custom block size for entropy
binwalk -E -K 1024 firmware.bin

# Combine signature scan with entropy
binwalk -E firmware.bin && binwalk firmware.bin
```

**Interpreting entropy:**
- **8.0 (red)**: Encrypted or highly compressed
- **7.0-7.5 (orange/yellow)**: Compressed data
- **5.0-6.5 (green)**: Normal mixed data
- **<5.0 (blue)**: Structured or sparse data

## Extraction Strategies

### Automatic Extraction

Binwalk's automatic extraction uses magic signatures and known file formats.

```bash
binwalk -e firmware.bin
```

**Output structure:**
```
_firmware.bin.extracted/
├── 0.squashfs           # Raw extracted data
├── squashfs-root/       # Extracted filesystem
├── 10000.gzip           # Compressed section
└── 20000.jffs2          # Another filesystem
```

### Manual Extraction with DD

For better control, use manual dd extraction rules:

```bash
# Extract specific types
binwalk -e --dd='squashfs:squashfs' firmware.bin
binwalk -e --dd='jffs2:jffs2' firmware.bin
binwalk -e --dd='gzip:gzip' firmware.bin

# Extract all
binwalk -e --dd='.*' firmware.bin

# Custom rules
binwalk -e --dd='squashfs filesystem:sqsh:squashfs' firmware.bin
```

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
| `-e` | Extract known file types |
| `-E` | Calculate file entropy |
| `-J` | Save entropy plot as PNG |
| `-A` | Scan for common executable opcodes |
| `-R` | Raw signature scan (no smart filtering) |
| `-v` | Verbose output |
| `-q` | Quiet mode (errors only) |
| `-M` | Recursively scan extracted files |
| `-C <dir>` | Extract to custom directory |
| `-K <size>` | Set custom block size |
| `-y <type>` | Show only specified signature types |
| `-X <type>` | Exclude specified signature types |
| `-I` | Disable smart signature scanning |
| `-B` | Use custom signature file |
| `--dd='<rule>'` | Manual DD extraction rules |
