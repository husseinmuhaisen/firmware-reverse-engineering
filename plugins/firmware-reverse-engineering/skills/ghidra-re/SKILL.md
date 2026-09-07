---
name: ghidra-re
description: "Expert-level Ghidra reverse engineering for firmware binaries with emphasis on stripped binary analysis, automated function discovery, cryptographic routine identification, authentication logic detection, and vulnerability hunting. Use when the agent needs to perform deep static analysis of firmware binaries in Ghidra. Covers: (1) Stripped binary analysis techniques (function discovery via prologues, xrefs, string tracing), (2) Type recovery and structure reconstruction, (3) Automated analysis via Python scripting (Ghidra API), (4) Cryptographic function identification (AES, MD5, SHA constants), (5) Authentication and authorization function discovery, (6) Vulnerability detection (buffer overflows, format strings, command injection, manual data-flow verification), (7) Decompiler enhancement and custom type propagation, (8) Integration with emulation workflow. Assumes expert RE knowledge. Complements firmware-static-analysis (basic recon) and firmware-emulation (dynamic analysis)."
---

# Ghidra Reverse Engineering for Firmware

Expert-level Ghidra workflows for analyzing stripped firmware binaries, with automation via Python scripting.

## Skill Scope

**Use this skill for:**
- Deep analysis of individual firmware binaries in Ghidra
- Stripped binary reverse engineering
- Automated vulnerability hunting
- Cryptographic routine identification
- Authentication logic discovery
- Custom script development

**Prerequisites:**
- Ghidra 12.1.3 with its bundled **Jython extension** installed (File → Install Extensions → Jython, then restart). Scripts explicitly select `# @runtime Jython`; they do not run in a standalone Python interpreter.
- JDK required by the installed Ghidra release (JDK 21 for 12.1.3)
- Python scripting knowledge
- Understanding of assembly (ARM/MIPS/x86)
- Binary already extracted (use firmware-extraction skill)

**Integration:**
- After: firmware-extraction, firmware-static-analysis (initial recon)
- Before/During: firmware-emulation (validate findings dynamically)

The four bundled scripts produce review candidates, not confirmed vulnerabilities. They
inspect recovered instructions and resolved references; indirect calls, inlined code and
unrecovered data may be missed. They preserve existing names and comments; candidate
renames apply only to default symbols. Save the project before running analysis scripts.

Set these paths for the headless examples (replace with absolute local paths):

```bash
export GHIDRA_INSTALL_DIR=/path/to/ghidra_12.1.3_PUBLIC
export GHIDRA_SCRIPT_DIR=/path/to/ghidra-re/scripts
mkdir -p /projects
```

## Analysis Workflow

### 1. Project Setup

```bash
# Create project
"$GHIDRA_INSTALL_DIR/ghidraRun"

# Or headless for automation
"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" /projects FirmwareProject -scriptPath "$GHIDRA_SCRIPT_DIR" -import /path/to/binary.elf

# Batch import
for bin in extracted/bin/*; do
    "$GHIDRA_INSTALL_DIR/support/analyzeHeadless" /projects Firmware -scriptPath "$GHIDRA_SCRIPT_DIR" -import "$bin"
done
```

### 2. Initial Analysis (Stripped Binary Focus)

**Automated approach:**
```bash
# Run analysis scripts in sequence
"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" /projects Firmware -scriptPath "$GHIDRA_SCRIPT_DIR" -process binary.elf \
  -postScript find_crypto.py \
  -postScript find_auth_functions.py \
  -postScript find_buffer_overflows.py
```

**Manual approach:**

1. **Run Auto-Analysis** (Analysis → Auto Analyze)
   - Enable: Aggressive Instruction Finder, Stack, Decompiler Parameter ID

2. **Find Functions** - Stripped binaries need manual function discovery
   - Entry point: Find _start or main
   - Prologue scanning (see `references/stripped-analysis.md`)
   - Cross-reference analysis
   - String reference tracing

3. **Initial Renaming**
   - Run `scripts/auto_rename.py` for heuristic-based naming
   - Manually rename critical functions

### 3. Target-Specific Analysis

Choose analysis path based on goal:

