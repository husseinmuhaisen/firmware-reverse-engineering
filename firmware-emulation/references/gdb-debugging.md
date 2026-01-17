# GDB Debugging Reference for Firmware Emulation

Advanced debugging techniques for emulated firmware using GDB and gdb-multiarch.

## Setup

### Install GDB Multi-Architecture

```bash
# Install gdb-multiarch (supports all architectures)
sudo apt-get install gdb-multiarch

# Or install architecture-specific GDB
sudo apt-get install gdb-arm-none-eabi      # ARM bare-metal
sudo apt-get install gdb-aarch64-linux-gnu  # AArch64
sudo apt-get install gdb-mips-linux-gnu     # MIPS
```

### Starting QEMU with GDB Server

**User-mode:**
```bash
qemu-arm -g 1234 -L ./rootfs/ ./binary
```

**System-mode:**
```bash
qemu-system-arm -M versatilepb -kernel zImage ... -gdb tcp::1234 -S
# -gdb tcp::1234 : Start GDB server on port 1234
# -S : Pause at startup (wait for GDB connection)
```

## Basic GDB Commands

### Connecting to QEMU

```bash
# Start gdb-multiarch with binary
gdb-multiarch ./binary

# Or for kernel debugging
gdb-multiarch ./vmlinux

# Connect to QEMU
(gdb) target remote :1234

# Or specify host
(gdb) target remote localhost:1234
```

### Essential Commands

```gdb
# Execution control
continue (c)              # Continue execution
step (s)                  # Step into (source level)
next (n)                  # Step over (source level)
stepi (si)                # Step one instruction
nexti (ni)                # Step over one instruction
finish                    # Run until function returns

# Breakpoints
break main                # Break at main function
break *0x8048000          # Break at address
break filename.c:42       # Break at source line
break func if var == 5    # Conditional breakpoint
delete 1                  # Delete breakpoint 1
info breakpoints          # List all breakpoints
disable 1                 # Disable breakpoint 1
enable 1                  # Enable breakpoint 1

# Examination
info registers (i r)      # Show all registers
info registers r0 r1      # Show specific registers (ARM)
x/10x $sp                 # Examine 10 hex words at stack pointer
x/10i $pc                 # Disassemble 10 instructions at PC
x/s 0x8048000             # Examine string at address
print variable            # Print variable value
print/x $r0               # Print register in hex
display $pc               # Auto-display PC after each step

# Stack
backtrace (bt)            # Show call stack
frame 0                   # Select stack frame
info frame                # Show current frame details
up                        # Move up stack
down                      # Move down stack

# Memory
set {int}0x8048000 = 0x90 # Write to memory
dump binary memory file.bin 0x8000000 0x8001000  # Dump memory region

# Symbols
info functions            # List all functions
info variables            # List all variables
info symbol 0x8048000     # Find symbol at address
```

## Architecture-Specific Debugging

### ARM (32-bit)

```gdb
# Registers
info registers
# r0-r12: General purpose
# sp (r13): Stack pointer
# lr (r14): Link register (return address)
# pc (r15): Program counter
# cpsr: Current program status register

# Common breakpoints
break main
break *0x8000              # Address breakpoint

# Examine ARM instructions
x/10i $pc
set disassembly-flavor arm
disassemble main

# Thumb mode handling
# ARM can switch between ARM and Thumb modes
# PC LSB indicates mode: 0=ARM, 1=Thumb
print/x $pc                # Check mode

# Step through Thumb code
si
ni
```

### AArch64 (ARM 64-bit)

```gdb
# Registers
info registers
# x0-x30: General purpose (64-bit)
# sp: Stack pointer
# pc: Program counter
# lr (x30): Link register

# Examine instructions
x/10i $pc
disassemble main

# Print 64-bit registers
print/x $x0
print/x $sp
```

### MIPS

```gdb
# Registers
info registers
# $0 (zero): Always zero
# $1 (at): Assembler temporary
# $2-$3 ($v0-$v1): Function return values
# $4-$7 ($a0-$a3): Function arguments
# $8-$15 ($t0-$t7): Temporaries
# $16-$23 ($s0-$s7): Saved registers
# $28 ($gp): Global pointer
# $29 ($sp): Stack pointer
# $30 ($fp): Frame pointer
# $31 ($ra): Return address
# $pc: Program counter

# Examine MIPS instructions
x/10i $pc
disassemble main

# Print registers
print/x $v0
print/x $a0
print/x $ra
```

### x86/x86_64

```gdb
# Registers (x86)
info registers
# eax, ebx, ecx, edx: General purpose
# esp: Stack pointer
# ebp: Base pointer
# eip: Instruction pointer

# Registers (x86_64)
# rax, rbx, rcx, rdx, rsi, rdi, r8-r15
# rsp: Stack pointer
# rbp: Base pointer
# rip: Instruction pointer

# Set Intel syntax
set disassembly-flavor intel
disassemble main
```

