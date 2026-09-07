---
name: firmware-emulation
description: "Comprehensive firmware dynamic analysis and emulation using QEMU (user-mode and system-mode), GDB debugging, network traffic analysis, and automated tools (Firmadyne/FirmAE). Use when Claude needs to run extracted firmware for dynamic analysis. Covers: (1) Deciding between automated vs manual emulation approaches, (2) QEMU user-mode emulation for individual binaries, (3) QEMU system-mode emulation for full firmware stack, (4) Advanced GDB debugging with gdb-multiarch, (5) Network traffic capture and protocol analysis, (6) MITM attacks and traffic manipulation, (7) Automated emulation with Firmadyne/FirmAE, (8) Troubleshooting boot failures and network issues. Requires extracted firmware (use firmware-extraction skill first). Complements firmware-static-analysis skill with runtime behavior observation."
---

# Firmware Dynamic Analysis & Emulation

Run extracted firmware in controlled environments for dynamic analysis, debugging, and vulnerability testing. This skill provides comprehensive workflows for both automated and manual emulation approaches.

## Emulation Strategy Decision Tree

Before starting emulation, determine the best approach:

**Use AUTOMATED (Firmadyne/FirmAE)** when:
- Analyzing multiple router/IoT firmware images quickly
- Need quick initial assessment
- Firmware is Linux-based embedded system
- You want network services automatically configured
- Time-constrained analysis

**Use USER-MODE (qemu-user)** when:
- Running individual binaries from extracted firmware
- Need quick testing of specific executables
- Debugging single applications
- Fuzzing specific binaries
- Full system emulation is overkill

**Use SYSTEM-MODE (qemu-system)** when:
- Need authentic complete environment
- Analyzing kernel-level behavior
- Require hardware emulation (GPIO, MTD, etc.)
- Automated tools failed
- Advanced debugging of boot process needed
- Custom firmware with non-standard init

## Prerequisites

### Install Required Tools

```bash
# QEMU (all architectures)
sudo apt-get install qemu-system qemu-user-static qemu-user

# Cross-architecture debugging
sudo apt-get install gdb-multiarch

# Network tools
sudo apt-get install bridge-utils uml-utilities tcpdump wireshark tshark

# Filesystem tools
sudo apt-get install squashfs-tools mtd-utils

# Optional but recommended
pip3 install python-magic scapy
sudo apt-get install binwalk

# For Firmadyne/FirmAE
sudo apt-get install postgresql python3-psycopg2
```

### Verify Installation

```bash
# Check QEMU versions
qemu-arm --version
qemu-system-arm --version

# Check GDB
gdb-multiarch --version

# List available QEMU machines
qemu-system-arm -M help
qemu-system-mips -M help
```

## Workflow Overview

Follow this systematic approach for firmware emulation:

1. **Strategy Selection** - Automated vs manual (use decision tree)
2. **Preparation** - Extract firmware, identify architecture
3. **Initial Emulation** - Try automated tools first
4. **Manual Emulation** - If automated fails, use QEMU directly
5. **Debugging** - GDB integration for deep analysis
6. **Network Analysis** - Traffic capture and protocol analysis
7. **Vulnerability Testing** - Fuzzing and exploitation
8. **Documentation** - Record findings and techniques

## Path 1: Automated Emulation (Quick Start)

Try automated tools first - they handle 80% of common firmware.

### Step 1: Prepare Firmware

```bash
# Ensure firmware is extracted
# Use firmware-extraction skill if needed
ls -la squashfs-root/

# Note firmware details
file vmlinux  # Kernel if present
cat squashfs-root/etc/version  # Firmware version
```

### Step 2: Run FirmAE

FirmAE is recommended over Firmadyne (better success rate).

```bash
cd /path/to/FirmAE

# Automated analysis
sudo ./run.sh -r "Brand" /path/to/firmware.bin

# Wait for completion (5-15 minutes typically)
# FirmAE will:
# - Extract filesystem
# - Detect architecture
# - Create QEMU image
# - Boot firmware
# - Run network analysis
```

### Step 3: Access Running Firmware

```bash
# Check FirmAE output for IP address
# Typical: 192.168.0.1 or 192.168.1.1

# Scan for open services
nmap -p- -A 192.168.0.1

# Access web interface
curl http://192.168.0.1/
# Or open in browser

# Try telnet/SSH
telnet 192.168.0.1
ssh admin@192.168.0.1
```

