---
name: firmware-security-reports
description: "Evidence-based security report generation for firmware assessments. Use when the agent needs to create technical security reports from firmware analysis. Covers: (1) Full penetration test reports with executive summaries and technical details, (2) Individual vulnerability findings with CVSS 3.1 scoring, (3) Working notes for documentation during assessment, (4) Integration with firmware analysis skills (extraction, static analysis, Ghidra RE, emulation). Outputs to markdown and PDF formats. Technical audience only. Includes templates for findings, PoC code, remediation guidance, and evidence documentation."
---

# Firmware Security Report Generation

Professional technical security reports for firmware assessments, following industry standards from elite American security firms.

All example findings, products, versions, addresses and scores in this skill
and its templates are illustrative. Replace them with verified assessment
evidence; do not carry example results into a deliverable.

## Skill Scope

**Use this skill for:**
- Generating penetration test reports from firmware analysis
- Documenting individual security findings
- Creating working notes during assessments
- Converting analysis results to professional deliverables

**Output Formats:**
- Markdown (version-controllable, easy to edit)
- PDF (via Pandoc, or a separately installed PDF skill if available)

**Integration:**
- Consumes outputs from: firmware-extraction, firmware-static-analysis, ghidra-re, firmware-emulation
- Produces: Professional security reports for clients/stakeholders

## Report Types

### 1. Full Penetration Test Report

**Template:** `assets/pentest_report_template.md`

**Sections:**
- Executive Summary (key findings, risk summary, priority recommendations)
- Scope and Methodology (detailed approach, tools used)
- Findings (with CVSS scores, PoC, remediation)
- Technical Analysis Details (architecture, security mitigations, network services)
- Remediation Roadmap (phased approach with timelines)
- Appendices (CVSS calculations, exploit code, evidence)

**Usage:**
```markdown
# Fill in template placeholders:
[CLIENT_NAME] → Acme Corporation
[PRODUCT_NAME] → IoT Gateway Pro
[FIRMWARE_VERSION] → v2.3.1
[ARCHITECTURE] → ARM Cortex-A9
etc.

# Add findings from analysis:
FW-001: Remote Command Injection
FW-002: Hardcoded Cryptographic Keys
FW-003: MD5 Password Hashing
```

### 2. Individual Finding Report

**Template:** `assets/finding_template.md`

**Sections:**
- Finding metadata (severity, CVSS, CWE)
- Technical description
- Impact analysis
- Proof of concept with exploit code
- Evidence (screenshots, PCAPs, logs)
- Remediation guidance with code fixes
- Verification steps

**Usage:**
```markdown
# Create one file per finding:
FW-001-command-injection.md
FW-002-hardcoded-keys.md
FW-003-weak-hashing.md

# Compile into main report
```

### 3. Working Notes

**Template:** `assets/working_notes_template.md`

**Sections:**
- Daily activity log
- Vulnerability tracking table
- Technical details and file system map
- Exploitation notes
- Evidence file inventory
- Time tracking

**Usage:**
```markdown
# Update daily during assessment
# Track progress and findings
# Reference when writing final report
# Internal documentation only (not for client)
```

## Workflow

### Phase 1: Assessment Execution

Use your firmware analysis skills to find vulnerabilities:

```bash
# 1. Extract firmware
binwalk -e firmware.bin

# 2. Static analysis
readelf -h binary
strings binary | grep password

# 3. Ghidra RE (set GHIDRA_INSTALL_DIR/GHIDRA_SCRIPT_DIR as in ghidra-re)
"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" /proj Firmware -scriptPath "$GHIDRA_SCRIPT_DIR" -import binary \
  -postScript find_auth_functions.py \
  -postScript find_buffer_overflows.py

# 4. Emulation & testing
qemu-arm -L ./rootfs/ ./binary
curl -X POST http://192.168.1.1/vuln.cgi -d "param=;id"

# 5. Document in working notes
```

### Phase 2: Finding Documentation

For each vulnerability discovered:

**Step 1: Copy finding template**
```bash
cp assets/finding_template.md findings/FW-001-command-injection.md
```

