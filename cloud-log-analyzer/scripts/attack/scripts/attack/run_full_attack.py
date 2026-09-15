# scripts/attack/run_full_attack.py
#
# Orchestrator — runs the full kill chain, phase by phase, with a pause
# between each so CloudTrail events stay distinguishable in the timeline.
#
# Each phase is ALSO runnable on its own (python phaseN_*.py) — this file
# just imports and sequences them. LAB ONLY, see README.md.
#
# Phase 5 (covering tracks) is intentionally LAST — see its own docstring.

import time

from phase0_reconnaissance import run_iam_enumeration
from phase1_credential_abuse import run_credential_abuse
from phase2_privilege_escalation import run_privilege_escalation
from phase3_s3_exfiltration import run_s3_exfiltration
from phase4_role_chaining import run_role_chaining
from phase5_covering_tracks import run_covering_tracks

PAUSE_SECONDS = 15  # gap between phases, for a readable CloudTrail timeline


def run_full_attack():
    phases = [
        ("Phase 0 — Reconnaissance",        run_iam_enumeration),
        ("Phase 1 — Credential Abuse",      run_credential_abuse),
        ("Phase 2 — Privilege Escalation",  run_privilege_escalation),
        ("Phase 3 — S3 Exfiltration",       run_s3_exfiltration),
        ("Phase 4 — Role Chaining",         run_role_chaining),
        ("Phase 5 — Covering Tracks",       run_covering_tracks),
    ]

    print("=" * 60)
    print(" FULL ATTACK SIMULATION — LAB ONLY")
    print("=" * 60)

    for i, (label, fn) in enumerate(phases):
        print(f"\n{'#' * 60}")
        print(f"# {label}")
        print(f"{'#' * 60}")
        fn()

        if i < len(phases) - 1:
            print(f"\n[i] Pausing {PAUSE_SECONDS}s before next phase...")
            time.sleep(PAUSE_SECONDS)

    print("\n" + "=" * 60)
    print(" SCENARIO COMPLETE")
    print(" Wait ~5-15 min for CloudTrail delivery, then open the dashboard.")
    print(" Remember to run: python teardown.py")
    print("=" * 60)


if __name__ == "__main__":
    run_full_attack()