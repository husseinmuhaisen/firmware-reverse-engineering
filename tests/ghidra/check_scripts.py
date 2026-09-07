# @runtime Jython
# @category Firmware
# Run by analyzeHeadless; this tests Ghidra APIs, not mocked Python objects.
from ghidra.program.model.symbol import SourceType
from ghidra.program.model.listing import CodeUnit

fm = currentProgram.getFunctionManager()
listing = currentProgram.getListing()
funcs = {f.getName(): f for f in fm.getFunctions(True)}
caller = funcs['call_candidates']
caller.setComment('Analyst note: bounds checked in fixture')
for instr in listing.getInstructions(caller.getBody(), True):
    if instr.getFlowType().isCall():
        setEOLComment(instr.getAddress(), 'Existing call annotation')
# Force one original function to the default name, as in a stripped import.
renamed = funcs['rename_candidate']
renamed.setName(None, SourceType.DEFAULT)
# A huge uninitialized block ensures scans cannot walk all virtual addresses.
currentProgram.getMemory().createUninitializedBlock('test_sparse', toAddr('100000000'), 0x10000000, False)

for script in ['find_crypto.py', 'find_auth_functions.py', 'find_buffer_overflows.py', 'auto_rename.py']:
    runScript(script)

assert funcs['auth_check'].getName() == 'auth_check', 'User/import names changed'
assert 'candidate_' in renamed.getName(), 'Default function was not named'
assert caller.getComment().startswith('Analyst note:'), 'Analyst comment overwritten'
assert 'data flow unverified' in caller.getComment(), 'Source/sink candidate absent'
call_notes = []
for instr in listing.getInstructions(caller.getBody(), True):
    note = listing.getComment(CodeUnit.EOL_COMMENT, instr.getAddress()) or ''
    if 'REVIEW: Unbounded string copy' in note:
        assert note.startswith('Existing call annotation'), 'EOL comment overwritten'
        call_notes.append(note)
assert len(call_notes) == 2, 'Not all strcpy call sites reported'
symbols = currentProgram.getSymbolTable()
for prefix in ['AES_Sbox_candidate_', 'MD5_Constants_LE_candidate_', 'SHA256_K_BE_candidate_']:
    assert any(s.getName().startswith(prefix) for s in symbols.getAllSymbols(True)), prefix
before = [(str(s.getAddress()), s.getName()) for s in symbols.getAllSymbols(True)]
comment_before = caller.getComment()
for script in ['find_crypto.py', 'find_auth_functions.py', 'find_buffer_overflows.py', 'auto_rename.py']:
    runScript(script)
after = [(str(s.getAddress()), s.getName()) for s in symbols.getAllSymbols(True)]
assert before == after, 'Repeat run changed symbols'
assert caller.getComment() == comment_before, 'Repeat run duplicated comments'
print('GHIDRA_REGRESSION_OK: crypto byte orders, sparse memory, repeated calls, naming, preservation, repeatability')