### Step 4: Analyze Network Traffic

```bash
# FirmAE captures traffic automatically
# Check scratch/<IMAGE_ID>/ for pcap files

# Or capture live
sudo tcpdump -i tap1_0 -w analysis.pcap

# Analyze in Wireshark
wireshark analysis.pcap
```

### When Automated Fails

If FirmAE/Firmadyne doesn't boot the firmware:

1. Check console output for errors
2. Try manual architecture specification: `./run.sh -a arm firmware.bin`
3. Review `/path/to/FirmAE/scratch/<ID>/` for logs
4. **Proceed to Path 2** (Manual Emulation)

**Reference**: See `references/automated-emulation.md` for complete Firmadyne/FirmAE guide.

## Path 2: Manual User-Mode Emulation

Run individual binaries without full system emulation.

### Step 1: Setup Chroot Environment

```bash
# Mount extracted filesystem
sudo mkdir -p /mnt/firmware
sudo mount -o loop rootfs.ext4 /mnt/firmware
# Or if directory: sudo mount --bind squashfs-root/ /mnt/firmware

# Copy qemu-static (critical!)
sudo cp /usr/bin/qemu-arm-static /mnt/firmware/usr/bin/
# Use appropriate arch: qemu-mips-static, qemu-aarch64-static, etc.
```

### Step 2: Test Basic Execution

```bash
# Run simple command
sudo chroot /mnt/firmware /usr/bin/qemu-arm-static /bin/busybox

# Interactive shell
sudo chroot /mnt/firmware /usr/bin/qemu-arm-static /bin/sh

# Check architecture matches
file /mnt/firmware/bin/busybox
# Should match qemu-XXX-static used
```

### Step 3: Run Target Binary

```bash
# Identify target (e.g., web server)
find /mnt/firmware -name "*httpd*"

# Run with arguments
sudo chroot /mnt/firmware /usr/bin/qemu-arm-static /usr/sbin/httpd -f -p 8080

# -f: foreground (don't daemonize)
# -p 8080: port 8080

# Access from host
curl http://localhost:8080/
```

### Step 4: Debug with GDB

```bash
# Start binary with GDB server
sudo chroot /mnt/firmware /usr/bin/qemu-arm-static -g 1234 /usr/sbin/httpd

# In another terminal
gdb-multiarch /mnt/firmware/usr/sbin/httpd
(gdb) target remote :1234
(gdb) break main
(gdb) continue
```

**Reference**: See `references/qemu-user.md` for comprehensive user-mode guide.

## Path 3: Manual System-Mode Emulation

Full firmware stack emulation - most authentic but complex.

### Step 1: Identify Components

```bash
# Locate kernel
find extracted/ -name "vmlinux" -o -name "zImage" -o -name "uImage"

# Check kernel arch
file vmlinux
# ELF 32-bit LSB executable, ARM → use qemu-system-arm

# Locate device tree (ARM/AArch64)
find extracted/ -name "*.dtb"

# Prepare rootfs
# If extracted as directory, create ext4 image
dd if=/dev/zero of=rootfs.ext4 bs=1M count=256
mkfs.ext4 rootfs.ext4
mkdir /tmp/mnt
sudo mount -o loop rootfs.ext4 /tmp/mnt
sudo cp -a squashfs-root/* /tmp/mnt/
sudo umount /tmp/mnt
```

### Step 2: Determine QEMU Machine

```bash
# List available machines for architecture
qemu-system-arm -M help

# Common choices:
# ARM: versatilepb (most compatible), vexpress-a9
# MIPS: malta
# AArch64: virt
# x86: pc (default)
```

### Step 3: Boot Firmware

```bash
# ARM example
qemu-system-arm \
  -M versatilepb \
  -kernel zImage \
  -dtb versatile-pb.dtb \
  -drive file=rootfs.ext4,if=sd,format=raw \
  -append "root=/dev/mmcblk0 console=ttyAMA0 rw debug" \
  -nographic \
  -m 256M

# MIPS example
qemu-system-mips \
  -M malta \
  -kernel vmlinux \
  -hda rootfs.ext4 \
  -append "root=/dev/sda console=ttyS0 nokaslr" \
  -nographic \
  -m 256M
```

### Step 4: Configure Networking

