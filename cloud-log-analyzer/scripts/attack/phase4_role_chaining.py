# scripts/attack/phase4_role_chaining.py
#
# Phase 4 — Role chaining (progressive privilege escalation via AssumeRole).
# LAB ONLY. Mirrors: phase4_role_chaining.sh
# Exercises: detect_role_chaining()
#
# Requires ROLE_ARNS in config.py to already exist in the sandbox, with a
# trust policy allowing the attacker identity (or the previous role in the
# chain) to assume them.

import boto3

try:
    from config import PROFILE, ROLE_ARNS
except ImportError:
    PROFILE = "attacker"
    ROLE_ARNS = []


def run_role_chaining(profile_name=PROFILE, role_arns=ROLE_ARNS):
    """
    Simulates progressive privilege escalation: assume role A, use its
    credentials to assume role B, then role C — each hop = one AssumeRole
    CloudTrail event for the same identity.
    """
    if not role_arns:
        print("[!] No ROLE_ARNS configured in config.py — nothing to do.")
        print("    Create 2-3 sandbox roles and list their ARNs first.")
        return

    print(f"[*] Phase 4 — Role Chaining ({len(role_arns)} hops)")

    session = boto3.Session(profile_name=profile_name)
    sts = session.client("sts")

    for i, role_arn in enumerate(role_arns):
        print(f"[*] Hop {i+1}/{len(role_arns)}: AssumeRole {role_arn}")
        creds = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName=f"lab-hop-{i+1}",
        )["Credentials"]
        print(f"[+] Assumed — session key starts with {creds['AccessKeyId'][:8]}...")

        # Chain: the next hop uses THIS role's credentials, not the
        # original attacker identity, to make the escalation progressive.
        sts = boto3.client(
            "sts",
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"],
        )

    print("[+] Phase 4 complete — check CloudTrail in ~5-15 min")
    print("    Expected: detect_role_chaining -> ALERT")


if __name__ == "__main__":
    run_role_chaining()