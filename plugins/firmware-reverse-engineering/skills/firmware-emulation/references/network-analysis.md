# Network Analysis Reference for Firmware Emulation

Comprehensive guide to capturing, analyzing, and manipulating network traffic from emulated firmware.

## Network Traffic Capture

### Basic Packet Capture with tcpdump

```bash
# Capture all traffic on tap0 interface
sudo tcpdump -i tap0 -w capture.pcap

# Capture with filters
sudo tcpdump -i tap0 port 80 -w http.pcap
sudo tcpdump -i tap0 'tcp port 23' -w telnet.pcap
sudo tcpdump -i tap0 host 10.0.2.15 -w firmware.pcap

# Real-time display
sudo tcpdump -i tap0 -n -v

# Capture only specific protocols
sudo tcpdump -i tap0 udp -w udp.pcap
sudo tcpdump -i tap0 icmp -w icmp.pcap
```

### Wireshark Capture

```bash
# Start Wireshark on tap interface
sudo wireshark -i tap0 -k

# Or capture with tshark (CLI)
sudo tshark -i tap0 -w capture.pcap

# With display filter
sudo tshark -i tap0 -f "port 80 or port 443" -w web.pcap
```

### Capture from QEMU User-Mode

```bash
# User-mode networking is NATed, capture on host interface
# Find QEMU process network activity
sudo tcpdump -i lo port 1234 -w qemu.pcap

# Or capture all loopback
sudo tcpdump -i lo -w loopback.pcap
```

## Protocol Analysis

### HTTP/HTTPS Traffic

**Capture HTTP:**
```bash
# Filter HTTP traffic
sudo tcpdump -i tap0 'tcp port 80' -A -s 0 -w http.pcap

# Extract HTTP requests in real-time
sudo tcpdump -i tap0 -n -A 'tcp port 80' | grep -E 'GET|POST|HTTP'
```

**Analyze in Wireshark:**
1. Open capture.pcap
2. Filter: `http`
3. Right-click packet → Follow → HTTP Stream
4. Export Objects → HTTP to extract files

**Extract credentials:**
```bash
# With tshark
tshark -r capture.pcap -Y "http.request.method == POST" -T fields -e http.file_data

# Look for login attempts
tshark -r capture.pcap -Y "http.request.uri contains login" -T fields -e http.request.uri -e ip.src
```

### HTTPS/TLS Traffic

**Decrypt TLS (if you have keys):**
```bash
# Set SSLKEYLOGFILE in firmware environment
# Inside QEMU/chroot:
export SSLKEYLOGFILE=/tmp/sslkeys.log

# Then in Wireshark:
# Edit → Preferences → Protocols → TLS
# (Pre)-Master-Secret log filename: /tmp/sslkeys.log
```

**Analyze without decryption:**
```bash
# View TLS handshake
tshark -r capture.pcap -Y "tls.handshake"

# Extract server certificates
tshark -r capture.pcap -Y "tls.handshake.certificate" -T fields -e tls.handshake.certificate > cert.der
openssl x509 -inform DER -in cert.der -text
```

### DNS Traffic

```bash
# Capture DNS queries
sudo tcpdump -i tap0 port 53 -w dns.pcap

# Analyze DNS
tshark -r dns.pcap -Y "dns.qry.name"

# Extract all DNS queries
tshark -r capture.pcap -Y "dns.flags.response == 0" -T fields -e dns.qry.name | sort -u
```

### Telnet/FTP (Cleartext Protocols)

```bash
# Capture telnet
sudo tcpdump -i tap0 port 23 -A -w telnet.pcap

# Extract passwords
tshark -r telnet.pcap -T fields -e data.text | grep -i password

# Follow FTP session
tshark -r capture.pcap -Y "ftp" -z follow,tcp,ascii,0
```

### Custom/Proprietary Protocols

```bash
# Capture unknown protocol on specific port
sudo tcpdump -i tap0 port 9000 -w unknown.pcap -s 65535

# Hex dump for analysis
tcpdump -r unknown.pcap -X | less

# Extract payload data
tshark -r unknown.pcap -T fields -e data.data > payload.hex

# Convert to binary
xxd -r -p payload.hex > payload.bin
```

