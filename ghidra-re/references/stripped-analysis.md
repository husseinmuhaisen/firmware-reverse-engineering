# Stripped Binary Analysis in Ghidra

Expert techniques for reverse engineering binaries with no symbols.

## Initial Reconnaissance

### Import and Auto-Analysis

```python
# analyze_binary.py - Headless analysis script
# Usage: analyzeHeadless /project ProjectName -import binary.elf -postScript analyze_binary.py

from ghidra.program.model.symbol import SourceType
from ghidra.app.decompiler import DecompInterface

currentProgram = getCurrentProgram()
listing = currentProgram.getListing()
fm = currentProgram.getFunctionManager()

# Run auto-analysis with aggressive settings
from ghidra.app.script import GhidraScriptUtil
from ghidra.program.util import GhidraProgramUtilities

state.addAnalysisOption("Decompiler Parameter ID", "true")
state.addAnalysisOption("Stack", "true")
state.addAnalysisOption("Aggressive Instruction Finder", "true")

analyzeAll(currentProgram)
```

### Identify Entry Points

```python
# find_entry_points.py
# Locate function starts in stripped binaries

from ghidra.program.model.symbol import SymbolType, SourceType

mem = currentProgram.getMemory()
listing = currentProgram.getListing()

# 1. Known entry point
entry = currentProgram.getImageBase().add(
    currentProgram.getMinAddress().getOffset()
)
createFunction(entry, "entry")

# 2. Find prologues (ARM example)
# ARM: push {r11, lr} / push {r4-r7, lr}
# MIPS: addiu sp, sp, -XX / sw ra, XX(sp)
# x86: push ebp / mov ebp, esp

def find_arm_prologues():
    """Find ARM function prologues"""
    functions_found = []
    
    # Search for push {r11, lr} - 0xe92d4800
    # and variations
    patterns = [
        "e92d4800",  # push {r11, lr}
        "e92d48",    # push {r4-r7, lr}
        "e52de004",  # push {lr}
    ]
    
    for pattern in patterns:
        addr = mem.getMinAddress()
        while addr is not None:
            addr = mem.findBytes(addr, pattern, None, True, monitor)
            if addr and not listing.getFunctionAt(addr):
                # Verify it's executable
                if mem.getBlock(addr).isExecute():
                    createFunction(addr, None)
                    functions_found.append(addr)
            if addr:
                addr = addr.next()
    
    return functions_found

funcs = find_arm_prologues()
print("Found {} potential functions".format(len(funcs)))
```

## Function Identification

### Cross-Reference Analysis

```python
# xref_analysis.py - Identify functions via xrefs

def find_functions_by_xrefs():
    """Find likely function starts by analyzing call instructions"""
    
    # Get all references
    ref_mgr = currentProgram.getReferenceManager()
    addr_factory = currentProgram.getAddressFactory()
    
    candidates = set()
    
    # Scan for CALL/BL/JAL instructions
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
        if not listing.getFunctionAt(addr):
            func = createFunction(addr, None)
            if func:
                created += 1
    
    print("Created {} functions from xref analysis".format(created))
    return created

find_functions_by_xrefs()
```

### String Reference Tracing

```python
# string_xref_functions.py
# Find functions using string references

def find_string_using_functions():
    """Identify functions by their string usage"""
    
    # Get all defined strings
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
        # Authentication function heuristics
        auth_keywords = ["password", "login", "auth", "user"]
        if any(kw in s.lower() for s in strings for kw in auth_keywords):
            func.setName("auth_function_" + func.getEntryPoint().toString(), 
                        SourceType.USER_DEFINED)
        
        # Network functions
        net_keywords = ["http", "socket", "connect", "send"]
        if any(kw in s.lower() for s in strings for kw in net_keywords):
            func.setName("net_function_" + func.getEntryPoint().toString(),
                        SourceType.USER_DEFINED)

find_string_using_functions()
```

## Type Recovery

### Automatic Structure Analysis

```python
# recover_structures.py
# Analyze memory access patterns to recover structures

from ghidra.program.model.data import *

def analyze_structure_accesses(func):
    """Recover structure definitions from access patterns"""
    
    decompiler = DecompInterface()
    decompiler.openProgram(currentProgram)
    
    results = decompiler.decompileFunction(func, 30, monitor)
    if not results.decompileCompleted():
        return None
    
    high_func = results.getHighFunction()
    
    # Track offset accesses to same base pointer
    access_patterns = {}
    
    for op in high_func.getPcodeOps():
        if op.getOpcode() == PcodeOp.LOAD or op.getOpcode() == PcodeOp.STORE:
            # Analyze memory access
            pass  # Complex analysis here
    
    return access_patterns

# Iterate all functions
fm = currentProgram.getFunctionManager()
for func in fm.getFunctions(True):
    patterns = analyze_structure_accsets(func)
```

