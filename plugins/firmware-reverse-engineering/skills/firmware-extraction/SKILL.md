---
name: firmware-extraction
description: "Comprehensive firmware extraction and unpacking from binary images using binwalk and filesystem-specific tools. Use when Claude needs to extract filesystems and files from firmware binaries (.bin files) obtained from device dumps or manufacturer downloads. Covers: (1) Initial reconnaissance and entropy analysis, (2) Signature-based extraction with binwalk, (3) Filesystem-specific extraction (SquashFS, JFFS2, UBIFS, CramFS, YAFFS2, ext, etc.), (4) Handling encrypted and obfuscated firmware, (5) Multi-stage and nested firmware images, (6) Edge cases like corrupted or non-standard formats. Does NOT handle individual ELF binary analysis (use firmware-static-analysis skill for that) or dynamic analysis/emulation."
---

# Firmware Extraction & Unpacking

Systematic extraction and unpacking of firmware binaries into analyzable filesystems and components. This skill provides methodical workflows for handling common and edge-case firmware formats, encryption, and obfuscation.

## Extraction Workflow Overview

Follow this workflow sequentially for comprehensive firmware extraction:

1. **Initial Assessment** - Identify firmware type and components
2. **Entropy Analysis** - Detect encryption, compression, and structure
3. **Signature Scanning** - Locate filesystems and embedded files
4. **Primary Extraction** - Extract identified components
5. **Filesystem-Specific Processing** - Handle each filesystem appropriately
6. **Verification** - Validate extracted data
7. **Nested Extraction** - Process embedded firmware recursively
8. **Documentation** - Record extraction process and findings

## Prerequisites

Ensure required tools are installed before starting:

```bash
# Core tools
sudo apt-get install binwalk squashfs-tools mtd-utils gzip bzip2 xz-utils

# Filesystem-specific tools
pip3 install jefferson ubi_reader  # JFFS2 and UBIFS
git clone https://github.com/devttys0/sasquatch && cd sasquatch && ./build.sh  # Non-standard SquashFS

# Optional but recommended
sudo apt-get install cramfsprogs android-sdk-libsparse-utils
pip3 install python-lzo  # For UBIFS LZO compression
```

## Step 1: Initial Assessment

Understand what you're working with before attempting extraction.

### File Type Identification

```bash
# Basic file information
file firmware.bin

# Check file size and structure
ls -lh firmware.bin
xxd -l 512 firmware.bin  # Examine first 512 bytes
```

**Look for:**
- Firmware format indicators (TRX, uImage, etc.)
- Architecture hints (ARM, MIPS, x86)
- Manufacturer-specific headers
- Magic bytes of known formats

### Document Source Information

Record critical metadata:
- **Source**: Device dump (UART/JTAG/SPI) or manufacturer download
- **Device**: Make, model, version
- **URL**: If downloaded, save the source URL
- **Hash**: Calculate and save SHA256
```bash
sha256sum firmware.bin > firmware.bin.sha256
```

## Step 2: Entropy Analysis

Entropy analysis reveals encryption, compression, and data structure.

### Generate Entropy Plot

```bash
# Create entropy analysis
binwalk -E firmware.bin

# Generate visual plot
binwalk -E -J firmware.bin
# Creates firmware.bin.png showing entropy visualization
```

### Interpret Entropy Results

**Entropy values:**
- **~8.0 (flat high)**: Likely encrypted - see `references/encryption.md`
- **~7.0-7.5 (variable)**: Compressed data (normal)
- **~5.0-6.5 (medium)**: Mixed code and data (normal)
- **~4.0-5.0 (low)**: Structured data or sparse regions
- **Sharp transitions**: Boundaries between components

**Common patterns:**
```
[Header - low] [Compressed Kernel - high] [SquashFS - high] [Config - low]
0-0x1000       0x1000-0x200000           0x200000-0x600000  0x600000-end
```

### Encryption Detection

If entropy is consistently ~8.0:

```bash
# Check for crypto-related strings
strings firmware.bin | grep -i -E 'crypt|aes|rsa|cipher|key'

# Look for crypto libraries
strings firmware.bin | grep -i -E 'openssl|mbedtls|wolfssl'
```

**If encrypted**: Follow workflows in `references/encryption.md` before continuing.

## Step 3: Signature Scanning

Identify all embedded components using binwalk's signature database.

### Comprehensive Scan

