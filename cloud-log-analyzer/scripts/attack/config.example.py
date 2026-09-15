# scripts/attack/config.example.py
#
# Copy this to config.py and fill in YOUR sandbox values.
# config.py is gitignored — never commit real account IDs / ARNs.
#
#   cp config.example.py config.py
#
# Resource names below are used BOTH to create resources (phases 1-5) AND
# to find and delete them (teardown.py). Keep them as-is unless you know
# you need to change them — teardown.py relies on these exact names.

# AWS CLI profile that plays the attacker (its access keys).
PROFILE = "attacker"

# Your sandbox account id (12 digits). Keep the real one out of Git.
ACCOUNT_ID = "123456789012"

REGION = "us-east-1"

# ── Victim identities (created by setup_victim_users.py) ──────
VICTIM_USERS = ["alice", "bob", "charlie"]

# ── Phase 2 — Privilege escalation ─────────────────────────────
# Disposable IAM user the attacker creates as a backdoor.
BACKDOOR_USER = "backdoor-svc"
BACKDOOR_POLICY_ARN = "arn:aws:iam::aws:policy/ReadOnlyAccess"

# ── Phase 3 — S3 exfiltration ───────────────────────────────────
EXFIL_BUCKET = "voldi-lab-exfil-demo"   # must be globally unique — edit it
EXFIL_OBJECT_COUNT = 8

# ── Phase 4 — Role chaining ─────────────────────────────────────
# Roles to chain in order (least -> most privileged), created in the sandbox.
ROLE_ARNS = [
    f"arn:aws:iam::{ACCOUNT_ID}:role/lab-hop-role-1",
    f"arn:aws:iam::{ACCOUNT_ID}:role/lab-hop-role-2",
    f"arn:aws:iam::{ACCOUNT_ID}:role/lab-hop-role-3",
]

# ── Phase 5 — Covering tracks ───────────────────────────────────
TRAIL_NAME = "log-analyzer-trail"