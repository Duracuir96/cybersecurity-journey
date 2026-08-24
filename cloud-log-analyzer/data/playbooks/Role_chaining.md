# Role Chaining

**Detection key:** `role_chaining`
**MITRE ATT&CK:** [T1548 — Abuse Elevation Control Mechanism](https://attack.mitre.org/techniques/T1548/)
**Default severity:** Medium — High when the chain ends on a highly privileged role.

## What triggered this
A single identity called `AssumeRole` many times, chaining through roles above the
threshold. Progressive role assumption is a known privilege-escalation technique.

## Investigate
1. Map the full chain — which roles were assumed, in what order?
2. Inspect the final role's permissions and trust policy.
3. Confirm whether the chain matches a legitimate workflow.

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRole --max-results 50
aws iam get-role --role-name <final-role>
```

## Remediate
1. Tighten trust policies so only intended principals can assume each role.
2. Add `sts:AssumeRole` conditions (source IP, MFA, external ID).
3. Alert on assumption of sensitive roles.
4. Reduce the length of legitimate role chains where possible.

## Common false positives
- CI/CD or cross-account automation that assumes roles by design.
- SSO / identity-federation workflows that chain roles normally.