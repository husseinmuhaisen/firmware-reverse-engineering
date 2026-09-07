# Stripped Binary Analysis in Ghidra

Expert techniques for reverse engineering binaries with no symbols.

## Initial Reconnaissance

### Import and Auto-Analysis

```python
# @runtime Jython
# analyze_binary.py - Headless analysis script
# Usage: "$GHIDRA_INSTALL_DIR/support/analyzeHeadless" /project ProjectName -scriptPath "$GHIDRA_SCRIPT_DIR" -import binary.elf -postScript analyze_binary.py

from ghidra.program.model.symbol import SourceType
from ghidra.app.decompiler import DecompInterface

currentProgram = getCurrentProgram()
listing = currentProgram.getListing()
fm = currentProgram.getFunctionManager()

# Run auto-analysis with aggressive settings
from ghidra.app.script import GhidraScriptUtil
from ghidra.program.util import GhidraProgramUtilities

setAnalysisOption(currentProgram, "Decompiler Parameter ID", "true")
setAnalysisOption(currentProgram, "Stack", "true")
setAnalysisOption(currentProgram, "Aggressive Instruction Finder", "true")

analyzeAll(currentProgram)
```

### Identify Entry Points

```python
# @runtime Jython
# find_entry_points.py
# Locate function starts in stripped binaries

from ghidra.program.model.symbol import SymbolType, SourceType

mem = currentProgram.getMemory()
listing = currentProgram.getListing()

# 1. Loader-provided entry points are not the image base.
for entry in currentProgram.getSymbolTable().getExternalEntryPointIterator():
    print("Loader entry: {}".format(entry))
    # Review executable memory, instruction mode and existing function boundaries
    # before disassembling/creating functions. Raw imports need a researched entry.

# 2. A32 prologue candidates (does not create functions automatically).
# Only use for 32-bit ARM A32 code, not Thumb or AArch64.
from jarray import array

def find_arm_prologues():
    if str(currentProgram.getLanguage().getProcessor()) != "ARM":
        raise ValueError("This example requires ARM32 A32 code")
    # push {r11, lr}, instruction word 0xe92d4800; encode by memory byte order.
    values = [0xe9, 0x2d, 0x48, 0x00] if currentProgram.getLanguage().isBigEndian() else [0x00, 0x48, 0x2d, 0xe9]
    pattern = array([b if b < 128 else b - 256 for b in values], 'b')
    candidates = []
    for block in mem.getBlocks():
        if not block.isInitialized() or not block.isExecute() or block.getSize() < 4:
            continue
        addr = block.getStart()
        last = block.getEnd().subtract(3)
        while addr and addr.compareTo(last) <= 0:
            monitor.checkCancelled()
            addr = mem.findBytes(addr, block.getEnd(), pattern, None, True, monitor)
            if addr is None or addr.compareTo(last) > 0:
                break
            if addr.getOffset() % 4 == 0:
                candidates.append(addr)
            addr = addr.next() if addr.compareTo(last) < 0 else None
    return candidates

# Review candidates in the listing: matching data and embedded constants are possible.
print(find_arm_prologues())

```

## Function Identification

### Cross-Reference Analysis

```python
# @runtime Jython
# xref_analysis.py - Identify functions via xrefs

def find_functions_by_xrefs():
    """Find likely function starts by analyzing call instructions"""
    
    # Get all references
    ref_mgr = currentProgram.getReferenceManager()
    addr_factory = currentProgram.getAddressFactory()
    
    candidates = set()
    
    # Scan for CALL/BL/JAL instructions
    listing = currentProgram.getListing()
    mem = currentProgram.getMemory()
    instr = listing.getInstructions(True)
    
    for ins in instr:
        mnemonic = ins.getMnemonicString()
        
        # Architecture-specific call instructions
        if mnemonic in ["bl", "blx", "call", "jal", "jalr"]:
            # Get flow references
            for ref in ins.getReferencesFrom():
                if ref.getReferenceType().isCall():
                    target = ref.getToAddress()
                    
                    # Check if target is in executable memory
                    block = mem.getBlock(target)
                    if block and block.isExecute():
                        candidates.add(target)
    
    # Create functions at candidates
    created = 0
    for addr in candidates:
        if not listing.getFunctionContaining(addr) and listing.getInstructionAt(addr):
            func = createFunction(addr, None)
            if func:
                created += 1
    
    print("Created {} functions from xref analysis".format(created))
    return created

find_functions_by_xrefs()
```

### String Reference Tracing

