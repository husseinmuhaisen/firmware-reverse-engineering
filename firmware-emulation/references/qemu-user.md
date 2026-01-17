# QEMU User-Mode Emulation Reference

Guide to running individual binaries from firmware without full system emulation.

## Overview

User-mode emulation runs a single binary from the extracted firmware using the host kernel, translating system calls on the fly. This is faster and simpler than system-mode but less authentic.

## Architecture Support

QEMU user-mode binaries for common architectures:

```bash
qemu-arm              # ARM 32-bit
qemu-aarch64          # ARM 64-bit
qemu-mips             # MIPS big-endian
qemu-mipsel           # MIPS little-endian
qemu-mips64           # MIPS64 big-endian
qemu-mips64el         # MIPS64 little-endian
qemu-ppc              # PowerPC 32-bit
qemu-ppc64            # PowerPC 64-bit
qemu-i386             # x86 32-bit
qemu-x86_64           # x86 64-bit
qemu-riscv32          # RISC-V 32-bit
qemu-riscv64          # RISC-V 64-bit
```

## Basic Usage

### Run Single Binary

```bash
# Identify architecture first
file binary
# Output: ELF 32-bit LSB executable, ARM

# Run with appropriate QEMU
qemu-arm binary

# With arguments
qemu-arm binary arg1 arg2 --flag

# With environment variables
ENV_VAR=value qemu-arm binary
```

### Chroot Environment

**Most authentic user-mode approach - provides correct library paths:**

```bash
# Setup chroot environment
sudo mkdir -p /mnt/firmware
sudo mount -o loop rootfs.ext4 /mnt/firmware

# Copy qemu-static binary into chroot
sudo cp /usr/bin/qemu-arm-static /mnt/firmware/usr/bin/

# Chroot and run
sudo chroot /mnt/firmware /usr/bin/qemu-arm-static /bin/busybox
sudo chroot /mnt/firmware /usr/bin/qemu-arm-static /usr/bin/httpd

# Alternative: using systemd-nspawn (more isolated)
sudo systemd-nspawn -D /mnt/firmware /usr/bin/qemu-arm-static /bin/sh
```

### Library Path Configuration

When running without chroot, specify library paths:

```bash
# Single library directory
qemu-arm -L /path/to/rootfs/ binary

# This tells QEMU where to find shared libraries
# Equivalent to setting LD_LIBRARY_PATH but for emulated arch

# Example with extracted firmware
qemu-arm -L ./squashfs-root/ ./squashfs-root/bin/busybox
```

## Advanced Options

### CPU Model Selection

```bash
# List available CPU models
qemu-arm -cpu help

# Run with specific CPU
qemu-arm -cpu cortex-a9 binary

# Example for newer ARM features
qemu-arm -cpu cortex-a15 binary
```

### Environment Variables

```bash
# QEMU-specific environment variables
QEMU_LD_PREFIX=/path/to/rootfs qemu-arm binary

# Useful for debugging
QEMU_STRACE=1 qemu-arm binary         # Trace system calls
QEMU_LOG=in_asm qemu-arm binary       # Log translated instructions
```

### Debugging with GDB

```bash
# Start binary with GDB server on port 1234
qemu-arm -g 1234 binary

# Connect with GDB
gdb-multiarch binary
(gdb) target remote :1234
(gdb) break main
(gdb) continue
```

### Networking

User-mode QEMU automatically forwards networking:

```bash
# Binary makes network calls - they work transparently
qemu-arm -L ./rootfs/ ./rootfs/usr/bin/wget http://example.com

# No special configuration needed
```

## Common Use Cases

### 1. Running Shell/BusyBox

```bash
# Interactive shell
sudo chroot /mnt/firmware /usr/bin/qemu-arm-static /bin/sh

# Execute commands
sudo chroot /mnt/firmware /usr/bin/qemu-arm-static /bin/sh -c "ls -la /etc"
```

### 2. Running Web Server