**Step 2: Fill in details**
```markdown
## FW-001: Remote Command Injection in Diagnostic Interface

**Severity:** Critical
**CVSS v3.1 Score:** 9.8 (Critical)
**CVSS Vector:** CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H

**Affected Component:** /cgi-bin/diagnostic.cgi
**Location:** /www/cgi-bin/diagnostic.cgi, line 42

### Description

The diagnostic.cgi script accepts a 'target' parameter for network ping
functionality. User input is passed directly to system() without validation,
allowing arbitrary command execution.

[Continue filling template...]
```

**Step 3: Calculate CVSS**

Use `references/cvss-scoring.md` for guidance:
```
Remote command injection, no auth:
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H = 9.8
```

**Step 4: Create PoC**
```python
#!/usr/bin/env python3
import requests

target = "http://192.168.1.1"
payload = {"target": "127.0.0.1;id"}

r = requests.post(f"{target}/cgi-bin/diagnostic.cgi", data=payload)
print(r.text)  # uid=0(root)
```

**Step 5: Collect evidence**
```bash
mkdir -p evidence/
# Screenshot exploitation
# Save PCAP
tcpdump -i tap0 -w evidence/fw-001-exploit.pcap
# Save exploit script
cp exploit.py evidence/fw-001-exploit.py
```

### Phase 3: Report Assembly

**Step 1: Start with template**
```bash
cp assets/pentest_report_template.md final_report.md
```

**Step 2: Fill metadata**
```markdown
**Client:** Acme Corporation
**Product:** IoT Gateway Pro
**Firmware Version:** v2.3.1
**Assessment Period:** January 1-15, 2024
**Report Date:** January 20, 2024
**Assessed By:** [Your Name]
```

**Step 3: Add findings summary**
```markdown
**Critical Issues:** 2
**High Severity:** 3
**Medium Severity:** 5
**Low Severity:** 2
**Informational:** 1

| ID | Title | Severity | CVSS |
|----|-------|----------|------|
| FW-001 | Remote Command Injection | Critical | 9.8 |
| FW-002 | Authentication Bypass | Critical | 9.1 |
| FW-003 | Hardcoded Crypto Keys | High | 7.5 |
```

**Step 4: Import individual findings**
```markdown
# Copy full finding details from FW-001-command-injection.md
# Paste into Findings section
# Repeat for each finding
```

**Step 5: Add technical analysis**

From your assessment notes:
```markdown
### Architecture Analysis
- ARM Cortex-A9 (32-bit, little-endian)
- Entry Point: 0x00400000
- Base Address: 0x00400000

### Security Mitigations
| Mitigation | Status | Notes |
|------------|--------|-------|
| PIE | No | Example ET_EXEC executable |
| ASLR | Not tested | Verify runtime policy and mappings |
| Stack Canaries | Enabled | Present in httpd |
| NX Stack | Enabled | Non-executable stack |

### Network Services
- Port 23/tcp: Telnet (CRITICAL - enabled by default)
- Port 80/tcp: HTTP (Multiple vulnerabilities)
- Port 443/tcp: HTTPS (Self-signed certificate)
```

**Step 6: Create remediation roadmap**
```markdown
### Phase 1: Critical Issues (0-30 days)
1. Disable telnet service
2. Patch command injection (FW-001, FW-004)
3. Fix authentication bypass (FW-002)
4. Remove default credentials

### Phase 2: High Severity (30-60 days)
1. Replace hardcoded keys
2. Implement input validation framework
3. Build supported executables as PIE and verify runtime ASLR
```

**Step 7: Review and polish**
- Verify all placeholders filled
- Check CVSS calculations
- Ensure evidence files referenced
- Proofread technical content

### Phase 4: PDF Generation

**Option 1: Use a separately installed PDF skill, if available**
```bash
# Read pdf skill for conversion
# Convert markdown to professional PDF
```

**Option 2: Use Pandoc with XeLaTeX installed**

Choose fonts that cover the report characters, replace unsupported symbols and
review the rendered pages for clipping and missing glyphs before delivery.
```bash
pandoc final_report.md -o final_report.pdf \
  --pdf-engine=xelatex \
  --toc \
  --number-sections \
  -V geometry:margin=1in \
  --highlight-style=tango
```

## Integration with Firmware Analysis Skills

### From firmware-extraction

```markdown
## Filesystem Analysis

**Root Filesystem:** SquashFS (extracted at offset 0x40000)
**Filesystems Found:**
- 0x0 - TRX header
- 0x1C - LZMA compressed kernel
- 0x40000 - SquashFS root filesystem
- 0x2C0000 - JFFS2 configuration partition

**Extraction Method:** binwalk -e firmware.bin
**Total Files Extracted:** 1,247
```

