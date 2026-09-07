---
name: firmware-static-analysis
description: "Systematic static analysis of ELF firmware binaries using command-line tools (file, strings, readelf, objdump, xxd). Use when the agent needs to perform initial reconnaissance on firmware/embedded binaries before reverse engineering, specifically for (1) Identifying architecture and binary characteristics, (2) Extracting metadata, strings, and imports, (3) Analyzing symbols, sections, and entry points, (4) Understanding binary structure and dependencies, (5) Generating structured analysis reports. Covers ARM, MIPS, x86, RISC-V, PowerPC architectures. Does NOT handle firmware extraction/unpacking (use separate skill for that)."
---

# Firmware Static Analysis

Perform comprehensive static analysis of ELF firmware binaries using command-line reconnaissance tools. This skill guides systematic metadata extraction and binary characterization before deeper reverse engineering.

## Analysis Workflow

Follow this workflow when analyzing firmware binaries. Always start from Step 1 and proceed sequentially:

1. **Binary identification** - Determine architecture, bitness, endianness
2. **String extraction** - Find human-readable strings and clues
3. **Symbol analysis** - Examine imports, exports, and functions
4. **Structure analysis** - Analyze segments, sections, and entry points
5. **Security analysis** - Check PIE, RELRO, stack canaries
6. **Metadata extraction** - Find compiler info and build metadata
7. **Report generation** - Create structured markdown report

## Step 1: Binary Identification

Identify the target architecture and basic characteristics.

```bash
file <binary>
```

**Extract these details:**
- CPU architecture (ARM, MIPS, x86, RISC-V, PowerPC, etc.)
- Bitness (32-bit or 64-bit)
- Endianness (LSB/little-endian or MSB/big-endian)
- Link type (dynamically linked, statically linked, or not linked)
- Binary type (executable, shared object, relocatable)

**Architecture reference:** If unfamiliar with the detected architecture, read `references/architectures.md` for architecture-specific details including calling conventions and common use cases.

## Step 2: String Extraction

Extract all printable strings to understand program behavior and inputs.

```bash
strings -a <binary> > strings.txt
```

**Analyze for:**
- Usage/help text patterns (`usage|help|--`)
- Format strings (`%s|%d|%x`)
- Error messages (`error|fail|invalid`)
- File paths and directories (`/etc/|/tmp/|/var/`)
- URLs and network addresses
- Hardcoded credentials (common in firmware!)
- Library names and debug paths
- Version strings and build info

**Targeted searches:**
```bash
strings -a <binary> | grep -i -E 'usage|error|%d|%s'
strings -a <binary> | grep -i -E 'password|admin|root|key'
strings -a <binary> | grep -E '^/|^\.'  # File paths
```

## Step 3: Symbol Analysis

Examine what functions the binary imports and exports.

### Dynamic Symbols (when .dynsym is present, including many stripped binaries)
```bash
readelf --dyn-syms --wide <binary>
```

**Look for:**
- Imported functions (from libc, libssl, custom libraries)
- Exported functions (what this binary provides)
- Function names that hint at behavior (`authenticate`, `encrypt`, `parse`, etc.)
- Standard library usage patterns

**Alternative command:**
```bash
objdump -T <binary>
```

### Function Discovery
Identify key functions for later disassembly:
```bash
readelf -Ws <binary> | grep ' main$'
readelf -Ws <binary> | grep -E 'FUNC.*GLOBAL'
```

Common firmware functions to look for: `main`, `init`, `setup`, `parse_config`, `handle_request`, `authenticate`, `encrypt`, `decrypt`

## Step 4: Structure Analysis

Analyze the binary's internal structure.

### ELF Header
```bash
readelf -h <binary>
```

**Key information:**
- **Entry point address** - Where execution begins
- **Type** - ET_EXEC (non-PIE) or ET_DYN (PIE/shared object)
- **Machine** - Confirm architecture
- **Section headers** - Number and locations

### Program Headers (Segments)
```bash
readelf -lW <binary>
```

**Check for:**
- **INTERP segment** - Dynamic linker path (if dynamically linked)
- **LOAD segments** - Memory layout (addresses, permissions)
- **DYNAMIC segment** - Dynamic linking information
- **GNU_STACK** - Stack permissions (NX bit)

### Section Headers
```bash
readelf -S <binary>
```

