# Firmware Filesystem Reference

Comprehensive guide to common firmware filesystems and their characteristics.

## SquashFS

**Most common in**: Consumer routers, embedded Linux devices, OpenWrt-based systems

### Characteristics
- **Compression**: LZMA, LZO, XZ, ZLIB, or LZ4
- **Read-only**: Designed for compressed read-only filesystems
- **Signature**: `hsqs` (little-endian) or `sqsh` (big-endian) at start
- **Variants**: Multiple versions (1.x - 4.x), different compression algorithms

### Extraction
```bash
# Using binwalk (auto-detection)
binwalk -e firmware.bin

# Manual extraction with unsquashfs
unsquashfs -d output_dir squashfs_image.bin

# Using sasquatch (for non-standard SquashFS)
sasquatch squashfs_image.bin

# Force specific version
unsquashfs -d output_dir -force squashfs_image.bin
```

### Troubleshooting
- **Error: "unknown compression type"** → Use sasquatch instead of unsquashfs
- **Error: "filesystem corruption"** → Try forcing extraction or use dd to extract from offset
- **Multiple SquashFS images** → Extract each separately by offset

### Common Issues
- Non-standard compression (LZMA variants)
- Big-endian vs little-endian
- Concatenated images (bootloader + rootfs)

## JFFS2 (Journaling Flash File System 2)

**Most common in**: Older routers, embedded devices with NOR flash

### Characteristics
- **Compression**: ZLIB, RTIME, or none
- **Journaling**: Designed for wear-leveling on flash
- **Signature**: `0x1985` magic number
- **Endianness**: Can be big or little-endian

### Extraction
```bash
# Using binwalk
binwalk -e firmware.bin

# Using jefferson (Python-based JFFS2 extractor)
jefferson firmware.bin -d output_dir

# Manual mounting (Linux only, requires root)
modprobe mtdblock
modprobe jffs2
dd if=firmware.bin of=/tmp/jffs2.img bs=1 skip=OFFSET
mkdir /tmp/jffs2_mount
mount -t jffs2 -o loop /tmp/jffs2.img /tmp/jffs2_mount
```

### Troubleshooting
- **Endianness errors** → Use jefferson with `--big-endian` flag
- **Corrupted nodes** → jefferson is more forgiving than mount
- **Incomplete extraction** → May need to manually carve and reassemble

### Common Issues
- Mixed endianness in multi-architecture firmware
- Corrupted journal entries
- Empty or partially written blocks

## UBIFS (Unsorted Block Image File System)

**Most common in**: Modern embedded Linux, NAND flash devices, newer routers

### Characteristics
- **Compression**: LZO, ZLIB
- **Wear-leveling**: UBI layer on top of MTD
- **Signature**: `0x06101831` (UBIFS) or `0x55424923` (UBI)
- **Complex**: Requires UBI and UBIFS layers

### Extraction
```bash
# Using binwalk (limited support)
binwalk -e firmware.bin

# Using ubi_reader (recommended)
ubireader_extract_images -o output_dir firmware.bin
ubireader_extract_files -o output_dir firmware.bin

# Manual extraction (Linux with MTD/UBI support)
modprobe nandsim first_id_byte=0x2c second_id_byte=0xda third_id_byte=0x90 fourth_id_byte=0x95
modprobe ubi
ubiattach -m 0 -d 0 /path/to/ubi.img
mkdir /mnt/ubifs
mount -t ubifs ubi0_0 /mnt/ubifs
```

### Troubleshooting
- **Multiple UBI volumes** → Extract each volume separately
- **Version mismatches** → Use ubi_reader instead of mount
- **PEB (Physical Erase Block) errors** → Check block size and alignment

### Common Issues
- Multiple volumes in single UBI image
- LEB (Logical Erase Block) size mismatches
- Requires kernel with UBI/UBIFS support for mounting

## CramFS (Compressed ROM File System)

**Most common in**: Very old embedded devices, bootloaders

### Characteristics
- **Compression**: ZLIB
- **Read-only**: Simple compressed filesystem
- **Signature**: `0x28cd3d45` magic number
- **Legacy**: Largely replaced by SquashFS

### Extraction
```bash
# Using binwalk
binwalk -e firmware.bin

# Using cramfsck
cramfsck -x output_dir cramfs_image.bin

# Manual mounting
mkdir /tmp/cramfs_mount
mount -t cramfs -o loop cramfs_image.bin /tmp/cramfs_mount
```

### Troubleshooting
- **Old format** → May need specific cramfs tools version
- **Byte order** → Check endianness

### Common Issues
- Limited tool support in modern systems
- May need to compile cramfs-tools from source

## YAFFS2 (Yet Another Flash File System 2)

