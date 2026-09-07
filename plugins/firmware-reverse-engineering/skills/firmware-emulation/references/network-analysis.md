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
wireshark -i tap0 -k  # Configure dumpcap capture permissions first

# Or capture with tshark (CLI)
sudo tshark -i tap0 -w capture.pcap

# With capture filter (BPF; display filters use -Y)
sudo tshark -i tap0 -f "port 80 or port 443" -w web.pcap
```

### Capture from QEMU User-Mode

```bash
# qemu-user shares the host network stack; it does not create a NAT guest.
# Capture the interface and application port actually used (e.g. loopback 8080).
sudo tcpdump -i lo 'tcp port 8080' -w application.pcap
# Port 1234 in these examples is GDB traffic, not firmware application traffic.
# System QEMU -netdev user is a different networking mode (SLIRP/NAT).

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
# Only applications/TLS libraries that implement key logging honor this variable.
# Merely linking OpenSSL does not guarantee support. Verify a key log is written.
# Set SSLKEYLOGFILE before launching a supported process.
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
tshark -r capture.pcap -Y "tls.handshake.certificate" -T fields \
  -e tls.handshake.certificate -E occurrence=f | head -n 1 | tr -d ":" | xxd -r -p > cert.der
openssl x509 -inform DER -in cert.der -text -noout
# TLS 1.3 encrypts certificates after ServerHello; decryption keys are needed.
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
tshark -r telnet.pcap -q -z follow,tcp,ascii,0
# Choose the correct tcp.stream index and reconstruct the session; no generic
# password field exists and characters can span packets.

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

# This concatenates packet payload fields only; it does not reassemble TCP
# sequence numbers, directions, retransmissions or application messages.
# Use Follow TCP Stream / protocol-specific exports for reassembled evidence.
# Convert to binary
xxd -r -p payload.hex > payload.bin
```

## Man-in-the-Middle (MITM) Attacks

### Setup MITM Proxy

**Using mitmproxy:**
```bash
# Install mitmproxy
pipx install mitmproxy

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
# Burp → Settings → Tools → Proxy → Proxy listeners; enable invisible
# proxying for redirected non-proxy-aware clients.
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
# Start mitmproxy once to generate its CA in the selected config directory.
mitmproxy --set confdir=/path/to/analysis-proxy --mode transparent

# In the isolated guest, install THAT proxy's certificate (not a different CA).
# Debian-like example only; BusyBox firmware may lack this update utility:
sudo cp /path/to/analysis-proxy/mitmproxy-ca-cert.pem /mnt/firmware/usr/local/share/ca-certificates/analysis-proxy.crt
# Run update-ca-certificates inside a booted guest or properly configured binfmt chroot.
# Other firmware may use a custom CA bundle. Pinning may still reject the proxy.

```

## Traffic Manipulation

### Modify a Capture with Scapy

Passive `sniff()` observes copies; calling `send()` does not replace intercepted
packets and can cause duplicate traffic or a capture/send loop. Use mitmproxy
above for live application changes. This offline example writes a separate
capture and keeps TCP payload lengths unchanged; it is not a TCP stream editor.

```python
#!/usr/bin/env python3
from scapy.all import IP, TCP, Raw, rdpcap, wrpcap

packets = rdpcap('capture.pcap')
needle = b'vulnerable_cmd'
for packet in packets:
    if IP in packet and TCP in packet and Raw in packet:
        payload = packet[Raw].load
        if needle in payload:
            packet[Raw].load = payload.replace(needle, b'X' * len(needle))
            del packet[IP].len
            del packet[IP].chksum
            del packet[TCP].chksum
wrpcap('modified.pcap', packets)
```

### Replay Attacks

Packet replay does not establish a new TCP session or refresh sequence numbers,
cookies and anti-replay tokens. For application authentication replay, recreate
a valid session and resend the recorded request using an application client.

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
import os
import socket

def fuzz_protocol(target_ip, target_port):
    """Send application bytes over established TCP connections in the test lab."""
    for i in range(1000):
        payload = os.urandom(100)
        try:
            with socket.create_connection((target_ip, target_port), timeout=1) as conn:
                conn.sendall(payload)
                response = conn.recv(4096)
                if not response:
                    print(f"Connection closed for input {i}: {payload.hex()}")
        except OSError as error:
            print(f"Input {i}: {payload.hex()} -> {error}")
        # Missing responses/timeouts are observations, not proof of a crash.
        # Correlate with process state, logs and a reproducible saved input.

fuzz_protocol("192.168.100.2", 9000)
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
    local offset = 0
    while offset < buffer:len() do
        local remaining = buffer:len() - offset
        if remaining < 7 then
            pinfo.desegment_offset = offset
            pinfo.desegment_len = 7 - remaining
            return
        end
        local data_len = buffer(offset + 5, 2):uint()
        local pdu_len = 7 + data_len
        if remaining < pdu_len then
            pinfo.desegment_offset = offset
            pinfo.desegment_len = pdu_len - remaining
            return
        end
        local subtree = tree:add(my_protocol, buffer(offset, pdu_len), "My Protocol Data")
        subtree:add(f_header, buffer(offset, 4))
        subtree:add(f_command, buffer(offset + 4, 1))
        subtree:add(f_length, buffer(offset + 5, 2))
        subtree:add(f_data, buffer(offset + 7, data_len))
        offset = offset + pdu_len
    end
end

-- Register for port 9000
local tcp_port = DissectorTable.get("tcp.port")
tcp_port:add(9000, my_protocol)
```

Save as `my_protocol.lua`; load using `tshark -X lua_script:my_protocol.lua -r capture.pcap`, or put it in the Wireshark personal Lua plugins directory. Enable TCP subdissector reassembly. This assumes a 7-byte header with a big-endian 16-bit payload length; validate the actual protocol layout.

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
    sudo timeout --signal=INT "$ROTATE_INTERVAL" tcpdump -i "$INTERFACE" -w "$FILENAME"
    
    # Compress old captures
    gzip "$FILENAME"
    
    echo "Rotated to new capture file"
done
```

### Alert on Suspicious Traffic

This is a plaintext keyword triage example, not an injection detector. It misses
encryption and split/encoded payloads and produces false positives.

```bash
#!/bin/bash
# monitor_traffic.sh

INTERFACE="tap0"

# Monitor for suspicious patterns
sudo tcpdump -i "$INTERFACE" -l -n -A -s 0 | while IFS= read -r line; do
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
    if echo "$line" | grep -Eq '\.\./|\.\.\\'; then
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
                        'reason': 'Credential-related keywords in raw payload; verify protocol context'
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
CAPTURE_PID=$!

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
# Verify the application implements key logging and has actually written secrets.

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