### From firmware-static-analysis

```markdown
## Binary Security Analysis

**Binaries Analyzed:** 15 (in /usr/sbin/)

**Key Findings:**
- /usr/sbin/httpd: No PIE, stack canaries present
- /usr/sbin/telnetd: No security mitigations
- /usr/lib/libcrypto.so: AES implementation uses OpenSSL 1.0.2k

**Architecture:** ARM 32-bit, little-endian
**Calling Convention:** ARM EABI
```

### From ghidra-re

````markdown
## Reverse Engineering Findings

**Authentication Function Analysis:**

Function: `check_password` at 0x00401234
- Uses strcmp(); assess whether a remotely measurable secret-dependent timing difference exists
- Rate limiting and empty-password acceptance require separate verification; the snippet alone does not establish them

Decompiled code:
```c
int check_password(char *username, char *password) {
    char stored_hash[32];
    load_user_hash(username, stored_hash);
    
    if (strcmp(password_hash(password), stored_hash) == 0) {
        return AUTH_SUCCESS;
    }
    return AUTH_FAIL;
}
```

**Cryptographic Analysis:**
- AES S-box found at 0x0040A000
- MD5 constants in auth_daemon
- Hardcoded key: `0x0123456789ABCDEF0123456789ABCDEF`
````

### From firmware-emulation

````markdown
## Dynamic Analysis Results

**Emulation Environment:**
- QEMU system-mode (ARM versatilepb)
- Kernel: Extracted from firmware (Linux 4.9.118)
- Network: TAP interface (192.168.100.1/24)

**Runtime Behavior:**
- Firmware boots successfully in 45 seconds
- All services start automatically
- Debug logging enabled (sensitive data in logs)

**Network Traffic Analysis:**
```
tcpdump capture: evidence/network_traffic.pcap
Key findings:
- Cleartext credentials in HTTP POST
- No TLS for admin interface
- API keys in HTTP headers: X-API-Key: 0x123456...
```

**Exploitation:**
```bash
# Successful RCE via command injection
$ curl -X POST http://192.168.100.2/cgi-bin/admin.cgi \
  -d "cmd=;id"

Response: uid=0(root) gid=0(root)
```
````

## Best Practices

### Writing Technical Findings

**DO:**
Use precise technical language
Include addresses, file paths, line numbers
Provide working proof-of-concept code
Show before/after code for remediation
Calculate accurate CVSS scores
Include evidence (screenshots, PCAPs)
Explain impact clearly

**DON'T:**
Use vague descriptions ("security issue found")
Over-hype severity without justification
Provide theoretical exploits without validation
Skip remediation guidance
Forget to include CWE/OWASP references

### CVSS Scoring

Always justify your scores. Use `references/cvss-scoring.md` for guidance.

**Example:**
```markdown
**CVSS v3.1 Score:** 9.8 (Critical)
**CVSS Vector:** CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H

**Justification:**
- AV:N - Exploitable remotely over network
- AC:L - No special conditions required, reliable exploitation
- PR:N - No authentication required
- UI:N - No user interaction needed
- S:U - Impact contained to vulnerable component
- C:H - Full file system access as root
- I:H - Complete system modification possible
- A:H - Can crash or brick device
```

### Evidence Organization

```
project/
├── final_report.md
├── findings/
│   ├── FW-001-command-injection.md
│   ├── FW-002-auth-bypass.md
│   └── FW-003-hardcoded-keys.md
├── evidence/
│   ├── screenshots/
│   │   ├── fw-001-ghidra-analysis.png
│   │   ├── fw-001-exploitation.png
│   │   └── fw-002-admin-access.png
│   ├── pcaps/
│   │   ├── fw-001-exploit.pcap
│   │   └── full-session.pcap
│   ├── exploits/
│   │   ├── fw-001-exploit.py
│   │   └── fw-002-bypass.py
│   └── binaries/
│       ├── httpd
│       └── auth_daemon
└── working_notes.md
```

### Report Quality Checklist

**Before delivery:**