## Man-in-the-Middle (MITM) Attacks

### Setup MITM Proxy

**Using mitmproxy:**
```bash
# Install mitmproxy
pip3 install mitmproxy

# Start transparent proxy
sudo mitmproxy --mode transparent --showhost

# Configure iptables to redirect traffic
sudo iptables -t nat -A PREROUTING -i tap0 -p tcp --dport 80 -j REDIRECT --to-port 8080
sudo iptables -t nat -A PREROUTING -i tap0 -p tcp --dport 443 -j REDIRECT --to-port 8080

# Inside firmware, traffic will go through mitmproxy
# View/modify requests in real-time
```

**Using Burp Suite:**
```bash
# Configure Burp to listen on tap interface
# Burp → Proxy → Options → Add proxy listener
# Bind to address: tap0 IP (e.g., 192.168.100.1)
# Port: 8080

# Redirect firmware traffic
sudo iptables -t nat -A PREROUTING -i tap0 -p tcp --dport 80 -j REDIRECT --to-port 8080
sudo iptables -t nat -A PREROUTING -i tap0 -p tcp --dport 443 -j REDIRECT --to-port 8080

# For HTTPS, import Burp CA cert into firmware
```

### ARP Spoofing (for multiple emulated devices)

```bash
# If running multiple QEMU instances on bridge
# Use arpspoof to intercept traffic between them

# Install dsniff
sudo apt-get install dsniff

# Spoof ARP
sudo arpspoof -i br0 -t 192.168.100.10 192.168.100.1
sudo arpspoof -i br0 -t 192.168.100.1 192.168.100.10

# Enable forwarding
sudo sysctl -w net.ipv4.ip_forward=1

# Capture traffic
sudo tcpdump -i br0 -w mitm.pcap
```

### SSL/TLS Interception

```bash
# Install custom CA certificate in firmware

# 1. Generate CA cert (or use mitmproxy's)
openssl genrsa -out ca.key 2048
openssl req -new -x509 -key ca.key -out ca.crt -days 365

# 2. Copy to firmware rootfs
sudo cp ca.crt /mnt/firmware/etc/ssl/certs/
sudo chroot /mnt/firmware /usr/bin/qemu-arm-static /usr/sbin/update-ca-certificates

# 3. Run mitmproxy with custom CA
mitmproxy --set confdir=~/.mitmproxy --mode transparent
```

## Traffic Manipulation

### Modify Packets with Scapy

```python
#!/usr/bin/env python3
from scapy.all import *

def packet_callback(packet):
    """Modify packets on the fly"""
    if packet.haslayer(TCP) and packet.haslayer(Raw):
        payload = packet[Raw].load
        
        # Example: Replace command
        if b"vulnerable_cmd" in payload:
            new_payload = payload.replace(b"vulnerable_cmd", b"safe_command")
            packet[Raw].load = new_payload
            
            # Recalculate checksums
            del packet[IP].chksum
            del packet[TCP].chksum
            
            # Send modified packet
            send(packet)
            return
    
    # Forward unmodified packets
    send(packet)

# Sniff and modify
sniff(iface="tap0", prn=packet_callback)
```

### Replay Attacks

```bash
# Capture authentication sequence
sudo tcpdump -i tap0 port 80 -w auth.pcap

# Replay packets
tcpreplay -i tap0 auth.pcap

# Or with specific timing
tcpreplay -i tap0 --mbps=10 auth.pcap

# Replay with modifications (use scapy)
```

### Fuzzing Network Protocols

```python
#!/usr/bin/env python3
from scapy.all import *
import random

def fuzz_protocol(target_ip, target_port):
    """Fuzz custom protocol"""
    for i in range(1000):
        # Generate random payload
        payload = bytes([random.randint(0, 255) for _ in range(100)])
        
        # Send to target
        pkt = IP(dst=target_ip)/TCP(dport=target_port)/Raw(load=payload)
        send(pkt)
        
        # Check for response or crash
        response = sniff(filter=f"tcp and src {target_ip}", count=1, timeout=1)
        if not response:
            print(f"No response for payload {i}")

# Run fuzzer
fuzz_protocol("10.0.2.15", 9000)
```

