# Unusual EC2 Instance Launch

**Detection key:** `ec2_suspicious`
**MITRE ATT&CK:** [T1578 — Modify Cloud Compute Infrastructure](https://attack.mitre.org/techniques/T1578/)
**Default severity:** High — unexpected compute often means crypto-mining or a backdoor.

## What triggered this
Suspicious EC2 write events were seen: `RunInstances`, `CreateKeyPair`,
`AuthorizeSecurityGroupIngress` or `ModifyInstanceAttribute`. Attackers spin up
instances for mining or to establish persistence.

## Investigate
1. List new instances — region, type, count and who launched them.
2. Check for wide-open Security Group ingress (`0.0.0.0/0` on SSH/RDP).
3. Confirm whether the launch matches a known deployment.

```bash
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"
aws ec2 describe-security-groups
```

## Remediate
1. Terminate unauthorised instances immediately.
2. Revoke overly permissive Security Group rules.
3. Delete any rogue key pair created during the event.
4. Restrict who can call `RunInstances` and in which regions (SCPs / IAM conditions).

## Common false positives
- Auto Scaling launching instances under load.
- A developer or IaC pipeline deploying reviewed infrastructure.