## Advanced Debugging Techniques

### 1. Kernel Debugging (System-Mode)

```bash
# Start QEMU in paused state
qemu-system-arm -M versatilepb -kernel zImage ... -gdb tcp::1234 -S

# In another terminal
gdb-multiarch vmlinux
(gdb) target remote :1234
(gdb) break start_kernel    # Early kernel function
(gdb) continue
```

**Useful kernel breakpoints:**
```gdb
break start_kernel          # Kernel entry
break do_fork               # Process creation
break sys_execve            # Program execution
break __do_page_fault       # Page faults
break do_IRQ                # Interrupt handling
```

### 2. Userspace Debugging in System-Mode

```gdb
# After kernel boots and shell is available
# Load userspace binary symbols
(gdb) add-symbol-file /path/to/binary 0x00008000

# Set breakpoint in userspace
(gdb) break main
(gdb) continue

# When userspace binary starts, GDB will break
```

### 3. Watchpoints (Hardware/Software)

```gdb
# Watch memory location
watch *0x8048000              # Break when value changes
watch variable                # Watch variable
rwatch *0x8048000             # Break on read
awatch *0x8048000             # Break on read or write

# Watch with conditions
watch variable if variable > 100

# List watchpoints
info watchpoints
```

### 4. Tracepoints and Commands

```gdb
# Set tracepoint
trace main

# Execute commands at breakpoint
break main
commands
  print variable
  backtrace
  continue
end

# Automatic logging
break function
commands
  silent
  printf "Called with arg: %d\n", $r0
  continue
end
```

### 5. Scripting GDB

**GDB Python scripting:**
```python
# In GDB
python
import gdb

class MyBreakpoint(gdb.Breakpoint):
    def __init__(self, location):
        super().__init__(location)
        self.count = 0
    
    def stop(self):
        self.count += 1
        print(f"Hit {self.count} times")
        return False  # Don't actually stop

bp = MyBreakpoint("main")
end
```

**GDB command files:**
```bash
# Create debug.gdb
cat > debug.gdb << 'EOF'
target remote :1234
break main
commands
  backtrace
  info registers
  continue
end
continue
EOF

# Run GDB with script
gdb-multiarch -x debug.gdb ./binary
```

### 6. Core Dump Analysis

```bash
# Generate core dump from running QEMU
# In QEMU monitor
(qemu) dump-guest-memory core.dump

# Analyze with GDB
gdb-multiarch ./binary core.dump
(gdb) backtrace
(gdb) info registers
(gdb) x/10i $pc
```

### 7. Remote Process Attach (User-Mode)

```bash
# For already-running process in QEMU
# Start QEMU normally
qemu-arm -L ./rootfs/ ./binary &
PID=$!

# Attach GDB to QEMU process
gdb-multiarch ./binary
(gdb) attach $PID
```

## Debugging Complex Issues

### Buffer Overflow Detection

```gdb
# Set breakpoint before vulnerable function
break vulnerable_function

# Examine stack before call
x/20x $sp

# Step through function
si

# Watch for stack corruption
watch *($sp + 100)  # Watch stack region

# Check return address
x/x $sp             # ARM: look for lr on stack
```

### Format String Vulnerabilities

```gdb
# Break at printf/sprintf
break printf
break sprintf

# Examine format string argument
commands
  x/s $r0  # ARM: first argument
  continue
end

# Check for %n or excessive %s
```

### Heap Corruption

```gdb
# Break at malloc/free
break malloc
break free

# Log allocations
commands
  silent
  printf "malloc(%d) = ", $r0
  finish
  printf "%p\n", $r0
  continue
end

# Watch for double-free or use-after-free
```

### Race Conditions (Multi-threaded)

```gdb
# List threads
info threads

# Switch thread
thread 2

# Set thread-specific breakpoint
break function thread 2

# Schedule locking
set scheduler-locking on   # Only current thread runs
set scheduler-locking off  # All threads run
```

## Integration with Reverse Engineering Tools

### IDA Pro

```gdb
# 1. In IDA: Debugger -> Attach to process -> Remote GDB debugger
# 2. Host: localhost, Port: 1234
# 3. IDA will sync with GDB breakpoints and symbols
```

### Ghidra

```gdb
# 1. In Ghidra: Debugger -> Debug -> Connect to gdb
# 2. Configure gdb:
#    - Launch: gdb-multiarch
#    - Connect: gdb://localhost:1234
# 3. Ghidra provides decompiler view with debugging
```

### radare2

```bash
# Connect r2 to GDB server
r2 -D gdb gdb://localhost:1234

# Or use r2's own debug mode with QEMU
r2 -d qemu-arm -L ./rootfs/ ./binary
```

## GDB Initialization File

Create `~/.gdbinit` for persistent settings:

```gdb
# ~/.gdbinit

# Set architecture
set architecture arm

# Syntax preference
set disassembly-flavor intel

# Pagination
set pagination off

# History
set history save on
set history size 10000

# Pretty printing
set print pretty on
set print array on

# Auto-load safe path (for .gdbinit in project dirs)
set auto-load safe-path /

# Custom commands
define hook-stop
    info registers
    x/5i $pc
end

# ARM-specific helpers
define arm_regs
    printf "r0:  0x%08x   r1:  0x%08x   r2:  0x%08x   r3:  0x%08x\n", $r0, $r1, $r2, $r3
    printf "r4:  0x%08x   r5:  0x%08x   r6:  0x%08x   r7:  0x%08x\n", $r4, $r5, $r6, $r7
    printf "r8:  0x%08x   r9:  0x%08x   r10: 0x%08x   r11: 0x%08x\n", $r8, $r9, $r10, $r11
    printf "r12: 0x%08x   sp:  0x%08x   lr:  0x%08x   pc:  0x%08x\n", $r12, $sp, $lr, $pc
end

# MIPS-specific helpers
define mips_regs
    printf "v0: 0x%08x   v1: 0x%08x   a0: 0x%08x   a1: 0x%08x\n", $v0, $v1, $a0, $a1
    printf "a2: 0x%08x   a3: 0x%08x   sp: 0x%08x   ra: 0x%08x\n", $a2, $a3, $sp, $ra
end
```

## GDB Extensions

### pwndbg (Recommended for exploit dev)

```bash
# Install pwndbg
git clone https://github.com/pwndbg/pwndbg
cd pwndbg
./setup.sh

# Usage with QEMU
gdb-multiarch ./binary
pwndbg> target remote :1234
pwndbg> context      # Show comprehensive context
```

### GEF (GDB Enhanced Features)

```bash
# Install GEF
bash -c "$(curl -fsSL https://gef.blah.cat/sh)"

# Usage
gdb-multiarch ./binary
gef> target remote :1234
```

### Voltron

```bash
# Install Voltron (multi-pane UI)
pip3 install voltron

# Start voltron views in separate terminals
voltron view disasm
voltron view register
voltron view stack
voltron view backtrace

# Then connect GDB
gdb-multiarch ./binary
(gdb) source /path/to/voltron/entry.py
(gdb) target remote :1234
```

## Troubleshooting GDB Issues

### Issue: "Remote 'g' packet reply is too long"

**Cause:** Architecture mismatch between GDB and QEMU

**Solution:**
```gdb
# Force architecture
(gdb) set architecture arm
(gdb) target remote :1234

# Or use correct GDB variant
gdb-multiarch instead of gdb
```

### Issue: No symbols loaded

**Cause:** Binary is stripped or wrong binary loaded

**Solution:**
```gdb
# Load symbols manually
(gdb) file ./binary
(gdb) add-symbol-file ./binary 0x8000

# Or use unstripped version if available
(gdb) file ./binary.unstripped
```

### Issue: Breakpoint not hit

**Cause:** ASLR, wrong address, or code not reached

**Solution:**
```gdb
# Disable ASLR in QEMU kernel command line
-append "nokaslr ..."

# Check if code is actually reached
(gdb) break *0x0   # Break at entry
(gdb) continue
(gdb) x/10i $pc    # See where we are

# For dynamic libraries, break after load
(gdb) catch load
```

### Issue: Source code not shown

**Cause:** Source paths don't match compiled paths

**Solution:**
```gdb
# Set source directory
(gdb) directory /path/to/source

# Or use substitute-path
(gdb) set substitute-path /old/path /new/path
```

## Best Practices

1. **Use gdb-multiarch** - Handles all architectures
2. **Load symbols before connecting** - `file ./binary` first
3. **Start QEMU with -S** - Pause at start for kernel debugging
4. **Use .gdbinit** - Automate repetitive commands
5. **Learn Python scripting** - Automate complex debugging tasks
6. **Use GDB extensions** - pwndbg/GEF enhance productivity significantly
7. **Keep GDB updated** - Newer versions support more architectures/features
8. **Save sessions** - Use `logging on` to record debug sessions
9. **Create debug scripts** - Automate common debugging workflows
10. **Combine with other tools** - IDA/Ghidra + GDB is powerful

## Quick Reference Card

```
Connection:           target remote :1234
Execution:            continue (c), step (s), next (n), stepi (si), nexti (ni)
Breakpoints:          break, delete, disable, enable, info breakpoints
Memory:               x/FMT addr (FMT: count+format+size, e.g., x/10xw $sp)
Registers:            info registers, print/x $reg
Stack:                backtrace (bt), frame, up, down
Watchpoints:          watch, rwatch, awatch
Search:               find /b 0x8000000, +0x10000, 0x90, 0x90
Dump memory:          dump binary memory file.bin start end
Set memory:           set {type}addr = value
Disassemble:          disassemble, x/10i $pc
Info:                 info functions, info variables, info symbol addr
```
