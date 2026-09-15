# scripts/attack/phase1_credential_abuse.py
#
# Phase 1 — Credential abuse (same identity, multiple source IPs).
# LAB ONLY. Mirrors: phase1_credential_abuse.sh
# Exercises: detect_credential_abuse()
#
# NOTE: to actually trigger the detection you need this script to run
# from 2+ DISTINCT IPs with the SAME attacker credentials (e.g. your
# laptop + your phone on 4G, or a VPN). Running it twice from the same
# IP will not produce a second distinct sourceIPAddress in CloudTrail.

import boto3

try:
    from config import PROFILE
except ImportError:
    PROFILE = "attacker"


def run_credential_abuse(profile_name=PROFILE, calls=5):
    """
    Simulates an attacker verifying a (possibly stolen) access key works,
    repeatedly, as the first thing done with a new/compromised credential.
    """
    session = boto3.Session(profile_name=profile_name)
    sts = session.client("sts")

    print(f"[*] Phase 1 — Credential Abuse ({calls}x GetCallerIdentity)")
    print("[!] Run this from a 2nd distinct IP too, to trigger the detection.")

    for i in range(calls):
        identity = sts.get_caller_identity()
        print(f"[+] ({i+1}/{calls}) {identity['Arn']}")

    print("[+] Phase 1 complete — check CloudTrail in ~5-15 min")
    print("    Expected (with 2+ IPs): detect_credential_abuse -> ALERT")


if __name__ == "__main__":
    run_credential_abuse()