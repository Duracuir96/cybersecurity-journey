# Unauthorized API Calls

**Detection key:** `api_calls_by_ip`
**MITRE ATT&CK:** [T1046 — Network Service Discovery](https://attack.mitre.org/techniques/T1046/)
**Default severity:** Medium — High if paired with errors suggesting probing.

## What triggered this
A single source IP made an abnormally high number of API calls across services,
above the threshold — consistent with automated scanning, credential testing or a
misconfigured client hammering the API.

## Investigate
1. Geolocate the IP and confirm whether it is one of yours.
2. Look at which APIs were called and how many returned `AccessDenied` (probing signal).
3. Check whether one identity or many were used from that IP.

```bash
aws cloudtrail lookup-events --max-results 50
```

## Remediate
1. Block the IP in WAF or Security Groups if external and hostile.
2. If credentials were tested, rotate any that responded successfully.
3. Enable AWS Shield / rate limiting if a DDoS or scan pattern is confirmed.

## Common false positives
- A busy but legitimate application or SDK client.
- Monitoring, backup or automation tools with high call volume.