### Manual Structure Definition

```python
# define_struct.py - Create structures programmatically

dtm = currentProgram.getDataTypeManager()

# Create new structure
struct = StructureDataType("device_config", 0)

# Add fields
struct.add(DWordDataType(), 4, "magic", None)
struct.add(PointerDataType(new CharDataType()), 
          currentProgram.getDefaultPointerSize(), "name", None)
struct.add(WordDataType(), 2, "port", None)
struct.add(ArrayDataType(new ByteDataType(), 16, 1), "ip_addr", None)

# Add to program
dtm.addDataType(struct, DataTypeConflictHandler.DEFAULT_HANDLER)

# Apply to memory location
addr = toAddr("0x00012000")
createData(addr, struct)
```

## Advanced Analysis Techniques

### Constant Propagation

```python
# const_prop.py - Track constant values through execution

from ghidra.program.model.pcode import PcodeOp

def trace_constant(func, reg_name):
    """Trace constant value propagation"""
    
    decompiler = DecompInterface()
    decompiler.openProgram(currentProgram)
    results = decompiler.decompileFunction(func, 30, monitor)
    
    if not results.decompileCompleted():
        return None
    
    high_func = results.getHighFunction()
    
    # Build def-use chains
    for op in high_func.getPcodeOps():
        if op.getOpcode() == PcodeOp.COPY:
            output = op.getOutput()
            input = op.getInput(0)
            
            if input.isConstant():
                print("Constant {} assigned to {}".format(
                    input.getOffset(), output))
```

### Control Flow Flattening Detection

```python
# detect_obfuscation.py
# Identify control flow obfuscation

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
                prev_addr = prev_addr.previous()
                if not prev_addr:
                    break
                
                prev_instr = listing.getInstructionAt(prev_addr)
                if not prev_instr:
                    continue
                
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
# track_returns.py

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
        
        if mnemonic in ["bx", "pop", "jr", "ret"]:
            # Look at previous instruction for return value
            prev_addr = instr.getAddress().previous()
            prev_instr = listing.getInstructionAt(prev_addr)
            
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

```python
# auto_rename.py - Intelligent function renaming

def smart_rename_functions():
    """Apply heuristics to name functions meaningfully"""
    
    fm = currentProgram.getFunctionManager()
    
    for func in fm.getFunctions(True):
        name_hints = []
        
        # 1. String references
        strings = get_strings_in_function(func)
        if "init" in [s.lower() for s in strings]:
            name_hints.append("init")
        if any("error" in s.lower() for s in strings):
            name_hints.append("error_handler")
        
        # 2. Called functions
        called = get_called_functions(func)
        if "printf" in called:
            name_hints.append("print")
        if "malloc" in called or "free" in called:
            name_hints.append("mem")
        if "socket" in called or "connect" in called:
            name_hints.append("network")
        
        # 3. Complexity
        if func.getBody().getNumAddresses() < 10:
            name_hints.append("simple")
        
        # Build name
        if name_hints and not func.getName().startswith("FUN_"):
            continue  # Already renamed
        
        new_name = "_".join(name_hints) if name_hints else None
        if new_name:
            try:
                func.setName(new_name + "_" + 
                           func.getEntryPoint().toString()[-4:],
                           SourceType.ANALYSIS)
            except:
                pass

def get_strings_in_function(func):
    """Extract strings referenced by function"""
    strings = []
    instr_iter = listing.getInstructions(func.getBody(), True)
    
    for instr in instr_iter:
        for ref in instr.getReferencesFrom():
            to_addr = ref.getToAddress()
            data = listing.getDataAt(to_addr)
            if data and data.hasStringValue():
                strings.append(str(data.getValue()))
    
    return strings

def get_called_functions(func):
    """Get list of called function names"""
    called = []
    instr_iter = listing.getInstructions(func.getBody(), True)
    
    for instr in instr_iter:
        if instr.getFlowType().isCall():
            for ref in instr.getReferencesFrom():
                if ref.getReferenceType().isCall():
                    target_func = listing.getFunctionAt(ref.getToAddress())
                    if target_func:
                        called.append(target_func.getName())
    
    return called

smart_rename_functions()
```

## Decompiler Enhancement

### Custom Type Propagation

```python
# propagate_types.py

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
