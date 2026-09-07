# @runtime Jython
# @category Firmware
# find_buffer_overflows.py
"""
Identify potential buffer overflow vulnerabilities
Focuses on dangerous functions and unbounded operations
"""

from ghidra.program.model.listing import CodeUnit

from ghidra.util.task import TaskMonitor

# Nested/headless invocations can have no monitor; use the active one if supplied.
monitor = monitor or getControls().getMonitor() or TaskMonitor.DUMMY


listing = currentProgram.getListing()

DANGEROUS_FUNCTIONS = {
    'strcpy': 'Unbounded string copy',
    'strcat': 'Unbounded string concatenation',
    'sprintf': 'Unbounded format string',
    'gets': 'Unbounded input',
    'scanf': 'Potentially unbounded input',
    'vsprintf': 'Unbounded format string',
    'strncpy': 'Can leave non-null terminated',
    'strncat': 'Off-by-one risks',
}

INPUT_SOURCES = [
    'recv', 'read', 'fgets', 'getenv', 'scanf'
]

def find_dangerous_calls():
    """Find calls to dangerous functions"""
    
    fm = currentProgram.getFunctionManager()
    results = []
    
    print("=== Scanning for Dangerous Function Calls ===\n")
    
    for func in fm.getFunctions(True):
        monitor.checkCancelled()
        for location, call in get_call_sites(func):
            if call in DANGEROUS_FUNCTIONS:
                results.append({
                    'caller': func,
                    'dangerous_call': call,
                    'reason': DANGEROUS_FUNCTIONS[call],
                    'location': location
                })
    
    # Report findings
    if results:
        print("Found {} dangerous function calls:\n".format(len(results)))
        
        for i, vuln in enumerate(results, 1):
            print("{}. {} calls {}() - {}".format(
                i, 
                vuln['caller'].getName(),
                vuln['dangerous_call'],
                vuln['reason']
            ))
            print("   Location: {}".format(vuln['location']))
            
            # Add comment at call site
            if vuln['location']:
                append_eol_comment(vuln['location'],
                    "REVIEW: {}".format(vuln['reason']))
            
            print()
    else:
        print("No dangerous function calls found.")
    
    return results

def find_source_sink_candidates():
    """Report same-function source/sink co-occurrence; no data-flow proof."""
    
    fm = currentProgram.getFunctionManager()
    candidates = []
    
    print("\n=== Source/sink co-occurrence (not taint analysis) ===\n")
    
    for func in fm.getFunctions(True):
        monitor.checkCancelled()
        called = get_called_functions(func)
        
        # Check for source and sink names in the same function
        has_source = any(source in called for source in INPUT_SOURCES)
        has_sink = any(sink in called for sink in DANGEROUS_FUNCTIONS.keys())
        
        if has_source and has_sink:
            candidates.append({
                'function': func,
                'sources': [s for s in called if s in INPUT_SOURCES],
                'sinks': [s for s in called if s in DANGEROUS_FUNCTIONS.keys()]
            })
    
    if candidates:
        print("Found {} source/sink candidates:\n".format(len(candidates)))
        
        for flow in candidates:
            print("Function: {}".format(flow['function'].getName()))
            print("  Sources: {}".format(", ".join(flow['sources'])))
            print("  Sinks: {}".format(", ".join(flow['sinks'])))
            print("  REVIEW: Verify data flow, bounds, and attacker control before reporting")
            
            # Add function comment
            func = flow['function']
            note = "REVIEW: source/sink co-occurrence: {} / {}; data flow unverified".format(
                ", ".join(flow['sources']), ", ".join(flow['sinks']))
            previous = func.getComment() or ""
            if note not in previous.splitlines():
                func.setComment(previous + ("\n" if previous else "") + note)
            
            print()

def find_stack_buffers():
    """Identify large recovered stack objects near risky API calls"""
    
    fm = currentProgram.getFunctionManager()
    buffer_risks = []
    
    print("\n=== Analyzing Stack Buffer Usage ===\n")
    
    for func in fm.getFunctions(True):
        monitor.checkCancelled()
        # Get stack frame
        stack_frame = func.getStackFrame()
        if not stack_frame:
            continue
        
        # Look for large local variables (potential buffers)
        locals = stack_frame.getLocals()
        
        for var in locals:
            size = var.getLength()
            
            # Buffers typically 16+ bytes
            if size >= 16:
                # Check if function uses dangerous ops
                called = get_called_functions(func)
                if any(d in called for d in DANGEROUS_FUNCTIONS.keys()):
                    buffer_risks.append({
                        'function': func,
                        'buffer': var,
                        'size': size
                    })
    
    if buffer_risks:
        print("Found {} large stack objects in functions with risky API calls:\n".format(
            len(buffer_risks)))
        
        for risk in buffer_risks[:20]:  # Top 20
            print("Function: {} at {}".format(
                risk['function'].getName(),
                risk['function'].getEntryPoint()))
            print("  Stack object (type/bounds unverified): {} ({} bytes)".format(
                risk['buffer'].getName(),
                risk['size']))
            print()

def get_call_sites(func):
    """Enumerate resolved direct calls, including repeated calls to the same API."""
    for instr in listing.getInstructions(func.getBody(), True):
        monitor.checkCancelled()
        seen = set()
        for ref in instr.getReferencesFrom():
            if ref.getReferenceType().isCall():
                target = getFunctionAt(ref.getToAddress())
                if target:
                    if target.isThunk():
                        target = target.getThunkedFunction(True) or target
                    name = target.getName()
                    if name not in seen:
                        seen.add(name)
                        yield instr.getAddress(), name


def get_called_functions(func):
    return sorted(set(name for _, name in get_call_sites(func)))


def append_eol_comment(addr, note):
    previous = listing.getComment(CodeUnit.EOL_COMMENT, addr) or ""
    if note not in previous.splitlines():
        setEOLComment(addr, previous + ("\n" if previous else "") + note)

# Run all analyses
dangerous = find_dangerous_calls()
find_source_sink_candidates()
find_stack_buffers()

print("\n=== Summary ===")
print("Review all findings above for potential vulnerabilities.")
print("Candidates only: unresolved indirect calls and inlined operations may be missed.")
print("Verify attacker control, destination size, lengths and reachability manually.")
