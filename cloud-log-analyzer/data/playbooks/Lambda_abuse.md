# Lambda Function Tampering

**Detection key:** `lambda_abuse`
**MITRE ATT&CK:** [T1648 — Serverless Execution](https://attack.mitre.org/techniques/T1648/)
**Default severity:** High — modified function code is a stealthy persistence vector.

## What triggered this
Lambda write events were observed: `UpdateFunctionCode`, `UpdateFunctionConfiguration`,
`AddPermission` or `CreateFunction`. Injecting code into a function lets an attacker
run inside a trusted execution role.

## Investigate
1. Review what changed and diff it against the last known-good version.
2. Check the function's execution role — what can it access?
3. Inspect resource-based policy changes from `AddPermission` (public invoke?).

```bash
aws lambda get-function --function-name <fn>
aws lambda get-policy --function-name <fn>
```

## Remediate
1. Roll back to the last known-good version (`aws lambda update-function-code`).
2. Remove any unexpected permission granted via `AddPermission`.
3. Audit all invocations since the change (CloudWatch Logs).
4. Require code review + signing for Lambda deployments.

## Common false positives
- A normal CI/CD deployment updating function code.
- A developer patching configuration (memory, timeout, env vars).