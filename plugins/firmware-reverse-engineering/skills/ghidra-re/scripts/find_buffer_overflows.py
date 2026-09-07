# find_buffer_overflows.py
"""
Identify potential buffer overflow vulnerabilities
Focuses on dangerous functions and unbounded operations
"""

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

TAINTED_SOURCES = [
    'recv', 'read', 'fgets', 'getenv', 'scanf'
]

def find_dangerous_calls():
    """Find calls to dangerous functions"""
    
    fm = currentProgram.getFunctionManager()
    results = []
    
    print("=== Scanning for Dangerous Function Calls ===\n")
    
    for func in fm.getFunctions(True):
        called = get_called_functions(func)
        
        for call in called:
            if call in DANGEROUS_FUNCTIONS:
                results.append({
                    'caller': func,
                    'dangerous_call': call,
                    'reason': DANGEROUS_FUNCTIONS[call],
                    'location': find_call_site(func, call)
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
                setEOLComment(vuln['location'],
                    "DANGEROUS: {}".format(vuln['reason']))
            
            print()
    else:
        print("No dangerous function calls found.")
    
    return results

def analyze_taint_flow():
    """Trace data flow from untrusted sources to sinks"""
    
    fm = currentProgram.getFunctionManager()
    taint_flows = []
    
    print("\n=== Analyzing Taint Flow ===\n")
    
    for func in fm.getFunctions(True):
        called = get_called_functions(func)
        
        # Check if function receives tainted input
        has_source = any(source in called for source in TAINTED_SOURCES)
        has_sink = any(sink in called for sink in DANGEROUS_FUNCTIONS.keys())
        
        if has_source and has_sink:
            taint_flows.append({
                'function': func,
                'sources': [s for s in called if s in TAINTED_SOURCES],
                'sinks': [s for s in called if s in DANGEROUS_FUNCTIONS.keys()]
            })
    
    if taint_flows:
        print("Found {} potential taint flows:\n".format(len(taint_flows)))
        
        for flow in taint_flows:
            print("Function: {}".format(flow['function'].getName()))
            print("  Sources: {}".format(", ".join(flow['sources'])))
            print("  Sinks: {}".format(", ".join(flow['sinks'])))
            print("  RISK: Untrusted data may reach dangerous function")
            
            # Add function comment
            func = flow['function']
            func.setComment("SECURITY: Taint flow from {} to {}".format(
                flow['sources'][0], flow['sinks'][0]
            ))
            
            print()

def find_stack_buffers():
    """Identify local stack buffers that could overflow"""
    
    fm = currentProgram.getFunctionManager()
    buffer_risks = []
    
    print("\n=== Analyzing Stack Buffer Usage ===\n")
    
    for func in fm.getFunctions(True):
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
        print("Found {} functions with stack buffers and dangerous calls:\n".format(
            len(buffer_risks)))
        
        for risk in buffer_risks[:20]:  # Top 20
            print("Function: {} at {}".format(
                risk['function'].getName(),
                risk['function'].getEntryPoint()))
            print("  Buffer: {} ({} bytes)".format(
                risk['buffer'].getName(),
                risk['size']))
            print()

def get_called_functions(func):
    """Get list of called function names"""
    called = set()
    instr_iter = listing.getInstructions(func.getBody(), True)
    
    for instr in instr_iter:
        if instr.getFlowType().isCall():
            for ref in instr.getReferencesFrom():
                if ref.getReferenceType().isCall():
                    target = listing.getFunctionAt(ref.getToAddress())
                    if target:
                        called.add(target.getName())
    
    return list(called)

def find_call_site(caller, callee_name):
    """Find address where function calls another function"""
    instr_iter = listing.getInstructions(caller.getBody(), True)
    
    for instr in instr_iter:
        if instr.getFlowType().isCall():
            for ref in instr.getReferencesFrom():
                if ref.getReferenceType().isCall():
                    target = listing.getFunctionAt(ref.getToAddress())
                    if target and target.getName() == callee_name:
                        return instr.getAddress()
    
    return None

# Run all analyses
dangerous = find_dangerous_calls()
analyze_taint_flow()
find_stack_buffers()

print("\n=== Summary ===")
print("Review all findings above for potential vulnerabilities.")
print("Manually verify each case - static analysis can have false positives.")
