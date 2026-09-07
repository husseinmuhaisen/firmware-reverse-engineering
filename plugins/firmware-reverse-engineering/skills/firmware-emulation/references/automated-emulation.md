# Automated Firmware Emulation Reference

Guide to using Firmadyne and FirmAE for automated firmware analysis.

## Firmadyne Overview

Firmadyne is an automated framework for emulating and analyzing Linux-based firmware. It's particularly effective for router and IoT device firmware.

**Strengths:**
- Automated extraction and emulation
- Large database of pre-analyzed firmware
- Network emulation built-in
- Web interface for interaction

**Limitations:**
- Primarily supports Linux-based firmware
- May struggle with heavily customized kernels
- Not all firmware will boot successfully
- Requires significant setup

## Installation

### Prerequisites

```bash
# Install dependencies
sudo apt-get install busybox-static fakeroot git dmsetup kpartx netcat-openbsd nmap python3-psycopg2 python3-pip snmp uml-utilities util-linux vlan

# Install PostgreSQL
sudo apt-get install postgresql

# Install binwalk
sudo apt-get install binwalk

# Python dependencies
pip3 install python-magic
```

### Firmadyne Setup

```bash
# Clone Firmadyne
git clone --recursive https://github.com/firmadyne/firmadyne.git
cd firmadyne

# Download pre-built binaries
cd ./binaries
wget https://github.com/firmadyne/binaries/releases/download/v1.0/binaries.tar.gz
tar -xzvf binaries.tar.gz
cd ..

# Build database
sudo -u postgres createuser -P firmadyne  # Password: firmadyne
sudo -u postgres createdb -O firmadyne firmware

# Initialize database
sudo -u postgres psql -d firmware < ./database/schema

# Configure settings
cp firmadyne.config.example firmadyne.config
# Edit firmadyne.config:
# - Set FIRMWARE_DIR to absolute path
# - Configure PostgreSQL credentials
```

### FirmAE Setup (Improved Firmadyne)

FirmAE is an enhanced version of Firmadyne with better success rates.

```bash
# Clone FirmAE
git clone https://github.com/pr0v3rbs/FirmAE
cd FirmAE

# Install
./download.sh
sudo ./install.sh

# The installer will:
# - Setup PostgreSQL database
# - Install QEMU and dependencies
# - Configure network interfaces
```

## Using Firmadyne

### Basic Analysis Workflow

```bash
cd /path/to/firmadyne

# 1. Extract firmware
./sources/extractor/extractor.py -b Netgear -sql 127.0.0.1 -np -nk "firmware.bin" images

# Parameters:
# -b BRAND: Brand name (Netgear, TP-Link, etc.)
# -sql: PostgreSQL host
# -np: No password for PostgreSQL
# -nk: Don't check kernel version
# images: Output directory

# This creates database entry and extracts filesystem
# Note the IMAGE_ID returned (e.g., 1)

# 2. Identify architecture
./scripts/getArch.sh ./images/1.tar.gz

# 3. Load filesystem into database
./scripts/tar2db.py -i 1 -f ./images/1.tar.gz

# 4. Create QEMU image
sudo ./scripts/makeImage.sh 1

# 5. Infer network configuration
./scripts/inferNetwork.sh 1

# 6. Run emulation
sudo ./scratch/1/run.sh
```

### Monitor Emulation

```bash
# In another terminal, check if firmware booted
# Wait ~60 seconds after starting run.sh

# Check for network
sudo ./analyses/snmpwalk.sh 1

# Web interface check
./analyses/webAccess.sh 1 8080  # Port depends on firmware

# Try to connect
curl http://192.168.1.1/  # Default IP, varies by firmware
```

### Debugging Failed Emulation

```bash
# Check console output
sudo ./scratch/1/run.sh
# Look for kernel panics or boot errors

# Try different kernel
# Edit ./scratch/1/run.sh
# Change: -kernel /path/to/different/vmlinux

# Manual network configuration
# After boot, inside QEMU console:
ifconfig eth0 192.168.1.1 netmask 255.255.255.0 up
route add default gw 192.168.1.254

# Check what's running
ps aux
netstat -tulpn
```

## Using FirmAE

FirmAE simplifies the process significantly.

### Basic Usage

```bash
cd /path/to/FirmAE

# Run automated analysis
sudo ./run.sh -r Netgear firmware.bin

# Parameters:
# -r BRAND: Router brand
# -c: Continue from previous run
# -a ARCH: Specify architecture (arm, mips, mipsel, x86)
# -d: Debug mode (more verbose)
```

### FirmAE Workflow

```bash
# 1. Extract and analyze
sudo ./run.sh -r Netgear firmware.bin

# FirmAE will automatically:
# - Extract filesystem
# - Identify architecture
# - Create QEMU image
# - Infer network configuration
# - Start emulation
# - Run analyses (web, snmp, network services)

# 2. Check results
# FirmAE creates work directory in ./scratch/<IMAGE_ID>/

# 3. Access running firmware
# Check output for IP address and open ports

# Example: Web interface at http://192.168.0.1
curl http://192.168.0.1

# 4. Interactive access
# FirmAE may provide shell access
```