```bash
# Create TAP interface (requires root)
sudo tunctl -t tap0 -u $USER
sudo ifconfig tap0 192.168.100.1 netmask 255.255.255.0 up

# Enable forwarding
sudo sysctl -w net.ipv4.ip_forward=1
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Boot with TAP networking
qemu-system-arm \
  -M versatilepb \
  -kernel zImage \
  ... \
  -net nic,macaddr=52:54:00:12:34:56 \
  -net tap,ifname=tap0,script=no,downscript=no

# Inside guest, configure network
ifconfig eth0 192.168.100.2 netmask 255.255.255.0 up
route add default gw 192.168.100.1
```

### Step 5: Troubleshoot Boot Issues

**Kernel panic - cannot mount root:**
```bash
# Try different root devices
-append "root=/dev/sda ..."     # IDE disk
-append "root=/dev/vda ..."     # VirtIO disk
-append "root=/dev/mmcblk0 ..." # SD card

# Specify filesystem type
-append "root=/dev/sda rootfstype=ext4 ..."

# Boot to shell for debugging
-append "init=/bin/sh ..."
```

**No output / black screen:**
```bash
# Ensure -nographic flag
# Try different console device
-append "console=ttyS0 ..."      # Serial
-append "console=ttyAMA0 ..."    # ARM UART

# Enable early kernel messages
-append "earlyprintk debug loglevel=8 ..."
```

**Wrong machine type:**
```bash
# Try more generic/compatible machines
-M versatilepb  # Instead of device-specific
-M virt         # Generic virtual machine
```

**Reference**: See `references/qemu-system.md` for architecture-specific boot recipes.

## Advanced Debugging with GDB

### Setup GDB Session

```bash
# Start QEMU with GDB server (paused)
qemu-system-arm \
  -M versatilepb \
  -kernel zImage \
  ... \
  -gdb tcp::1234 -S
  # -S: Pause at startup

# Connect GDB
gdb-multiarch vmlinux
(gdb) target remote :1234
(gdb) break start_kernel
(gdb) continue
```

### Kernel Debugging

```gdb
# Set breakpoints on kernel functions
break do_fork
break sys_execve
break do_IRQ

# Step through boot
continue
step
nexti

# Examine kernel state
info registers
x/10i $pc
backtrace
```

### Userspace Debugging

```gdb
# After kernel boots and reaches userspace
# Load userspace binary symbols
add-symbol-file /path/to/binary 0x00008000

# Break in userspace application
break main
continue

# Examine application state
print variable
x/10x $sp
info threads
```

### Hardware Watchpoints

```gdb
# Watch memory location
watch *0x8048000

# Watch variable
watch global_var

# Conditional watchpoint
watch variable if variable > 100
```

**Reference**: See `references/gdb-debugging.md` for comprehensive GDB techniques.

## Network Traffic Analysis

### Capture Traffic

```bash
# Start capture before booting firmware
sudo tcpdump -i tap0 -w capture.pcap &

# Boot firmware
qemu-system-arm ...

# Interact with firmware
# Traffic is being captured

# Stop capture
sudo killall tcpdump
```

### Analyze with Wireshark

```bash
# Open in Wireshark
wireshark capture.pcap

# Or use tshark for CLI analysis
tshark -r capture.pcap -Y "http"
tshark -r capture.pcap -Y "tcp.port == 23"  # Telnet
```

### Extract Credentials

```bash
# HTTP POST data
tshark -r capture.pcap -Y "http.request.method == POST" -T fields -e http.file_data

# Telnet passwords (cleartext)
tshark -r capture.pcap -Y "telnet" -T fields -e data.text | grep -i password

# FTP credentials
tshark -r capture.pcap -Y "ftp.request.command == USER || ftp.request.command == PASS"
```

### Man-in-the-Middle Testing

```bash
# Install mitmproxy
pip3 install mitmproxy

# Start transparent proxy
sudo mitmproxy --mode transparent --showhost

# Redirect firmware traffic
sudo iptables -t nat -A PREROUTING -i tap0 -p tcp --dport 80 -j REDIRECT --to-port 8080
sudo iptables -t nat -A PREROUTING -i tap0 -p tcp --dport 443 -j REDIRECT --to-port 8080

# Firmware HTTP/HTTPS traffic now goes through mitmproxy
# View and modify in real-time
```

**Reference**: See `references/network-analysis.md` for protocol analysis and MITM techniques.

## Vulnerability Testing

### Web Interface Testing

