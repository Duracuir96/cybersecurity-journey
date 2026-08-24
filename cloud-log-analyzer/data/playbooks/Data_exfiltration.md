# Network Data Exfiltration

**Detection key:** `data_exfiltration`
**MITRE ATT&CK:** [T1041 — Exfiltration Over C2 Channel](https://attack.mitre.org/techniques/T1041/)
**Default severity:** High — network changes can open a covert exfiltration path.

## What triggered this
Network-level tampering was seen: `CreateVpcPeeringConnection`, ACL/route changes,
`DeleteFlowLogs` or `StopLogging`. These can route data to an attacker-controlled
account or remove the evidence of it.

## Investigate
1. Check any new VPC peering — to which account is it connected?
2. Review NACL / route-table / security-group changes for newly opened egress.
3. If flow logs were deleted, pull whatever S3 backups or duplicate trails exist.

```bash
aws ec2 describe-vpc-peering-connections
aws ec2 describe-flow-logs
```

## Remediate
1. Remove unauthorised peering connections and revert routing changes.
2. Re-enable VPC Flow Logs.
3. Isolate the affected VPC if active exfiltration is suspected.
4. Engage the incident response team immediately.

## Common false positives
- A planned network change (new peering, VPN) by the platform team.
- IaC reconfiguring routing during a controlled deployment.