# Expert Ghidra Workflow

Streamlined workflow for analyzing firmware binaries in Ghidra.

## Project Setup

```bash
# Headless analysis (automation-friendly)
"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" /projects MyProject -scriptPath "$GHIDRA_SCRIPT_DIR" -import binary.elf

# With post-analysis script
"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" /projects MyProject -scriptPath "$GHIDRA_SCRIPT_DIR" -import binary.elf \
  -postScript find_crypto.py -postScript find_auth_functions.py

# Batch import
for bin in extracted/bin/*; do
    "$GHIDRA_INSTALL_DIR/support/analyzeHeadless" /projects FirmwareAnalysis -scriptPath "$GHIDRA_SCRIPT_DIR" -import "$bin"
done
```

## Initial Analysis Checklist

1. **Run Auto-Analysis** (Analysis → Auto Analyze)
   - Enable all default analyzers
   - Add: "Aggressive Instruction Finder", "Non-Returning Functions"

2. **Identify Entry Point**
   ```python
# @runtime Jython
   # If stripped, find _start or main manually
   for entry in currentProgram.getSymbolTable().getExternalEntryPointIterator():
       print(entry)  # Loader entry points; raw images need a researched address
   ```

3. **Find Functions** (examples in `references/stripped-analysis.md`)
   - Prologue scanning
   - Cross-reference analysis
   - String reference tracing

4. **Initial Naming** (scripts/auto_rename.py)
   - String-based heuristics
   - API call patterns
   - Complexity analysis

## Function Analysis Pattern

For each interesting function:

1. **Decompile** (Window → Decompiler)
2. **Rename variables** (Right-click → Rename Variable)
3. **Set types** (Right-click → Retype Variable)
4. **Add comments** (;=EOL comment, Ctrl-;=pre comment, Alt-;=post comment)
5. **Define structures** (if member accesses visible)

## Keyboard Shortcuts (Essential)

```
G           Go to address
L           Label/rename
;           Add EOL comment
Ctrl-;      Add pre-comment
Alt-;       Add post-comment
D           Disassemble
C           Clear code bytes
P           Create function
U           Undefine
T           Set data type
X           Show references to
Ctrl-Shift-E  Set function signature
```

## Decompiler Tips

### Improve Decompilation

```python
# @runtime Jython
# Set function signature manually
func = getFunctionAt(currentAddress)
sig = "int auth_check(char *username, char *password)"
from ghidra.app.cmd.function import ApplyFunctionSignatureCmd
from ghidra.app.util.parser import FunctionSignatureParser
from ghidra.program.model.symbol import SourceType
assert func is not None
signature = FunctionSignatureParser(currentProgram.getDataTypeManager(), None).parse(func.getSignature(), sig)
assert ApplyFunctionSignatureCmd(func.getEntryPoint(), signature, SourceType.USER_DEFINED).applyTo(currentProgram)

# Or via GUI: Ctrl-Shift-E
```

### Understanding Output

- **undefined4** → Unknown 4-byte type (likely int)
- **UNIMPLEMENTED** → Instruction not supported by decompiler
- **DAT_XXXXX** → Unnamed data at address XXXXX
- **(cast)** → Decompiler inserted type cast

The snippets below illustrate individual operations and assume a valid `func`,
`listing`, `fm`, and task monitor where used. They are not all standalone scripts.
Use the bundled scripts for executable automation.

## Scripting Patterns

### Iterate All Functions

```python
# @runtime Jython
fm = currentProgram.getFunctionManager()
for func in fm.getFunctions(True):
    # Process each function
    pass
```

### Modify Function Signature

```python
# @runtime Jython
func = getFunctionAt(currentAddress)
from ghidra.program.model.listing import Function, ParameterImpl
from ghidra.program.model.data import *
from ghidra.program.model.symbol import SourceType
params = [
    ParameterImpl("buffer", PointerDataType(CharDataType()), currentProgram),
    ParameterImpl("size", DWordDataType(), currentProgram)
]
func.replaceParameters(Function.FunctionUpdateType.DYNAMIC_STORAGE_ALL_PARAMS, True, SourceType.USER_DEFINED, *params)
```

### Create Custom Data Type

```python
# @runtime Jython
dtm = currentProgram.getDataTypeManager()
struct = StructureDataType("request_packet", 0)
struct.add(DWordDataType(), "magic", None)
struct.add(WordDataType(), "command", None)
struct.add(PointerDataType(CharDataType()), "data", None)
dtm.addDataType(struct, DataTypeConflictHandler.REPLACE_HANDLER)
```