```bash
# Access web interface
curl http://192.168.100.2/

# Directory brute-force
dirb http://192.168.100.2/ /usr/share/dirb/wordlists/common.txt

# Vulnerability scanning
nikto -h http://192.168.100.2/
nmap --script vuln -p 80 192.168.100.2

# SQL injection testing
sqlmap -u "http://192.168.100.2/login.php" --forms --batch

# Command injection
curl "http://192.168.100.2/cgi-bin/test.cgi?cmd=;ls"
```

### Binary Fuzzing

```bash
# With AFL++ in QEMU mode
export AFL_QEMU_CPU=cortex-a9
afl-fuzz -Q -i input_dir -o output_dir -- \
  qemu-arm -L ./rootfs/ ./rootfs/usr/bin/target @@

# Custom fuzzer for network service
for i in {1..1000}; do
  echo "Fuzzing iteration $i"
  python3 fuzzer.py 192.168.100.2 9000
done
```

### Exploit Development

```bash
# Develop exploit against running firmware

# 1. Identify vulnerability through fuzzing
# 2. Debug with GDB to understand crash
qemu-arm -g 1234 -L ./rootfs/ ./vulnerable_binary
gdb-multiarch ./vulnerable_binary
(gdb) target remote :1234

# 3. Craft exploit
# 4. Test against emulated firmware
python3 exploit.py 192.168.100.2
```

## Troubleshooting Common Issues

### Issue: QEMU Boot Failures

**Symptom**: Kernel panic, no output, or boot hang

**Solutions**:
1. Verify architecture matches: `file vmlinux` vs `qemu-system-XXX`
2. Try different machine types: `-M help` to list options
3. Adjust kernel command line: Different console, root device
4. Use `-append "debug loglevel=8"` for more output
5. Try `-append "init=/bin/sh"` to bypass normal init
6. Check for missing DTB file (ARM/AArch64)

### Issue: Network Not Working

**Symptom**: Can't ping or connect to emulated firmware

**Solutions**:
1. Verify TAP interface is up: `ip addr show tap0`
2. Check QEMU network configuration: `-net nic -net tap,ifname=tap0`
3. Configure guest network manually inside QEMU
4. Use user-mode networking instead: `-netdev user,id=net0`
5. Check firewall rules on host

### Issue: GDB Won't Connect

**Symptom**: `Connection refused` or `Remote 'g' packet reply is too long`

**Solutions**:
1. Ensure QEMU started with `-gdb tcp::1234`
2. Use `gdb-multiarch` not regular `gdb`
3. Set architecture in GDB: `set architecture arm`
4. Load correct binary: `file vmlinux` before connecting

### Issue: Binary Crashes Immediately (User-Mode)

**Symptom**: Segfault or illegal instruction

**Solutions**:
1. Check library path: Use `-L ./rootfs/`
2. Verify dependencies: `ldd` inside chroot
3. Try different CPU model: `-cpu cortex-a9`
4. Use QEMU_STRACE for debugging: `QEMU_STRACE=1 qemu-arm ...`

### Issue: Services Won't Start

**Symptom**: Daemon fails to start or exits immediately

**Solutions**:
1. Run in foreground with `-f` flag
2. Check for missing /dev nodes
3. Verify permissions
4. Look at error messages with `strace`
5. Run init scripts manually to identify failure point

## Integration with Other Skills

### With Firmware Extraction

```bash
# 1. Extract firmware (firmware-extraction skill)
binwalk -e firmware.bin

# 2. Emulate extracted firmware (this skill)
qemu-system-arm -kernel zImage ...
```

### With Static Analysis

```bash
# 1. Emulate and identify interesting binaries
nmap -sV 192.168.100.2

# 2. Extract those binaries
cp /mnt/firmware/usr/sbin/httpd ./

# 3. Static analysis (firmware-static-analysis skill)
readelf -h httpd
objdump -d httpd
```

### Full Workflow Example

```bash
# Complete firmware analysis pipeline

# 1. Extract
binwalk -e firmware.bin
cd _firmware.bin.extracted/squashfs-root/

# 2. Quick automated emulation attempt
cd /path/to/FirmAE
sudo ./run.sh -r Brand /path/to/firmware.bin

# 3. If automated fails, manual system emulation
qemu-system-arm -M versatilepb -kernel zImage ...

# 4. Capture network traffic
sudo tcpdump -i tap0 -w capture.pcap &

# 5. Identify services
nmap -p- -A 192.168.100.2

# 6. Static analysis of key binaries
readelf -Ws /usr/sbin/httpd

# 7. Debug specific binary
qemu-arm -g 1234 -L ./rootfs/ /usr/sbin/httpd
gdb-multiarch /usr/sbin/httpd
(gdb) target remote :1234

# 8. Test for vulnerabilities
nikto -h http://192.168.100.2/
sqlmap -u "http://192.168.100.2/login.php"

# 9. Document findings
```