**Important sections:**
- `.text` - Code section (note size and address)
- `.rodata` - Read-only data (strings, constants)
- `.data` - Initialized data
- `.bss` - Uninitialized data
- `.dynsym` / `.dynstr` - Dynamic symbols and strings
- `.plt` / `.got` - Procedure linkage table and global offset table
- `.comment` - Compiler information

**Verify symbol tables directly:**
```bash
# Get .dynsym and .dynstr offsets from readelf -S
xxd -s 0x<DYNSYM_OFFSET> -l 256 <binary>
xxd -s 0x<DYNSTR_OFFSET> -l 256 <binary>
```

### Dynamic Section
```bash
readelf -d <binary>
```

**Extract:**
- **NEEDED** - Shared library dependencies
- **SONAME** - Shared object name (if present)
- **RPATH/RUNPATH** - Library search paths
- **FLAGS** - Dynamic linking flags

## Step 5: Security Analysis

Assess available evidence, retaining an **unknown/not observed** result where needed.
`PT_GNU_RELRO` is a program header. For conventional dynamically linked ELF,
that segment plus immediate binding (`BIND_NOW` or `FLAGS/FLAGS_1` containing
`NOW`) indicates full RELRO; the segment alone indicates partial RELRO.
Absent dynamic tags in a static binary require a different assessment.

`GNU_STACK` without `E` requests a non-executable stack. A missing header is
unknown and depends on the ABI/kernel. Canary or `_chk` symbols show some
instrumentation, not complete coverage; absence does not prove absence in
stripped, static or inlined code. Inspect relevant functions when reporting.

### PIE/ASLR Check
```bash
readelf -h <binary> | grep Type
```
- `Type: EXEC (Executable file)` = Non-PIE (fixed addresses)
- `Type: DYN (Shared object file)` = PIE candidate OR shared library. Check `FLAGS_1: PIE`, loader metadata and intended use.
- ASLR is runtime policy, not established by ELF type. Verify on the target kernel and compare mappings across runs.

### Security Features Check
```bash
readelf -dW <binary> | grep -E 'BIND_NOW|FLAGS.*NOW'
readelf -lW <binary> | grep -E 'GNU_RELRO|GNU_STACK'
readelf -Ws <binary> | grep -E '__stack_chk_fail|__(memcpy|memmove|strcpy|strncpy|sprintf|snprintf|printf)_chk'
```

**Look for:**
- **RELRO** (RELocation Read-Only) - GOT protections
- **Stack canaries** (`__stack_chk_fail`)
- **NX stack** (non-executable stack via GNU_STACK)
- **Fortify evidence**: checked wrappers such as `__memcpy_chk` or `__snprintf_chk`

## Step 6: Metadata Extraction

Extract compiler and build information.

### Compiler Info
```bash
readelf -p .comment <binary>
strings <binary> | grep -i -E 'gcc|clang|build|version'
```

**Look for:**
- GCC/Clang version
- Target triplet (e.g., `arm-linux-gnueabihf-gcc`)
- Optimization level hints
- Build date/time

### Build Metadata
```bash
readelf -n <binary>  # Build ID and ABI info
```

## Step 7: Disassembly (with symbols)

If symbols are present, disassemble key functions.

### Verify Symbol Availability
```bash
readelf -Ws <binary> | grep ' main$'
readelf -Ws <binary> | grep -E '<function_name>'
```

### Disassemble Functions
```bash
objdump -d --disassemble=main <binary>
objdump -d --disassemble=<function_name> <binary>
```

**Analysis tips:**
- Look for calls to imported functions (e.g., `printf@plt`, `strcmp@plt`)
- Identify control flow (branches, loops)
- Note register usage patterns
- Track function call arguments

## Step 8: Handling Stripped Binaries

When symbols are removed, adapt the analysis approach.

### Strip and Compare
```bash
cp <binary> <binary>_stripped
strip <binary>_stripped

# Compare before/after
readelf -Ws <binary>
readelf -Ws <binary>_stripped
```

### Disassemble Without Symbols
```bash
# Name-based disassembly will fail:
objdump -d --disassemble=main <binary>_stripped  # FAILS

# Instead, dump entire .text section:
objdump -d -j .text <binary>_stripped | less
```

**Function identification strategies:**
- Look for common prologues (e.g., ARM: `push {r11, lr}`, x86: `push rbp`)
- Find calls to known PLT functions (e.g., `atoi@plt`, `printf@plt`)
- Use entry point address from readelf -h as starting point
- Look for string references (xrefs to .rodata)