```bash
# Full signature scan with verbose output
binwalk -v firmware.bin | tee scan_results.txt

# Scan for specific types
binwalk -y filesystem firmware.bin
binwalk -y compression firmware.bin
binwalk -y archive firmware.bin
```

### Analyze Scan Results

Example output:
```
DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
0             0x0             TRX firmware header, little endian
28            0x1C            LZMA compressed data
262144        0x40000         Squashfs filesystem, little endian
2883584       0x2C0000        JFFS2 filesystem, little endian
```

**Key information to extract:**
- **Offsets**: Where each component starts (DECIMAL/HEX)
- **Types**: Filesystem types, compression formats
- **Sizes**: Implied by next offset or file size
- **Endianness**: Critical for multi-architecture firmware

### Save and Review

```bash
# Create detailed scan record
binwalk -v firmware.bin > scan_detailed.txt

# Quick reference of just filesystems
binwalk firmware.bin | grep -E 'Squashfs|JFFS2|UBIFS|Cramfs|ext' > filesystems.txt
```

## Step 4: Primary Extraction

Extract all identified components using binwalk's automatic extraction.

### Automatic Extraction

```bash
# Extract everything binwalk can handle
binwalk -e firmware.bin -C extracted/

# Alternative: Manual control with dd rules
binwalk -e --dd='.*' firmware.bin -C extracted/
```

**Output structure:**
```
extracted/
├── _firmware.bin.extracted/
│   ├── 0                    # Raw data at offset 0
│   ├── 1C.7z               # LZMA compressed (if recognized)
│   ├── 40000               # SquashFS raw data
│   ├── squashfs-root/      # Extracted SquashFS (if successful)
│   └── 2C0000.jffs2        # JFFS2 raw data
```

### Verify Extraction

```bash
cd extracted/_firmware.bin.extracted/

# Check what was extracted
ls -lh

# Identify file types
file *

# Look for successfully extracted filesystems
ls -d */ 2>/dev/null
```

## Step 5: Filesystem-Specific Processing

Each filesystem type requires specific handling. Binwalk doesn't always extract perfectly.

### Decision Tree

For each filesystem found in scan results, determine the approach:

**SquashFS** → Step 5.1
**JFFS2** → Step 5.2  
**UBIFS** → Step 5.3
**CramFS** → Step 5.4
**ext2/3/4** → Step 5.5
**YAFFS2** → Step 5.6
**Compressed archives (gzip/LZMA/XZ)** → Step 5.7

### Step 5.1: SquashFS Extraction

Most common filesystem in firmware.

```bash
# If binwalk extracted successfully
ls squashfs-root/  # Check if directory exists

# If automatic extraction failed, manual approach:
# 1. Extract raw SquashFS using offset from scan
dd if=firmware.bin of=squashfs.img bs=1 skip=OFFSET

# 2. Try standard unsquashfs
unsquashfs -d squashfs-root squashfs.img

# 3. If that fails (common with routers), use sasquatch
sasquatch squashfs.img

# 4. Force extraction even with errors
unsquashfs -force -d squashfs-root squashfs.img
```

**Troubleshooting SquashFS:**
- **"unknown compression type"** → Use sasquatch (supports non-standard variants)
- **"filesystem corruption"** → Try `-force` flag
- **Wrong endianness** → Check binwalk scan for endianness hint
- **Multiple SquashFS images** → Extract each by offset separately

**Reference**: See `references/filesystems.md` section on SquashFS for comprehensive details.

### Step 5.2: JFFS2 Extraction

Common in older routers and NOR flash devices.

```bash
# Extract raw JFFS2 image
dd if=firmware.bin of=jffs2.img bs=1 skip=OFFSET

# Use jefferson (better than binwalk's built-in extractor)
jefferson jffs2.img -d jffs2-root/

# If endianness issues
jefferson --big-endian jffs2.img -d jffs2-root/
```

**Alternative (requires root on Linux):**
```bash
# Mount as loopback device
modprobe mtdblock mtdram
modprobe jffs2
dd if=jffs2.img of=/tmp/jffs2.img
mkdir /mnt/jffs2
mount -t jffs2 -o loop /tmp/jffs2.img /mnt/jffs2
# Copy out files
cp -a /mnt/jffs2/* ./jffs2-root/
umount /mnt/jffs2
```

**Troubleshooting JFFS2:**
- **Incomplete extraction** → jefferson handles corrupted nodes better than mount
- **Endianness errors** → Use `--big-endian` or `--little-endian` flags
- **Empty output** → Verify offset is correct with `xxd`

