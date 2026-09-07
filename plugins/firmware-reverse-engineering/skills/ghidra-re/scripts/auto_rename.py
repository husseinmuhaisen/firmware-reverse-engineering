# @runtime Jython
# @category Firmware
# auto_rename.py - Candidate naming from strings and direct calls

from ghidra.program.model.symbol import SourceType

from ghidra.util.task import TaskMonitor

# Nested/headless invocations can have no monitor; use the active one if supplied.
monitor = monitor or getControls().getMonitor() or TaskMonitor.DUMMY


listing = currentProgram.getListing()

def smart_rename_functions():
    """Apply heuristics to name functions meaningfully"""
    
    fm = currentProgram.getFunctionManager()
    
    for func in fm.getFunctions(True):
        monitor.checkCancelled()
        if func.getSymbol().getSource() != SourceType.DEFAULT:
            continue
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
            func.setName(new_name + "_candidate_" +
                         str(func.getEntryPoint()).replace(":", "_"),
                         SourceType.ANALYSIS)

def get_strings_in_function(func):
    """Extract strings referenced by function"""
    strings = []
    instr_iter = listing.getInstructions(func.getBody(), True)
    
    for instr in instr_iter:
        monitor.checkCancelled()
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
        monitor.checkCancelled()
        if instr.getFlowType().isCall():
            for ref in instr.getReferencesFrom():
                if ref.getReferenceType().isCall():
                    target_func = listing.getFunctionAt(ref.getToAddress())
                    if target_func:
                        called.append(target_func.getName())
    
    return called

smart_rename_functions()
