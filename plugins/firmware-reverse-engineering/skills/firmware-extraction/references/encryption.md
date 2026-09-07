# Encrypted & Obfuscated Firmware Reference

Guide for identifying and handling encrypted, compressed, or obfuscated firmware.

## Detection Strategies

### Entropy Analysis

High entropy (close to 8 bits/byte) is compatible with encryption or compression; it proves neither.

```bash
# Using binwalk entropy analysis
binwalk -E firmware.bin

# Using ent
ent firmware.bin

# Visual entropy plot
binwalk -E firmware.bin  # Creates PNG plot
```

**Interpretation:** High values indicate a near-uniform byte distribution;
lower values indicate more repetition. No fixed entropy threshold distinguishes
code, compression or encryption. Compare windows and verify candidate formats.

### Signature Scanning

```bash
# Scan for known signatures
binwalk firmware.bin

# Look for encryption indicators
strings firmware.bin | grep -i -E 'crypt|aes|rsa|cipher|encrypt'

# Check for encryption libraries
strings firmware.bin | grep -i -E 'openssl|mbedtls|wolfssl|libcrypto'
```

### Manual Analysis

```bash
# Hexdump first 512 bytes
xxd -l 512 firmware.bin

# Look for patterns or lack thereof
# Encrypted data: random-looking bytes, no patterns
# Compressed data: may have some structure
# Plaintext: readable strings, clear headers
```

## Common Encryption Schemes

### AES Encryption

**Most common in**: Modern routers, IoT devices, enterprise equipment

#### Indicators
- High entropy throughout
- ECB/CBC ciphertext is block-aligned (16 bytes); CTR/GCM payloads need not be
- May have IV (Initialization Vector) at start
- References to AES in strings

#### Approaches
1. **Look for keys in firmware or bootloader**
```bash
strings firmware.bin | grep -i -E 'key|password|secret'
strings bootloader.bin | grep -E '[0-9a-fA-F]{32,64}'  # Look for hex keys
```

2. **Check for hardcoded keys in companion binaries**
```bash
# Extract other binaries from device
# Check update utilities, management software
strings update_tool.exe | grep -E '[0-9a-fA-F]{32,64}'
```

3. **Search for decryption code in bootloader**
```bash
# If bootloader is available, look for crypto routines
objdump -d bootloader.elf | grep -A 20 -i aes
```

4. **Known vendor keys** (check public databases)
- Some vendors reuse keys across product lines
- Check exploit-db, GitHub, security advisories

#### Common Key Locations
- Hardcoded in bootloader
- Derived from serial number or MAC address
- Stored in separate partition (check `mtd` partitions)
- In accompanying Windows update tools
- In GPL source code releases

### XOR Obfuscation

**Most common in**: Cheap IoT devices, some embedded systems

#### Indicators
- Single-byte XOR preserves Shannon entropy; entropy cannot detect it
- Repeating patterns in byte differences
- Magic bytes are corrupted predictably

#### Detection
```bash
# Check for XOR patterns
# If magic bytes should be "hsqs" (0x68 0x73 0x71 0x73) but appear as:
xxd firmware.bin | head -n 10

# Try simple XOR brute force
for key in {0..255}; do
    dd if=firmware.bin bs=1 count=4 | xxd -p | python3 -c "import sys; data=bytes.fromhex(sys.stdin.read().strip()); print(bytes([b^$key for b in data]))" 2>/dev/null | grep -q "hsqs" && echo "Possible key: $key"
done
```

#### Decryption
```bash
# Python script for XOR decryption
python3 << 'EOF'
with open('firmware.bin', 'rb') as f:
    data = f.read()

key = 0x42  # Replace with found key
decrypted = bytes([b ^ key for b in data])

with open('firmware_decrypted.bin', 'wb') as f:
    f.write(decrypted)
EOF
```

For multi-byte XOR:
```python
def xor_decrypt(data, key):
    """Decrypt with multi-byte XOR key"""
    key_bytes = bytes.fromhex(key) if isinstance(key, str) else key
    if not key_bytes:
        raise ValueError('XOR key must not be empty')
    return bytes([data[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(data))])

# Example usage
with open('firmware.bin', 'rb') as f:
    encrypted = f.read()

# Try known patterns (e.g., if expecting SquashFS)
for key_byte in range(256):
    if encrypted and encrypted[0] ^ key_byte == 0x68:  # 'h' in hsqs
        key = bytes([key_byte])
        decrypted = xor_decrypt(encrypted, key)
        if decrypted[:4] == b'hsqs':
            print(f"Found key: {key_byte:02x}")
            with open('decrypted.bin', 'wb') as f:
                f.write(decrypted)
            break
```