**Reference**: See `references/filesystems.md` section on JFFS2.

### Step 5.3: UBIFS Extraction

Modern NAND flash filesystem, more complex than others.

```bash
# Extract raw UBI image
dd if=firmware.bin of=ubi.img bs=1 skip=OFFSET

# Use ubi_reader (essential for UBIFS)
ubireader_extract_images ubi.img -o ubi_images/
ubireader_extract_files ubi.img -o ubifs-root/

# Check for multiple volumes
ubireader_list_files ubi.img
```

**Troubleshooting UBIFS:**
- **Multiple volumes** → Extract each volume separately
- **PEB errors** → Check Physical Erase Block size alignment
- **LEB size mismatch** → Consult device datasheet for correct block sizes

**Reference**: See `references/filesystems.md` section on UBIFS for detailed extraction procedures.

### Step 5.4: CramFS Extraction

Legacy compressed filesystem.

```bash
# Extract raw CramFS
dd if=firmware.bin of=cramfs.img bs=1 skip=OFFSET

# Extract with cramfsck
cramfsck -x cramfs-root/ cramfs.img

# Alternative: mount (requires root)
mkdir /mnt/cramfs
mount -t cramfs -o loop cramfs.img /mnt/cramfs
cp -a /mnt/cramfs/* ./cramfs-root/
umount /mnt/cramfs
```

**Reference**: See `references/filesystems.md` section on CramFS.

### Step 5.5: ext2/3/4 Extraction

Standard Linux filesystems, easiest to extract.

```bash
# Extract raw ext image
dd if=firmware.bin of=ext.img bs=1 skip=OFFSET

# Mount directly (easiest, may require root)
mkdir ext-root
sudo mount -o loop ext.img ext-root/
# Copy files
sudo cp -a ext-root/* ./extracted-ext/
sudo umount ext-root/

# Alternative: use debugfs (no root needed)
debugfs ext.img
  ls
  rdump / extracted-ext/
  quit
```

**Troubleshooting ext:**
- **Journal errors** → Mount with `-o noload` to skip journal
- **Superblock errors** → Try alternative superblocks: `-o sb=32768`

**Reference**: See `references/filesystems.md` section on ext2/3/4.

### Step 5.6: YAFFS2 Extraction

Android and some embedded NAND flash systems.

```bash
# Extract raw YAFFS2 image
dd if=firmware.bin of=yaffs2.img bs=1 skip=OFFSET

# Use unyaffs
unyaffs yaffs2.img yaffs2-root/
```

**Troubleshooting YAFFS2:**
- **OOB data** → May need special handling
- **Sparse images** → Check for missing blocks

**Reference**: See `references/filesystems.md` section on YAFFS2.

### Step 5.7: Compressed Data Extraction

Handle standalone compressed sections (not filesystems).

```bash
# GZIP
dd if=firmware.bin of=compressed.gz bs=1 skip=OFFSET
gunzip compressed.gz
# or
zcat compressed.gz > decompressed.bin

# LZMA/XZ
dd if=firmware.bin of=compressed.xz bs=1 skip=OFFSET
unxz compressed.xz
# or
xz -dc compressed.xz > decompressed.bin

# BZIP2
dd if=firmware.bin of=compressed.bz2 bs=1 skip=OFFSET
bunzip2 compressed.bz2
```

**After decompression**, scan the result:
```bash
file decompressed.bin
binwalk decompressed.bin
```

## Step 6: Verification

Validate that extraction was successful and complete.

### Filesystem Structure Check

```bash
# For each extracted filesystem root
ls -lah squashfs-root/

# Check for expected structure
ls squashfs-root/bin squashfs-root/etc squashfs-root/lib 2>/dev/null

# Look for key files
find squashfs-root/ -name "passwd" -o -name "*.conf" -o -name "*.sh"
```

### Content Verification

```bash
# Check binaries are valid
find squashfs-root/ -type f -name "*" | head -10 | xargs file

# Verify shared libraries
find squashfs-root/ -name "*.so*" | head -5 | xargs file

# Look for web interface
ls squashfs-root/www/ squashfs-root/htdocs/ squashfs-root/var/www/ 2>/dev/null
```

### Compare to Original

```bash
# Count files extracted
find squashfs-root/ -type f | wc -l

# Check total extracted size
du -sh squashfs-root/

# Ensure reasonable compared to firmware size
ls -lh firmware.bin
```

## Step 7: Nested Extraction