```python
# @runtime Jython
# string_xref_functions.py
# Find functions using string references

def find_string_using_functions():
    """Identify functions by their string usage"""
    
    # Get all defined strings
    listing = currentProgram.getListing()
    data_iter = listing.getDefinedData(True)
    string_refs = {}
    
    for data in data_iter:
        if data.hasStringValue():
            string_val = data.getValue()
            refs = getReferencesTo(data.getAddress())
            
            for ref in refs:
                from_addr = ref.getFromAddress()
                func = listing.getFunctionContaining(from_addr)
                
                if func:
                    if func not in string_refs:
                        string_refs[func] = []
                    string_refs[func].append(str(string_val))
    
    # Analyze and rename based on strings
    for func, strings in string_refs.items():
        if func.getSymbol().getSource() != SourceType.DEFAULT:
            continue
        # Authentication function heuristics
        auth_keywords = ["password", "login", "auth", "user"]
        if any(kw in s.lower() for s in strings for kw in auth_keywords):
            func.setName("auth_candidate_" + func.getEntryPoint().toString(),
                        SourceType.ANALYSIS)
        
        # Network functions
        net_keywords = ["http", "socket", "connect", "send"]
        if func.getSymbol().getSource() == SourceType.DEFAULT and any(
                kw in s.lower() for s in strings for kw in net_keywords):
            func.setName("net_candidate_" + func.getEntryPoint().toString(),
                        SourceType.ANALYSIS)

find_string_using_functions()
```

## Type Recovery

### Structure Analysis Sketch (Incomplete)

```python
# @runtime Jython
# recover_structures.py
# Skeleton only: the LOAD/STORE interpretation is deliberately left to the analyst.
# This does not recover structures.
from ghidra.app.decompiler import DecompInterface
from ghidra.program.model.pcode import PcodeOp

from ghidra.program.model.data import *

def analyze_structure_accesses(func):
    """Recover structure definitions from access patterns"""
    
    decompiler = DecompInterface()
    decompiler.openProgram(currentProgram)
    
    results = decompiler.decompileFunction(func, 30, monitor)
    if not results.decompileCompleted():
        decompiler.dispose()
        return None
    
    high_func = results.getHighFunction()
    
    # Track offset accesses to same base pointer
    access_patterns = {}
    
    for op in high_func.getPcodeOps():
        if op.getOpcode() == PcodeOp.LOAD or op.getOpcode() == PcodeOp.STORE:
            # Analyze memory access
            pass  # Complex analysis here
    
    decompiler.dispose()
    return access_patterns

# Iterate all functions
fm = currentProgram.getFunctionManager()
for func in fm.getFunctions(True):
    patterns = analyze_structure_accesses(func)
```

### Manual Structure Definition

```python
# @runtime Jython
# define_struct.py - Create structures programmatically
from ghidra.program.model.data import *

dtm = currentProgram.getDataTypeManager()

# Create new structure
struct = StructureDataType("device_config", 0)

# Add fields
struct.add(DWordDataType(), 4, "magic", None)
struct.add(PointerDataType(CharDataType()),
          currentProgram.getDefaultPointerSize(), "name", None)
struct.add(WordDataType(), 2, "port", None)
struct.add(ArrayDataType(ByteDataType(), 16, 1), "ip_addr", None)

# Add to program
dtm.addDataType(struct, DataTypeConflictHandler.DEFAULT_HANDLER)

# Apply to memory location
addr = toAddr("0x00012000")
createData(addr, struct)
```

## Advanced Analysis Techniques

### Constant Propagation

```python
# @runtime Jython
# const_prop.py - Track constant values through execution

from ghidra.program.model.pcode import PcodeOp

def list_constant_copies(func):
    """List decompiler COPY constants; not a register def-use analysis."""
    
    decompiler = DecompInterface()
    decompiler.openProgram(currentProgram)
    results = decompiler.decompileFunction(func, 30, monitor)
    
    if not results.decompileCompleted():
        decompiler.dispose()
        return None
    
    high_func = results.getHighFunction()
    
    # List constant COPY operations (does not build def-use chains)
    for op in high_func.getPcodeOps():
        if op.getOpcode() == PcodeOp.COPY:
            output = op.getOutput()
            input = op.getInput(0)
            
            if input.isConstant():
                print("Constant {} assigned to {}".format(
                    input.getOffset(), output))
    decompiler.dispose()
```

### Control Flow Flattening Detection

```python
# @runtime Jython
# detect_obfuscation.py
# Identify high-fan-out blocks for manual review; ordinary switches also match.
from ghidra.program.model.block import BasicBlockModel

def detect_flattening(func):
    """Detect control flow flattening patterns"""
    
    # Check for dispatcher pattern:
    # 1. Switch/dispatch block with many cases
    # 2. State variable updated in each block
    # 3. Return to dispatcher
    
    bb_model = BasicBlockModel(currentProgram)
    blocks = bb_model.getCodeBlocksContaining(
        func.getBody(), monitor)
    
    dispatcher_candidates = []
    
    while blocks.hasNext():
        block = blocks.next()
        
        # Count outgoing edges
        dests = block.getDestinations(monitor)
        dest_count = 0
        while dests.hasNext():
            dests.next()
            dest_count += 1
        
        # Dispatcher has many outgoing edges
        if dest_count > 5:
            dispatcher_candidates.append(block)
            print("Potential dispatcher at {}".format(
                block.getFirstStartAddress()))
    
    return dispatcher_candidates
```