**Authentication Analysis** → Use `scripts/find_auth_functions.py`
- Identifies strcmp, password string refs, multi-return patterns
- Ranks by heuristic score (not a probability)
- Adds candidate names to highly ranked default symbols

**Crypto Analysis** → Use `scripts/find_crypto.py`
- Searches for AES S-boxes, MD5/SHA constants
- Labels crypto tables
- Finds functions referencing crypto constants

**Vulnerability Hunting** → Use `scripts/find_buffer_overflows.py`
- Detects dangerous function calls (strcpy, sprintf, gets)
- Flags source/sink co-occurrence within a function; does not trace taint
- Lists large recovered stack objects in functions with risky API calls

**Network Protocol Analysis**
- Find socket/recv/send calls
- Trace data flow from network input
- Identify protocol parsing functions

### 4. Deep Function Analysis

For each interesting function:

```python
# @runtime Jython
# Decompile and enhance
func = getFunctionAt(toAddr("0x00401000"))

# Set signature (if known)
sig = "int verify_password(char *user_input, char *stored_hash)"
from ghidra.app.cmd.function import ApplyFunctionSignatureCmd
from ghidra.app.util.parser import FunctionSignatureParser
from ghidra.program.model.symbol import SourceType
from ghidra.program.model.listing import Function, ParameterImpl
from ghidra.program.model.data import *
assert func is not None, "Select a valid function entry"
definition = FunctionSignatureParser(currentProgram.getDataTypeManager(), None).parse(func.getSignature(), sig)
assert ApplyFunctionSignatureCmd(func.getEntryPoint(), definition, SourceType.USER_DEFINED).applyTo(currentProgram)

# Define structures
dtm = currentProgram.getDataTypeManager()
struct = StructureDataType("auth_request", 0)
struct.add(DWordDataType(), "session_id", None)
struct.add(PointerDataType(CharDataType()), "username", None)
struct.add(PointerDataType(CharDataType()), "password", None)
dtm.addDataType(struct, DataTypeConflictHandler.REPLACE_HANDLER)

# Apply to function parameters
param = ParameterImpl("request", PointerDataType(struct), currentProgram)
func.replaceParameters(Function.FunctionUpdateType.DYNAMIC_STORAGE_ALL_PARAMS, True, SourceType.USER_DEFINED, param)
```

### 5. Vulnerability Analysis

**Buffer Overflow Detection:**
```python
# @runtime Jython
# Manual verification after script identifies candidates
# 1. Check buffer size
# 2. Trace input length
# 3. Verify bounds checking (or lack thereof)
# 4. Confirm exploitability

# Example: strcpy without length check
# Decompiler shows:
#   strcpy(local_buffer, user_input);
# Check local_buffer size in stack frame
# Verify attacker-controlled length exceeds the destination and reaches this call.
# A write beyond the buffer is a vulnerability; code execution needs separate evidence.
```

**Format String Bugs:**
```python
# @runtime Jython
# Find printf(user_controlled_string)
# Script pattern:
if "printf" in called_functions:
    # Check if format arg is from user input
    # A variable format is not necessarily attacker-controlled; trace its origin.
    pass  # Manual review, not a complete detector
```

**Command Injection:**
```python
# @runtime Jython
# Find system/popen with user data
# Pattern: system(cmd) where cmd contains user input
# Look for string concatenation before system() call
```

### 6. Type and Structure Recovery

**Automated structure inference:**
```python
# @runtime Jython
# See references/stripped-analysis.md for a sketch, not a complete inference engine
# Analyzes memory access patterns:
# - *(ptr + 0) → field at offset 0
# - *(ptr + 4) → field at offset 4
# Define the structure manually after verifying offsets and field sizes
```

**Manual structure definition:**
```python
# @runtime Jython
# From decompiler output showing member accesses
struct = StructureDataType("device_state", 0)
struct.add(DWordDataType(), "magic", None)          # offset 0
struct.add(ByteDataType(), "enabled", None)         # offset 4
struct.add(ArrayDataType(CharDataType(), 32, 1), "name", None)  # offset 5
# Apply and watch decompiler improve
```

### 7. Cross-Referencing

**Find callers:**
```
Right-click function → References → Show References to
```

