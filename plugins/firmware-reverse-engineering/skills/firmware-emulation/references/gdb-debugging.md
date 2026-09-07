# GDB Debugging Reference for Firmware Emulation

Advanced debugging techniques for emulated firmware using GDB and gdb-multiarch.

## Setup

### Install GDB Multi-Architecture

```bash
# Install gdb-multiarch (supports many architectures; confirm the installed build)
sudo apt-get install gdb-multiarch

# Architecture-specific package names vary by distribution; gdb-multiarch
# is the Debian/Ubuntu example used here.
```

### Starting QEMU with GDB Server

**User-mode:**
```bash
qemu-arm -g 1234 -L ./rootfs/ ./binary
```

**System-mode:**
```bash
qemu-system-arm -M versatilepb -kernel zImage ... -gdb tcp:127.0.0.1:1234 -S
# -gdb tcp:127.0.0.1:1234 : Start GDB server on port 1234
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
continue                  # Alias: c; Continue execution
step                      # Alias: s; Step into (source level)
next                      # Alias: n; Step over (source level)
stepi                     # Alias: si; Step one instruction
nexti                     # Alias: ni; Step over one instruction
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
info registers            # Alias: i r; Show all registers
info registers r0 r1      # Show specific registers (ARM)
x/10x $sp                 # Examine 10 hex words at stack pointer
x/10i $pc                 # Disassemble 10 instructions at PC
x/s 0x8048000             # Examine string at address
print variable            # Print variable value
print/x $r0               # Print register in hex
display $pc               # Auto-display PC after each step

# Stack
backtrace                 # Alias: bt; Show call stack
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
# disassembly-flavor is an x86 option, not an ARM mode selector.
disassemble main

# Thumb mode handling
# ARM can switch between ARM and Thumb modes
# On A/R-profile ARM, CPSR.T (bit 5) is the current instruction state.
# Function-pointer bit 0 encodes interworking; the displayed PC is usually aligned.
print/x (($cpsr >> 5) & 1)  # 0=A32, 1=Thumb; M-profile uses xPSR.T instead

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
qemu-system-arm -M versatilepb -kernel zImage ... -gdb tcp:127.0.0.1:1234 -S

# In another terminal
gdb-multiarch vmlinux
(gdb) target remote :1234
(gdb) break start_kernel    # Early kernel function
(gdb) continue
```

**Example kernel breakpoints (names vary by version; inspect `info functions`):**
```gdb
break start_kernel          # Kernel entry
break do_fork               # Process creation
break sys_execve            # Program execution
break __do_page_fault       # Page faults
break do_IRQ                # Interrupt handling
```

### 2. Userspace Debugging in System-Mode

Run a matching target-architecture `gdbserver` inside the guest. The system
QEMU stub exposes virtual CPUs, not a process-aware userspace debugger.

```bash
# Inside guest, over an isolated network
gdbserver :2345 /usr/sbin/httpd -f
# On host
gdb-multiarch ./rootfs/usr/sbin/httpd
```

```gdb
target remote 192.168.100.2:2345
set sysroot ./rootfs
break main
continue
```

For stripped code, use verified instruction addresses and runtime load bias.
Loading the same stripped file with `add-symbol-file` cannot restore lost names.

### 3. Watchpoints (Hardware/Software)

Availability depends on the target stub: QEMU user-mode does not provide the
same watchpoint support as full-system TCG. Verify support before relying on it.

```gdb
# Watch memory location
watch *(unsigned int *)0x8048000              # Break when value changes
watch variable                # Watch variable
rwatch *(unsigned int *)0x8048000             # Break on read
awatch *(unsigned int *)0x8048000             # Break on read or write

# Watch with conditions
watch variable if variable > 100

# List watchpoints
info watchpoints
```

### 4. Tracepoints and Commands

```gdb
# Remote tracepoints require target-agent support; QEMU stubs generally do
# not provide it. Use breakpoint commands below for logging.

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
```gdb
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

```gdb
# On a supported process-aware target, write a process core:
generate-core-file process.core
# Later, with the exact executable and target libraries:
# gdb-multiarch ./binary process.core
```

QEMU monitor `dump-guest-memory` creates a full guest memory dump, not a normal
userspace process core. Analyze it with the matching kernel symbols and a
kernel-dump workflow; opening it with an arbitrary userspace binary is incorrect.
Support for process core generation varies by remote stub.

### 7. Remote Process Attach

Attaching host GDB to the QEMU PID debugs the emulator, not the foreign process.
Start QEMU user-mode with its GDB stub, or use gdbserver within a full-system guest:

```bash
qemu-arm -g 1234 -L ./rootfs/ ./binary
# In another terminal
gdb-multiarch ./binary -ex 'target remote localhost:1234'
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
watch *(unsigned int *)($sp + 100)  # Watch stack region

# Check return address
info registers lr sp
# Find the saved LR from the function prologue/unwind info; it need not be at SP.
```

### Format String Vulnerabilities

```gdb
# AAPCS32 integer argument convention, not AArch64:
break printf
commands
  x/s $r0  # printf(format, ...)
  continue
end
break sprintf
commands
  x/s $r1  # sprintf(destination, format, ...)
  continue
end
# A variable format requires input-origin verification; %n is not automatically a bug.

```

### Heap Corruption

```gdb
# Manual AAPCS32 malloc inspection:
break malloc
continue
print/u $r0  # Requested size at entry
finish
print/x $r0  # Returned pointer after finish
# Record entry/return pairs; use Python FinishBreakpoint for automation.
# A resume command inside a GDB commands list ends that list, so commands
# after finish in such a list do not automatically execute.
break free

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
#    - In the GDB terminal: target remote localhost:1234
# 3. Ghidra provides decompiler view with debugging
```

### radare2

```bash
# Connect r2 to GDB server
r2 -D gdb gdb://localhost:1234

# Or use r2's own debug mode with QEMU
# A native -d attach debugs QEMU itself; use its GDB endpoint above.
```

## GDB Initialization File

Create `~/.gdbinit` for persistent settings:

```gdb
# ~/.gdbinit

# Let the loaded ELF/remote target select architecture.
# Use set disassembly-flavor intel only in x86 sessions.

# Pagination
set pagination off

# History
set history save on
set history size 10000

# Pretty printing
set print pretty on
set print array on

# Auto-load safe path (for .gdbinit in project dirs)
add-auto-load-safe-path /absolute/path/to/reviewed/debug-scripts

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
# add-symbol-file needs an unstripped symbol file and the actual .text address.
# The runtime load bias must be calculated; 0x8000 is not a generic address.

# Or use unstripped version if available
(gdb) file ./binary.unstripped
```

### Issue: Breakpoint not hit

**Cause:** ASLR, wrong address, or code not reached

**Solution:**
```gdb
# nokaslr in the kernel command line affects kernel ASLR, not userspace ASLR.
# For userspace, inspect the process mappings and relocate breakpoints.

# Check if code is actually reached
# Obtain the actual entry from ELF metadata and runtime mappings; it is not 0.
(gdb) info files
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

1. **Use gdb-multiarch** - Confirm support for the target architecture
2. **Load symbols before connecting** - `file ./binary` first
3. **Start QEMU with -S** - Pause at start for kernel debugging
4. **Use .gdbinit** - Automate repetitive commands
5. **Learn Python scripting** - Automate complex debugging tasks
6. **Use GDB extensions** - pwndbg/GEF enhance productivity significantly
7. **Keep GDB updated** - Newer versions support more architectures/features
8. **Save sessions** - Use `set logging enabled on` to record debug sessions
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