### Advanced FirmAE Options

```bash
# Continue from failed run
sudo ./run.sh -c <IMAGE_ID>

# Specify architecture
sudo ./run.sh -a arm -r Netgear firmware.bin

# Debug mode
sudo ./run.sh -d -r Netgear firmware.bin

# Skip analysis phases
sudo ./run.sh --skip-analysis -r Netgear firmware.bin
```

## Analyzing Running Firmware

### Network Service Enumeration

```bash
# Nmap scan
nmap -p- -A 192.168.0.1

# Specific service checks
nc -v 192.168.0.1 80    # HTTP
nc -v 192.168.0.1 23    # Telnet
nc -v 192.168.0.1 22    # SSH
nc -v 192.168.0.1 21    # FTP
```

### Web Interface Analysis

```bash
# Burp Suite proxy
# Configure browser to proxy through Burp
# Access http://192.168.0.1

# Or use curl
curl -v http://192.168.0.1/
curl http://192.168.0.1/cgi-bin/status.cgi

# Directory brute-force
dirb http://192.168.0.1 /usr/share/dirb/wordlists/common.txt

# Or gobuster
gobuster dir -u http://192.168.0.1 -w /usr/share/wordlists/dirb/common.txt
```

### Shell Access

```bash
# If telnet is open
telnet 192.168.0.1

# Common default credentials
# admin:admin
# admin:password
# root:root
# admin:

# If SSH is available
ssh admin@192.168.0.1

# Backdoor checks
# Some firmware has hidden telnet
telnet 192.168.0.1 9999
telnet 192.168.0.1 5555
```

### Filesystem Exploration

```bash
# If you have shell access
ls -la /
ls -la /etc
ls -la /www

# Find SUID binaries
find / -perm -4000 -ls 2>/dev/null

# Check cron jobs
cat /etc/crontabs/*
cat /var/spool/cron/*

# Running processes
ps aux

# Network connections
netstat -tulpn
```

## Manual Intervention When Automation Fails

### Custom Kernel Compilation

```bash
# If Firmadyne/FirmAE kernel doesn't work
# Get kernel source matching firmware version

# Check firmware kernel version
strings vmlinux | grep "Linux version"

# Download matching kernel
wget https://cdn.kernel.org/pub/linux/kernel/v4.x/linux-4.14.tar.xz

# Use firmware's config if available
cp /path/to/extracted/.config linux-4.14/.config

# Or use Firmadyne's config as base
cp /path/to/firmadyne/kernel/config/config.arm linux-4.14/.config

# Enable required drivers
make ARCH=arm menuconfig

# Compile
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabi- -j$(nproc)

# Replace kernel in run.sh
# Edit scratch/<ID>/run.sh: -kernel /path/to/new/vmlinux
```

### Custom Network Configuration

```bash
# If inferNetwork.sh fails
# Manually edit scratch/<ID>/run.sh

# Set static networking
-append "root=/dev/sda1 console=ttyS0 nandsim.parts=64,64,64,64,64,64,64,64,64,64 rdinit=/firmadyne/preInit.sh rw debug print-fatal-signals=1 user_debug=31 firmadyne.syscall=0 ip=192.168.0.1::192.168.0.254:255.255.255.0"

# Adjust IP/gateway/netmask as needed
```

### Custom Init Scripts

```bash
# Firmadyne uses preInit.sh to setup environment
# Located in firmware at /firmadyne/preInit.sh

# To customize, modify before creating image
# Edit images/<ID>.tar.gz contents

# Example modifications:
# - Force specific network config
# - Skip problematic init scripts
# - Add debugging
```

## Database Queries

Firmadyne stores analysis results in PostgreSQL.

```bash
# Connect to database
psql -U firmadyne -d firmware -h 127.0.0.1

# Useful queries:

# List all firmware images
SELECT * FROM image;

# Get firmware details
SELECT * FROM image WHERE id = 1;

# List extracted files for firmware
SELECT * FROM object_to_image WHERE iid = 1;

# Find firmware by brand
SELECT * FROM brand WHERE name LIKE '%Netgear%';

# Search for specific files across all firmware
SELECT DISTINCT(filename) FROM object WHERE filename LIKE '%passwd%';
```

## Automated Vulnerability Testing

### Run Security Scans

```bash
# After firmware is running

# Nikto web vulnerability scan
nikto -h http://192.168.0.1

# Nmap vulnerability scripts
nmap --script vuln -p 80,443,23,21 192.168.0.1

# SQLmap for SQL injection
sqlmap -u "http://192.168.0.1/login.php" --forms --batch

# Check for common vulns
curl http://192.168.0.1/../../etc/passwd  # Directory traversal
curl http://192.168.0.1/cgi-bin/test.cgi?cmd=ls  # Command injection
```

