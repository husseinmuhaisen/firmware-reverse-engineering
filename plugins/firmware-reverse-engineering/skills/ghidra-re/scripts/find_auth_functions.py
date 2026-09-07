# @runtime Jython
# @category Firmware
# find_auth_functions.py
"""
Identify authentication and authorization functions
Looks for password checks, strcmp calls, credential validation
"""

from ghidra.program.model.symbol import SourceType

from ghidra.util.task import TaskMonitor

# Nested/headless invocations can have no monitor; use the active one if supplied.
monitor = monitor or getControls().getMonitor() or TaskMonitor.DUMMY

from ghidra.program.model.pcode import PcodeOp

listing = currentProgram.getListing()

def find_auth_functions():
    """Find potential authentication functions"""
    
    fm = currentProgram.getFunctionManager()
    auth_candidates = []
    
    # Authentication keywords in strings
    auth_keywords = [
        "password", "passwd", "login", "auth", "credential",
        "username", "user", "admin", "root", "secret", "key"
    ]
    
    # Functions commonly used in auth
    auth_apis = [
        "strcmp", "strncmp", "memcmp", "strcasecmp",
        "crypt", "md5", "sha", "verify", "check"
    ]
    
    print("=== Authentication candidates (manual verification required) ===\n")
    
    for func in fm.getFunctions(True):
        monitor.checkCancelled()
        score = 0
        reasons = []
        
        # Check 1: String references
        strings = get_function_strings(func)
        auth_string_count = sum(
            1 for s in strings 
            if any(kw in s.lower() for kw in auth_keywords)
        )
        if auth_string_count > 0:
            score += auth_string_count * 2
            reasons.append("{} auth-related strings".format(auth_string_count))
        
        # Check 2: Calls to comparison functions
        called = get_called_functions(func)
        auth_api_count = sum(
            1 for c in called
            if any(api in c.lower() for api in auth_apis)
        )
        if auth_api_count > 0:
            score += auth_api_count * 3
            reasons.append("Calls {}".format(", ".join(
                c for c in called if any(api in c.lower() for api in auth_apis)
            )))
        
        # Check 3: Multiple return paths (success/fail pattern)
        if count_return_sites(func) >= 2:
            score += 1
            reasons.append("Multiple returns")
        
        # Check 4: Complexity (auth logic is often moderately complex)
        complexity = estimate_complexity(func)
        if 10 < complexity < 100:
            score += 1
            reasons.append("Moderate complexity")
        
        if score >= 3:
            auth_candidates.append({
                'function': func,
                'score': score,
                'reasons': reasons
            })
    
    # Sort by score
    auth_candidates.sort(key=lambda x: x['score'], reverse=True)
    
    # Report and rename
    print("Found {} potential authentication functions:\n".format(len(auth_candidates)))
    
    for i, candidate in enumerate(auth_candidates[:20]):  # Top 20
        func = candidate['function']
        score = candidate['score']
        reasons = candidate['reasons']
        
        print("{}. {} (score: {})".format(
            i+1, func.getEntryPoint(), score))
        print("   {}".format(", ".join(reasons)))
        
        # Rename only default symbols; the score is a ranking heuristic, not confidence
        if score >= 5 and func.getSymbol().getSource() == SourceType.DEFAULT:
            new_name = "auth_candidate_" + str(func.getEntryPoint()).replace(":", "_")
            func.setName(new_name, SourceType.ANALYSIS)
            print("   -> Renamed to {}".format(new_name))
        
        print()

def get_function_strings(func):
    """Extract all string references in function"""
    strings = []
    instr_iter = listing.getInstructions(func.getBody(), True)
    
    for instr in instr_iter:
        monitor.checkCancelled()
        for ref in instr.getReferencesFrom():
            data = listing.getDataAt(ref.getToAddress())
            if data and data.hasStringValue():
                strings.append(str(data.getValue()))
    
    return strings

def get_called_functions(func):
    """Get names of all called functions"""
    called = set()
    instr_iter = listing.getInstructions(func.getBody(), True)
    
    for instr in instr_iter:
        monitor.checkCancelled()
        if instr.getFlowType().isCall():
            for ref in instr.getReferencesFrom():
                if ref.getReferenceType().isCall():
                    target = listing.getFunctionAt(ref.getToAddress())
                    if target:
                        called.add(target.getName())
    
    return list(called)

def count_return_sites(func):
    """Count number of return instructions"""
    count = 0
    instr_iter = listing.getInstructions(func.getBody(), True)
    
    for instr in instr_iter:
        monitor.checkCancelled()
        if any(op.getOpcode() == PcodeOp.RETURN for op in instr.getPcode()):
            count += 1
    
    return count

def estimate_complexity(func):
    """Rough estimate of function complexity"""
    # Count instructions
    instr_count = 0
    branch_count = 0
    
    instr_iter = listing.getInstructions(func.getBody(), True)
    for instr in instr_iter:
        monitor.checkCancelled()
        instr_count += 1
        if instr.getFlowType().isConditional():
            branch_count += 1
    
    # Instruction/branch ranking heuristic; this is not cyclomatic complexity
    return instr_count + branch_count * 2

# Run analysis
find_auth_functions()
