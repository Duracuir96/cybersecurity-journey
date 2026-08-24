# IAM Enumeration Activity

**Detection key:** `iam_enumeration`
**MITRE ATT&CK:** [T1087 — Account Discovery](https://attack.mitre.org/techniques/T1087/)
**Default severity:** Medium — reconnaissance that often precedes escalation.

## What triggered this
A single identity issued a burst of IAM read calls (`ListUsers`, `ListRoles`,
`ListPolicies`, `GetAccountAuthorizationDetails`) above the threshold — typical of an
attacker mapping the account before choosing a target.

## Investigate
1. Identify the principal and whether this is a legitimate audit.
2. Check specifically for `GetAccountAuthorizationDetails`, which dumps the whole IAM config.
3. Correlate with any subsequent IAM **write** activity from the same actor.

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=Username,AttributeValue=<user> --max-results 50
```

## Remediate
1. Apply least privilege — restrict `iam:List*` / `iam:Get*` to those who need it.
2. If the actor is not a known auditor, disable its credentials pending review.
3. Alert on `GetAccountAuthorizationDetails` calls.

## Common false positives
- A legitimate security audit or compliance scan.
- Cloud security posture tools (CSPM) inventorying IAM.