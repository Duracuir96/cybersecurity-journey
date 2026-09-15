# scripts/attack/setup_victim_users.py
#
# Creates disposable "victim" IAM users (config.VICTIM_USERS) for the
# brute-force / enumeration scenario: console login enabled, NO access
# keys, NO permissions — pure targets, not actors.
#
# LAB ONLY. Run with an ADMIN profile (not the attacker profile) —
# this is setup done by you, the lab owner, not by the simulated attacker.

import secrets
import string

import boto3

try:
    from config import PROFILE, VICTIM_USERS
except ImportError:
    PROFILE = "default"
    VICTIM_USERS = ["alice", "bob", "charlie"]


def _random_password(length=16):
    """Generates a password meeting AWS's default complexity requirements."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        pw = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in pw) and any(c.isupper() for c in pw)
                and any(c.isdigit() for c in pw)):
            return pw


def setup_victim_users(profile_name=PROFILE, usernames=VICTIM_USERS):
    session = boto3.Session(profile_name=profile_name)
    iam = session.client("iam")
    sts = session.client("sts")

    account_id = sts.get_caller_identity()["Account"]
    print(f"[*] Target account: {account_id} (profile: {profile_name})")
    confirm = input("[?] Is this your SANDBOX account? Type 'yes': ")
    if confirm.strip().lower() != "yes":
        print("[-] Aborted.")
        return

    created = {}

    for user in usernames:
        print(f"\n----- {user} -----")

        try:
            iam.get_user(UserName=user)
            print(f"[!] User '{user}' already exists — skipping.")
            continue
        except iam.exceptions.NoSuchEntityException:
            pass

        iam.create_user(UserName=user)
        print(f"[+] Created user: {user}")

        password = _random_password()
        iam.create_login_profile(
            UserName=user,
            Password=password,
            PasswordResetRequired=False,
        )
        print(f"[+] Console login enabled for: {user}")
        created[user] = password
        # Intentionally: no create_access_key, no attach_user_policy.

    print("\n" + "=" * 50)
    print(f"DONE. Sign-in URL:")
    print(f"  https://{account_id}.signin.aws.amazon.com/console")
    print("\nCredentials (save them now — shown once):")
    for user, pw in created.items():
        print(f"  {user} : {pw}")
    print("=" * 50)
    print("[i] These users have NO keys and NO permissions — pure targets.")
    print("[i] Remember to run teardown.py after your demo.")


if __name__ == "__main__":
    setup_victim_users()