# QEMU System-Mode Emulation Reference

Complete guide to full-system firmware emulation with QEMU.

## Overview

System-mode emulation runs the complete firmware stack: bootloader, kernel, and root filesystem. This provides the most authentic environment but is more complex to configure.

## Architecture-Specific QEMU Machines

### ARM (32-bit)

**Common machines:**
```bash
# Versatile Platform Board (most compatible)
qemu-system-arm -M versatilepb

# Versatile Express (Cortex-A9)
qemu-system-arm -M vexpress-a9

# Versatile Express (Cortex-A15)
qemu-system-arm -M vexpress-a15

# List all available ARM machines
qemu-system-arm -M help
```

**Typical firmware boot:**
```bash
qemu-system-arm \
  -M versatilepb \
  -kernel zImage \
  -dtb device-tree.dtb \
  -drive file=rootfs.ext4,if=sd,format=raw \
  -append "root=/dev/mmcblk0 console=ttyAMA0" \
  -nographic \
  -net nic -net tap,ifname=tap0,script=no
```

### AArch64 (ARM 64-bit)

**Common machines:**
```bash
# Virtual machine (most flexible)
qemu-system-aarch64 -M virt

# Versatile Express
qemu-system-aarch64 -M vexpress-a15

# Raspberry Pi 3
qemu-system-aarch64 -M raspi3b
```

**Typical firmware boot:**
```bash
qemu-system-aarch64 \
  -M virt \
  -cpu cortex-a57 \
  -kernel Image \
  -append "root=/dev/vda console=ttyAMA0" \
  -drive file=rootfs.ext4,if=virtio,format=raw \
  -netdev user,id=net0 -device virtio-net-device,netdev=net0 \
  -nographic
```

### MIPS (Big-Endian)

**Common machines:**
```bash
# Malta board (most common for routers)
qemu-system-mips -M malta

# List available MIPS machines
qemu-system-mips -M help
```

**Typical firmware boot:**
```bash
qemu-system-mips \
  -M malta \
  -kernel vmlinux \
  -hda rootfs.ext4 \
  -append "root=/dev/sda console=ttyS0" \
  -nographic \
  -net nic -net tap,ifname=tap0,script=no
```

### MIPSEL (Little-Endian)

```bash
qemu-system-mipsel \
  -M malta \
  -kernel vmlinux \
  -hda rootfs.ext4 \
  -append "root=/dev/sda console=ttyS0" \
  -nographic
```

### x86/x86_64

```bash
# 32-bit
qemu-system-i386 \
  -kernel bzImage \
  -hda rootfs.ext4 \
  -append "root=/dev/sda console=ttyS0" \
  -nographic

# 64-bit
qemu-system-x86_64 \
  -kernel bzImage \
  -hda rootfs.ext4 \
  -append "root=/dev/sda1 console=ttyS0" \
  -enable-kvm \
  -nographic
```

### PowerPC

```bash
qemu-system-ppc \
  -M mac99 \
  -kernel vmlinux \
  -hda rootfs.ext4 \
  -append "root=/dev/hda console=ttyS0" \
  -nographic
```

## Boot Process Components

### 1. Kernel

**Locate kernel in extracted firmware:**
```bash
# Search for kernel image
find extracted/ -name "vmlinux" -o -name "zImage" -o -name "uImage" -o -name "Image"

# Check if compressed
file vmlinux
binwalk vmlinux

# Extract kernel from uImage
dd if=uImage of=kernel.bin bs=64 skip=1
```

**Decompress kernel if needed:**
```bash
# LZMA
unlzma kernel.lzma

# Gzip
gunzip kernel.gz

# If embedded in uImage
binwalk -e uImage
```

### 2. Device Tree Blob (DTB)

**Required for ARM/AArch64, optional for others.**

```bash
# Find DTB in firmware
find extracted/ -name "*.dtb"

# Or extract from kernel if embedded
binwalk -e zImage  # Look for DTB signature

# Decompile DTB to DTS (text format) for inspection
dtc -I dtb -O dts -o device.dts device.dtb

# Modify and recompile
dtc -I dts -O dtb -o device_modified.dtb device.dts
```

**Common DTB modifications:**
- Change console device
- Adjust memory size
- Modify peripheral addresses

### 3. Root Filesystem

**Prepare filesystem for QEMU:**
```bash
# If extracted as directory, create ext4 image
dd if=/dev/zero of=rootfs.ext4 bs=1M count=256
mkfs.ext4 rootfs.ext4
mkdir /tmp/mnt
sudo mount -o loop rootfs.ext4 /tmp/mnt
sudo cp -a squashfs-root/* /tmp/mnt/
sudo umount /tmp/mnt

# Alternative: Use existing SquashFS directly
# (Some QEMU configs support SquashFS as root)
```

**Filesystem formats QEMU supports:**
- ext2/ext3/ext4 (recommended)
- SquashFS (read-only, needs initramfs setup)
- JFFS2/UBIFS (requires MTD emulation, advanced)

