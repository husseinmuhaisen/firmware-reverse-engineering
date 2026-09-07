# CVSS 3.1 Scoring Reference

Quick reference for **CVSS 3.1**, retained for assessments using that version.
CVSS 4.0 is also available; agree the reporting version and do not mix metric
sets. These examples are illustrative assumptions, not automatic scores for
vulnerability classes. Justify every metric using observed capabilities and
prerequisites; CVSS measures severity, not business risk.

Use the [FIRST specification](https://www.first.org/cvss/v3.1/specification-document)
and [user guide](https://www.first.org/cvss/v3.1/user-guide) for edge cases.

## CVSS Calculator

**Online:** https://www.first.org/cvss/calculator/3.1

## Base Score Metrics

### Attack Vector (AV)

**N - Network (0.85):** Exploitable remotely
- Examples: Remote command injection, unauthenticated API exploitation
- "An attacker can exploit from any network"

**A - Adjacent (0.62):** Exploitation is constrained to a shared physical/logical network
- Examples: link-local protocol attacks such as ARP spoofing
- A TCP service restricted by deployment to a LAN is not automatically AV:A; assess the protocol and exploitation path.

**L - Local (0.55):** Requires local system access
- Examples: local privilege escalation, malicious local file processing
- Local file inclusion through HTTP can be AV:N; the word "local" in its name does not determine AV.

**P - Physical (0.20):** Requires physical access to device
- Examples: UART/JTAG exploitation, physical reset button attacks
- "An attacker must have physical access to the device"

### Attack Complexity (AC)

**L - Low (0.77):** No special conditions required
- Exploit works reliably
- No special configuration needed
- Examples: Direct command injection, hardcoded credentials

**H - High (0.44):** Requires special conditions
- Timing-dependent, race conditions
- Requires specific configuration
- Examples: a required race or on-path position outside attacker control
- Number of exploit steps or research effort alone does not determine AC:H.

### Privileges Required (PR)

**N - None (0.85):** No authentication needed
- Examples: unauthenticated endpoints; assess shared hardcoded credentials in the specific vulnerability context

**L - Low (0.62 / 0.68):** Basic user privileges
- Examples: Authenticated user exploitation, requires user account

**H - High (0.27 / 0.50):** Administrative privileges required
- Examples: Admin-only vulnerabilities, requires root access

*Note: Different values for Scope Changed (S:C)*

### User Interaction (UI)

**N - None (0.85):** No user action required
- Examples: exploitation of a reachable service without another user acting

**R - Required (0.62):** User must take action
- Examples: Click malicious link, open malicious file, social engineering

### Scope (S)

**U - Unchanged:** Impact remains under the same security authority as the vulnerable component.

**C - Changed:** Exploitation crosses a security-authority boundary, such as a
VM escape affecting the host. Reaching another process or escalating privileges
within one authority does not by itself establish S:C.

### Impact Metrics (C/I/A)

**Confidentiality (C):**
- **H - High (0.56):** Total information disclosure
- **L - Low (0.22):** Limited information disclosure
- **N - None (0.00):** No confidentiality impact

**Integrity (I):**
- **H - High (0.56):** Complete integrity compromise
- **L - Low (0.22):** Limited modification capability
- **N - None (0.00):** No integrity impact

**Availability (A):**
- **H - High (0.56):** Complete denial of service
- **L - Low (0.22):** Reduced performance/availability
- **N - None (0.00):** No availability impact

## Severity Ratings

| Score | Rating |
|-------|--------|
| 0.0 | None |
| 0.1 - 3.9 | Low |
| 4.0 - 6.9 | Medium |
| 7.0 - 8.9 | High |
| 9.0 - 10.0 | Critical |

## Common Firmware Vulnerability Patterns

### Remote Command Injection
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
Base Score: 9.8 (Critical)

Rationale:
- Network exploitable (AV:N)
- Low complexity (AC:L)
- No auth required (PR:N)
- No user interaction (UI:N)
- Unchanged scope (S:U)
- Full system compromise (C:H/I:H/A:H)
```

### Authentication Bypass
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N
Base Score: 9.1 (Critical)

Rationale:
- Network exploitable (AV:N)
- Low complexity (AC:L)
- No auth required (PR:N)
- Bypasses authentication (C:H/I:H)
- Assumes the bypass cannot impair availability (A:N); absence of a crash is insufficient
```

### Hardcoded Credentials
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
Base Score: 9.8 (Critical)

If remote access:
- Network exploitable (AV:N)
- Anyone can use them (PR:N)
- Full compromise (C:H/I:H/A:H)

If local only:
CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H
Base Score: 7.8 (High)
```

### Buffer Overflow (Remote, No Auth)
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
Base Score: 9.8 (Critical)

If exploitation requires a demonstrated condition outside attacker control (ASLR alone is insufficient):
CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H
Base Score: 8.1 (High)
```

### Weak Cryptography
```
CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N
Base Score: 5.9 (Medium)

Rationale:
- Network attacker can intercept (AV:N)
- High complexity (requires crypto attack) (AC:H)
- Confidentiality compromised (C:H)
- Doesn't affect integrity directly (I:N)
```

### Information Disclosure
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N
Base Score: 5.3 (Medium)

For sensitive data:
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N
Base Score: 7.5 (High)
```

### Denial of Service
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H
Base Score: 7.5 (High)

Permanent DoS (brick device):
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H
Base Score: 7.5 (High)
```

### Cross-Site Scripting (Reflected)
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N
Base Score: 6.1 (Medium)

Rationale:
- Network exploitable (AV:N)
- Requires user click (UI:R)
- Scope changed (affects user's browser) (S:C)
- Limited impact (C:L/I:L)
```

### SQL Injection
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
Base Score: 9.8 (Critical)

If limited to data read:
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N
Base Score: 7.5 (High)
```

### Missing Authentication
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
Base Score: 9.8 (Critical)

Or based on exposed functionality:
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:N
Base Score: 6.5 (Medium)
```

## Decision Flow

```
1. How is it exploited?
   Network → AV:N
   Adjacent network → AV:A
   Local → AV:L
   Physical access → AV:P

2. How hard to exploit?
   Reliable/straightforward → AC:L
   Required condition outside attacker control → AC:H

3. Authentication needed?
   No auth → PR:N
   User account → PR:L
   Admin account → PR:H

4. User action needed?
   Automatic → UI:N
   Requires click/action → UI:R

5. Escapes original scope?
   Same security authority → S:U
   Crosses security authority (for example VM to host) → S:C

6. What can attacker do?
   Read all data → C:H
   Read some data → C:L
   No data read → C:N
   
   Modify all data → I:H
   Modify some data → I:L
   No modification → I:N
   
   Crash/DoS device → A:H
   Degrade performance → A:L
   No availability impact → A:N
```

## Temporal Metrics (Optional)

### Exploit Code Maturity (E)
- **X - Not Defined:** Default
- **H - High:** Reliable autonomous exploitation, or detailed reliable exploitation evidence
- **F - Functional:** Functional exploit works in most applicable situations
- **P - Proof-of-Concept:** PoC exists but may need substantial modification
- **U - Unproven:** Theoretical; no exploit code or demonstrated exploitation known

### Remediation Level (RL)
- **X - Not Defined:** Default
- **U - Unavailable:** No fix available
- **W - Workaround:** Unofficial fix exists
- **T - Temporary Fix:** Official temp fix
- **O - Official Fix:** Official patch available

### Report Confidence (RC)
- **X - Not Defined:** Default
- **C - Confirmed:** Verified vulnerability
- **R - Reasonable:** Likely vulnerable
- **U - Unknown:** Unconfirmed

## Environmental Metrics (Optional)

Adjust based on specific deployment:
- Modified Attack Vector (MAV)
- Modified Attack Complexity (MAC)
- Modified Privileges Required (MPR)
- Modified User Interaction (MUI)
- Modified Scope (MS)
- Modified Confidentiality (MC)
- Modified Integrity (MI)
- Modified Availability (MA)

## Quick Reference Card

Use the numeric severity table above after calculating the full vector.
Vulnerability names do not determine severity: unauthenticated remote DoS with
only A:H is 7.5 (High), while a demonstrated unauthenticated remote full
compromise may be 9.8 (Critical). A theoretical concern needs evidence before
it is treated as a vulnerability.

## Common Mistakes

**Don't:**
- Give C:H/I:H/A:H to everything
- Ignore attack prerequisites (set PR:N for admin-only vuln)
- Confuse complexity with impact
- Score based on "feels critical"

**Do:**
- Consider actual attack vector
- Account for required privileges
- Be consistent across findings
- Justify scores in report

## Illustrative Firmware Scenarios

### Telnet with Shared Hardcoded Root Credentials
```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
Score: 9.8 (Critical)

- TCP service reachable over a routed network (AV:N)
- No credentials needed if hardcoded (PR:N)
- Full compromise (C:H/I:H/A:H)
```

### Unsigned Firmware Update Over HTTP (On-Path Attacker)
```
CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:H/A:H
Score: 7.5 (High)

- Assumes an on-path position on a routed network (AV:N, AC:H)
- No effective image signature verification; HTTP alone does not prove arbitrary firmware installation
- User must trigger update (UI:R)
- Can install malicious firmware (C:H/I:H/A:H)
```

### Debug Symbols in Production

Debug symbols alone are not a scored confidentiality vulnerability merely
because they make reverse engineering easier. Record them as an informational
observation unless they expose information that a security policy protects.
If such exposure exists, score the actual access path and impact with evidence.