## Best Practices

### Before Starting
1. **Try automated first** - FirmAE saves time on common firmware
2. **Identify architecture correctly** - Prevents many issues
3. **Create workspace** - Organized directory structure
4. **Backup originals** - Keep untouched firmware copies
5. **Document everything** - Record commands and findings

### During Emulation
1. **Start simple** - User-mode before system-mode when possible
2. **Incremental debugging** - Boot to shell first, then full system
3. **Network isolation** - Use separate network namespace or VM
4. **Snapshot frequently** - QEMU snapshots save time
5. **Monitor resources** - QEMU can be resource-intensive

### Security Considerations
1. **Isolated environment** - Don't run untrusted firmware on main system
2. **Network segmentation** - Separate emulation network
3. **Monitor egress** - Watch for unexpected network activity
4. **Limit privileges** - Don't run as root unless necessary
5. **Clean up** - Remove TAP interfaces and iptables rules after

### Efficiency Tips
1. **Use screen/tmux** - Multiple terminals for QEMU, GDB, tcpdump
2. **Script common tasks** - Automate repetitive emulation setups
3. **Keep notes** - Working configurations for different architectures
4. **Build kernel library** - Pre-compiled kernels for common platforms
5. **Learn one architecture well** - Master ARM before moving to MIPS

## Documentation Template

Record emulation setup and findings:

```markdown
# Firmware Emulation Report

**Firmware**: [filename]
**Date**: [date]
**Analyst**: [name]

## Emulation Method

- **Approach**: [Automated/User-Mode/System-Mode]
- **Tool**: [FirmAE/QEMU/Both]
- **Architecture**: [ARM/MIPS/x86/etc.]
- **Success**: [Yes/Partial/No]

## Configuration

### QEMU Command
```
[paste working qemu command]
```

### Network Configuration
- **IP Address**: [guest IP]
- **Gateway**: [gateway IP]
- **Interface**: [tap0/user-mode]

## Services Identified

| Port | Service | Version | Notes |
|------|---------|---------|-------|
| 80   | HTTP    | lighttpd 1.4.x | Web interface |
| 23   | Telnet  | BusyBox | Default creds: admin/admin |

## Findings

### Network Traffic
- [Key observations from packet capture]
- [Credentials found]
- [Suspicious protocols]

### Vulnerabilities
- [CVE-XXXX-XXXX: Description]
- [Command injection in cgi-bin/admin.cgi]

### Debug Notes
- [Breakpoints set]
- [Interesting memory locations]
- [Crash analysis]

## Issues Encountered

- [Problems and solutions]
- [Workarounds used]

## Next Steps

1. [Further testing needed]
2. [Exploit development targets]
3. [Code review recommendations]
```

## Additional References

- **QEMU System-Mode**: `references/qemu-system.md` - Architecture-specific system emulation
- **QEMU User-Mode**: `references/qemu-user.md` - Individual binary emulation
- **GDB Debugging**: `references/gdb-debugging.md` - Advanced debugging techniques
- **Network Analysis**: `references/network-analysis.md` - Traffic capture and protocol analysis
- **Automated Tools**: `references/automated-emulation.md` - Firmadyne and FirmAE complete guide

## Quick Reference Commands

```bash
# User-mode emulation
sudo chroot /mnt/firmware /usr/bin/qemu-arm-static /bin/sh

# System-mode emulation (ARM)
qemu-system-arm -M versatilepb -kernel zImage -drive file=rootfs.ext4,if=sd \
  -append "root=/dev/mmcblk0 console=ttyAMA0" -nographic

# GDB debugging
qemu-arm -g 1234 binary
gdb-multiarch binary → target remote :1234

# Network capture
sudo tcpdump -i tap0 -w capture.pcap

# FirmAE automated
sudo ./run.sh -r Brand firmware.bin

# Check architecture
file binary

# Create TAP interface
sudo tunctl -t tap0 -u $USER
sudo ifconfig tap0 192.168.100.1/24 up
```