## Kernel Command Line Arguments

The `-append` parameter is critical for boot success.

### Essential Arguments

```bash
# Root device (adjust based on your storage type)
root=/dev/sda        # IDE/SATA disk
root=/dev/vda        # VirtIO disk
root=/dev/mmcblk0    # SD card
root=/dev/mtdblock0  # MTD (flash)

# Console output
console=ttyS0        # Serial console (most common)
console=ttyAMA0      # ARM PL011 UART
console=tty0         # VGA console

# Root filesystem type
rootfstype=ext4
rootfstype=squashfs

# Additional useful arguments
rw                   # Mount root as read-write
init=/bin/sh         # Override init (useful for debugging)
single               # Single-user mode
debug                # Enable kernel debug messages
loglevel=8           # Maximum kernel logging
```

### Example complete append strings:

```bash
# Standard ARM
-append "root=/dev/mmcblk0 rootfstype=ext4 rw console=ttyAMA0 loglevel=8"

# MIPS router
-append "root=/dev/sda rootfstype=squashfs console=ttyS0 debug"

# x86 with init override for debugging
-append "root=/dev/sda1 rw console=ttyS0 init=/bin/sh"
```

## Network Configuration

### TAP Interface Setup

**Create TAP interface (requires root):**
```bash
# Install bridge utilities
sudo apt-get install bridge-utils uml-utilities

# Create TAP interface
sudo tunctl -t tap0 -u $USER
sudo ifconfig tap0 192.168.100.1 netmask 255.255.255.0 up

# Enable forwarding
sudo sysctl -w net.ipv4.ip_forward=1

# Setup NAT for internet access
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -A FORWARD -i tap0 -o eth0 -j ACCEPT
sudo iptables -A FORWARD -i eth0 -o tap0 -m state --state RELATED,ESTABLISHED -j ACCEPT
```

**QEMU network options with TAP:**
```bash
# Basic TAP
-net nic -net tap,ifname=tap0,script=no,downscript=no

# With MAC address specification
-net nic,macaddr=52:54:00:12:34:56 -net tap,ifname=tap0,script=no

# VirtIO network (faster)
-netdev tap,id=net0,ifname=tap0,script=no -device virtio-net-device,netdev=net0
```

### User-Mode Networking (No Root Required)

```bash
# Basic user networking (easiest)
-netdev user,id=net0 -device virtio-net-device,netdev=net0

# With port forwarding (host:guest)
-netdev user,id=net0,hostfwd=tcp::8080-:80,hostfwd=tcp::2222-:22 \
-device virtio-net-device,netdev=net0

# Multiple NICs
-netdev user,id=net0 -device virtio-net-device,netdev=net0 \
-netdev user,id=net1 -device virtio-net-device,netdev=net1
```

**Configure guest networking after boot:**
```bash
# Inside QEMU guest
ifconfig eth0 10.0.2.15 netmask 255.255.255.0
route add default gw 10.0.2.2
echo "nameserver 10.0.2.3" > /etc/resolv.conf
```

## Memory and CPU Configuration

```bash
# Memory size
-m 256M              # 256 MB
-m 1G                # 1 GB

# CPU cores
-smp 2               # 2 cores
-smp cores=4         # 4 cores

# CPU type (important for compatibility)
-cpu cortex-a9       # ARM Cortex-A9
-cpu cortex-a57      # AArch64 Cortex-A57
-cpu 24Kf            # MIPS 24Kf
```

## Storage Options

### IDE/SATA Disk
```bash
-hda rootfs.ext4
-drive file=rootfs.ext4,format=raw,index=0,media=disk
```

### VirtIO (Faster)
```bash
-drive file=rootfs.ext4,if=virtio,format=raw
```

### SD Card (ARM)
```bash
-sd rootfs.ext4
-drive file=rootfs.ext4,if=sd,format=raw
```

### MTD (Flash) - Advanced
```bash
# Requires MTD support in kernel
-mtdblock file=rootfs.jffs2
```

## Display Options

```bash
# No graphics (serial only)
-nographic

# VGA display
-vga std

# Redirect serial to stdio
-serial stdio

# Redirect serial to TCP
-serial tcp::4444,server,nowait

# Multiple serial ports
-serial stdio -serial tcp::4444,server,nowait
```

## Debugging Options

### GDB Server

```bash
# Start QEMU with GDB server on port 1234
-gdb tcp::1234 -S

# Alternative syntax
-s -S
# -s: shorthand for -gdb tcp::1234
# -S: Pause at startup (wait for GDB)
```

**Connect with GDB:**
```bash
gdb-multiarch vmlinux
(gdb) target remote :1234
(gdb) continue
```

### Monitor Console

```bash
# Enable QEMU monitor
-monitor stdio

# Or on separate window
-monitor telnet::4444,server,nowait

# Then connect
telnet localhost 4444
```