### Custom Encryption

**Most common in**: Proprietary systems, security-focused devices

#### Indicators
- High entropy
- No standard crypto library references
- Custom/unknown header format
- Non-standard block sizes

#### Approaches
1. **Reverse engineer bootloader/updater**
   - Extract decryption routine from bootloader
   - Analyze update tools for decryption logic
   - Check GPL source releases

2. **Look for static analysis clues**
```bash
# Find crypto-like operations in bootloader
objdump -d bootloader.elf | grep -E 'xor|rol|ror|shl|shr' | head -50

# Look for key derivation
strings bootloader.elf | grep -i -E 'serial|mac|id|device'
```

3. **Dynamic analysis**
   - Run update process in controlled environment
   - Monitor memory for keys
   - Intercept decryption calls

4. **Known vulnerabilities**
   - Check CVE databases
   - Search security research papers
   - Check manufacturer advisories

## Compression Detection

### Gzip/Zlib

```bash
# Check for gzip magic
xxd firmware.bin | grep "1f8b 08"

# Extract gzip
gunzip -c firmware.bin > firmware_decompressed.bin
# Or
zcat firmware.bin > firmware_decompressed.bin

# If embedded in larger file
dd if=firmware.bin bs=1 skip=OFFSET | gunzip > decompressed.bin
```

### LZMA/XZ

```bash
# XZ magic is fd 37 7a 58 5a 00; legacy .lzma has a different header
xxd firmware.bin | grep "fd37 7a58 5a"

# Extract XZ
xz -dc firmware.bin > firmware_decompressed.bin
# Or
unxz firmware.bin

# LZMA (older format)
unlzma firmware.bin
# Or
lzma -dc firmware.bin > firmware_decompressed.bin
```

### Custom/Proprietary Compression

#### Detection
- Entropy may be high, including values near 8; use format/code evidence
- No standard compression headers
- May have small header with size/checksum

#### Approaches
1. Check for decompression code in bootloader
2. Look for compression library names in strings
3. Try standard decompressors with various options
4. Reverse engineer decompression routine

## Obfuscation Techniques

### Header Manipulation

Some firmware has modified headers to prevent easy extraction.

```bash
# Check if binwalk misses filesystems
binwalk firmware.bin

# Manual search for filesystem signatures with offset tolerance
hexdump -C firmware.bin | grep -E "68 73 71 73|19 85|53 ef"  # hsqs, JFFS2, ext

# Hexdump searches can miss signatures split across lines. The ext magic is
# 0x438 bytes after the filesystem start; subtract that before carving.
# Try extracting with dd at the verified filesystem offset
dd if=firmware.bin of=extracted.bin bs=1 skip=OFFSET
```

### Byte Swapping

Sometimes bytes are swapped (e.g., big-endian to little-endian).

```bash
# Python script for byte swapping
python3 << 'EOF'
with open('firmware.bin', 'rb') as f:
    data = f.read()

# Swap every 2 bytes (16-bit swap)
swapped = bytearray()
for i in range(0, len(data), 2):
    if i+1 < len(data):
        swapped.extend([data[i+1], data[i]])
    else:
        swapped.append(data[i])

with open('firmware_swapped.bin', 'wb') as f:
    f.write(swapped)
EOF
```

### Padding/Alignment

Firmware may have unusual padding that confuses tools.

```bash
# Do not delete internal zero bytes: they may be meaningful data.
# conv=notrunc only preserves an existing output file; it does not strip padding.

# Skip initial padding
dd if=firmware.bin of=firmware_clean.bin bs=1 skip=OFFSET
```

## Decryption Workflow

1. **Identify encryption type**
   - Run entropy analysis
   - Check for crypto library strings
   - Analyze headers

2. **Search for keys**
   - Check bootloader
   - Examine update tools
   - Search GPL source code
   - Try vendor default keys
   - Derive from device identifiers

