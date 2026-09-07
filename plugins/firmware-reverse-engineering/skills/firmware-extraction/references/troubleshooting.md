# Firmware Extraction Troubleshooting

Common issues and solutions when extracting firmware.

## Binwalk Issues

### Issue: Binwalk finds nothing
**Symptoms:** `binwalk firmware.bin` returns no results or minimal results

**Possible Causes & Solutions:**

1. **Encrypted firmware**
   ```bash
   binwalk -E firmware.bin  # Check entropy
   # High entropy (>0.9) suggests encryption
   # See encryption.md for decryption workflows
   ```

2. **Wrong offset/alignment**
   ```bash
   # Try different starting offsets
   binwalk -o 0x1000 firmware.bin
   binwalk -o 0x10000 firmware.bin
   ```

3. **Custom/proprietary format**
   ```bash
   # Manual inspection
   xxd firmware.bin | head -50
   strings -a firmware.bin | head -100
   ```

### Issue: Extraction produces corrupted files
**Symptoms:** `binwalk -e` completes but extracted files are unreadable

**Solutions:**
```bash
# 1. Manual extraction with exact offset
binwalk firmware.bin  # Note offset
dd if=firmware.bin of=part.img bs=1 skip=<OFFSET>

# 2. Try filesystem-specific tools
unsquashfs part.img    # For SquashFS
jefferson part.img -d out/  # For JFFS2

# 3. Check endianness
sasquatch -le part.img  # Little endian
sasquatch -be part.img  # Big endian
```

## SquashFS Issues

### Issue: "invalid superblock" error
**Solution:**
```bash
# Use sasquatch for non-standard SquashFS
sasquatch firmware.squashfs

# Or force extraction
unsquashfs -f firmware.squashfs
```

### Issue: LZMA decompression errors
**Solution:**
```bash
# sasquatch supports more LZMA variants
sasquatch firmware.squashfs

# Or use binwalk auto-extraction
binwalk -e --run-as=root firmware.bin
```

## JFFS2 Issues

### Issue: jefferson incomplete extraction
**Solution:**
```bash
# Specify endianness
jefferson -e little firmware.jffs2 -d out/
jefferson -e big firmware.jffs2 -d out/

# Verbose mode for debugging
jefferson -v firmware.jffs2 -d out/
```

## UBIFS Issues

### Issue: "Invalid PEB size" error
**Solution:**
```bash
# Try common PEB sizes
ubireader_extract_images -p 0x20000 firmware.ubi
ubireader_extract_images -p 0x40000 firmware.ubi
ubireader_extract_images -p 0x80000 firmware.ubi
```

## Encrypted Firmware

### High entropy throughout
**Solution:**
1. Check for decryption tools from vendor
2. Search GPL sources for keys
3. Reverse engineer update utilities
4. See encryption.md for detailed workflows

## General Tips

- Always verify extraction with `file` and `binwalk`
- Check file sizes - unreasonably small/large suggests errors
- Try multiple tools - binwalk, sasquatch, jefferson, etc.
- Document what works and what doesn't
- Search for device-specific guides online