**Useful monitor commands:**
```
info registers       # Show CPU registers
info mem             # Show memory mappings
info mtree           # Memory tree
savevm snapshot1     # Save VM state
loadvm snapshot1     # Restore VM state
quit                 # Exit QEMU
```

## Common Boot Issues & Solutions

### Issue: Kernel panic - not syncing: VFS: Unable to mount root fs

**Causes:**
- Wrong root device in `-append`
- Filesystem type mismatch
- Corrupted filesystem

**Solutions:**
```bash
# Try different root devices
-append "root=/dev/sda ..."   # Then try /dev/vda, /dev/mmcblk0, etc.

# Specify filesystem type explicitly
-append "root=/dev/sda rootfstype=ext4 ..."

# Use init=/bin/sh to bypass normal init
-append "root=/dev/sda init=/bin/sh ..."
```

### Issue: No output / black screen

**Solutions:**
```bash
# Ensure -nographic is set
-nographic

# Correct console device
-append "console=ttyS0 ..."      # Try ttyAMA0, ttyS1, etc.

# Enable kernel debug
-append "debug loglevel=8 earlyprintk ..."
```

### Issue: Kernel loads but nothing happens

**Solutions:**
```bash
# Add earlyprintk
-append "earlyprintk console=ttyS0 ..."

# Try simpler init
-append "init=/bin/sh ..."

# Check if init exists in filesystem
# Inside rootfs: ls -la /sbin/init /bin/init
```

### Issue: Wrong machine type errors

**Solutions:**
```bash
# List available machines
qemu-system-arm -M help

# Try more compatible machines
-M versatilepb    # Instead of specific board
-M virt           # Generic virtual machine
```

### Issue: Network not working

**Solutions:**
```bash
# Use user-mode networking first
-netdev user,id=net0 -device virtio-net-device,netdev=net0

# Check guest network config
# Inside guest: ifconfig -a, dmesg | grep eth

# Try legacy network syntax
-net nic -net user
```

## Advanced Techniques

### Snapshot and Restore

```bash
# Boot QEMU
qemu-system-arm -M versatilepb ... -monitor stdio

# In monitor console
(qemu) savevm boot_complete

# Later, restore from snapshot
# Add to command line: -loadvm boot_complete
```

### Custom Kernel Compilation

Sometimes firmware kernel won't boot. Compile a compatible kernel:

```bash
# Get kernel source matching firmware version
wget https://cdn.kernel.org/pub/linux/kernel/v4.x/linux-4.14.tar.xz
tar xf linux-4.14.tar.xz
cd linux-4.14

# Use firmware's kernel config if available
cp /path/to/extracted/.config .config

# Or start from arch defaults
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabi- versatile_defconfig

# Enable required options
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabi- menuconfig
# Enable: VirtIO, networking, ext4, etc.

# Compile
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabi- -j$(nproc)

# Use newly compiled kernel
qemu-system-arm -kernel arch/arm/boot/zImage ...
```

### Combining with Chroot

For partial emulation when full system emulation fails:

```bash
# Mount rootfs
sudo mount -o loop rootfs.ext4 /mnt

# Copy qemu-arm-static for user-mode
sudo cp /usr/bin/qemu-arm-static /mnt/usr/bin/

# Chroot and execute
sudo chroot /mnt /usr/bin/qemu-arm-static /bin/sh
```

## Performance Optimization

```bash
# Enable KVM (x86/x64 only)
-enable-kvm

# Use VirtIO devices (faster than IDE)
-drive file=rootfs.ext4,if=virtio
-netdev user,id=net0 -device virtio-net-device,netdev=net0

# Allocate more resources
-m 1G -smp 4

# Use raw disk format (faster than qcow2)
format=raw
```

## Complete Example Recipes

### ARM Router Firmware
```bash
qemu-system-arm \
  -M versatilepb \
  -kernel zImage \
  -dtb versatile-pb.dtb \
  -drive file=rootfs.ext4,if=sd,format=raw \
  -append "root=/dev/mmcblk0 console=ttyAMA0 rw" \
  -net nic,macaddr=52:54:00:12:34:56 \
  -net tap,ifname=tap0,script=no \
  -nographic \
  -m 256M
```

### MIPS Router Firmware
```bash
qemu-system-mips \
  -M malta \
  -kernel vmlinux \
  -hda rootfs.ext4 \
  -append "root=/dev/sda console=ttyS0 nokaslr" \
  -netdev user,id=net0,hostfwd=tcp::8080-:80 \
  -device e1000,netdev=net0 \
  -nographic \
  -m 256M
```

### AArch64 Modern Device
```bash
qemu-system-aarch64 \
  -M virt \
  -cpu cortex-a57 \
  -m 1G \
  -smp 2 \
  -kernel Image \
  -append "root=/dev/vda console=ttyAMA0" \
  -drive file=rootfs.ext4,if=virtio,format=raw \
  -netdev user,id=net0,hostfwd=tcp::2222-:22 \
  -device virtio-net-device,netdev=net0 \
  -nographic \
  -gdb tcp::1234 -S
```
