# Expert Ghidra Workflow

Streamlined workflow for analyzing firmware binaries in Ghidra.

## Project Setup

```bash
# Headless analysis (automation-friendly)
analyzeHeadless /projects MyProject -import binary.elf -scriptPath /scripts

# With post-analysis script
analyzeHeadless /projects MyProject -import binary.elf \
  -postScript find_crypto.py -postScript find_auth_functions.py

# Batch import
for bin in extracted/bin/*; do
    analyzeHeadless /projects FirmwareAnalysis -import "$bin"
done
```

## Initial Analysis Checklist

1. **Run Auto-Analysis** (Analysis → Auto Analyze)
   - Enable all default analyzers
   - Add: "Aggressive Instruction Finder", "Non-Returning Functions"

2. **Identify Entry Point**
   ```python
   # If stripped, find _start or main manually
   entry = currentProgram.getImageBase()
   createFunction(entry, "entry")
   ```

3. **Find Functions** (scripts/find_functions.py)
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
# Set function signature manually
func = getFunctionAt(currentAddress)
sig = "int auth_check(char *username, char *password)"
ApplyFunctionSignatureCmd(func.getEntryPoint(), sig, SourceType.USER_DEFINED).applyTo(currentProgram)

# Or via GUI: Ctrl-Shift-E
```

### Understanding Output

- **undefined4** → Unknown 4-byte type (likely int)
- **UNIMPLEMENTED** → Instruction not supported by decompiler
- **DAT_XXXXX** → Unnamed data at address XXXXX
- **(cast)** → Decompiler inserted type cast

## Scripting Patterns

### Iterate All Functions

```python
fm = currentProgram.getFunctionManager()
for func in fm.getFunctions(True):
    # Process each function
    pass
```

### Modify Function Signature

```python
func = getFunctionAt(currentAddress)
params = [
    ParameterImpl("buffer", PointerDataType(CharDataType()), currentProgram),
    ParameterImpl("size", DWordDataType(), currentProgram)
]
func.replaceParameters(params, Function.FunctionUpdateType.DYNAMIC_STORAGE_ALL_PARAMS, True, SourceType.USER_DEFINED)
```

### Create Custom Data Type

```python
dtm = currentProgram.getDataTypeManager()
struct = StructureDataType("request_packet", 0)
struct.add(DWordDataType(), "magic", None)
struct.add(WordDataType(), "command", None)
struct.add(PointerDataType(CharDataType()), "data", None)
dtm.addDataType(struct, DataTypeConflictHandler.REPLACE_HANDLER)
```

### Batch Rename

```python
# Rename all FUN_* functions with pattern
fm = currentProgram.getFunctionManager()
for func in fm.getFunctions(True):
    if func.getName().startswith("FUN_"):
        addr_hex = str(func.getEntryPoint())[-4:]
        func.setName("sub_" + addr_hex, SourceType.ANALYSIS)
```

## Advanced Techniques

### P-Code Analysis

```python
# Analyze at IL level
from ghidra.app.decompiler import DecompInterface

decompiler = DecompInterface()
decompiler.openProgram(currentProgram)
results = decompiler.decompileFunction(func, 30, monitor)

high_func = results.getHighFunction()
for op in high_func.getPcodeOps():
    print("{}: {}".format(op.getOpcode(), op))
```

### Custom Analysis Pass

```python
# Create custom analyzer
from ghidra.app.services import AbstractAnalyzer, AnalyzerType

class MyAnalyzer(AbstractAnalyzer):
    def __init__(self):
        super().__init__("Custom Analyzer", "Description", AnalyzerType.FUNCTION_ANALYZER)
    
    def canAnalyze(self, program):
        return True
    
    def analyze(self, program, addrSet, monitor, log):
        # Your analysis logic
        return True
```

### Export Analysis

```python
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
# Then import in IDA
```

### Binary Diff

```
Tools → Version Tracking
# Compare two versions of firmware
```

### Collaborate

```
File → Add to Version Control (if using Git)
File → Merge Tool (resolve conflicts)
```

## Performance Optimization

```bash
# Increase heap for large binaries
ghidraRun -Xmx8G

# Disable auto-analysis for very large files
# Import, then selectively analyze regions
```

## Debugging Ghidra Scripts

```python
# Print to console
print("Debug: value={}".format(value))

# Use monitor for progress
monitor.setMessage("Processing function...")
monitor.setProgress(i, total)

# Check for cancellation
if monitor.isCancelled():
    return

# Exception handling
try:
    # risky operation
except Exception as e:
    print("Error: {}".format(e))
    import traceback
    traceback.print_exc()
```

## Common Patterns

### Find Format String Bugs

```python
# Find printf-family calls with user-controlled format
for func in fm.getFunctions(True):
    for call in get_call_sites(func):
        if call['target'] in ['printf', 'sprintf', 'fprintf']:
            # Check if format arg is from untrusted source
            pass
```

### Identify Command Injection

```python
# Find system/exec calls
dangerous_exec = ['system', 'popen', 'exec', 'execve']

for func in fm.getFunctions(True):
    called = get_called_functions(func)
    if any(d in called for d in dangerous_exec):
        # Analyze arguments for user input
        print("Potential command injection in {}".format(func.getName()))
```

### Map Memory Regions

```python
mem = currentProgram.getMemory()
for block in mem.getBlocks():
    print("{}: {} - {} ({} bytes) [{}]".format(
        block.getName(),
        block.getStart(),
        block.getEnd(),
        block.getSize(),
        "RWX" if block.isExecute() else "R" if block.isRead() else ""
    ))
```