## Advanced Analysis

### Protocol Dissection with Wireshark

**Custom protocol dissector (Lua):**
```lua
-- my_protocol.lua
my_protocol = Proto("MyProto", "Custom Firmware Protocol")

local f_header = ProtoField.uint32("myproto.header", "Header", base.HEX)
local f_command = ProtoField.uint8("myproto.command", "Command", base.HEX)
local f_length = ProtoField.uint16("myproto.length", "Length", base.DEC)
local f_data = ProtoField.bytes("myproto.data", "Data")

my_protocol.fields = {f_header, f_command, f_length, f_data}

function my_protocol.dissector(buffer, pinfo, tree)
    pinfo.cols.protocol = "MyProto"
    local subtree = tree:add(my_protocol, buffer(), "My Protocol Data")
    
    subtree:add(f_header, buffer(0,4))
    subtree:add(f_command, buffer(4,1))
    subtree:add(f_length, buffer(5,2))
    
    local data_len = buffer(5,2):uint()
    subtree:add(f_data, buffer(7, data_len))
end

-- Register for port 9000
local tcp_port = DissectorTable.get("tcp.port")
tcp_port:add(9000, my_protocol)
```

Load in Wireshark: Tools → Lua → Evaluate

### Statistical Analysis

```bash
# Connection statistics
tshark -r capture.pcap -q -z conv,tcp

# Protocol hierarchy
tshark -r capture.pcap -q -z io,phs

# HTTP request statistics
tshark -r capture.pcap -q -z http,tree

# Endpoints
tshark -r capture.pcap -q -z endpoints,tcp
```

### Extract Files from Network Traffic

```bash
# Export HTTP objects
tshark -r capture.pcap --export-objects http,./extracted_http/

# Extract FTP files
tshark -r capture.pcap --export-objects ftp-data,./extracted_ftp/

# Manual extraction with NetworkMiner
# GUI tool: https://www.netresec.com/?page=NetworkMiner
```

## Automation and Monitoring

### Continuous Capture Script

```bash
#!/bin/bash
# continuous_capture.sh

INTERFACE="tap0"
CAPTURE_DIR="./captures"
ROTATE_INTERVAL=300  # 5 minutes

mkdir -p "$CAPTURE_DIR"

while true; do
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    FILENAME="$CAPTURE_DIR/capture_$TIMESTAMP.pcap"
    
    echo "Starting capture: $FILENAME"
    
    # Capture for ROTATE_INTERVAL seconds
    timeout $ROTATE_INTERVAL sudo tcpdump -i $INTERFACE -w "$FILENAME" -G $ROTATE_INTERVAL
    
    # Compress old captures
    gzip "$FILENAME"
    
    echo "Rotated to new capture file"
done
```

### Alert on Suspicious Traffic

```bash
#!/bin/bash
# monitor_traffic.sh

INTERFACE="tap0"

# Monitor for suspicious patterns
sudo tcpdump -i $INTERFACE -l -n | while read line; do
    # Alert on SQL injection attempts
    if echo "$line" | grep -qi "union.*select\|drop.*table"; then
        echo "[ALERT] Possible SQL injection: $line"
        # Send notification
        notify-send "Security Alert" "Possible SQL injection detected"
    fi
    
    # Alert on command injection
    if echo "$line" | grep -E "\||;|&|\`"; then
        echo "[ALERT] Possible command injection: $line"
    fi
    
    # Alert on directory traversal
    if echo "$line" | grep -E "\.\.\/|\.\.\\"; then
        echo "[ALERT] Possible directory traversal: $line"
    fi
done
```

### Automated Protocol Analysis

