# scripts/attack/phase5_covering_tracks.py
#
# Phase 5 — Covering tracks (log tampering).
# LAB ONLY. Mirrors: phase5_covering_tracks.sh
# Exercises: detect_critical_events(), detect_data_exfiltration()
#
# SAFETY: uses try/finally so CloudTrail logging is ALWAYS re-enabled,
# even if something fails in between. The blind window is a few seconds.
# Run this LAST in a full scenario — nothing after it will be logged
# until start-logging completes.

import time
import boto3

try:
    from config import PROFILE, TRAIL_NAME
except ImportError:
    PROFILE = "attacker"
    TRAIL_NAME = "log-analyzer-trail"


def run_covering_tracks(profile_name=PROFILE, trail_name=TRAIL_NAME,
                        blind_seconds=5):
    """
    Simulates an attacker disabling audit logging to hide their tracks,
    then (safely, for the lab) re-enabling it a few seconds later.
    """
    session = boto3.Session(profile_name=profile_name)
    ct = session.client("cloudtrail")

    print(f"[*] Phase 5 — Covering Tracks (trail: {trail_name})")
    print(f"[!] Logging will be OFF for ~{blind_seconds}s, then restored.")

    try:
        print("[*] StopLogging...")
        ct.stop_logging(Name=trail_name)
        print("[+] Logging stopped (this call itself is NOT logged)")

        time.sleep(blind_seconds)

    finally:
        print("[*] StartLogging (restoring, always runs)...")
        ct.start_logging(Name=trail_name)
        print("[+] Logging restored")

    # This call happens AFTER logging is back on, so it IS captured —
    # it's what the analyzer will actually see and flag.
    status = ct.get_trail_status(Name=trail_name)
    print(f"[+] IsLogging: {status['IsLogging']}")

    print("[+] Phase 5 complete — check CloudTrail in ~5-15 min")
    print("    Expected: detect_critical_events -> ALERT (StopLogging event)")


if __name__ == "__main__":
    run_covering_tracks()