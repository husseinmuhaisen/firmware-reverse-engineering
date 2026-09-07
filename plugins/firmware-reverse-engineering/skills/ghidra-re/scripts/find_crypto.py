# @runtime Jython
# @category Firmware
# find_crypto.py
"""
Identify cryptographic functions in firmware
Searches for crypto constants, S-boxes, key schedules
"""

from ghidra.program.model.symbol import SourceType

from ghidra.util.task import TaskMonitor

# Nested/headless invocations can have no monitor; use the active one if supplied.
monitor = monitor or getControls().getMonitor() or TaskMonitor.DUMMY

from jarray import array
import struct

# AES S-box (first 16 bytes)
AES_SBOX = [
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5,
    0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76
]

# MD5/SHA constants
MD5_CONSTANTS = [0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee]
SHA256_K = [0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5]

def find_byte_array(byte_array, name):
    """Search initialized blocks only, with a bounded Java byte[] search."""
    mem = currentProgram.getMemory()
    results = []
    search_bytes = array([b if b < 128 else b - 256 for b in byte_array], 'b')
    for block in mem.getBlocks():
        monitor.checkCancelled()
        if not block.isInitialized() or block.getSize() < len(byte_array):
            continue
        cursor = block.getStart()
        last_start = block.getEnd().subtract(len(byte_array) - 1)
        while cursor is not None and cursor.compareTo(last_start) <= 0:
            monitor.checkCancelled()
            addr = mem.findBytes(cursor, block.getEnd(), search_bytes, None, True, monitor)
            if addr is None or addr.compareTo(last_start) > 0:
                break
            results.append(addr)
            print("Found {} candidate at {}".format(name, addr))
            label = name + "_candidate_" + str(addr).replace(":", "_")
            if not any(symbol.getName() == label for symbol in currentProgram.getSymbolTable().getSymbols(addr)):
                createLabel(addr, label, False, SourceType.ANALYSIS)
            # Keep existing data definitions, instructions, primary symbols and comments.
            cursor = addr.next() if addr.compareTo(last_start) < 0 else None
    return results


def find_dword_array(dword_array, name):
    """Check both byte orders; tables can differ from the program's byte order."""
    results = []
    for endian, suffix in [('<', 'LE'), ('>', 'BE')]:
        packed = struct.pack(endian + 'I' * len(dword_array), *dword_array)
        values = [ord(b) if not isinstance(b, int) else b for b in packed]
        results.extend(find_byte_array(values, name + '_' + suffix))
    return results

# Search for crypto constants
print("=== Searching for crypto constant prefixes (candidates only) ===")
aes_sbox_addrs = find_byte_array(AES_SBOX, "AES_Sbox")
md5_addrs = find_dword_array(MD5_CONSTANTS, "MD5_Constants")
sha256_addrs = find_dword_array(SHA256_K, "SHA256_K")

print("\nResults:")
print("  AES S-boxes: {}".format(len(aes_sbox_addrs)))
print("  MD5 constants: {}".format(len(md5_addrs)))
print("  SHA256 constants: {}".format(len(sha256_addrs)))

# Find functions that reference these
if aes_sbox_addrs or md5_addrs or sha256_addrs:
    print("\n=== Functions referencing candidate tables ===")
    
    for addr in aes_sbox_addrs + md5_addrs + sha256_addrs:
        refs = currentProgram.getReferenceManager().getReferencesTo(addr)
        for ref in refs:
            func = getFunctionContaining(ref.getFromAddress())
            if func:
                print("Candidate reference: {} at {}".format(
                    func.getName(), func.getEntryPoint()))
                
                # Rename if not already named
                if func.getSymbol().getSource() == SourceType.DEFAULT:
                    func.setName("crypto_candidate_" + str(func.getEntryPoint()).replace(":", "_"),
                               SourceType.ANALYSIS)

print("A constant prefix does not prove algorithm use, security, or key material.")