### Batch Rename

```python
# @runtime Jython
# Rename all FUN_* functions with pattern
fm = currentProgram.getFunctionManager()
for func in fm.getFunctions(True):
    if func.getSymbol().getSource() == SourceType.DEFAULT:
        addr_hex = str(func.getEntryPoint()).replace(":", "_")
        func.setName("sub_" + addr_hex, SourceType.ANALYSIS)
```

## Advanced Techniques

### P-Code Analysis

```python
# @runtime Jython
# Analyze at IL level
from ghidra.app.decompiler import DecompInterface

decompiler = DecompInterface()
decompiler.openProgram(currentProgram)
results = decompiler.decompileFunction(func, 30, monitor)

if results.decompileCompleted():
    high_func = results.getHighFunction()
    for op in high_func.getPcodeOps():
        print("{}: {}".format(op.getOpcode(), op))
decompiler.dispose()
```

### Custom Analysis Pass

```python
# @runtime Jython
# API sketch only: defining this Python class does not register an analyzer.
# Deploy a Java Ghidra extension for automatic analyzer discovery.
from ghidra.app.services import AbstractAnalyzer, AnalyzerType

class MyAnalyzer(AbstractAnalyzer):
    def __init__(self):
        AbstractAnalyzer.__init__(self, "Custom Analyzer", "Description", AnalyzerType.FUNCTION_ANALYZER)
    
    def canAnalyze(self, program):
        return True
    
    def added(self, program, addrSet, monitor, log):
        # Your analysis logic
        return True
```

### Export Analysis

```python
# @runtime Jython
# Export to JSON for external processing
import json

results = {}
fm = currentProgram.getFunctionManager()

for func in fm.getFunctions(True):
    results[str(func.getEntryPoint())] = {
        'name': func.getName(),
        'size': func.getBody().getNumAddresses(),
        'calls': [str(c.getEntryPoint()) for c in func.getCalledFunctions(monitor)]
    }

with open('/tmp/analysis.json', 'w') as f:
    json.dump(results, f, indent=2)
```

## Integration with Other Tools

### Export for IDA

```
File → Export Program → Intel Hex
# Intel Hex exports bytes/address layout, not Ghidra names/types/comments.
# Prefer the original ELF when loading the same executable in IDA.
```

### Binary Diff

```
Tools → Version Tracking
# Compare two versions of firmware
```

### Collaborate

```
Use a shared project on Ghidra Server for program versioning/check-in.
Use Git for scripts and exported notes, not live project database files.
```

## Performance Optimization

```bash
# Increase heap for large binaries
# Set MAXMEM=8G in the ghidraRun launcher (see its existing MAXMEM setting).
"$GHIDRA_INSTALL_DIR/ghidraRun"

# Disable auto-analysis for very large files
# Import, then selectively analyze regions
```

## Debugging Ghidra Scripts

```python
# @runtime Jython
# Print to console
print("Debug: value={}".format(value))

# Use monitor for progress
monitor.setMessage("Processing function...")
monitor.initialize(total)
monitor.setProgress(i)

# Check for cancellation
monitor.checkCancelled()

# Exception handling
try:
    pass  # Replace with the operation being investigated
except Exception as e:
    print("Error: {}".format(e))
    import traceback
    traceback.print_exc()
```

## Common Patterns

### Find Format String Bugs

```python
# @runtime Jython
# Find printf-family calls with user-controlled format
for func in fm.getFunctions(True):
    for call in get_call_sites(func):
        if call['target'] in ['printf', 'sprintf', 'fprintf']:
            # Check if format arg is from untrusted source
            pass
```

### Identify Command Injection

```python
# @runtime Jython
# Find system/exec calls
dangerous_exec = ['system', 'popen', 'execl', 'execve']
# execve does not invoke a shell; assess executable/argument control separately.

for func in fm.getFunctions(True):
    called = get_called_functions(func)
    if any(d in called for d in dangerous_exec):
        # Analyze arguments for user input
        print("Execution API candidate in {}".format(func.getName()))
```

### Map Memory Regions

```python
# @runtime Jython
mem = currentProgram.getMemory()
for block in mem.getBlocks():
    print("{}: {} - {} ({} bytes) [{}]".format(
        block.getName(),
        block.getStart(),
        block.getEnd(),
        block.getSize(),
        ("R" if block.isRead() else "-") +
        ("W" if block.isWrite() else "-") +
        ("X" if block.isExecute() else "-")
    ))
```
