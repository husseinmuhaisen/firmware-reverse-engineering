# CVSS 3.1 Scoring Reference

Quick reference for calculating Common Vulnerability Scoring System scores.

## CVSS Calculator

**Online:** https://www.first.org/cvss/calculator/3.1

## Base Score Metrics

### Attack Vector (AV)

**N - Network (0.85):** Exploitable remotely
- Examples: Remote command injection, unauthenticated API exploitation
- "An attacker can exploit from any network"

**A - Adjacent (0.62):** Requires local network access
- Examples: ARP spoofing, DHCP attacks, same subnet exploitation
- "An attacker must be on the same physical or logical network"

**L - Local (0.55):** Requires local system access
- Examples: Privilege escalation, local file inclusion
- "An attacker must have local access or local account"

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
- Examples: TOCTOU bugs, complex multi-step exploits

### Privileges Required (PR)

**N - None (0.85):** No authentication needed
- Examples: Unauthenticated endpoints, default credentials

**L - Low (0.62 / 0.68):** Basic user privileges
- Examples: Authenticated user exploitation, requires user account

**H - High (0.27 / 0.50):** Administrative privileges required
- Examples: Admin-only vulnerabilities, requires root access

*Note: Different values for Scope Changed (S:C)*

### User Interaction (UI)

**N - None (0.85):** No user action required
- Examples: Automatic exploitation, drive-by attacks

**R - Required (0.62):** User must take action
- Examples: Click malicious link, open malicious file, social engineering

### Scope (S)

**U - Unchanged (Impact * Base):** Vulnerability limited to vulnerable component
- Impact stays within original security scope

**C - Changed (Impact * 7.52 - 8):** Vulnerability affects resources beyond vulnerable component
- Can impact other components/systems
- Examples: VM escape, container breakout, privilege escalation

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
- Doesn't crash device (A:N)
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

If ASLR present (more complex):
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
   Timing/race/complex → AC:H

3. Authentication needed?
   No auth → PR:N
   User account → PR:L
   Admin account → PR:H

4. User action needed?
   Automatic → UI:N
   Requires click/action → UI:R

5. Escapes original scope?
   Stays in component → S:U
   Breaks out (container/VM/privilege) → S:C

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
- **H - High:** Public exploit available
- **F - Functional:** PoC exists
- **P - Proof-of-Concept:** Theoretical exploit
- **U - Unproven:** No known exploit

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

**Critical (9.0-10.0):**
- Remote code execution, no auth required
- Authentication bypass with full access
- Remote DoS, no auth required

**High (7.0-8.9):**
- RCE requiring authentication
- Privilege escalation to root
- Sensitive data disclosure

**Medium (4.0-6.9):**
- XSS, CSRF
- Limited information disclosure
- Authenticated DoS

**Low (0.1-3.9):**
- Low-impact information disclosure
- Self-DoS only
- Theoretical attacks

## Common Mistakes

❌ **Don't:**
- Give C:H/I:H/A:H to everything
- Ignore attack prerequisites (set PR:N for admin-only vuln)
- Confuse complexity with impact
- Score based on "feels critical"

✅ **Do:**
- Consider actual attack vector
- Account for required privileges
- Be consistent across findings
- Justify scores in report

## Examples from Real Firmware

### Telnet Enabled by Default
```
CVSS:3.1/AV:A/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
Score: 8.8 (High)

- Adjacent network (local network) (AV:A)
- No credentials needed if hardcoded (PR:N)
- Full compromise (C:H/I:H/A:H)
```

### Firmware Update Over HTTP
```
CVSS:3.1/AV:A/AC:H/PR:N/UI:R/S:U/C:H/I:H/A:H
Score: 7.1 (High)

- Requires MITM position (AV:A, AC:H)
- User must trigger update (UI:R)
- Can install malicious firmware (C:H/I:H/A:H)
```

### Debug Symbols in Production
```
CVSS:3.1/AV:L/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N
Score: 4.0 (Medium)

- Need local access to binary (AV:L)
- Makes reverse engineering easier (C:L)
- Doesn't directly compromise (I:N/A:N)
```
