# Binary Analysis Toolchain Reference

Quick reference for common command-line tools used in firmware static analysis.

## file

Identifies file type and architecture.

```bash
file <binary>
```

**Key output indicators:**
- Architecture: `ARM`, `x86-64`, `MIPS`, etc.
- Bitness: `32-bit` or `64-bit`
- Endianness: `LSB` (little) or `MSB` (big)
- Type: `executable`, `shared object`, `relocatable`
- Link type: `dynamically linked` or `statically linked`

## strings

Extracts printable strings from binaries.

```bash
strings -a <binary>           # All strings
strings -a <binary> | grep -i <pattern>  # Filter strings
strings -n <min_length> <binary>         # Minimum length (default: 4)
strings -t x <binary>         # Show hex offsets
```

**What to look for:**
- Usage/help messages
- Format strings (`%s`, `%d`, etc.)
- File paths and directory names
- URLs and domains
- Error messages
- Library names
- Debug symbols
- Hardcoded credentials (common in firmware!)

## readelf

Displays ELF file information.

### Basic Info
```bash
readelf -h <binary>           # ELF header (entry point, type, machine)
readelf -lW <binary>           # Program headers (segments)
readelf -S <binary>           # Section headers
readelf -d <binary>           # Dynamic section (shared libraries)
```

### Symbols
```bash
readelf -s <binary>           # Symbol tables (.symtab and .dynsym, when present)
readelf --dyn-syms --wide <binary>  # Dynamic symbols only (if .dynsym exists)
readelf -Ws <binary>          # All symbol tables; -W prevents line wrapping
readelf -Ws <binary> | grep <function_name>  # Find specific symbol
```

### Other
```bash
readelf -p .comment <binary>  # Compiler info
readelf -p .rodata <binary>   # Read-only data strings
readelf -n <binary>           # Notes (build ID, ABI info)
```

**Key sections to check:**
- `.text`: Code
- `.rodata`: Read-only data (strings, constants)
- `.data`: Initialized data
- `.bss`: Uninitialized data
- `.dynsym`: Dynamic symbols (imports/exports)
- `.dynstr`: Dynamic string table
- `.plt`: Procedure linkage table (function stubs)
- `.got`: Global offset table (addresses)

Use a target-capable binutils build (for example `arm-linux-gnueabi-objdump`)
for foreign architectures. `objdump -i` lists supported targets; the host
`objdump` and `strip` may not support the firmware architecture.

## objdump

Disassembles and displays object file information.

### Disassembly
```bash
objdump -d <binary>                      # Disassemble all executable sections
objdump -d --disassemble=<function> <binary>  # Disassemble specific function
objdump -d -j .text <binary>             # Disassemble only .text section
objdump -d -M intel <binary>             # Intel syntax (x86/x64 only)
```

### Other Info
```bash
objdump -T <binary>           # Dynamic symbol table (alternative to readelf --dyn-syms)
objdump -t <binary>           # All symbol table
objdump -x <binary>           # All headers
objdump -s <binary>           # Full contents (hex dump)
```

**Tips:**
- Use `| less` for large outputs
- After stripping, function names are lost; use `-d -j .text` to browse code sections
- Look for `@plt` suffixes (e.g., `printf@plt`) to identify library calls

## xxd

Hex dump utility for raw binary inspection.

```bash
xxd <binary>                  # Full hex dump
xxd -s 0x<offset> -l <length> <binary>  # Dump at specific offset
xxd -g 1 <binary>             # Group by 1 byte
xxd -b <binary>               # Binary output
```

**Use cases:**
- Verify string table contents
- Examine section data directly
- Look for magic bytes
- Inspect specific offsets from readelf output

## nm

Lists symbols from object files (alternative to readelf -s).

```bash
nm <binary>                   # All symbols
nm -D <binary>                # Dynamic symbols only
nm -g <binary>                # Global symbols only
nm --demangle <binary>        # Demangle C++ symbols
```

**Symbol types:**
- `T`: Text section (code)
- `D`: Initialized data
- `B`: Uninitialized data (BSS)
- `U`: Undefined (imported)
- `W`: Weak symbol

## ldd

Shows shared library dependencies (runtime).

```bash
ldd <binary>
```

**Warning:** Don't run `ldd` on untrusted binaries - it executes the dynamic linker. Use `readelf -d` instead for static analysis.

## strip

Removes symbols from binaries.

```bash
strip <binary>                        # Strip in-place
strip <binary> -o <output>            # Strip to new file
strip --strip-debug <binary>          # Keep function names, remove debug info
```

**Analysis tip:** Compare before/after to understand what symbols were present.

## binwalk

Firmware analysis tool for finding embedded files and filesystems.

```bash
binwalk <firmware>                    # Scan for signatures
binwalk -e <firmware>                 # Extract found files
binwalk -E <firmware>                 # Entropy analysis
```

**Note:** binwalk is useful for full firmware blobs (.bin) but less relevant for individual ELF binaries.

## Common Analysis Workflow

```bash
# 1. Identify the binary
file <binary>

# 2. Extract strings
strings -a <binary> > strings.txt

# 3. Check architecture and entry point
readelf -h <binary>

# 4. List imports/exports
readelf -Ws <binary>

# 5. Check shared library dependencies
readelf -d <binary> | grep NEEDED

# 6. Check for PIE/ASLR
readelf -h <binary> | grep Type

# 7. Look for compiler info
readelf -p .comment <binary>

# 8. Disassemble key functions
objdump -d --disassemble=main <binary>
```