**Find call sites:**
```python
# @runtime Jython
func = getFunctionAt(currentAddress)
refs = getReferencesTo(func.getEntryPoint())
for ref in refs:
    if ref.getReferenceType().isCall():
        caller = getFunctionContaining(ref.getFromAddress())
        if caller:
            print("Called from: {}".format(caller.getName()))
```

**Trace data flow:**
```python
# @runtime Jython
# From source to sink
# 1. Find all calls to source (e.g., recv)
# 2. Track where data goes
# 3. Check if reaches sink (e.g., system)
# See scripts/find_buffer_overflows.py for manual data-flow verification
```

## Provided Scripts

All scripts in `scripts/` run in Ghidra with the Jython runtime above:

### find_crypto.py
Finds candidate constant prefixes and their direct references; absence is not evidence that crypto is absent:
- First 16 bytes of the AES S-box
- First four MD5 / SHA256 constants in either byte order
- Auto-labels crypto tables
- Finds functions referencing crypto data

**Usage:**
```bash
"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" /projects Project -scriptPath "$GHIDRA_SCRIPT_DIR" -process binary -postScript find_crypto.py
```

### find_auth_functions.py
Discovers authentication logic via heuristics:
- String analysis (password, login, auth keywords)
- API calls (strcmp, crypt, verify)
- Multi-return patterns (success/fail branches)
- Scores and ranks candidates

**Usage:**
```bash
"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" /projects Project -scriptPath "$GHIDRA_SCRIPT_DIR" -process binary -postScript find_auth_functions.py
```

### find_buffer_overflows.py
Detects potential buffer overflow vulnerabilities:
- Dangerous function calls (strcpy, sprintf, gets)
- Source/sink co-occurrence (data flow unverified)
- Stack buffer identification
- Appends review notes at candidate locations without deleting analyst comments

**Usage:**
```bash
"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" /projects Project -scriptPath "$GHIDRA_SCRIPT_DIR" -process binary -postScript find_buffer_overflows.py
```

## Scripting Patterns

### Template Script

```python
# @runtime Jython
# my_analysis.py
# Description: Custom analysis for firmware

from ghidra.program.model.symbol import SourceType

currentProgram = getCurrentProgram()
listing = currentProgram.getListing()
fm = currentProgram.getFunctionManager()
mem = currentProgram.getMemory()

# Your analysis logic
for func in fm.getFunctions(True):
    # Process each function
    pass
```

### Common Operations

```python
# @runtime Jython
# Navigate
addr = toAddr("0x00400000")
func = getFunctionAt(addr)
func = getFunctionContaining(addr)

# Modify
func.setName("new_name", SourceType.USER_DEFINED)
createFunction(addr, "function_name")
createLabel(addr, "label_name", True)

# Data types
from ghidra.program.model.data import *
DWordDataType()
PointerDataType(CharDataType())
StructureDataType("struct_name", 0)

# Instructions
instr = listing.getInstructionAt(addr)
instr.getMnemonicString()  # "bl", "mov", etc.
instr.getReferencesFrom()

# Decompiler
from ghidra.app.decompiler import DecompInterface
decompiler = DecompInterface()
decompiler.openProgram(currentProgram)
results = decompiler.decompileFunction(func, 30, monitor)
high_func = results.getHighFunction()
```

## Stripped Binary Techniques

### Function Discovery

**Method 1: Prologue Scanning**
```python
# @runtime Jython
# ARM: push {r11, lr} = 0xe92d4800
# MIPS: addiu sp,sp,-XX
# x86: push ebp; mov ebp,esp

# Search for patterns in executable memory
# See references/stripped-analysis.md for complete implementation
```

**Method 2: Cross-Reference Analysis**
```python
# @runtime Jython
# Find all call instructions
# Target addresses likely are function starts
# See references/stripped-analysis.md
```

**Method 3: String References**
```python
# @runtime Jython
# Functions that reference strings
# Use string content to infer function purpose
# See references/stripped-analysis.md
```

### Automatic Renaming Heuristics