**Most common in**: Android devices, some embedded systems with NAND flash

### Characteristics
- **No compression**: Stores files directly
- **NAND-specific**: Designed for NAND flash characteristics
- **Signature**: No standard magic number, identified by structure
- **OOB data**: Includes out-of-band data for ECC

### Extraction
```bash
# Using unyaffs
unyaffs yaffs2_image.bin output_dir/

# Using binwalk (limited)
binwalk -e firmware.bin
```

### Troubleshooting
- **OOB data issues** → May need to strip or process separately
- **Sparse images** → Handle missing blocks

### Common Issues
- Requires understanding of NAND flash structure
- OOB (Out-Of-Band) data handling
- Limited extraction tool options

## ext2/ext3/ext4

**Most common in**: Linux-based embedded systems, development boards, some IoT devices

### Characteristics
- **Standard Linux**: Full-featured filesystems
- **Compression**: ext4 can have inline compression
- **Signature**: `0x53ef` at offset 0x438
- **Journaling**: ext3/ext4 have journals

### Extraction
```bash
# Direct mounting (easiest)
mkdir /tmp/ext_mount
mount -o loop firmware.bin /tmp/ext_mount

# Using debugfs (read-only)
debugfs firmware.bin
  ls
  cd /path
  rdump / /output/dir
  quit

# Copy entire filesystem
mkdir output_dir
mount -o loop firmware.bin /tmp/mnt
cp -a /tmp/mnt/* output_dir/
umount /tmp/mnt
```

### Troubleshooting
- **Journal errors** → Use `-o noload` to skip journal replay
- **Orphaned inodes** → Run e2fsck to clean

### Common Issues
- May require root for mounting
- Journal replay failures
- Extended attributes handling

## RomFS

**Most common in**: Very minimal embedded systems, bootloaders

### Characteristics
- **Simple**: Very basic read-only filesystem
- **No compression**: Stores files as-is
- **Signature**: `-rom1fs-` at start
- **Alignment**: 16-byte aligned

### Extraction
```bash
# Using binwalk
binwalk -e firmware.bin

# Manual mounting
mkdir /tmp/romfs_mount
mount -t romfs -o loop romfs_image.bin /tmp/romfs_mount

# Using genromfs (for creating/extracting)
genromfs -d output_dir -f romfs_image.bin
```

### Troubleshooting
- **Alignment issues** → Ensure proper offset
- **Legacy format** → May need old tools

## TarFS / Initramfs (CPIO)

**Most common in**: Initramfs, update packages, some bootloaders

### Characteristics
- **Archive format**: Not a filesystem per se
- **Compression**: Often gzip, bzip2, or xz compressed
- **Signature**: CPIO: `070707` or `070701`; TAR: `ustar` at offset 257
- **Common**: Used for initial ramdisks

### Extraction
```bash
# CPIO extraction
cpio -idv < initramfs.cpio
# Or if compressed
zcat initramfs.cpio.gz | cpio -idv

# TAR extraction
tar -xvf archive.tar
# Or if compressed
tar -xzvf archive.tar.gz
tar -xjvf archive.tar.bz2
tar -xJvf archive.tar.xz
```

### Troubleshooting
- **Format detection** → Use `file` command first
- **Nested archives** → May have multiple compression layers

## Comparison Table

| Filesystem | Compression | Use Case | Extraction Difficulty | Tool Support |
|------------|-------------|----------|---------------------|--------------|
| SquashFS | Yes (various) | Most common | Easy | Excellent |
| JFFS2 | Yes (ZLIB) | Older NOR flash | Medium | Good |
| UBIFS | Yes (LZO/ZLIB) | Modern NAND flash | Hard | Moderate |
| CramFS | Yes (ZLIB) | Legacy devices | Easy | Good |
| YAFFS2 | No | Android/NAND | Medium | Limited |
| ext2/3/4 | Optional | Linux systems | Easy | Excellent |
| RomFS | No | Minimal systems | Easy | Good |
| CPIO/TAR | External | Initramfs/packages | Easy | Excellent |

## Filesystem Detection Tips

1. **Use binwalk signature scanning** first
2. **Check magic bytes** manually with hexdump/xxd
3. **Look for filesystem names** in strings output
4. **Entropy analysis** can reveal compressed sections
5. **Try mounting** if Linux filesystem signature detected
6. **Check manufacturer documentation** for hints

## Multi-Filesystem Firmware

Many firmware images contain multiple filesystems:
- Bootloader (often raw or RomFS)
- Kernel (compressed, sometimes in uImage format)
- Root filesystem (SquashFS, JFFS2, UBIFS)
- Data partition (ext4, UBIFS)

Extract each separately using offsets from binwalk output.