## Function Signature Recovery

### Calling Convention Analysis

```python
# @runtime Jython
# analyze_calling_convention.py

def analyze_call_sites(func):
    """Determine calling convention from call sites"""
    
    # Track register usage before calls
    calls = []
    
    instr_iter = listing.getInstructions(func.getBody(), True)
    
    for instr in instr_iter:
        if instr.getFlowType().isCall():
            # Look at previous instructions for argument setup
            prev_addr = instr.getAddress()
            args_detected = []
            
            for i in range(5):  # Look back 5 instructions
                prev_instr = listing.getInstructionBefore(prev_addr)
                if prev_instr is None or not func.getBody().contains(prev_instr.getAddress()):
                    break
                prev_addr = prev_instr.getAddress()
                # Register mentions are hints, not proof of argument assignments.
                # ARM: arguments in r0-r3
                # MIPS: arguments in $a0-$a3
                # x86: arguments on stack or registers
                
                # Example for ARM
                for reg in ["r0", "r1", "r2", "r3"]:
                    if reg in str(prev_instr):
                        args_detected.append(reg)
            
            calls.append({
                'address': instr.getAddress(),
                'args': args_detected
            })
    
    return calls
```

### Return Value Tracking

```python
# @runtime Jython
# track_returns.py
from ghidra.program.model.pcode import PcodeOp

def analyze_return_value(func):
    """Identify what function returns"""
    
    # Check all return sites
    returns = []
    
    instr_iter = listing.getInstructions(func.getBody(), True)
    
    for instr in instr_iter:
        mnemonic = instr.getMnemonicString()
        
        # ARM: bx lr, pop {pc}
        # MIPS: jr $ra
        # x86: ret
        
        if any(op.getOpcode() == PcodeOp.RETURN for op in instr.getPcode()):
            # Look at previous instruction for return value
            prev_instr = listing.getInstructionBefore(instr.getAddress())
            
            if prev_instr:
                # ARM: return in r0
                # MIPS: return in $v0
                # x86: return in eax/rax
                
                returns.append({
                    'address': instr.getAddress(),
                    'prev_instr': str(prev_instr)
                })
    
    return returns
```

## Renaming Strategy

### Automated Function Naming

Run the bundled `scripts/auto_rename.py` with the headless setup in SKILL.md.
It uses the string/API heuristics described here, marks names as candidates, and
only renames default symbols. Existing analyst/imported names remain intact.

## Decompiler Enhancement

### Custom Type Propagation Sketch (Incomplete)

```python
# @runtime Jython
# propagate_types.py - requires an analyst implementation of analyze_pointer_usage
from ghidra.program.model.data import Pointer, PointerDataType
from ghidra.program.model.symbol import SourceType

def propagate_pointer_types():
    """Improve decompilation by propagating type information"""
    
    dtm = currentProgram.getDataTypeManager()
    fm = currentProgram.getFunctionManager()
    
    for func in fm.getFunctions(True):
        # Get function signature
        params = func.getParameters()
        
        for param in params:
            # If parameter is pointer, try to determine pointed-to type
            data_type = param.getDataType()
            
            if isinstance(data_type, Pointer):
                # Analyze how pointer is used
                pointed_type = analyze_pointer_usage(func, param)
                if pointed_type:
                    new_type = PointerDataType(pointed_type)
                    param.setDataType(new_type, SourceType.ANALYSIS)

def analyze_pointer_usage(func, param):
    """Determine pointer target type from usage"""
    # Analyze decompiled code for member accesses
    # Return inferred structure type
    pass
```

## Quick Reference

### Essential Ghidra Python APIs

```python
# @runtime Jython
# Navigation
currentProgram                    # Current binary
listing = currentProgram.getListing()
mem = currentProgram.getMemory()
fm = currentProgram.getFunctionManager()

# Address operations
addr = toAddr("0x00400000")
addr = currentAddress              # Current cursor position
addr.add(offset)
addr.subtract(offset)

# Functions
func = getFunctionAt(addr)
func = getFunctionContaining(addr)
createFunction(addr, name)
func.getName()
func.setName(name, SourceType.USER_DEFINED)
func.getBody()                    # AddressSetView
func.getParameters()
func.getReturn()

# Instructions
instr = listing.getInstructionAt(addr)
instr.getMnemonicString()
instr.getFlowType()
instr.getReferencesFrom()

# Data
data = listing.getDataAt(addr)
createData(addr, dataType)
data.getValue()
data.hasStringValue()

# References
refs = getReferencesTo(addr)
refs = getReferencesFrom(addr)

# Decompiler
decompiler = DecompInterface()
decompiler.openProgram(currentProgram)
results = decompiler.decompileFunction(func, 30, monitor)
high_func = results.getHighFunction()

# Data types
dtm = currentProgram.getDataTypeManager()
struct = StructureDataType(name, size)
dtm.addDataType(struct, handler)
```
