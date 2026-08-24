# CloudTrail Logging Disabled

**Detection key:** `critical_events`
**MITRE ATT&CK:** [T1562 — Impair Defenses](https://attack.mitre.org/techniques/T1562/)
**Default severity:** Critical — this is often an attacker covering their tracks.

## What triggered this
Audit-tampering events were seen: `StopLogging`, `DeleteTrail`, `DeleteFlowLogs` or
`UpdateTrail` weakening coverage. Disabling logging blinds the defenders and usually
precedes or hides malicious activity.

## Investigate
1. **Immediately** confirm whether logging is currently on or off.
2. Identify the principal that disabled it and whether the change was authorised.
3. Determine the blind window — what happened between the stop and now.

```bash
aws cloudtrail get-trail-status --name <trail-name>
aws cloudtrail describe-trails
```

## Remediate
1. Re-enable logging now (`aws cloudtrail start-logging --name <trail-name>`).
2. Treat this as an active incident and escalate to the security team.
3. Rotate the acting principal's credentials; assume compromise until proven otherwise.
4. Protect the trail with SCPs and enable log file validation + S3 object-lock.

## Common false positives
- A planned trail migration or reconfiguration by your platform team.
- IaC recreating a trail (delete + create) during a controlled change.