```python
#!/usr/bin/env python3
"""
Automated network protocol analysis for firmware
"""
from scapy.all import *
import json

class ProtocolAnalyzer:
    def __init__(self, pcap_file):
        self.packets = rdpcap(pcap_file)
        self.analysis = {
            'total_packets': len(self.packets),
            'protocols': {},
            'endpoints': set(),
            'suspicious': []
        }
    
    def analyze(self):
        for pkt in self.packets:
            # Count protocols
            if IP in pkt:
                proto = pkt[IP].proto
                self.analysis['protocols'][proto] = \
                    self.analysis['protocols'].get(proto, 0) + 1
                
                # Track endpoints
                self.analysis['endpoints'].add(pkt[IP].src)
                self.analysis['endpoints'].add(pkt[IP].dst)
            
            # Check for suspicious patterns
            if Raw in pkt:
                payload = pkt[Raw].load
                if b'admin' in payload and b'password' in payload:
                    self.analysis['suspicious'].append({
                        'packet': pkt.summary(),
                        'reason': 'Credentials in cleartext'
                    })
        
        return self.analysis
    
    def report(self):
        print(json.dumps({
            **self.analysis,
            'endpoints': list(self.analysis['endpoints'])
        }, indent=2))

# Usage
analyzer = ProtocolAnalyzer('capture.pcap')
analysis = analyzer.analyze()
analyzer.report()
```

## Integration with Firmware Analysis

### Correlate Network Activity with Behavior

```bash
# 1. Start firmware with logging
qemu-system-arm ... 2>&1 | tee firmware.log &

# 2. Start network capture
sudo tcpdump -i tap0 -w capture.pcap &

# 3. Interact with firmware
# Make requests, trigger behaviors

# 4. Stop captures
# Stop tcpdump and QEMU

# 5. Analyze correlation
# Match timestamps between firmware.log and capture.pcap
```

### Map Network Services to Binaries

```bash
# Inside running firmware
netstat -tulpn

# Cross-reference with process list
ps aux

# Example output:
# tcp   0.0.0.0:80    0.0.0.0:*    LISTEN    1234/httpd
# tcp   0.0.0.0:23    0.0.0.0:*    LISTEN    1235/telnetd

# Extract and analyze those binaries
# Use firmware-static-analysis skill on /usr/sbin/httpd, /usr/sbin/telnetd
```

## Best Practices

1. **Capture early** - Start tcpdump before starting firmware
2. **Use filters** - Reduce capture size with BPF filters
3. **Save everything** - Disk space is cheap, missed packets aren't
4. **Tag captures** - Name files descriptively (auth_attempt.pcap, exploit_test.pcap)
5. **Multiple formats** - Save both pcap and text output
6. **Correlate logs** - Match network activity with system logs
7. **Baseline first** - Capture normal traffic before fuzzing/testing
8. **Document findings** - Note interesting packets and their context
9. **Encrypt at rest** - Captures may contain sensitive data
10. **Legal compliance** - Only analyze your own firmware/network

## Troubleshooting

### No traffic captured

```bash
# Check interface is up
ip link show tap0

# Check QEMU network config
# Ensure -net nic -net tap,ifname=tap0 is set

# Verify firmware has network configured
# Inside QEMU: ifconfig
```

### Can't decrypt HTTPS

```bash
# Ensure SSLKEYLOGFILE is set in firmware environment
# Check if binary uses OpenSSL (not all do)

# Alternative: MITM with custom CA
# May break certificate pinning
```

### Missing packets in capture

```bash
# Increase snapshot length
sudo tcpdump -i tap0 -s 65535 -w full.pcap

# Check for buffer overruns
sudo tcpdump -i tap0 -B 4096 -w buffered.pcap
```

## Tools Summary

| Tool | Purpose | Command |
|------|---------|---------|
| tcpdump | CLI packet capture | `tcpdump -i tap0 -w file.pcap` |
| Wireshark | GUI packet analysis | `wireshark -i tap0` |
| tshark | CLI packet analysis | `tshark -r file.pcap -Y filter` |
| mitmproxy | MITM proxy | `mitmproxy --mode transparent` |
| Burp Suite | Web MITM | GUI |
| Scapy | Packet crafting/analysis | Python library |
| tcpreplay | Packet replay | `tcpreplay -i tap0 file.pcap` |
| arpspoof | ARP spoofing | `arpspoof -i tap0 -t target gateway` |
| NetworkMiner | Passive analysis | GUI |