3. **Attempt decryption**
   - Use found keys with OpenSSL/cryptography libraries
   - Test multiple key candidates
   - Verify decryption by checking for filesystem signatures

4. **Validate decryption**
```bash
# After decryption, verify
file decrypted.bin
binwalk decrypted.bin
xxd -l 512 decrypted.bin

# Should see valid headers/signatures
```

## Example Decryption Script

```python
#!/usr/bin/env python3
"""
Candidate AES-ECB/CBC probe, not a general firmware decryptor.
Install PyCryptodome. CBC assumes a prepended IV only as a hypothesis;
confirm mode, IV, key derivation, padding and authentication in updater code.
"""

from Crypto.Cipher import AES
import sys

def try_aes_decrypt(data, key, mode='ECB'):
    """Try AES decryption with given key"""
    try:
        if mode == 'ECB':
            cipher = AES.new(key, AES.MODE_ECB)
        elif mode == 'CBC':
            iv = data[:16]  # Assume IV at start
            cipher = AES.new(key, AES.MODE_CBC, iv)
            data = data[16:]
        else:
            raise ValueError('Unsupported probe mode')
        
        decrypted = cipher.decrypt(data)
        return decrypted
    except ValueError:
        return None

def check_firmware_candidate(data):
    """Recognize headers at expected offsets; this does not validate decryption."""
    at_start = (b'hsqs', b'sqsh', b'\x19\x85', b'\x85\x19',
                b'UBI#', b'\x31\x18\x10\x06',
                b'\x45\x3d\xcd\x28', b'\x28\xcd\x3d\x45')
    return data.startswith(at_start) or data[0x438:0x43a] == b'\x53\xef'

def main():
    if len(sys.argv) < 3:
        print("Usage: decrypt_firmware.py <firmware.bin> <key_in_hex>")
        sys.exit(1)
    
    firmware_file = sys.argv[1]
    key_hex = sys.argv[2]
    
    with open(firmware_file, 'rb') as f:
        encrypted = f.read()
    
    key = bytes.fromhex(key_hex)
    
    # Try different modes
    for mode in ['ECB', 'CBC']:
        print(f"Trying AES-{mode}...")
        decrypted = try_aes_decrypt(encrypted, key, mode)
        
        if decrypted and check_firmware_candidate(decrypted):
            output = f"decrypted_{mode}.bin"
            with open(output, 'wb') as f:
                f.write(decrypted)
            print(f"Header candidate saved to {output}")
            print("Verify full parsing, lengths/checksums and any authentication tag.")
    
    print("Probe complete; absent header matches do not rule out a correct key.")

if __name__ == '__main__':
    main()
```

## Resources & Tools

### Encryption Analysis
- **binwalk** - Entropy analysis and signature scanning
- **ent** - Entropy calculator
- **findcrypt** - Find crypto constants in binaries
- **Detect-It-Easy** - Packer/crypter detection

### Decryption Tools
- **OpenSSL** - CLI crypto operations
- **Python cryptography/PyCryptodome** - Scripting crypto operations
- **firmware-mod-kit** - Includes some decryption tools
- **unblob** - Modern firmware extraction with crypto support

### Reverse Engineering
- **Ghidra/IDA/Binary Ninja** - Analyze bootloader decryption routines
- **radare2** - Script-friendly RE tool
- **QEMU + GDB** - Dynamic analysis of decryption

## Vendor-Specific Cases

For TP-Link, D-Link, Netgear, Ubiquiti, Cisco and other vendors, determine the
exact model, hardware revision and firmware build before choosing a decoder.
A vendor name does not imply XOR, AES, a key location or absence of encryption.
Search model-specific advisories, GPL sources and the matching updater/bootloader.
TRX headers describe container metadata; do not assume they contain AES keys.
Record the source and verification for any reused key or decoding procedure.

## When All Else Fails

1. **Check public exploits/research**
   - GitHub repositories
   - Security conference presentations
   - CVE details and PoCs

2. **Contact vendor**
   - Request GPL source (if Linux-based)
   - May provide decryption tools for legitimate research

3. **Physical extraction**
   - UART/JTAG debugging
   - Flash chip reading (SPI/I2C)
   - Runtime memory dumping

4. **Community resources**
   - OpenWrt forums
   - DevttySO blog
   - /r/ReverseEngineering
   - Firmware analysis Discord/Slack channels
