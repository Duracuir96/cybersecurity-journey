# IAM Privilege Escalation

**Detection key:** `iam_changes`
**MITRE ATT&CK:** [T1098 — Account Manipulation](https://attack.mitre.org/techniques/T1098/)
**Default severity:** Critical — IAM changes alter the security posture of the whole account.

## What triggered this
Sensitive IAM write events were observed, such as `CreateUser`, `AttachUserPolicy`,
`CreateAccessKey` or `PutUserPolicy`. Attackers use these to grant themselves
persistence and elevated permissions after an initial foothold.

## Investigate
1. Identify the acting principal and confirm it was authorised to change IAM.
2. Review exactly what was granted — an inline or managed policy with `*:*` is a red flag.
3. Check for newly created users or access keys that no one recognises.

```bash
aws iam get-account-authorization-details --filter User Role
aws iam list-access-keys --user-name <suspect-user>
```

## Remediate
1. If unauthorised, revert the change immediately (detach the policy, delete the user/key).
2. Rotate the credentials of the principal that made the change.
3. Add a CloudWatch/EventBridge alarm on sensitive IAM API calls.
4. Apply least privilege and require approvals for IAM changes via change management.

## Common false positives
- Legitimate onboarding/offboarding handled by an admin or IaC pipeline.
- Terraform/CloudFormation applying reviewed IAM changes.