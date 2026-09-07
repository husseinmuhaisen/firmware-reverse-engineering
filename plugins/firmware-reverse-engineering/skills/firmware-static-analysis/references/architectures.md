# Firmware Architecture Reference

Quick reference for common firmware architectures and their characteristics.

## ARM Architectures

### ARM (32-bit)
- **File output**: `ELF 32-bit LSB executable, ARM`
- **Common in**: IoT devices, routers, older embedded systems
- **Endianness**: Usually little-endian (LE)
- **Calling convention**: Arguments in r0-r3, return in r0
- **Common toolchains**: arm-linux-gnueabi, arm-none-eabi

### AArch64 (ARM 64-bit)
- **File output**: `ELF 64-bit LSB executable, ARM aarch64`
- **Common in**: Modern routers, smartphones, high-end embedded systems
- **Endianness**: Usually little-endian (LE)
- **Calling convention**: Arguments in x0-x7, return in x0
- **Common toolchains**: aarch64-linux-gnu

## MIPS Architectures

### MIPS (32-bit)
- **File output**: `ELF 32-bit MSB executable, MIPS`
- **Common in**: Routers (especially older TP-Link, D-Link), network equipment
- **Endianness**: Can be big-endian (MSB) or little-endian (LSB)
- **Calling convention**: Arguments in $a0-$a3, return in $v0
- **Common toolchains**: mips-linux-gnu, mipsel-linux-gnu

### MIPS64
- **File output**: `ELF 64-bit MSB executable, MIPS`
- **Common in**: Enterprise network equipment
- **Endianness**: Usually big-endian
- **Calling convention**: Arguments in $a0-$a7, return in $v0

## x86 Architectures

### x86 (32-bit)
- **File output**: `ELF 32-bit LSB executable, Intel 80386`
- **Common in**: Legacy embedded x86 systems, some IoT gateways
- **Endianness**: Little-endian (LE)
- **Calling convention**: Arguments on stack (cdecl) or registers (fastcall), return in eax
- **Common toolchains**: gcc, clang

### x86-64 (AMD64)
- **File output**: `ELF 64-bit LSB executable, x86-64`
- **Common in**: Modern routers, NAS devices, industrial PCs
- **Endianness**: Little-endian (LE)
- **Calling convention**: Arguments in rdi, rsi, rdx, rcx, r8, r9; return in rax
- **Common toolchains**: gcc, clang

## RISC-V Architectures

### RISC-V (32-bit)
- **File output**: `ELF 32-bit LSB executable, UCB RISC-V`
- **Common in**: Newer IoT devices, embedded controllers
- **Endianness**: Little-endian (LE)
- **Calling convention**: Arguments in a0-a7, return in a0
- **Common toolchains**: riscv32-unknown-elf-gcc

### RISC-V (64-bit)
- **File output**: `ELF 64-bit LSB executable, UCB RISC-V`
- **Common in**: Modern embedded systems, some IoT devices
- **Endianness**: Little-endian (LE)
- **Calling convention**: Arguments in a0-a7, return in a0
- **Common toolchains**: riscv64-unknown-elf-gcc

## PowerPC Architectures

### PowerPC (32-bit)
- **File output**: `ELF 32-bit MSB executable, PowerPC`
- **Common in**: Network switches, some routers, embedded systems
- **Endianness**: Big-endian (MSB)
- **Calling convention**: Arguments in r3-r10, return in r3
- **Common toolchains**: powerpc-linux-gnu-gcc

## Architecture Detection Tips

- **Endianness matters**: LSB = Little-endian, MSB = Big-endian
- **Bitness**: 32-bit vs 64-bit affects address sizes and register widths
- **Cross-architecture**: Some devices use different architectures for bootloader vs main firmware
- **Toolchain hints**: Look for GCC/Clang version strings with target triplets (e.g., `arm-linux-gnueabihf-gcc`)
