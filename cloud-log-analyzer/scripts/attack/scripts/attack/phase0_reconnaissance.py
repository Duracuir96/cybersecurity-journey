# scripts/attack/phase0_reconnaissance.py
#
# Phase 0 — Reconnaissance (IAM enumeration).
# LAB ONLY. Run on your sandbox account with the attacker profile.
#
# Mirrors: phase0_reconnaissance.sh
# Exercises: detect_iam_enumeration(), count_api_calls_by_ip()

import boto3

try:
    from config import PROFILE
except ImportError:
    PROFILE = "attacker"


def run_iam_enumeration(profile_name=PROFILE):
    """
    Simulates an attacker mapping the environment before acting.
    Emits: GetCallerIdentity, ListUsers, ListRoles, ListPolicies,
           ListGroups, GetAccountAuthorizationDetails.
    """
    session = boto3.Session(profile_name=profile_name)
    iam = session.client("iam")
    sts = session.client("sts")

    print("[*] Phase 0 — IAM Enumeration")

    print("[*] Checking identity (GetCallerIdentity)...")
    identity = sts.get_caller_identity()
    print(f"[+] Identity: {identity['Arn']}")

    print("[*] Enumerating users (ListUsers)...")
    users = iam.list_users()
    print(f"[+] Found {len(users['Users'])} users")

    print("[*] Enumerating roles (ListRoles)...")
    roles = iam.list_roles()
    print(f"[+] Found {len(roles['Roles'])} roles")

    print("[*] Enumerating policies (ListPolicies)...")
    policies = iam.list_policies(Scope="Local")
    print(f"[+] Found {len(policies['Policies'])} local policies")

    print("[*] Enumerating groups (ListGroups)...")
    groups = iam.list_groups()
    print(f"[+] Found {len(groups['Groups'])} groups")

    print("[*] Dumping full IAM config (GetAccountAuthorizationDetails)...")
    details = iam.get_account_authorization_details()
    print(f"[+] Got {len(details['UserDetailList'])} user detail entries")

    print("[+] Phase 0 complete — check CloudTrail in ~5-15 min")
    print("    Expected: detect_iam_enumeration -> ALERT, api_calls_by_ip -> ALERT")


if __name__ == "__main__":
    run_iam_enumeration()