```bash
# Identify web server binary
find squashfs-root/ -name "*httpd*" -o -name "*lighttpd*" -o -name "*nginx*"

# Run in chroot
sudo chroot /mnt/firmware /usr/bin/qemu-arm-static /usr/sbin/httpd -f

# Or without chroot (less reliable)
qemu-arm -L ./squashfs-root/ ./squashfs-root/usr/sbin/httpd
```

### 3. Running Daemons

```bash
# Many firmware daemons
sudo chroot /mnt/firmware /usr/bin/qemu-arm-static /usr/sbin/telnetd -F
sudo chroot /mnt/firmware /usr/bin/qemu-arm-static /usr/sbin/dropbear -F -E

# -F flag typically means "foreground" - prevents daemonizing
```

### 4. Fuzzing Individual Binaries

```bash
# Use AFL++ with QEMU mode
export AFL_QEMU_CPU=cortex-a9
afl-fuzz -Q -i input_dir -o output_dir -- qemu-arm -L ./rootfs/ ./binary @@

# Or with custom fuzzer
for i in $(seq 1 1000); do
    echo "Test $i" | qemu-arm -L ./rootfs/ ./binary
done
```

## Limitations of User-Mode

### What Works
- System calls (translated to host)
- Library loading (with correct -L path)
- Network I/O
- File I/O
- Threading (basic)

### What Doesn't Work Well
- Kernel modules
- Device drivers
- Hardware-specific I/O (GPIO, SPI, etc.)
- Some threading edge cases
- Syscalls not implemented in QEMU
- `/proc` and `/sys` filesystem quirks

### Workarounds

**Missing syscalls:**
```bash
# Check QEMU version - newer = more syscalls
qemu-arm --version

# Update QEMU if encountering unsupported syscalls
sudo apt-get install qemu-user-static
# Or compile latest from source
```

**Hardware I/O:**
```bash
# Mock hardware interfaces
# Create fake devices in chroot
sudo mknod /mnt/firmware/dev/gpio0 c 254 0

# Or patch binary to skip hardware calls (advanced)
```

## Library Dependency Resolution

### Check Dependencies

```bash
# Inside chroot
ldd /bin/binary

# Outside chroot (for cross-arch)
qemu-arm -L ./rootfs/ /lib/ld-linux.so.3 --list ./rootfs/bin/binary
```

### Missing Libraries

```bash
# Find library in rootfs
find ./squashfs-root/ -name "libmissing.so*"

# If not found, may need to extract from another partition
# Or install in host system

# Copy to rootfs
sudo cp /lib/libmissing.so.1 /mnt/firmware/lib/
```

## Scripting User-Mode Emulation

### Batch Execution Script

```bash
#!/bin/bash
# run_firmware_binary.sh

ROOTFS="/mnt/firmware"
QEMU_ARCH="qemu-arm-static"

# Ensure qemu-static is present
if [ ! -f "$ROOTFS/usr/bin/$QEMU_ARCH" ]; then
    sudo cp /usr/bin/$QEMU_ARCH $ROOTFS/usr/bin/
fi

# Run binary with args
sudo chroot $ROOTFS /usr/bin/$QEMU_ARCH "$@"
```

Usage:
```bash
./run_firmware_binary.sh /bin/busybox ls -la
./run_firmware_binary.sh /usr/sbin/httpd -h
```

### Automated Service Launcher

```bash
#!/bin/bash
# launch_services.sh

ROOTFS="/mnt/firmware"
QEMU_ARCH="qemu-arm-static"

# Start multiple services in background
services=("/usr/sbin/httpd" "/usr/sbin/telnetd" "/usr/sbin/ftpd")

for service in "${services[@]}"; do
    echo "Starting $service..."
    sudo chroot $ROOTFS /usr/bin/$QEMU_ARCH $service -F &
done

echo "All services started. PIDs:"
jobs -p
```

## Debugging Techniques

### System Call Tracing

```bash
# Built-in QEMU strace
QEMU_STRACE=1 qemu-arm -L ./rootfs/ ./binary 2>&1 | tee strace.log

# Or use host strace (less detailed for cross-arch)
strace -f qemu-arm -L ./rootfs/ ./binary
```

### Logging