- [ ] All placeholders filled in
- [ ] CVSS scores calculated correctly
- [ ] Evidence files referenced and included
- [ ] PoC code tested and working
- [ ] Remediation guidance is actionable
- [ ] Technical details are accurate
- [ ] Grammar and spelling checked
- [ ] Sensitive client data redacted (if sharing publicly)
- [ ] PDF generated and reviewed
- [ ] Executive summary tells coherent story

## Common Report Sections

### Executive Summary

**Purpose:** High-level overview for decision-makers

**Template:**
```markdown
This assessment of [PRODUCT] version [VERSION] identified [COUNT] security
vulnerabilities, including [COUNT] critical issues that allow remote attackers
to [PRIMARY_IMPACT].

The most severe finding is [FW-ID]: [TITLE], which enables [ATTACK_SCENARIO].
Immediate remediation is recommended for all critical findings.

Key recommendations:
1. [ACTION_1] - Addresses FW-001, FW-002
2. [ACTION_2] - Addresses FW-003, FW-004
3. [ACTION_3] - Improves overall security posture
```

### Methodology

**Purpose:** Establish credibility, explain approach

**Template:**
```markdown
The assessment followed a structured methodology:

1. **Firmware Acquisition** - [How firmware was obtained]
2. **Extraction** - Tools: binwalk, jefferson, sasquatch
3. **Static Analysis** - Binary analysis, configuration review
4. **Reverse Engineering** - Ghidra-based deep analysis
5. **Dynamic Analysis** - QEMU emulation, runtime testing
6. **Exploitation** - PoC development and validation
7. **Documentation** - Report generation and evidence collection

Time invested: [HOURS] over [DAYS] days
```

### Risk Summary

**Purpose:** Quantify overall risk

**Template:**
```markdown
### Risk Distribution

[Chart showing Critical/High/Medium/Low distribution]

**Critical Risks (9.0-10.0):** 2 findings
- Enable remote code execution without authentication
- Full device compromise possible

**High Risks (7.0-8.9):** 3 findings
- Require authentication but lead to privilege escalation
- Sensitive data disclosure

**Overall Risk:** HIGH
The device is vulnerable to remote compromise. Immediate action required.
```

## Templates Reference

All templates located in `assets/` directory:

1. **pentest_report_template.md** - Complete assessment report
2. **finding_template.md** - Individual vulnerability documentation
3. **working_notes_template.md** - Assessment tracking and notes

Additional reference:

4. **references/cvss-scoring.md** - CVSS 3.1 calculation guide with examples

## Quick Start

```bash
# 1. During assessment - keep working notes
cp assets/working_notes_template.md working_notes.md
# Update daily with findings

# 2. For each vulnerability - create finding
cp assets/finding_template.md findings/FW-001-vuln-name.md
# Fill in technical details, PoC, remediation

# 3. At end - assemble full report
cp assets/pentest_report_template.md final_report.md
# Import findings, add analysis, create roadmap

# 4. Generate PDF (use pdf skill or pandoc)
# pandoc final_report.md -o final_report.pdf --pdf-engine=xelatex
```

## Integration Example

Complete workflow from analysis to report:

```bash
# Day 1-3: Analysis
binwalk -e firmware.bin
readelf -h binary
"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" /proj Firmware -scriptPath "$GHIDRA_SCRIPT_DIR" -import binary -postScript find_crypto.py
qemu-arm -g 1234 -L ./rootfs/ ./binary

# Day 3-5: Documentation
cp assets/finding_template.md findings/FW-001-cmdinj.md
# Fill in details from Ghidra/QEMU analysis

# Day 5-7: Report Writing
cp assets/pentest_report_template.md acme_iot_gateway_report.md
# Compile all findings into main report

# Day 7: Delivery
pandoc acme_iot_gateway_report.md -o acme_iot_gateway_report.pdf --pdf-engine=xelatex
# Send to client
```

## Professional Standards

Reports should distinguish verified findings, unverified candidates, test
limitations and informational observations. This repository does not claim
endorsement or certification by a security consultancy. Use the agreed
assessment methodology and the applicable FIRST CVSS specification.

**Key principles:**
1. **Accuracy** - Support claims with reproducible evidence; state what a PoC actually demonstrates
2. **Reproducibility** - Clear exploitation steps
3. **Actionability** - Specific remediation guidance
4. **Evidence** - Screenshots, PCAPs, code samples
5. **Professionalism** - Technical depth without fluff

Review all generated reports against the engagement scope and evidence before delivery.