### Fuzzing Network Services

```bash
# Telnet fuzzing
for i in {1..1000}; do
    echo "$i: $(head -c 1000 /dev/urandom | base64)" | nc 192.168.0.1 23
done

# HTTP fuzzing with wfuzz
wfuzz -c -z file,/usr/share/wordlists/wfuzz/general/common.txt http://192.168.0.1/FUZZ

# Custom protocol fuzzing with Boofuzz
python3 boofuzz_script.py 192.168.0.1 9000
```

## Troubleshooting Common Issues

### Issue: Extraction fails

```bash
# Try manual extraction with binwalk
binwalk -e firmware.bin

# Or use firmware-extraction skill
# Then manually create tar.gz for Firmadyne
cd _firmware.bin.extracted/squashfs-root
tar czf ../../image.tar.gz .
```

### Issue: Architecture detection wrong

```bash
# Manually specify architecture
# Edit database entry
psql -U firmadyne -d firmware -h 127.0.0.1
UPDATE image SET arch = 'armel' WHERE id = 1;

# Or for FirmAE
./run.sh -a arm firmware.bin
```

### Issue: Firmware won't boot

```bash
# Check kernel messages
sudo ./scratch/1/run.sh | tee boot.log

# Common fixes:
# 1. Try different kernel (mips, mipsel, armel, armhf)
# 2. Adjust kernel command line in run.sh
# 3. Check for missing /dev nodes
# 4. Verify init system (sysvinit, busybox init)

# Create minimal working image
# Sometimes helps to strip firmware to essentials
```

### Issue: Network not working

```bash
# Check network config in run.sh
cat scratch/1/run.sh | grep -- -net

# Manually configure inside QEMU
# Get to console and run:
ifconfig eth0 192.168.0.1 netmask 255.255.255.0 up
route add default gw 192.168.0.254

# On host, verify TAP interface
ip addr show tap1_0
```

### Issue: Services not starting

```bash
# Get console access
# Edit run.sh to boot to shell
-append "... init=/bin/sh"

# Check init scripts
ls /etc/init.d/
ls /etc/rc.d/

# Run services manually
/etc/init.d/httpd start
/usr/sbin/telnetd
```

## Performance Optimization

```bash
# Allocate more memory in run.sh
-m 512M  # Increase from default 256M

# Use KVM if host and guest arch match
# Edit run.sh: Add -enable-kvm (x86/x64 only)

# Reduce unnecessary services
# Inside firmware, disable unneeded daemons
```

## Integration with Manual Analysis

### Extract running filesystem

```bash
# While firmware is running
# From host, mount QEMU image
sudo kpartx -av scratch/1/image.raw
sudo mount /dev/mapper/loop0p1 /mnt

# Copy filesystem
sudo cp -a /mnt/* /tmp/running_firmware/

# Unmount
sudo umount /mnt
sudo kpartx -dv scratch/1/image.raw
```

### Combine with static analysis

```bash
# 1. Boot with Firmadyne/FirmAE
sudo ./run.sh -r Brand firmware.bin

# 2. Identify interesting binaries from network scan
nmap -sV 192.168.0.1

# 3. Extract and analyze those binaries
# Use firmware-static-analysis skill on /www/cgi-bin/admin.cgi

# 4. Use findings to test running firmware
curl http://192.168.0.1/cgi-bin/admin.cgi?exploit
```

## Best Practices

1. **Start with FirmAE** - Better success rate than Firmadyne
2. **Save work directories** - Don't delete scratch/<ID> until done
3. **Document IDs** - Keep track of which image ID is which firmware
4. **Network isolation** - Use separate network namespace or VM for emulation
5. **Snapshot before testing** - QEMU allows snapshots, use them
6. **Baseline behavior** - Understand normal operation before testing
7. **Check logs** - Firmadyne/FirmAE logs contain useful debug info
8. **Manual fallback** - Be ready to switch to manual QEMU when automation fails
9. **Database backups** - Backup PostgreSQL database regularly
10. **Version control** - Track modifications to run.sh and configs

## Comparison: Firmadyne vs FirmAE vs Manual

| Aspect | Firmadyne | FirmAE | Manual QEMU |
|--------|-----------|--------|-------------|
| Setup | Complex | Moderate | Simple |
| Success Rate | 60-70% | 80-90% | 95%+ (with effort) |
| Automation | High | Very High | Low |
| Flexibility | Low | Moderate | Very High |
| Learning Curve | Moderate | Low | High |
| Debug Info | Limited | Good | Excellent |
| Best For | Bulk analysis | Quick testing | Deep analysis |

**Recommendation:** Start with FirmAE for quick wins, fall back to manual QEMU for difficult cases.