```python
# @runtime Jython
# Pattern-based naming
def infer_name(func):
    strings = get_function_strings(func)
    called = get_called_functions(func)
    
    # Authentication
    if any("password" in s.lower() for s in strings):
        if "strcmp" in called:
            return "check_password"
    
    # Network
    if "socket" in called or "recv" in called:
        return "network_handler"
    
    # Crypto
    if "aes" in "".join(strings).lower():
        return "crypto_aes"
    
    return None
```

## Integration with Emulation

**Workflow:**
1. Static analysis in Ghidra (this skill)
2. Identify interesting functions
3. Set breakpoints in GDB at those addresses
4. Run in QEMU (firmware-emulation skill)
5. Observe behavior at breakpoints
6. Return to Ghidra with insights

**Example:**
```python
# @runtime Jython
# In Ghidra: Find auth function
auth_func = getFunctionAt(toAddr("0x00401234"))

# Note address: 0x00401234. For PIE/shared objects, translate using the actual
# runtime load bias; do not use a static address unchanged.

# In QEMU with GDB:
# gdb-multiarch binary
# (gdb) target remote :1234
# (gdb) break *0x00401234
# (gdb) continue
# ... trigger auth ...
# (gdb) info registers  # See actual values

# Return to Ghidra with understanding of runtime behavior
```

## Best Practices

1. **Start Automated** - Run scripts before manual analysis
2. **Name Incrementally** - Don't try to name everything at once
3. **Trust Decompiler, Verify Assembly** - Decompiler is good but not perfect
4. **Document Assumptions** - Use comments liberally
5. **Version Control** - Use a shared Ghidra Server project for program versioning; use Git for exported scripts and notes
6. **Cross-Reference Constantly** - Understand call graphs
7. **Type Everything** - Proper types improve decompilation dramatically
8. **Script Repetitive Tasks** - Don't do the same thing 100 times manually

## Keyboard Shortcuts

```
G                Go to address
L                Label/rename
;                EOL comment
Ctrl-;           Pre-comment
D                Disassemble
P                Create function
X                Show references to
Ctrl-Shift-E     Edit function signature
T                Set data type
```

## Troubleshooting

**Decompiler fails:**
- Check for unimplemented instructions
- Simplify function (may be too complex)
- Try different decompiler options

**Auto-analysis misses functions:**
- Use scripts from `scripts/` folder
- Manual prologue search (see `references/stripped-analysis.md`)

**Poor decompilation quality:**
- Set proper function signatures
- Define structures for complex data types
- Add type information to variables

## References

- **Stripped Analysis**: `references/stripped-analysis.md` - Complete techniques for analyzing stripped binaries, type recovery, function discovery
- **Workflow**: `references/workflow.md` - Expert workflow patterns, scripting examples, integration tips

## Quick Command Reference

```bash
# Headless analysis with scripts
"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" /projects Firmware -scriptPath "$GHIDRA_SCRIPT_DIR" -import binary.elf \
  -postScript find_crypto.py -postScript find_auth_functions.py

# Import without auto-analysis (manual control)
"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" /projects Firmware -scriptPath "$GHIDRA_SCRIPT_DIR" -import binary.elf -noanalysis

# Export analysis results (first save the JSON example in references/workflow.md
# as export_results.py in GHIDRA_SCRIPT_DIR; it is not a bundled script)
"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" /projects Firmware -scriptPath "$GHIDRA_SCRIPT_DIR" -process binary.elf \
  -postScript export_results.py
```

```python
# @runtime Jython
# Essential Ghidra Python APIs
currentProgram                              # Program object
getFunctionAt(addr)                         # Get function
createFunction(addr, name)                  # Create function
toAddr("0x00400000")                        # String to address
listing.getInstructions(body, True)         # Iterate instructions
getReferencesTo(addr)                       # Get xrefs to
func.setName(name, SourceType.USER_DEFINED) # Rename function
```

## Next Steps After Ghidra Analysis

1. **Document findings** - Create analysis report with key functions, vulnerabilities
2. **Test hypotheses** - Use firmware-emulation to verify static findings
3. **Develop exploits** - If vulnerabilities found, create PoCs
4. **Report** - Prepare comprehensive security assessment

This skill assumes expert RE knowledge and focuses on firmware-specific analysis patterns. For general Ghidra basics, consult official documentation.