Firmware often contains nested or multi-stage components.

### Identify Nested Firmware

```bash
# Scan extracted filesystems for more firmware
find extracted/ -type f -size +100k -exec file {} \; | grep -i -E 'firmware|filesystem|compressed'

# Binwalk scan extracted files
find extracted/ -type f -size +100k -exec binwalk {} \;
```

### Common Nested Patterns

**Pattern 1: Bootloader + Kernel + RootFS**
```
firmware.bin
├── 0x0      - U-Boot bootloader
├── 0x40000  - Compressed kernel (LZMA)
└── 0x200000 - SquashFS root filesystem
```

**Pattern 2: Update Package**
```
update.bin
├── Header with metadata
├── Compressed archive (tar.gz)
│   ├── bootloader.bin
│   ├── kernel.bin
│   └── rootfs.bin
```

**Pattern 3: Dual Firmware (A/B partitions)**
```
firmware.bin
├── 0x0       - Firmware A (complete image)
└── 0x2000000 - Firmware B (complete image, backup)
```

### Recursive Extraction

```bash
# For each large file found
cd extracted/

# Scan
binwalk suspicious_file.bin

# Extract if firmware detected
binwalk -e suspicious_file.bin

# Repeat process for each nested component
```

## Step 8: Edge Cases

Handle non-standard and problematic firmware.

### Edge Case 1: Encrypted Firmware

**Detection:**
- High entropy (~8.0) across entire file
- No recognized signatures in binwalk scan
- Strings contain crypto library references

**Approach:**
1. Read `references/encryption.md` in detail
2. Analyze bootloader for decryption routine
3. Search for hardcoded keys
4. Check vendor update tools for keys
5. Try known default keys from public databases

**Common strategies:**
```bash
# Search for potential keys in bootloader
strings bootloader.bin | grep -E '[0-9a-fA-F]{32,64}'

# Check for XOR obfuscation (simpler than AES)
# Test if first bytes XOR'd reveal known magic bytes
python3 -c "
data = open('firmware.bin', 'rb').read(4)
for key in range(256):
    result = bytes([b ^ key for b in data])
    if result in [b'hsqs', b'\\x19\\x85']:
        print(f'Possible XOR key: {key:02x}')
"
```

### Edge Case 2: Corrupted or Partial Firmware

**Detection:**
- Binwalk finds signatures but extraction fails
- Incomplete filesystem structure
- Truncated file sizes

**Approach:**
```bash
# Force extraction even with errors
unsquashfs -force squashfs.img

# Skip corrupted sections
jefferson --ignore-errors jffs2.img -d output/

# Manual carving
dd if=firmware.bin of=carved.bin bs=1 skip=OFFSET count=ESTIMATED_SIZE
```

### Edge Case 3: Non-Standard Headers

**Detection:**
- Known filesystem but offset doesn't match signature
- Modified magic bytes
- Proprietary header format

**Approach:**
```bash
# Search for filesystem signatures manually
xxd firmware.bin | grep -E "68 73 71 73|19 85"  # Look for hsqs, JFFS2

# Extract with adjusted offset
dd if=firmware.bin of=fs.img bs=1 skip=ADJUSTED_OFFSET

# Try extraction tools with force flags
```

### Edge Case 4: Concatenated Multiple Firmwares

**Detection:**
- Multiple complete firmware images in one file
- Dual-boot or A/B partition setups
- Size is exact multiple of expected firmware size

**Approach:**
```bash
# Check file size
ls -lh firmware.bin

# If size suggests 2x or 3x normal firmware
# Split into components
dd if=firmware.bin of=firmware_A.bin bs=1M count=SIZE_MB
dd if=firmware.bin of=firmware_B.bin bs=1M skip=SIZE_MB

# Extract each separately
binwalk -e firmware_A.bin
binwalk -e firmware_B.bin
```

### Edge Case 5: Signed/Verified Firmware

**Detection:**
- Signature blocks or certificates in header
- References to RSA/ECDSA in strings
- Bootloader checks signatures

**Approach:**
- Signatures typically don't prevent extraction (only flashing)
- Skip signature blocks and extract payload
```bash
# Identify signature block size from header
xxd -l 1024 firmware.bin

# Skip signature and extract payload
dd if=firmware.bin of=payload.bin bs=1 skip=SIGNATURE_SIZE
binwalk -e payload.bin
```

## Documentation Template

Create a comprehensive extraction report:

```markdown
# Firmware Extraction Report

**Firmware File:** firmware.bin
**SHA256:** [hash]
**Size:** [size]
**Source:** [manufacturer URL or dump method]
**Device:** [make/model/version]
**Date:** [extraction date]

## Summary

[Brief description of firmware type, components found, and extraction success]

## Entropy Analysis

- Overall entropy: [value]
- Encryption detected: [Yes/No]
- Key findings: [encrypted sections, compression, etc.]

## Component Map

| Offset (Hex) | Offset (Dec) | Size | Type | Extraction Status |
|--------------|--------------|------|------|-------------------|
| 0x0          | 0            | 256K | U-Boot | Success |
| 0x40000      | 262144       | 1.5M | LZMA Kernel | Success |
| 0x200000     | 2097152      | 12M  | SquashFS | Success |
| 0xE00000     | 14680064     | 2M   | JFFS2 Config | Success |

## Extracted Filesystems

### SquashFS Root (0x200000)
- **Extraction method:** sasquatch
- **Status:** Success
- **Files extracted:** [count]
- **Location:** `extracted/squashfs-root/`
- **Key findings:**
  - Web interface in `/www/`
  - Binaries in `/bin/` and `/sbin/`
  - Config templates in `/etc/`
  - Interesting file: `/etc/shadow` (check for default passwords)

### JFFS2 Config (0xE00000)
- **Extraction method:** jefferson
- **Status:** Partial (some corrupted nodes)
- **Files extracted:** [count]
- **Location:** `extracted/jffs2-root/`
- **Key findings:**
  - User configuration storage
  - Persistent settings

## Nested Components

[List any firmware found within extracted filesystems]

## Issues Encountered

[Any extraction failures, corrupted data, or unrecognized components]

## Next Steps

1. Static analysis of binaries (use firmware-static-analysis skill)
2. Configuration file analysis
3. Search for hardcoded credentials
4. Identify web interface vulnerabilities
5. Setup emulation environment

## File Inventory

[Attach or reference complete file listing]
```

## Additional References

- **Filesystem details**: `references/filesystems.md` - Comprehensive guide to all firmware filesystem types
- **Encryption handling**: `references/encryption.md` - Detecting and decrypting encrypted firmware
- **Binwalk usage**: `references/binwalk.md` - Complete binwalk command reference

## Best Practices

### Before Starting
1. **Preserve original** - Always work on copies
2. **Document source** - Record where firmware came from
3. **Calculate hash** - For verification and deduplication
4. **Check prerequisites** - Ensure all tools are installed

### During Extraction
1. **Scan before extracting** - Review binwalk output first
2. **Use entropy analysis** - Understand structure before diving in
3. **Save intermediate outputs** - Keep scan results and logs
4. **Verify each step** - Check extraction success before proceeding
5. **Use filesystem-specific tools** - Don't rely only on binwalk

### Edge Cases
1. **Read reference material** - Consult encryption/filesystem guides
2. **Try manual extraction** - If automatic fails, use dd + specific tools
3. **Document failures** - Note what didn't work for future reference
4. **Search for similar cases** - Check CVE databases, research papers

### After Extraction
1. **Verify structure** - Ensure filesystem looks complete
2. **Check for nested firmware** - Scan extracted files recursively
3. **Document findings** - Create extraction report
4. **Organize output** - Keep extracted files in logical structure
5. **Prepare for static analysis** - Ready to use firmware-static-analysis skill

## Common Pitfalls to Avoid

1. **Don't skip entropy analysis** - Saves time detecting encryption early
2. **Don't assume binwalk extracts everything** - Always verify and use filesystem-specific tools
3. **Don't ignore endianness** - Big vs little-endian matters for many tools
4. **Don't forget to recurse** - Firmware is often nested multiple levels
5. **Don't lose track of offsets** - Keep detailed notes of where components are located
6. **Don't work on originals** - Always preserve untouched firmware copy
7. **Don't give up on first failure** - Try alternative tools and manual methods

## Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| High entropy, no signatures | Check `references/encryption.md` |
| SquashFS extraction fails | Try sasquatch instead of unsquashfs |
| JFFS2 incomplete | Use jefferson with `--ignore-errors` |
| UBIFS won't extract | Use ubi_reader tools, check PEB size |
| Binwalk finds nothing | Manual hex analysis, check for obfuscation |
| Corrupted filesystem | Try force extraction flags |
| Tools missing | Install prerequisites at top of skill |
| Multiple nested levels | Recursive extraction, scan each component |
