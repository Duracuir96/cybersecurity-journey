# Brute Force Console Login

**Detection key:** `failed_logins`
**MITRE ATT&CK:** [T1110 — Brute Force](https://attack.mitre.org/techniques/T1110/)
**Default severity:** High — Critical if a success follows the failures.

## What triggered this
Multiple failed `ConsoleLogin` events came from the same source IP within the
detection window, above the configured threshold. This pattern is typical of
credential stuffing or password spraying against IAM users or the root account.

## Investigate
1. Identify the source IP and whether it belongs to your organisation.
2. Check whether any attempt **succeeded** after the failures — a `ConsoleLogin`
   with `responseElements.ConsoleLogin = "Success"` from the same IP is the worst case.
3. Note which identities were targeted; the root user or a service account raises priority.

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=ConsoleLogin \
  --max-results 50
```

## Remediate
1. Block the source IP at the edge (WAF, Security Group or NACL) if external and untrusted.
2. Enable and enforce MFA on every targeted identity.
3. If a login succeeded, treat the account as compromised: rotate its credentials and
   review every action taken from that session.
4. Never use the root user for daily work — protect it with hardware MFA.

## Common false positives
- A user mistyping their password repeatedly from a known office IP.
- Automated tooling retrying with stale credentials.
- Your own penetration tests or scheduled security scans.