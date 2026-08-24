# Access Key Usage Anomaly

**Detection key:** `credential_abuse`
**MITRE ATT&CK:** [T1078 — Valid Accounts](https://attack.mitre.org/techniques/T1078/)
**Default severity:** High — a valid key used from unexpected locations often means theft.

## What triggered this
The same identity called `GetCallerIdentity` (or other APIs) from several distinct
source IPs within the window. A single access key surfacing from multiple locations
suggests the key has been shared, leaked or stolen.

## Investigate
1. List every IP that used the identity and geolocate them.
2. Look for impossible travel — two far-apart regions in a short interval.
3. Confirm whether the identity is a human user, a CI runner or a service account.

```bash
aws iam list-access-keys --user-name <user>
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=Username,AttributeValue=<user> --max-results 50
```

## Remediate
1. Disable the suspicious access key immediately (`aws iam update-access-key --status Inactive`).
2. Issue a fresh key to the legitimate owner and update their tooling.
3. Audit every action taken with the key while it was active.
4. Prefer short-lived credentials (IAM roles / STS) over long-lived keys.

## Common false positives
- A CI/CD runner or service legitimately calling from several build agents.
- A user on a VPN or mobile network with rotating egress IPs.