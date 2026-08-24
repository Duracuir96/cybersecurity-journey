# S3 Mass Object Download

**Detection key:** `s3_exfiltration`
**MITRE ATT&CK:** [T1530 — Data from Cloud Storage](https://attack.mitre.org/techniques/T1530/)
**Default severity:** High — Critical if the data is sensitive or the bucket was public.

## What triggered this
A single identity performed a high volume of S3 read operations
(`GetObject`, `ListObjects`, `GetBucketAcl`) above the threshold — consistent with
bulk data access or exfiltration.

## Investigate
1. Identify the buckets and objects accessed and whether they hold sensitive data.
2. Review the bucket policy and ACLs — was the bucket public or over-shared?
3. Correlate the source IP and identity with other alerts for the same actor.

```bash
aws s3api get-bucket-policy --bucket <bucket>
aws s3api get-public-access-block --bucket <bucket>
```

## Remediate
1. Restrict the bucket: enable Block Public Access and tighten the policy.
2. Revoke the access used if the download was unauthorised.
3. Enable S3 server access logging / data events for future visibility.
4. Notify the data protection team if PII or secrets were involved.

## Common false positives
- A legitimate backup, migration or analytics job reading many objects.
- A data pipeline or ETL run scheduled by your team.