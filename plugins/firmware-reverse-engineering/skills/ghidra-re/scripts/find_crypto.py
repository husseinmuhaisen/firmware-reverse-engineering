# find_crypto.py
"""
Identify cryptographic functions in firmware
Searches for crypto constants, S-boxes, key schedules
"""

from ghidra.program.model.data import *

# AES S-box (first 16 bytes)
AES_SBOX = [
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5,
    0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76
]

# MD5/SHA constants
MD5_CONSTANTS = [0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee]
SHA256_K = [0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5]

def find_byte_array(byte_array, name):
    """Search for byte array in memory"""
    mem = currentProgram.getMemory()
    results = []
    
    # Convert to byte string for searching
    search_bytes = "".join([chr(b & 0xFF) for b in byte_array])
    
    addr = mem.getMinAddress()
    while addr:
        addr = mem.findBytes(addr, search_bytes, None, True, monitor)
        if addr:
            results.append(addr)
            print("Found {} at {}".format(name, addr))
            
            # Label it
            createLabel(addr, name + "_table", True)
            
            # Create data
            createData(addr, ArrayDataType(ByteDataType(), len(byte_array), 1))
            
            addr = addr.next()
    
    return results

def find_dword_array(dword_array, name):
    """Search for DWORD array"""
    mem = currentProgram.getMemory()
    results = []
    
    # Search for first constant, then verify others follow
    first_const = dword_array[0]
    
    addr = mem.getMinAddress()
    while addr:
        # Read 4 bytes as little-endian DWORD
        try:
            val = mem.getInt(addr) & 0xFFFFFFFF
            if val == first_const:
                # Verify rest of array
                match = True
                for i, const in enumerate(dword_array[1:4]):  # Check first few
                    test_addr = addr.add((i+1) * 4)
                    test_val = mem.getInt(test_addr) & 0xFFFFFFFF
                    if test_val != const:
                        match = False
                        break
                
                if match:
                    results.append(addr)
                    print("Found {} at {}".format(name, addr))
                    createLabel(addr, name + "_constants", True)
                    addr = addr.add(len(dword_array) * 4)
                    continue
        except:
            pass
        
        addr = addr.add(4)
    
    return results

# Search for crypto constants
print("=== Searching for Cryptographic Constants ===")
aes_sbox_addrs = find_byte_array(AES_SBOX, "AES_Sbox")
md5_addrs = find_dword_array(MD5_CONSTANTS, "MD5_Constants")
sha256_addrs = find_dword_array(SHA256_K, "SHA256_K")

print("\nResults:")
print("  AES S-boxes: {}".format(len(aes_sbox_addrs)))
print("  MD5 constants: {}".format(len(md5_addrs)))
print("  SHA256 constants: {}".format(len(sha256_addrs)))

# Find functions that reference these
if aes_sbox_addrs or md5_addrs or sha256_addrs:
    print("\n=== Finding Crypto Functions ===")
    
    for addr in aes_sbox_addrs + md5_addrs + sha256_addrs:
        refs = getReferencesTo(addr)
        for ref in refs:
            func = getFunctionContaining(ref.getFromAddress())
            if func:
                print("Crypto function: {} at {}".format(
                    func.getName(), func.getEntryPoint()))
                
                # Rename if not already named
                if func.getName().startswith("FUN_"):
                    func.setName("crypto_function_" + str(func.getEntryPoint())[-4:],
                               SourceType.ANALYSIS)