```bash
# Enable QEMU logging
qemu-arm -d in_asm,op,cpu -L ./rootfs/ ./binary 2>&1 | tee qemu.log

# Log specific events
QEMU_LOG=int,exec qemu-arm -L ./rootfs/ ./binary

# Available log options (qemu-arm -d help):
# - in_asm: Assembly code being executed
# - op: TCG operations
# - int: Interrupts/exceptions
# - exec: Execution flow
# - cpu: CPU state
```

### Memory Analysis

```bash
# Run with GDB
qemu-arm -g 1234 -L ./rootfs/ ./binary &

# In another terminal
gdb-multiarch ./binary
(gdb) target remote :1234
(gdb) x/20x $sp        # Examine stack
(gdb) x/20i $pc        # Disassemble from PC
(gdb) info registers
```

## Performance Considerations

### Speed

User-mode is significantly faster than system-mode:
- No full kernel emulation
- Direct system call translation
- Less overhead

**Typical speedup: 10-50x faster than system-mode**

### Optimization

```bash
# Use static QEMU binaries (faster)
qemu-arm-static vs qemu-arm

# Enable JIT (default, but can be tuned)
# Set environment: QEMU_JIT=1

# For long-running processes, consider cache
# QEMU caches translated blocks
```

## Combining with Other Tools

### With IDA/Ghidra

```bash
# Debug plugin workflow
# 1. Start binary with GDB server
qemu-arm -g 1234 -L ./rootfs/ ./binary

# 2. In IDA: Debugger -> Attach -> Remote GDB Debugger
# Host: localhost, Port: 1234

# 3. In Ghidra: Debugger -> Debug -> Connect to remote gdbserver
```

### With Frida

```bash
# Dynamic instrumentation
# Install frida-server for target arch
# Then inject into QEMU process

frida -U -f /bin/binary -l script.js --qemu
```

### With Radare2

```bash
# Debug with r2
r2 -d 'qemu-arm -g 1234 -L ./rootfs/ ./binary'

# Or connect to running QEMU
r2 -D gdb -d gdb://localhost:1234
```

## Troubleshooting

### Issue: "No such file or directory" (but file exists)

**Cause:** Missing dynamic linker or libraries

**Solution:**
```bash
# Check interpreter
readelf -l binary | grep interpreter
# Shows: /lib/ld-linux.so.3

# Ensure linker exists in rootfs
ls -la ./rootfs/lib/ld-linux.so.3

# If missing, copy from extracted firmware or cross-toolchain
```

### Issue: "Illegal instruction"

**Cause:** Binary uses instructions not supported by QEMU CPU model

**Solution:**
```bash
# Try different CPU model
qemu-arm -cpu cortex-a9 -L ./rootfs/ ./binary

# List available CPUs
qemu-arm -cpu help
```

### Issue: Binary crashes immediately

**Cause:** Library incompatibility or missing dependencies

**Solution:**
```bash
# Check dependencies in chroot
sudo chroot /mnt/firmware /usr/bin/qemu-arm-static /lib/ld-linux.so.3 --list /bin/binary

# Use strace to see what fails
QEMU_STRACE=1 qemu-arm -L ./rootfs/ ./binary 2>&1 | grep -A 5 "= -1"
```

### Issue: Cannot bind to port

**Cause:** Permissions or port already in use

**Solution:**
```bash
# Use high port (>1024) or run as root
sudo chroot /mnt/firmware /usr/bin/qemu-arm-static /usr/sbin/httpd -p 8080

# Check if port is free
netstat -tulpn | grep :80
```

## Best Practices

1. **Always use chroot when possible** - Most authentic environment
2. **Copy qemu-static, not qemu** - Static version has no dependencies
3. **Check architecture first** - Use `file` before selecting QEMU
4. **Start with -L flag** - Provide correct library paths
5. **Use GDB for deep debugging** - Much more powerful than printf debugging
6. **Log system calls** - QEMU_STRACE reveals what binary is trying to do
7. **Test with simple binaries first** - Start with busybox, not complex daemons
8. **Read error messages carefully** - Often indicate missing libraries or syscalls