## Report Generation

Create a structured markdown report with all findings. Use this template:

```markdown
# Firmware Static Analysis Report

**Binary:** <filename>
**Analysis Date:** <date>

## Executive Summary

[2-3 sentence overview of the binary: purpose, architecture, and key findings]

## Binary Characteristics

- **File Type:** [ELF type]
- **Architecture:** [CPU architecture, bitness, endianness]
- **Entry Point:** [address]
- **Link Type:** [static/dynamic]
- **PIE:** [Yes/No/Unknown; evidence]
- **ASLR:** [Runtime tested / Not tested; evidence]
- **Stripped:** [Yes/No]

## Architecture Details

- **CPU:** [ARM/MIPS/x86/RISC-V/etc.]
- **Bitness:** [32-bit / 64-bit]
- **Endianness:** [Little-endian / Big-endian]
- **Calling Convention:** [ABI details]

## Symbol Analysis

### Imported Functions
[List key imported functions and what they suggest about behavior]
- `printf` - Formatting and output
- `socket` - Network communication
- `strcmp` - String comparison
- etc.

### Exported Functions
[List exported functions if any]

### Key Functions Identified
[List main and other important functions found]

## String Analysis

### Interesting Strings
[List notable strings found, categorized by type]

**Configuration/Paths:**
- `/etc/config.conf`
- etc.

**Credentials/Keys:**
- `admin:default_password` [⚠️ SECURITY CONCERN]
- etc.

**Error Messages:**
- "Invalid input"
- etc.

**Network/URLs:**
- `http://update.example.com`
- etc.

## Structure Analysis

### Segments
[List key program segments with addresses and permissions]

### Sections
[List important sections with sizes]
- `.text`: [size] - Code
- `.rodata`: [size] - Read-only data
- etc.

### Dynamic Dependencies
[List required shared libraries]
- `libc.so.6`
- `libssl.so.1.1`
- etc.

## Security Analysis

### Mitigations Detected
- PIE: [Yes/No/Unknown; evidence]
- ASLR: [Runtime result/Not tested]
- RELRO: [Full/Partial/None/Unknown; evidence]
- Stack canary evidence: [Observed/Not observed/Unknown; coverage unverified]
- Stack execute request: [Non-executable/Executable/Missing; runtime unverified]
- Fortify evidence: [Observed/Not observed/Unknown]

### Security Concerns
[List any security issues found]
- Hardcoded credentials
- Weak/no ASLR
- Missing stack protection
- etc.

## Metadata

### Compiler Information
- **Compiler:** [GCC/Clang version]
- **Target:** [Toolchain target triplet]
- **Build Date:** [if available]

### Build ID
[Build ID from notes section]

## Disassembly Highlights

### main() Function
[Brief description of what main does based on disassembly]

### Other Key Functions
[Brief description of other important functions]

## Recommendations for Further Analysis

1. [Specific next steps based on findings]
2. [Tools to use next: Ghidra, IDA, Binary Ninja, etc.]
3. [Specific functions or areas to focus on]
4. [Dynamic analysis recommendations]

## Appendix

### Full Symbol Table
[Attach or reference full symbol list if relevant]

### Complete String Dump
[Reference to strings.txt file]
```

## Additional References

- **Architecture details:** See `references/architectures.md` for architecture-specific calling conventions and characteristics
- **Toolchain commands:** See `references/toolchain.md` for detailed command syntax and options

## Tips

- **Always work on a copy** - Never modify the original firmware binary
- **Save intermediate outputs** - Redirect command outputs to files for reference (e.g., `strings -a binary > strings.txt`)
- **Cross-reference findings** - Strings/imports are candidates; verify authentication use, attacker control and reachability before reporting a vulnerability
- **Architecture matters** - Load the architecture reference early if unfamiliar with the target
- **Document as you go** - Build the report incrementally during analysis
- **Look for the unusual** - Hardcoded credentials, unusual network addresses, and debug paths are common in firmware
- **Check toolchain** - Version strings are clues; verify component identity, backports and vulnerable code before assigning a CVE
- **PIE vs non-PIE** - ET_EXEC binaries have fixed addresses, making analysis easier
- **Stripped binaries** - Don't despair, entry point and PLT calls still provide context
